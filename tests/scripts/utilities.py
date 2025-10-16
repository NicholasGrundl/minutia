"""
Utilities for test fixture generation using python-ffmpeg wrapper.

This module provides helper functions for creating test fixtures without
importing minutia modules, avoiding circular dependencies.
"""

import json
from pathlib import Path
from typing import Any

import ffmpeg


def get_video_info(file_path: Path) -> Dict[str, Any]:
    """Get video information using ffmpeg probe."""
    probe = ffmpeg.probe(str(file_path))
    video_streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
    audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    
    return {
        "format": probe["format"],
        "video_streams": video_streams,
        "audio_streams": audio_streams,
        "duration": float(probe["format"]["duration"]),
        "size_bytes": int(probe["format"]["size"])
    }


def extract_video_clip(
    source_file: Path, 
    output_file: Path, 
    start_seconds: float = 0.0, 
    duration_seconds: float = None
) -> bool:
    """
    Extract a video clip using python-ffmpeg.
    
    Args:
        source_file: Source MKV file
        output_file: Output clip file
        start_seconds: Start time in seconds
        duration_seconds: Duration in seconds (None = entire file)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get source info
        source_info = get_video_info(source_file)
        source_duration = source_info["duration"]
        
        if duration_seconds is None:
            duration_seconds = source_duration - start_seconds
            
        # Validate clip bounds
        if start_seconds + duration_seconds > source_duration:
            print(f"⚠ Warning: Requested clip ({start_seconds:.1f}s + {duration_seconds:.1f}s = "
                  f"{start_seconds + duration_seconds:.1f}s) exceeds source duration ({source_duration:.1f}s)")
            duration_seconds = source_duration - start_seconds
            
        print(f"Creating clip: {start_seconds:.1f}s -> {start_seconds + duration_seconds:.1f}s "
              f"({duration_seconds:.1f}s duration)")
        
        # Create clip
        input_stream = ffmpeg.input(str(source_file), ss=start_seconds, t=duration_seconds)
        output = ffmpeg.output(input_stream, str(output_file), vcodec="copy", acodec="copy")
        ffmpeg.run(output, capture_stdout=True, capture_stderr=True, overwrite_output=True)
        
        return True
        
    except ffmpeg.Error as e:
        print(f"✗ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error creating clip: {e}")
        return False


def extract_all_audio_tracks(video_file: Path, output_dir: Path) -> List[Path]:
    """
    Extract all audio tracks from a video file.
    
    Args:
        video_file: Source video file
        output_dir: Directory to save audio tracks
        
    Returns:
        List of paths to extracted audio files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get audio stream info
        video_info = get_video_info(video_file)
        audio_streams = video_info["audio_streams"]
        
        if not audio_streams:
            print(f"⚠ No audio streams found in {video_file.name}")
            return []
            
        print(f"Found {len(audio_streams)} audio tracks in {video_file.name}")
        
        extracted_files = []
        
        # Extract each audio track
        for i, stream in enumerate(audio_streams):
            track_num = i + 1  # 1-indexed track numbers
            output_name = f"{video_file.stem}_track_{track_num}.wav"
            output_path = output_dir / output_name
            
            # Extract specific audio stream
            input_stream = ffmpeg.input(str(video_file))
            audio = input_stream[f"a:{i}"]  # Select audio stream by index
            output = ffmpeg.output(audio, str(output_path), acodec="pcm_s16le")
            
            try:
                ffmpeg.run(output, capture_stdout=True, capture_stderr=True, overwrite_output=True)
                extracted_files.append(output_path)
                
                # Get stream details for logging
                codec = stream.get("codec_name", "unknown")
                channels = stream.get("channels", "unknown")
                sample_rate = stream.get("sample_rate", "unknown")
                
                print(f"  ✓ Track {track_num}: {output_name} ({codec}, {channels}ch, {sample_rate}Hz)")
                
            except ffmpeg.Error as e:
                print(f"  ✗ Failed to extract track {track_num}: {e.stderr.decode() if e.stderr else str(e)}")
                
        return extracted_files
        
    except Exception as e:
        print(f"✗ Error extracting audio from {video_file.name}: {e}")
        return []


