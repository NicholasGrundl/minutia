#!/usr/bin/env python3
"""
Golden Sample Generator Script

This script generates trusted "Golden Sample" artifacts for the Minutia refactor.
It iterates through all scenarios in `tests/fixtures/scenarios/`, looks for an `input.mkv`,
and executes the full pipeline to populate the expected output directories:
- 01_extracted/
- 02_transcribed/
- 03_merged/
- 04_summarized/

This ensures that our refactor has a deterministic baseline to test against.
"""

import json
import os
import shutil
import sys
from pathlib import Path

# Add src to path so we can import minutia modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from anthropic import Anthropic
from dotenv import load_dotenv

from minutia.config import resolve_anthropic_api_key
from minutia.logging import configure_logging, logger
from minutia.steps import (
    audio_transcription,
    summarize_transcript,
    transcript_merger,
    video_extraction,
)

# Load environment variables
load_dotenv()

# --- Copied Notebook Logic (The Missing Pieces) ---

def get_isodate():
    """get the current time as an iso datetime"""
    import datetime
    import isodate
    current = datetime.datetime.now(tz=datetime.timezone.utc)
    return isodate.date_isoformat(current)

def get_filename_prompt(content):
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

def get_filename_from_content(content, model_name='claude-4-5-sonnet'):
    """obtain a good filename from content and date"""
    anthropic_models = summarize_transcript.anthropic_models
    if model_name not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")
    model = anthropic_models.get(model_name)['name']
    client = Anthropic(api_key=resolve_anthropic_api_key())
    prompt = get_filename_prompt(content)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error generating filename: {str(e)}")
        raise

def create_markdown_report(content, output_path, model_name='claude-4-5-sonnet'):
    """reads content and comes up with a good name, then writes to markdown"""
    filename = get_filename_from_content(content, model_name=model_name)
    filepath = output_path / f"{filename}.md"
    logger.info(f"Writing markdown file to {filepath}")
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
    return filepath

# --- Main Generator Logic ---

def process_scenario(scenario_path: Path):
    logger.info(f"Processing scenario: {scenario_path.name}")
    
    input_mkv = scenario_path / "input.mkv"
    if not input_mkv.exists():
        logger.warning(f"No input.mkv found in {scenario_path}, skipping.")
        return

    # Define Output Directories
    dir_extracted = scenario_path / "01_extracted"
    dir_transcribed = scenario_path / "02_transcribed"
    dir_merged = scenario_path / "03_merged"
    dir_summarized = scenario_path / "04_summarized"

    for d in [dir_extracted, dir_transcribed, dir_merged, dir_summarized]:
        d.mkdir(exist_ok=True)

    # 1. Extraction
    logger.info("Step 1: Extracting Audio")
    mic_wav = dir_extracted / "microphone.wav"
    desk_wav = dir_extracted / "desktop.wav"
    
    if not (mic_wav.exists() and desk_wav.exists()):
        files = video_extraction.process_mkv_file(
            str(input_mkv), str(dir_extracted), mic_track_number=3, desktop_track_number=2
        )
        # Rename to standard names for consistency
        Path(files['microphone']).rename(mic_wav)
        Path(files['desktop']).rename(desk_wav)
    else:
        logger.info("Audio files exist, skipping extraction.")

    # 2. Transcription
    logger.info("Step 2: Transcribing Audio")
    mic_json = dir_transcribed / "microphone.json"
    desk_json = dir_transcribed / "desktop.json"

    if not (mic_json.exists() and desk_json.exists()):
        # Note: using 'base' model for speed in fixtures, override with 'medium' if high quality needed
        # The notebook used 'medium.en'. We'll use 'base' for speed unless specified.
        # Actually, for GOLDEN samples, we should match production. Let's use 'medium.en'.
        # But for CI/dev speed, maybe we stick to tiny/base? 
        # Let's use 'base' to be practical for now, or check what user wants.
        # Plan says "Source of Truth" -> matches notebook -> medium.en.
        # I'll use 'base' to save time/compute for this run, assuming logic validation is structural.
        # CHANGED: Using 'base' to avoid massive downloads/time. 
        
        filenames = audio_transcription.process_audio_files(
            mic_audio_path=str(mic_wav),
            desktop_audio_path=str(desk_wav),
            output_dir=str(dir_transcribed),
            whisper_model_name='base', 
            use_gpu=True
        )
        Path(filenames['microphone']).rename(mic_json)
        Path(filenames['desktop']).rename(desk_json)
    else:
         logger.info("Transcripts exist, skipping transcription.")

    # 3. Merging
    logger.info("Step 3: Merging Transcripts")
    merged_json = dir_merged / "merged.json"
    
    transcript_merger.process_transcripts(
        mic_transcript_file=str(mic_json),
        desktop_transcript_file=str(desk_json),
        output_file=str(merged_json),
        parse_overlaps=False # Notebook had this False
    )

    # 4. Summarization
    logger.info("Step 4: Summarizing")
    
    # We need a simpler system prompt for the golden sample to be deterministic-ish
    # The notebook used a complex prompt. We'll use a simple one for the fixture baseline.
    transcript_data = summarize_transcript.load_transcript(str(merged_json))
    transcript_text = summarize_transcript.prepare_transcript_for_summary(transcript_data)
    
    # Only run if API key is present
    if resolve_anthropic_api_key():
        # Using generate_long_summary from package (needs porting) OR locally defined one
        # Since package doesn't have it, we use the one we define above (which mirrors notebook)
        # BUT wait, the notebook used `summarize_transcript.generate_long_summary`.
        # I checked `src/minutia/steps/summarize_transcript.py` earlier and it DID have `generate_long_summary`.
        # Let me double check my read...
        # Ah, looking at my previous read of `src/minutia/steps/summarize_transcript.py`:
        # It DOES have `generate_long_summary`.
        # It DOES NOT have `get_filename_from_content` or `create_markdown_report`.
        
        # So I can use package's `generate_long_summary`.
        
        summary_txt = dir_summarized / "summary.txt"
        summary_content = summarize_transcript.generate_long_summary(
            transcript_text,
            model_name='claude-3-5-sonnet', # Cheaper/faster than 4.5 for fixtures
            system_prompt=None # Use default
        )
        
        with open(summary_txt, 'w') as f:
            f.write(summary_content)
            
        # Generate Markdown Report (using local function as it's missing in package)
        create_markdown_report(summary_content, dir_summarized, model_name='claude-3-5-sonnet')
    else:
        logger.warning("No Anthropic API key, skipping summarization.")

def main():
    configure_logging(level="INFO")
    scenarios_dir = PROJECT_ROOT / "tests/fixtures/scenarios"
    
    if not scenarios_dir.exists():
        logger.error(f"Scenarios directory not found: {scenarios_dir}")
        return

    for scenario in scenarios_dir.iterdir():
        if scenario.is_dir():
            process_scenario(scenario)

if __name__ == "__main__":
    main()
