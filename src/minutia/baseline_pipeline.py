"""
Standalone pipeline script extracted from the original CreateTranscriptProd notebook.

This module preserves the current end-to-end workflow for the Minutia CLI MVP:
1. Extract audio tracks from an OBS MKV recording.
2. Transcribe the microphone and desktop audio with Whisper.
3. Merge the transcripts into a single JSON artifact.
4. Optionally generate a detailed meeting summary with Anthropic models.

The implementation intentionally mirrors notebook behaviour to provide a stable
baseline while the new architecture is built. It exposes a command-line
interface so that the same workflow can be executed outside of Jupyter.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import isodate
from dotenv import load_dotenv

from . import (
    audio_transcription,
    summarize_transcript,
    transcript_merger,
    video_extraction,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging to mirror the notebook defaults."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_isodatetime() -> str:
    """Return the current UTC time encoded as an ISO 8601 datetime string."""
    current = datetime.datetime.now(tz=datetime.timezone.utc)
    return isodate.datetime_isoformat(current)


def get_isodate() -> str:
    """Return the current UTC date encoded as an ISO 8601 date string."""
    current = datetime.datetime.now(tz=datetime.timezone.utc)
    return isodate.date_isoformat(current)


def ensure_output_directory(base_dir: Path | None, subfolder: str | None) -> Path:
    """
    Resolve and create the output directory.

    When a base directory is not specified the notebook convention of
    `<YYYY-MM-DD>-output` is used. A subfolder replicates the `dir_subfolder`
    behaviour from the notebook.
    """
    if base_dir is None:
        base_dir = Path.cwd() / f"{get_isodate()}-output"
    if subfolder:
        base_dir = base_dir / subfolder
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


# ---------------------------------------------------------------------------
# Advanced summarisation helpers
# ---------------------------------------------------------------------------


def get_filename_prompt(content: str) -> str:
    """Construct the Anthropic prompt used to derive markdown filenames."""
    current_date = get_isodate()
    return f"""Please read the <content> completely and provide a filename that can be used to write the file to disk as a markdown. The filename should be concise but also descriptive so its clear what the content contains.

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