def list_mkv_recordings(recordings_dir: Path) -> List[Path]:
    """
    List all MKV files in recordings directory with metadata.
    
    Args:
        recordings_dir: Directory containing MKV recordings
        
    Returns:
        List of MKV file paths
    """
    mkv_files = list(recordings_dir.glob("*.mkv"))
    
    print(f"Found {len(mkv_files)} MKV recordings in {recordings_dir}:")
    
    for mkv in sorted(mkv_files):
        try:
            info = get_video_info(mkv)
            size_mb = mkv.stat().st_size / (1024 * 1024)
            audio_count = len(info["audio_streams"])
            duration = info["duration"]
            
            print(f"  - {mkv.name}")
            print(f"    Duration: {duration:.1f}s, Size: {size_mb:.1f}MB, Audio tracks: {audio_count}")
            
        except Exception as e:
            print(f"  - {mkv.name} (error reading metadata: {e})")
            
    return mkv_files


def validate_video_clip(clip_path: Path) -> Dict[str, Any]:
    """
    Validate a video clip and return metadata.
    
    Args:
        clip_path: Path to video clip
        
    Returns:
        Dictionary with validation results and metadata
    """
    try:
        info = get_video_info(clip_path)
        
        # Basic validation
        if len(info["audio_streams"]) < 2:
            print(f"⚠ Warning: {clip_path.name} has only {len(info['audio_streams'])} audio track(s)")
            
        if info["duration"] < 1.0:
            print(f"⚠ Warning: {clip_path.name} is very short ({info['duration']:.1f}s)")
            
        return {
            "valid": True,
            "duration": info["duration"],
            "audio_tracks": len(info["audio_streams"]),
            "video_codec": info["video_streams"][0].get("codec_name", "unknown") if info["video_streams"] else None,
            "size_mb": clip_path.stat().st_size / (1024 * 1024)
        }
        
    except Exception as e:
        print(f"✗ Error validating {clip_path.name}: {e}")
        return {
            "valid": False,
            "error": str(e)
        }


def save_fixture_metadata(fixtures_dir: Path, metadata: Dict[str, Any]) -> Path:
    """
    Save fixture metadata to JSON file.
    
    Args:
        fixtures_dir: Directory containing fixtures
        metadata: Metadata dictionary
        
    Returns:
        Path to saved metadata file
    """
    metadata_file = fixtures_dir / "fixture_metadata.json"
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"📋 Metadata saved to {metadata_file}")
    return metadata_file


def create_test_fixture(
    source_mkv: Path,
    output_name: str,
    fixtures_dir: Path,
    start_seconds: float = 0.0,
    duration_seconds: float = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a complete test fixture: video clip + audio tracks + metadata.
    
    Args:
        source_mkv: Source MKV file
        output_name: Name for the fixture (without extension)
        fixtures_dir: Base fixtures directory
        start_seconds: Start time in source video
        duration_seconds: Duration of clip (None = entire file)
        description: Description of the fixture
        
    Returns:
        Metadata dictionary for the created fixture
    """
    video_dir = fixtures_dir / "video"
    audio_dir = fixtures_dir / "audio"
    
    # Create directories
    video_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"Creating fixture: {output_name}")
    print(f"Source: {source_mkv.name}")
    print(f"{'='*50}")
    
    # 1. Create video clip
    video_clip_path = video_dir / f"{output_name}.mkv"
    success = extract_video_clip(source_mkv, video_clip_path, start_seconds, duration_seconds)
    
    if not success:
        return {"error": f"Failed to create video clip for {output_name}"}
    
    # 2. Extract audio tracks
    audio_output_dir = audio_dir / output_name
    audio_files = extract_all_audio_tracks(video_clip_path, audio_output_dir)
    
    # 3. Validate clip
    validation = validate_video_clip(video_clip_path)
    
    # 4. Build metadata
    metadata = {
        "name": output_name,
        "description": description,
        "source": {
            "mkv_file": source_mkv.name,
            "start_seconds": start_seconds,
            "duration_seconds": duration_seconds
        },
        "artifacts": {
            "video_clip": str(video_clip_path.relative_to(fixtures_dir)),
            "audio_files": [str(af.relative_to(fixtures_dir)) for af in audio_files]
        },
        "validation": validation,
        "created_files_count": len(audio_files) + 1  # +1 for video clip
    }
    
    print(f"✅ Fixture '{output_name}' created successfully")
    print(f"   Video: {video_clip_path.name}")
    print(f"   Audio: {len(audio_files)} tracks in {audio_output_dir.name}/")
    
    return metadata