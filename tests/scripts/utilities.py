"""
Utilities for test fixture generation and complete pipeline execution.

This module provides helper functions for creating test fixtures and running
complete pipeline workflows without importing minutia modules directly,
avoiding circular dependencies during test setup.
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import ffmpeg
import isodate


# =============================================================================
# DateTime and Metadata Utilities
# =============================================================================

def get_isodatetime() -> str:
    """Get the current time as an ISO datetime string."""
    current = datetime.datetime.now(tz=datetime.timezone.utc)
    iso_value = isodate.datetime_isoformat(current)
    return iso_value

def get_isodate() -> str:
    """Get the current date as an ISO date string."""
    current = datetime.datetime.now(tz=datetime.timezone.utc)
    iso_value = isodate.date_isoformat(current)
    return iso_value

def create_scenario_metadata(
    scenario_name: str,
    description: str,
    characteristics: List[str],
    pipeline_parameters: Dict[str, Any],
    original_source: str = ""
) -> Dict[str, Any]:
    """Create metadata structure for a test scenario."""
    return {
        "scenario_name": scenario_name,
        "description": description,
        "characteristics": characteristics,
        "source_file": "input.mkv",
        "pipeline_parameters": pipeline_parameters,
        "stages": {
            "01_extracted": {
                "description": "FFmpeg audio extraction outputs",
                "files": [
                    "audio_track_1.wav",
                    "audio_track_2.wav", 
                    "audio_track_3.wav",
                    "microphone_audio.wav",
                    "desktop_audio.wav"
                ]
            },
            "02_transcribed": {
                "description": "Whisper transcription outputs",
                "files": [
                    "microphone-whisper-medium.en_transcription.json",
                    "desktop-whisper-medium.en_transcription.json"
                ]
            },
            "03_merged": {
                "description": "Chronologically merged transcript",
                "files": ["merged_transcript.json"]
            },
            "04_summarized": {
                "description": "AI-generated meeting summary", 
                "files": ["*.md"]  # Will be filled with actual filename
            }
        },
        "generated_at": get_isodatetime(),
        "original_source": original_source
    }

def save_scenario_metadata(scenario_dir: Path, metadata: Dict[str, Any]) -> Path:
    """Save scenario metadata to JSON file."""
    metadata_file = scenario_dir / "metadata.json"
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"📋 Scenario metadata saved to {metadata_file}")
    return metadata_file


# =============================================================================
# Video and Audio Processing Utilities  
# =============================================================================

def get_video_info(file_path: Path) -> dict[str, Any]:
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


def extract_all_audio_tracks(video_file: Path, output_dir: Path) -> list[Path]:
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


def list_mkv_recordings(recordings_dir: Path) -> list[Path]:
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


def validate_video_clip(clip_path: Path) -> dict[str, Any]:
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


def save_fixture_metadata(fixtures_dir: Path, metadata: dict[str, Any]) -> Path:
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
) -> dict[str, Any]:
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


# =============================================================================
# Pipeline Execution Utilities
# =============================================================================

def setup_directories(output_dir: Path, recording_dir: Path) -> tuple[Path, Path, List[Path]]:
    """Set up output directory and discover MKV recordings."""
    # Setup Output Directory
    print(f"Output dir: {output_dir.resolve()}")
    if output_dir.exists() is False:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"    Created output dir")
    print(f"    '{output_dir.resolve()}'")
    
    # Analyze Recordings directory
    print(f"Recording dir: {recording_dir.resolve()}")
    mkv_filepaths = list(recording_dir.glob("*.mkv"))
    if len(mkv_filepaths) == 0:
        print(f"❌ No *.mkv files found in '{recording_dir.resolve()}'")
        return output_dir, recording_dir, []
    else:
        print(f"Found {len(mkv_filepaths)} *.mkv files:")
        for p in mkv_filepaths:
            print(f"   '../{recording_dir.stem}/{str(p.name)}'")
    
    return output_dir, recording_dir, mkv_filepaths

def select_recording_file(recording_dir: Path, preferred_name: Optional[str] = None) -> Optional[Path]:
    """Select a recording file from available MKV files."""
    mkv_filepaths = list(recording_dir.glob("*.mkv"))
    
    if len(mkv_filepaths) == 0:
        print("❌ No recording file selected and no files found.")
        return None
    
    if preferred_name:
        recording_filepath = recording_dir / preferred_name
        if recording_filepath in mkv_filepaths:
            print(f"Selected *.mkv File:")
            print(f"    '../{recording_dir.stem}/{recording_filepath.name}'")
            return recording_filepath
    
    # Default to first found
    recording_filepath = mkv_filepaths[0]
    print(f"Could not find preferred file, defaulting to first found:")
    print(f"    '../{recording_dir.stem}/{recording_filepath.name}'")
    return recording_filepath

def create_scenario_directories(fixtures_dir: Path, scenario_name: str) -> Path:
    """Create the full directory structure for a scenario."""
    scenario_dir = fixtures_dir / "scenarios" / scenario_name
    
    # Create stage directories
    stage_dirs = ["01_extracted", "02_transcribed", "03_merged", "04_summarized"]
    for stage_dir in stage_dirs:
        (scenario_dir / stage_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created scenario directories for '{scenario_name}'")
    return scenario_dir

def organize_outputs_to_scenario(output_dir: Path, scenario_dir: Path, input_mkv: Path):
    """Organize pipeline outputs into scenario-based structure."""
    # Copy input video
    input_dest = scenario_dir / "input.mkv"
    if input_mkv.exists():
        import shutil
        shutil.copy2(input_mkv, input_dest)
        print(f"📁 Copied input: {input_mkv.name} -> input.mkv")
    
    # Organize outputs by stage
    file_mappings = {
        "01_extracted": [
            "audio_track_1.wav", "audio_track_2.wav", "audio_track_3.wav",
            "microphone_audio.wav", "desktop_audio.wav"
        ],
        "02_transcribed": [
            "*transcription.json"
        ],
        "03_merged": [
            "merged_transcript.json"
        ],
        "04_summarized": [
            "*summary.md"
        ]
    }
    
    import shutil
    for stage, patterns in file_mappings.items():
        stage_dir = scenario_dir / stage
        for pattern in patterns:
            if "*" in pattern:
                # Handle glob patterns
                for file_path in output_dir.glob(pattern):
                    if file_path.is_file():
                        dest = stage_dir / file_path.name
                        shutil.copy2(file_path, dest)
                        print(f"📁 Moved: {file_path.name} -> {stage}/{file_path.name}")
            else:
                # Handle exact filenames
                file_path = output_dir / pattern
                if file_path.exists():
                    dest = stage_dir / pattern
                    shutil.copy2(file_path, dest)
                    print(f"📁 Moved: {pattern} -> {stage}/{pattern}")

def get_filename_prompt(content: str) -> str:
    """Generate prompt for getting a good filename from content."""
    current_date = get_isodate()
    prompt = f"""Please read the <content> completely and provide a filename that can be used to write the file to disk as a markdown. The filename should be concise but also descriptive so its clear what the content contains.

    <filenamerules>
    - only use lowercase letters, numbers, and underscores or dashes
    - prefer underscores where possible as they are operating system independent
    - make the filename convenient for all operating systems (windows, macOS, linux)
    - include the current date in the filename as YYYMMDD (e.g. July 4th , 2024 would be 20240704)
    - include a concise but descriptive name related to the <content>
    - keep the filename as short as possible while containing a useful name and date
    - DONOT include the suffix of the filename and make sure their are no period characters in the filename
    - the current date is {current_date}
    </filenamerules>

    <content>
    {content}
    </content>

    remember ONLY return the filename as a string and follow the <filenamerules>
    """
    return prompt

def create_markdown_report(content: str, output_path: Path, model_name: str = 'claude-3-5-sonnet') -> Path:
    """Create markdown report with AI-generated filename."""
    # Note: This would require anthropic client, so we'll use a simple fallback
    # In the actual script, this would call the AI model
    timestamp = get_isodate().replace("-", "")
    filename = f"{timestamp}_meeting_summary"
    filepath = output_path / f"{filename}.md"
    
    print(f"Writing markdown file to {filepath}")
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
    return filepath


# =============================================================================
# Pipeline Workflow Functions
# =============================================================================

def generate_meeting_summary_prompt(markdown_notes: str = "", personal_info: str = "") -> str:
    """Generate the system prompt for meeting summarization."""
    prompt = f"""# 🧙‍♂️ Comprehensive and Detailed Meeting Insight Generator

