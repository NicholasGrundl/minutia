#!/usr/bin/env python3
"""
Generate test fixtures by extracting clips from specific MKV recordings.

This script provides methods to create test artifacts from named MKV files:
- Extract video clips of specified duration
- Generate audio tracks from clips  
- Create transcripts and other pipeline artifacts
- Store metadata about fixture characteristics

The diversity (clear speech, noisy, overlapping, etc.) comes from selecting
different source MKV files, not from processing variations.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import ffmpeg

from minutia.logging import logger
from minutia.steps.video_extraction import get_video_info, extract_all_audio_tracks


class FixtureGenerator:
    """Generate test fixtures from specific MKV recordings."""
    
    def __init__(self, recordings_dir: Path, output_dir: Path):
        self.recordings_dir = recordings_dir
        self.output_dir = output_dir
        self.fixtures_dir = output_dir / "fixtures"
        self.video_dir = self.fixtures_dir / "video"
        self.audio_dir = self.fixtures_dir / "audio"
        self.metadata_file = self.fixtures_dir / "fixture_metadata.json"
        
        # Ensure directories exist
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
    def list_available_recordings(self) -> list[Path]:
        """List all MKV files available for fixture generation."""
        mkv_files = list(self.recordings_dir.glob("**/*.mkv"))
        logger.info("Found {} MKV recordings in {}", len(mkv_files), self.recordings_dir)
        for mkv in mkv_files:
            logger.info("  - {}", mkv.relative_to(self.recordings_dir))
        return mkv_files
        
    def create_video_clip(
        self, 
        source_mkv: str,
        output_name: str, 
        start_seconds: float | None,
        duration_seconds: float | None
    ) -> Path:
        """
        Extract a video clip from the specified MKV file.
        
        Args:
            source_mkv: Name of source file (relative to recordings_dir)
            output_name: Name for output fixture (without extension)
            start_seconds: Start time in source video
            duration_seconds: Duration of clip to extract
            
        Returns:
            Path to created fixture file
        """
        source_path = self.recordings_dir / source_mkv
        if not source_path.exists():
            raise FileNotFoundError(f"Source MKV not found: {source_path}")
            
        output_path = self.video_dir / f"{output_name}.mkv"
        
        if start_seconds is None:
            start_seconds = 0.0
        
        # Validate source has sufficient duration
        probe = ffmpeg.probe(str(source_path))
        source_duration = float(probe["format"]["duration"])
        if duration_seconds is None:
            duration_seconds = source_duration

        logger.info("Creating video clip: {} -> {} ({:.1f}s @ {:.1f}s)", 
                   source_mkv, output_name, duration_seconds, start_seconds)
    
        if start_seconds + duration_seconds > source_duration:
            raise ValueError(
                f"Requested clip ({start_seconds:.1f}s + {duration_seconds:.1f}s = "
                f"{start_seconds + duration_seconds:.1f}s) exceeds source duration "
                f"({source_duration:.1f}s)"
            )
        
        # Extract clip using ffmpeg
        try:
            (
                ffmpeg
                .input(str(source_path), ss=start_seconds, t=duration_seconds)
                .output(str(output_path), vcodec="copy", acodec="copy")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            logger.error("FFmpeg error creating {}: {}", output_name, e.stderr.decode())
            raise
            
        # Validate created clip
        clip_info = self._validate_video_clip(output_path)
        
        logger.info("Created video fixture: {} ({:.1f}s, {} audio tracks)", 
                   output_name, clip_info["duration"], len(clip_info["audio_tracks"]))
        
        return output_path
        
    def extract_audio_from_clip(self, video_clip_path: Path) -> list[Path]:
        """
        Extract all audio tracks from a video clip fixture.
        
        Args:
            video_clip_path: Path to video clip fixture
            
        Returns:
            List of paths to extracted audio files
        """
        clip_name = video_clip_path.stem
        audio_output_dir = self.audio_dir / clip_name
        
        logger.info("Extracting audio tracks from {}", video_clip_path.name)
        
        # Use existing video extraction functionality
        audio_files = list(extract_all_audio_tracks(video_clip_path, audio_output_dir))
        
        logger.info("Extracted {} audio tracks to {}", len(audio_files), audio_output_dir)
        
        return audio_files
        
    def create_fixture_set(
        self,
        source_mkv: str,
        output_name: str,
        start_seconds: float, 
        duration_seconds: float,
        description: str = ""
    ) -> dict[str, Any]:
        """
        Create a complete fixture set: video clip + audio tracks + metadata.
        
        Args:
            source_mkv: Name of source file (relative to recordings_dir)
            output_name: Name for output fixture
            start_seconds: Start time in source video
            duration_seconds: Duration of clip
            description: Human-readable description of fixture characteristics
            
        Returns:
            Metadata dictionary for the created fixture set
        """
        logger.info("Creating fixture set '{}' from {}", output_name, source_mkv)
        
        # Create video clip
        video_path = self.create_video_clip(source_mkv, output_name, start_seconds, duration_seconds)
        
        # Extract audio tracks
        audio_paths = self.extract_audio_from_clip(video_path)
        
        # Validate fixture properties
        clip_info = self._validate_video_clip(video_path)
        
        # Build metadata
        metadata = {
            "name": output_name,
            "description": description,
            "source": {
                "mkv_file": source_mkv,
                "start_seconds": start_seconds,
                "duration_seconds": duration_seconds
            },
            "artifacts": {
                "video_clip": str(video_path.relative_to(self.output_dir)),
                "audio_files": [str(p.relative_to(self.output_dir)) for p in audio_paths]
            },
            "properties": {
                "actual_duration": clip_info["duration"],
                "audio_tracks": clip_info["audio_tracks"],
                "video_codec": clip_info["video_codec"]
            }
        }
        
        logger.info("Created fixture set '{}' with {} audio tracks", 
                   output_name, len(audio_paths))
        
        return metadata
        
    def _validate_video_clip(self, clip_path: Path) -> dict[str, Any]:
        """Validate video clip has required properties for testing."""
        try:
            # Get detailed info
            video_info = get_video_info(clip_path)
            audio_streams = video_info["audio_streams"]
            
            if len(audio_streams) < 2:
                raise ValueError(
                    f"Clip {clip_path} has only {len(audio_streams)} audio tracks, "
                    f"need at least 2 for pipeline testing"
                )
            
            # Get duration and other properties
            probe = ffmpeg.probe(str(clip_path))
            duration = float(probe["format"]["duration"])
            
            # Build track info
            track_info = []
            for i, stream in enumerate(audio_streams):
                track_info.append({
                    "track_number": i + 1,
                    "codec": stream.get("codec_name", "unknown"),
                    "sample_rate": stream.get("sample_rate", "unknown"),
                    "channels": stream.get("channels", "unknown")
                })
            
            return {
                "duration": duration,
                "audio_tracks": track_info,
                "video_codec": video_info["video"].get("codec_name", "unknown")
            }
            
        except Exception as e:
            logger.error("Failed to validate clip {}: {}", clip_path, e)
            raise
            
    def save_metadata(self, fixtures_metadata: list[dict[str, Any]]) -> None:
        """Save all fixture metadata to JSON file."""
        metadata = {
            "generated_by": "tests/scripts/generate_test_fixtures.py",
            "recordings_source": str(self.recordings_dir),
            "total_fixtures": len(fixtures_metadata),
            "fixtures": fixtures_metadata
        }
        
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Saved metadata for {} fixtures to {}", 
                   len(fixtures_metadata), self.metadata_file)


def main():
    """Main entry point - can be used interactively or with predefined fixture sets."""
    parser = argparse.ArgumentParser(description="Generate test fixtures from specific MKV recordings")
    parser.add_argument(
        "--recordings-dir",
        type=Path,
        default=Path("+recordings"),
        help="Directory containing source MKV recordings"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=Path("tests"),
        help="Output directory for test fixtures"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available MKV recordings and exit"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not args.recordings_dir.exists():
        logger.error("Recordings directory does not exist: {}", args.recordings_dir)
        return 1
        
    generator = FixtureGenerator(args.recordings_dir, args.output_dir)
    
    if args.list:
        generator.list_available_recordings()
        return 0
    
    # Example usage - create a few sample fixtures
    # In practice, these would be customized based on available recordings
    try:
        fixtures_metadata = []
        
        # Get available recordings
        available = generator.list_available_recordings()
        if not available:
            logger.error("No MKV recordings found")
            return 1
            
        # Example: Create fixture from first available recording
        first_recording = available[0].relative_to(args.recordings_dir)
        
        logger.info("Creating example fixture from {}", first_recording)
        metadata = generator.create_fixture_set(
            source_mkv=str(first_recording),
            output_name="example_10s",
            start_seconds=30.0,  # Skip first 30s to avoid intro/silence
            duration_seconds=10.0,
            description="Example 10-second clip for basic testing"
        )
        fixtures_metadata.append(metadata)
        
        # Save metadata
        generator.save_metadata(fixtures_metadata)
        
        logger.info("Fixture generation completed successfully")
        logger.info("To create specific fixtures, use the FixtureGenerator class methods")
        
        return 0
        
    except Exception as e:
        logger.error("Fixture generation failed: {}", e)
        return 1


if __name__ == "__main__":
    exit(main())