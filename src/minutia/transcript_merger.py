import json
import logging
import re
import sys


def setup_logger(name="merge_transcript", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

logger = setup_logger()

def parse_transcript(file_path):
    transcript = []
    logger.info(f"Parsing transcript file: {file_path}")
    with open(file_path) as f:
        for line in f:
            match = re.match(r'\[(\d+\.\d+) - (\d+\.\d+)\] (.+)', line.strip())
            if match:
                start_time, end_time, text = match.groups()
                transcript.append({
                    'start_time': float(start_time),
                    'end_time': float(end_time),
                    'text': text
                })
    logger.info(f"Parsed {len(transcript)} segments from {file_path}")
    return transcript

def merge_transcripts(mic_transcript, desktop_transcript, parse_overlaps=True):
    logger.info("Merging transcripts")
    combined_segments = (
        [{'source': 'microphone', **segment} for segment in mic_transcript] +
        [{'source': 'desktop', **segment} for segment in desktop_transcript]
    )

    sorted_segments = sorted(combined_segments, key=lambda x: x['start_time'])

    if not parse_overlaps:
        logger.info("Skipping overlap parsing")
        return sorted_segments

    logger.info("Parsing overlaps")
    merged_transcript = []

    for segment in sorted_segments:
        if not merged_transcript or segment['start_time'] >= merged_transcript[-1]['end_time']:
            # New non-overlapping segment
            merged_transcript.append(segment)
        else:
            # Overlapping segment
            overlap_start = segment['start_time']
            overlap_end = min(segment['end_time'], merged_transcript[-1]['end_time'])

            # Add overlapping part
            merged_transcript.append({
                'start_time': overlap_start,
                'end_time': overlap_end,
                'text': f"[{merged_transcript[-1]['source']}] {merged_transcript[-1]['text']} | [{segment['source']}] {segment['text']}",
                'source': 'overlap'
            })

            # Add remaining part of the new segment if it extends beyond the previous one
            if segment['end_time'] > merged_transcript[-1]['end_time']:
                merged_transcript.append({
                    'start_time': merged_transcript[-1]['end_time'],
                    'end_time': segment['end_time'],
                    'text': segment['text'],
                    'source': segment['source']
                })

    logger.info(f"Merged transcript contains {len(merged_transcript)} segments")
    return merged_transcript

def save_merged_transcript(merged_transcript, output_file, metadata=None):
    logger.info(f"Saving merged transcript to {output_file}")
    output_data = {
        'metadata': metadata or {},
        'transcript': merged_transcript
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info("Merged transcript saved successfully")


def process_transcripts(mic_transcript_file, desktop_transcript_file, output_file, parse_overlaps=True):
    logger.info("Starting transcript processing")
    # Parse transcripts
    mic_transcript = parse_transcript(mic_transcript_file)
    desktop_transcript = parse_transcript(desktop_transcript_file)

    # Merge transcripts
    merged_transcript = merge_transcripts(mic_transcript, desktop_transcript, parse_overlaps)

    # Prepare metadata
    metadata = {
        'source_files': {
            'microphone': mic_transcript_file,
            'desktop': desktop_transcript_file
        },
        'total_duration': max(segment['end_time'] for segment in merged_transcript),
        'segment_count': len(merged_transcript),
        'parse_overlaps': parse_overlaps
    }

    # Save merged transcript
    save_merged_transcript(merged_transcript, output_file, metadata)

    logger.info(f"Transcript processing completed. Output saved to {output_file}")
    return {
        'metadata': metadata,
        'transcript': merged_transcript
    }