#CONTEXT: Your task is to create a thorough and detailed summary of a meeting transcript. The summary should be comprehensive, capturing the nuances of discussions, technical details, and decisions made. The target audience may not have been present at the meeting but requires an in-depth understanding of the topics discussed.

#ROLE: You are an expert meeting analyst and technical communicator with a keen eye for detail. Your goal is to distill complex discussions into a structured, informative summary that provides significant value to both attendees and non-attendees.

#RESPONSE GUIDELINES:
1. Begin with an executive summary (who, what, where, when) that provides a high-level overview of the meeting's key points.
2. Analyze the transcript and determine the appropriate number of major topics discussed. Create a numbered list of these topics.
3. For each major topic:
   a. Create a detailed heading
   b. Provide an in-depth expansion on technical content, quoting relevant parts of the transcript where appropriate
   c. Describe existing or proposed projects/efforts in detail
   d. Outline decisions made, including the reasoning behind them
   e. Specify timelines and next steps
   f. Integrate relevant personal notes, highlighting them distinctly
   g. Analyze potential implications or impacts of the discussed items
4. Review and add any additional relevant information, including context from your knowledge base if applicable
5. Conclude with a comprehensive list of action items, responsibilities, and overall meeting outcomes
6. Create a section specifically addressing personal notes not covered in the main topics, explaining their context and importance