def get_filename_from_content(
    content: str, model_name: str = "claude-3-5-sonnet"
) -> str:
    """Use Anthropic to generate a descriptive filename for markdown exports."""
    anthropic_models = summarize_transcript.anthropic_models
    if model_name not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")
    model = anthropic_models[model_name]["name"]
    client = summarize_transcript.Anthropic(
        api_key=summarize_transcript.ANTHROPIC_API_KEY
    )
    prompt = get_filename_prompt(content)
    response = client.messages.create(
        model=model,
        max_tokens=100,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_markdown_report(
    content: str,
    output_path: Path,
    model_name: str = "claude-3-5-sonnet",
) -> Path:
    """
    Persist a markdown report alongside the summary using an Anthropic generated name.
    """
    filename = get_filename_from_content(content, model_name=model_name)
    filepath = output_path / f"{filename}.md"
    logger.info("Writing markdown report to %s", filepath)
    filepath.write_text(content, encoding="utf-8")
    return filepath


def format_personal_notes(notes: Iterable[Mapping[str, Any]]) -> str:
    """Render personal notes into markdown bullet lists for the system prompt."""
    lines: list[str] = []
    for note in notes:
        text = note.get("note")
        if not text:
            continue
        lines.append(f"- {text}")
        for bullet in note.get("bullets", []):
            lines.append(f"  * {bullet}")
    return "\n".join(lines)


def generate_meeting_summary_prompt(
    personal_notes: Iterable[Mapping[str, Any]],
    personal_info: str,
    markdown_notes: str = "",
) -> str:
    """Generate the structured system prompt used by the long summary flow."""
    formatted_notes = format_personal_notes(personal_notes)
    return f"""# 🧙‍♂️ Comprehensive and Detailed Meeting Insight Generator

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

#INFORMATION ABOUT ME: {personal_info}

#PERSONAL NOTES:
{formatted_notes}

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


def extract_transcript_text(transcript_data: Mapping[str, Any]) -> str:
    """
    Convert the merged transcript JSON into the meeting-note format used by the notebook.
    """
    transcript_entries = transcript_data["transcript"]
    sorted_entries = sorted(transcript_entries, key=lambda x: x["start_time"])
    formatted_lines = []
    for entry in sorted_entries:
        speaker = entry["source"].capitalize()
        start_time = f"{entry['start_time']:.2f}"
        text = entry["text"].strip()
        formatted_lines.append(f"[{speaker} {start_time}] {text}")
    return "\n".join(formatted_lines)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def read_personal_notes(path: Path | None) -> list[MutableMapping[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("personal notes must be a list of objects")
    return list(data)


def read_personal_info(info: str | None, path: Path | None) -> str:
    if info and path:
        raise ValueError("Specify personal info via --personal-info or --personal-info-file, not both.")
    if path:
        return path.read_text(encoding="utf-8")
    return info or ""


def read_markdown_notes(path: Path | None) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Core pipeline orchestration
# ---------------------------------------------------------------------------


@dataclass
class PipelineArtifacts:
    microphone_audio: Path
    desktop_audio: Path
    microphone_transcript: Path
    desktop_transcript: Path
    merged_transcript: Path
    summary_file: Path | None = None
    markdown_file: Path | None = None


def extract_audio(input_video: Path, output_dir: Path) -> Mapping[str, str]:
    """Extract audio tracks from the input video using the existing module."""
    logger.info("Extracting audio tracks from %s", input_video)
    return video_extraction.process_mkv_file(str(input_video), str(output_dir))


def transcribe_audio(
    microphone: Path,
    desktop: Path,
    output_dir: Path,
    whisper_model: str,
) -> Mapping[str, str]:
    """Transcribe microphone and desktop audio using Whisper."""
    logger.info("Transcribing audio with Whisper model '%s'", whisper_model)
    return audio_transcription.process_audio_files(
        str(microphone),
        str(desktop),
        output_dir=str(output_dir),
        whisper_model_name=whisper_model,
    )


def merge_transcripts(
    microphone_transcript: Path,
    desktop_transcript: Path,
    output_file: Path,
    parse_overlaps: bool,
) -> Mapping[str, Any]:
    """Merge Whisper transcripts into a single JSON artifact."""
    logger.info("Merging transcripts into %s", output_file)
    return transcript_merger.process_transcripts(
        mic_transcript_file=str(microphone_transcript),
        desktop_transcript_file=str(desktop_transcript),
        output_file=str(output_file),
        parse_overlaps=parse_overlaps,
    )


def summarise_transcript(
    transcript_text: str,
    summary_path: Path,
    *,
    model: str,
    use_long_summary: bool,
    system_prompt: str | None,
) -> str:
    """Generate a meeting summary using either the short or long flow."""
    if use_long_summary:
        summary = summarize_transcript.generate_long_summary(
            transcript_text=transcript_text,
            model_name=model,
            system_prompt=system_prompt,
        )
    else:
        summary = summarize_transcript.generate_summary(
            transcript_text=transcript_text,
            model_name=model,
            system_prompt=system_prompt,
        )
    summarize_transcript.save_summary(summary, str(summary_path))
    return summary


def estimate_summary_cost(
    transcript_text: str,
    model: str,
) -> None:
    """Log token and pricing estimates for the requested model."""
    total_tokens, estimated_price = summarize_transcript.estimate_tokens_and_price(
        transcript_text,
        model=model,
    )
    logger.info("Estimated tokens: %s", total_tokens)
    logger.info("Estimated price: $%.4f", estimated_price)


def run_pipeline(args: argparse.Namespace) -> PipelineArtifacts:
    """Execute the end-to-end workflow using the supplied CLI arguments."""
    load_dotenv()
    configure_logging()

    output_dir = ensure_output_directory(args.output_dir, args.subfolder)
    logger.info("Writing run artifacts to %s", output_dir)

    audio_files = extract_audio(args.input_video, output_dir)
    microphone_audio = Path(audio_files["microphone"])
    desktop_audio = Path(audio_files["desktop"])

    transcripts = transcribe_audio(
        microphone_audio,
        desktop_audio,
        output_dir,
        whisper_model=args.whisper_model,
    )
    microphone_transcript = Path(transcripts["microphone"])
    desktop_transcript = Path(transcripts["desktop"])

    merged_transcript_path = output_dir / args.transcript_filename
    transcript_data = merge_transcripts(
        microphone_transcript,
        desktop_transcript,
        merged_transcript_path,
        parse_overlaps=args.parse_overlaps,
    )

    personal_notes = read_personal_notes(args.personal_notes)
    personal_info = read_personal_info(args.personal_info, args.personal_info_file)
    markdown_notes = read_markdown_notes(args.markdown_notes)

    if personal_notes or personal_info or markdown_notes:
        system_prompt = generate_meeting_summary_prompt(
            personal_notes,
            personal_info,
            markdown_notes,
        )
        transcript_text_for_summary = extract_transcript_text(transcript_data)
    else:
        system_prompt = None
        transcript_text_for_summary = summarize_transcript.prepare_transcript_for_summary(
            transcript_data
        )

    estimate_summary_cost(transcript_text_for_summary, args.summary_model)

    summary_path: Path | None = None
    markdown_path: Path | None = None

    if args.skip_summary:
        logger.info("Skipping summary generation (--skip-summary provided).")
    else:
        summary_name = args.summary_filename
        if args.timestamp_summary:
            summary_name = f"{get_isodatetime()}-{summary_name}"
        summary_path = output_dir / summary_name

        summary_text = summarise_transcript(
            transcript_text=transcript_text_for_summary,
            summary_path=summary_path,
            model=args.summary_model,
            use_long_summary=args.long_summary,
            system_prompt=system_prompt,
        )

        if args.generate_markdown:
            markdown_path = create_markdown_report(
                summary_text,
                output_dir,
                model_name=args.summary_model,
            )

    return PipelineArtifacts(
        microphone_audio=microphone_audio,
        desktop_audio=desktop_audio,
        microphone_transcript=microphone_transcript,
        desktop_transcript=desktop_transcript,
        merged_transcript=merged_transcript_path,
        summary_file=summary_path,
        markdown_file=markdown_path,
    )


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Baseline Minutia pipeline extracted from the production notebook.",
    )
    parser.add_argument(
        "input_video",
        type=Path,
        help="Path to the OBS MKV recording to process.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write outputs. Defaults to ./<YYYY-MM-DD>-output.",
    )
    parser.add_argument(
        "--subfolder",
        type=str,
        default=None,
        help="Optional subfolder inside the output directory.",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="base",
        help="Whisper model name (matches notebook default).",
    )
    parser.add_argument(
        "--transcript-filename",
        type=str,
        default="merged_transcript.json",
        help="Filename for the merged transcript artifact.",
    )
    parser.add_argument(
        "--summary-filename",
        type=str,
        default="summary.txt",
        help="Base filename for summary output.",
    )
    parser.add_argument(
        "--summary-model",
        type=str,
        default="claude-3-5-sonnet",
        choices=list(summarize_transcript.anthropic_models.keys()),
        help="Anthropic model to use when summarising.",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Skip summary generation while still logging cost estimates.",
    )
    parser.add_argument(
        "--long-summary",
        action="store_true",
        help="Use the long-form summary flow with automatic continuation handling.",
    )
    parser.add_argument(
        "--timestamp-summary",
        action="store_true",
        help="Prefix summaries with an ISO timestamp (matches notebook behaviour).",
    )
    parser.add_argument(
        "--generate-markdown",
        action="store_true",
        help="Generate an additional markdown report with an AI-generated filename.",
    )
    parser.add_argument(
        "--personal-notes",
        type=Path,
        default=None,
        help="Path to a JSON file containing personal notes for the prompt.",
    )
    parser.add_argument(
        "--personal-info",
        type=str,
        default=None,
        help="Inline personal background string for the meeting prompt.",
    )
    parser.add_argument(
        "--personal-info-file",
        type=Path,
        default=None,
        help="Path to a file containing personal background text.",
    )
    parser.add_argument(
        "--markdown-notes",
        type=Path,
        default=None,
        help="Optional markdown snippet to inject into the meeting prompt.",
    )
    parser.add_argument(
        "--parse-overlaps",
        action="store_true",
        help="Enable overlap parsing when merging transcripts (off by default).",
    )
    return parser


def main(argv: list[str] | None = None) -> PipelineArtifacts:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_pipeline(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
