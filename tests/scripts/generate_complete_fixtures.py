#!/usr/bin/env python3
"""
Complete fixture generation script for Minutia test scenarios.

This script creates complete end-to-end test fixtures by running the full
pipeline (extraction -> transcription -> merge -> summarization) and organizing
outputs into the scenario-based structure.

Usage:
    python generate_complete_fixtures.py [scenario_name] [recording_file]
    
Examples:
    python generate_complete_fixtures.py microphone_only Example-Microphone.mkv
    python generate_complete_fixtures.py --all  # Process all recordings
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to path for minutia imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv

from minutia.steps import video_extraction, audio_transcription, transcript_merger, summarize_transcript
from minutia.logging import logger
from utilities import (
    get_isodatetime, get_isodate, create_scenario_metadata, save_scenario_metadata,
    setup_directories, select_recording_file, create_scenario_directories,
    organize_outputs_to_scenario, generate_meeting_summary_prompt, 
    extract_transcript_text, create_markdown_report
)


def create_complete_fixture(
    recording_name: str,
    scenario_name: str,
    description: str,
    characteristics: list[str],
    personal_info: str = "",
    markdown_notes: str = ""
) -> bool:
    """
    Create a complete fixture set by running the full pipeline.
    
    Args:
        recording_name: Name of the MKV file in +recordings
        scenario_name: Name for the test scenario
        description: Description of the scenario
        characteristics: List of scenario characteristics
        personal_info: Personal context for summarization
        markdown_notes: Meeting notes for summarization
        
    Returns:
        True if successful, False otherwise
    """
    # Setup directories
    project_root = Path(__file__).parent.parent.parent
    recording_dir = project_root / "+recordings"
    temp_output_dir = project_root / "+temp_output"
    fixtures_dir = project_root / "tests" / "fixtures"
    
    logger.info(f"Creating complete fixture: {scenario_name}")
    logger.info(f"Recording: {recording_name}")
    logger.info(f"Description: {description}")
    
    # Setup and validate
    temp_output_dir.mkdir(exist_ok=True)
    recording_filepath = select_recording_file(recording_dir, recording_name)
    
    if not recording_filepath:
        logger.error(f"Could not find recording: {recording_name}")
        return False
    
    try:
        # Step 1: Extract Audio
        logger.info("Step 1: Extracting Audio...")
        result = video_extraction.process_mkv_file(str(recording_filepath), str(temp_output_dir))
        if not result:
            logger.error("Audio extraction failed")
            return False
        
        # Step 2: Transcribe Audio
        logger.info("Step 2: Transcribing Audio...")
        microphone_audio_path = temp_output_dir / "microphone_audio.wav"
        desktop_audio_path = temp_output_dir / "desktop_audio.wav"
        
        filenames = audio_transcription.process_audio_files(
            mic_audio_path=str(microphone_audio_path),
            desktop_audio_path=str(desktop_audio_path),
            output_dir=str(temp_output_dir),
            whisper_model_name='medium.en',
            use_gpu=True,
        )
        logger.info(f"Transcribed Files: {list(filenames.keys())}")
        
        # Step 3: Merge Transcripts
        logger.info("Step 3: Merging Transcripts...")
        mic_transcript_path = filenames['microphone']
        desktop_transcript_path = filenames['desktop']
        transcript_file_path = temp_output_dir / "merged_transcript.json"
        
        transcript_json = transcript_merger.process_transcripts(
            mic_transcript_file=str(mic_transcript_path),
            desktop_transcript_file=str(desktop_transcript_path),
            output_file=str(transcript_file_path),
            parse_overlaps=False
        )
        
        # Step 4: Generate Summary
        logger.info("Step 4: Generating Summary...")
        transcript_data = summarize_transcript.load_transcript(str(transcript_file_path))
        transcript_text = summarize_transcript.prepare_transcript_for_summary(transcript_data)
        
        system_prompt = generate_meeting_summary_prompt(markdown_notes, personal_info)
        
        try:
            summary = summarize_transcript.generate_long_summary(
                transcript_text, 
                model_name='claude-4-5-sonnet', 
                system_prompt=system_prompt
            )
            summary_filepath = create_markdown_report(content=summary, output_path=temp_output_dir)
            logger.info(f"Summary generated: {summary_filepath}")
        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            # Create a placeholder summary
            summary_filepath = temp_output_dir / f"{get_isodate().replace('-', '')}_summary.md"
            with open(summary_filepath, 'w') as f:
                f.write(f"# Meeting Summary - {scenario_name}\n\nSummary generation skipped.\n\nTranscript:\n```\n{transcript_text}\n```")
        
        # Step 5: Organize into Scenario Structure
        logger.info("Step 5: Organizing into Scenario Structure...")
        scenario_dir = create_scenario_directories(fixtures_dir, scenario_name)
        organize_outputs_to_scenario(temp_output_dir, scenario_dir, recording_filepath)
        
        # Step 6: Create Metadata
        logger.info("Step 6: Creating Metadata...")
        pipeline_parameters = {
            "whisper_model": "medium.en",
            "mic_track": 3,
            "desktop_track": 2
        }
        
        metadata = create_scenario_metadata(
            scenario_name=scenario_name,
            description=description,
            characteristics=characteristics,
            pipeline_parameters=pipeline_parameters,
            original_source=f"+recordings/{recording_name}"
        )
        
        # Update summary filename in metadata
        if summary_filepath.exists():
            metadata["stages"]["04_summarized"]["files"] = [summary_filepath.name]
        
        save_scenario_metadata(scenario_dir, metadata)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_output_dir)
        
        logger.info(f"✅ Complete fixture '{scenario_name}' created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating fixture '{scenario_name}': {str(e)}")
        return False


def main():
    """Main script entry point."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate complete test fixtures")
    parser.add_argument("scenario_name", nargs="?", help="Name of the test scenario")
    parser.add_argument("recording_file", nargs="?", help="Name of the MKV recording file")
    parser.add_argument("--all", action="store_true", help="Process all recordings with default scenarios")
    parser.add_argument("--description", default="", help="Description of the scenario")
    
    args = parser.parse_args()
    
    if args.all:
        # Process all recordings with predefined scenarios
        scenarios = [
            {
                "recording": "Example-Microphone.mkv",
                "scenario": "microphone_only",
                "description": "Clear microphone recording with minimal background noise",
                "characteristics": [
                    "Primary source: microphone audio (track 3)",
                    "Clear speech quality",
                    "Minimal desktop audio",
                    "Good for testing basic transcription accuracy"
                ]
            },
            {
                "recording": "Example-Noisy.mkv",
                "scenario": "noisy_microphone", 
                "description": "Noisy microphone recording with background interference",
                "characteristics": [
                    "Primary source: microphone audio (track 3)",
                    "Background noise and interference present",
                    "Challenging audio conditions",
                    "Good for testing transcription robustness"
                ]
            },
            {
                "recording": "Example-Podcast.mkv",
                "scenario": "podcast_desktop",
                "description": "Desktop audio from podcast playback",
                "characteristics": [
                    "Primary source: desktop audio (track 2)",
                    "Clean podcast content",
                    "Minimal microphone input",
                    "Good for testing desktop audio transcription"
                ]
            },
            {
                "recording": "Example-Song+MLKSpeech.mkv",
                "scenario": "youtube_desktop",
                "description": "Mixed desktop audio from YouTube (music + speech)",
                "characteristics": [
                    "Primary source: desktop audio (track 2)",
                    "Mixed content: music and speech",
                    "Complex audio with overlapping elements",
                    "Good for testing challenging desktop audio scenarios"
                ]
            }
        ]
        
        success_count = 0
        for scenario_config in scenarios:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing scenario: {scenario_config['scenario']}")
            logger.info(f"{'='*60}")
            
            success = create_complete_fixture(
                recording_name=scenario_config["recording"],
                scenario_name=scenario_config["scenario"],
                description=scenario_config["description"],
                characteristics=scenario_config["characteristics"]
            )
            
            if success:
                success_count += 1
            
        logger.info(f"\n🎉 Completed processing: {success_count}/{len(scenarios)} scenarios successful")
        
    elif args.scenario_name and args.recording_file:
        # Process single scenario
        description = args.description or f"Test scenario: {args.scenario_name}"
        characteristics = [f"Generated from {args.recording_file}"]
        
        success = create_complete_fixture(
            recording_name=args.recording_file,
            scenario_name=args.scenario_name,
            description=description,
            characteristics=characteristics
        )
        
        if success:
            logger.info(f"✅ Fixture '{args.scenario_name}' created successfully")
        else:
            logger.error(f"❌ Failed to create fixture '{args.scenario_name}'")
            sys.exit(1)
            
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python generate_complete_fixtures.py --all")
        print("  python generate_complete_fixtures.py test_scenario Example-Test.mkv")
        sys.exit(1)


if __name__ == "__main__":
    main()