#TASK CRITERIA:
- Use markdown formatting for headers, lists, and emphasis
- Aim for a highly detailed summary, typically 3-6 pages of content
- Focus on technical accuracy and clarity, providing examples or elaborations where necessary
- Ensure the summary is self-contained and understandable without additional context
- Highlight personal notes using blockquotes and the 📝 emoji
- Prioritize addressing all personal notes, ensuring they are contextually integrated
- The number of major topics should be determined based on the meeting's content and complexity
- Use code blocks for any technical snippets or data presented in the meeting

#INFORMATION ABOUT ME: 
{personal_info}

#PERSONAL NOTES:
{markdown_notes}

#OUTPUT:
Provide the detailed comprehensive summary in the following structure:

## Executive Summary

[Comprehensive overview, including high-priority personal notes and key decisions]

## Major Topics Discussed

1. [Topic 1]
2. [Topic 2]
3. [Topic 3]
... (continue as needed based on the meeting's content)

## Detailed Discussion

### [Topic 1]

[In-depth technical details, projects, decisions, timelines, and analysis]

> 📝 Personal Note: [Relevant personal note integrated and highlighted]
> * [Related bullet point with additional context]
> * [Related bullet point with additional context]

[Additional content addressing the personal note, including potential implications]

[Relevant quotes from the transcript]

### [Topic 2]

[Same structure as Topic 1, with different content]

... (continue for all identified topics)

## Additional Notes and Context

[Any relevant information not covered in the main sections, including personal notes that didn't fit elsewhere and additional context from your knowledge base]

## Action Items and Conclusion

[Comprehensive list of action items, responsibilities, deadlines, and overall meeting outcomes]

## Personal Notes Summary

[A detailed section addressing any remaining personal notes that weren't integrated into the main summary, explaining their context, importance, and potential future implications]

Please summarize the meeting transcript based on the instructions given above, integrating and highlighting the provided personal notes throughout the summary. Ensure that the summary is as detailed and comprehensive as possible, capturing the full essence of the meeting discussions.

If the summary exceeds the token limit, please end your response with '[CONTINUE]' and I will prompt you to continue in a new message.
"""
    return prompt

def extract_transcript_text(transcript_data: Dict[str, Any]) -> str:
    """
    Extract text from the JSON transcript, combine it into a single string,
    including speaker and timestamp, and ensuring chronological order.
    """
    transcript_entries = transcript_data["transcript"]
    # Sort entries by start_time to ensure chronological order
    sorted_entries = sorted(transcript_entries, key=lambda x: x["start_time"])

    formatted_lines = []
    for entry in sorted_entries:
        speaker = entry["source"].capitalize()
        start_time = f"{entry['start_time']:.2f}"
        text = entry["text"].strip()
        formatted_line = f"[{speaker} {start_time}] {text}"
        formatted_lines.append(formatted_line)

    return "\n".join(formatted_lines)
