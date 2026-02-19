#!/usr/bin/env python3
"""
Script to generate golden samples for regression testing.
Ports logic from CreateNewFixtureSet.ipynb to a standalone CLI.
"""

import argparse
import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from minutia.steps import (
    video_extraction, 
    audio_transcription, 
    transcript_merger, 
    summarize_transcript
)

def discover_scenarios(fixtures_dir: Path):
    """Find all scenarios in the fixtures directory."""
    scenarios_dir = fixtures_dir / "scenarios"
    if not scenarios_dir.exists():
        logger.error(f"Scenarios directory not found: {scenarios_dir}")
        return []
    
    scenarios = [d for d in scenarios_dir.iterdir() if d.is_dir() and (d / "input.mkv").exists()]
    logger.info(f"Found {len(scenarios)} scenarios in {scenarios_dir}")
    return scenarios

def run_pipeline_for_scenario(scenario_dir: Path, force: bool = False):
    """Run the full pipeline for a single scenario to generate golden samples."""
    logger.info(f"🚀 Processing scenario: {scenario_dir.name}")
    
    input_mkv = scenario_dir / "input.mkv"
    stage_01 = scenario_dir / "01_extracted"
    stage_02 = scenario_dir / "02_transcribed"
    stage_03 = scenario_dir / "03_merged"
    stage_04 = scenario_dir / "04_summarized"
    
    # 1. Extraction
    logger.info("Step 1: Extracting Audio...")
    mic_file = stage_01 / "microphone_audio.wav"
    desktop_file = stage_01 / "desktop_audio.wav"
    
    if not force and mic_file.exists() and desktop_file.exists():
        logger.info("Audio files already exist. Skipping extraction.")
    else:
        video_extraction.process_mkv_file(str(input_mkv), str(stage_01))

    # 2. Transcription
    logger.info("Step 2: Transcribing Audio...")
    try:
        filenames = audio_transcription.process_audio_files(
            mic_audio_path=str(mic_file),
            desktop_audio_path=str(desktop_file),
            output_dir=str(stage_02),
            whisper_model_name='medium.en',
            use_gpu=True,
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return

    # 3. Merging
    logger.info("Step 3: Merging Transcripts...")
    mic_transcript = stage_02 / "microphone-whisper-medium.en_transcription.json"
    desktop_transcript = stage_02 / "desktop-whisper-medium.en_transcription.json"
    merged_json = stage_03 / "merged_transcript.json"
    
    transcript_merger.process_transcripts(
        mic_transcript_file=str(mic_transcript),
        desktop_transcript_file=str(desktop_transcript),
        output_file=str(merged_json),
        parse_overlaps=False
    )

    # 4. Summarization
    logger.info("Step 4: Summarizing Meeting...")
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not found. Skipping summarization.")
        return

    transcript_data = summarize_transcript.load_transcript(str(merged_json))
    transcript_text = summarize_transcript.prepare_transcript_for_summary(transcript_data)
    
    # Minimal version of prompt from notebook
    system_prompt = "Summarize the following meeting transcript accurately and concisely."
    
    try:
        summary = summarize_transcript.generate_long_summary(
            transcript_text, 
            model_name='claude-4-5-sonnet', 
            system_prompt=system_prompt
        )
        
        summary_path = stage_04 / "summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Summary saved to {summary_path}")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate golden samples for Minutia scenarios.")
    parser.add_argument("--fixtures-dir", type=Path, default=Path("tests/fixtures"), help="Path to the fixtures directory.")
    parser.add_argument("--dry-run", action="store_true", help="Discover scenarios without running the pipeline.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing intermediate files.")
    
    args = parser.parse_args()
    
    scenarios = discover_scenarios(args.fixtures_dir)
    
    for scenario in scenarios:
        print(f"Found scenario: {scenario.name}")
        if args.dry_run:
            continue
        
        run_pipeline_for_scenario(scenario, force=args.force)

if __name__ == "__main__":
    main()
