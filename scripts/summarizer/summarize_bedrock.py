# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "loguru",
#     "nanoid",
#     "anthropic>=1.14",
# ]
# ///
"""Summarize a Whisper meeting transcript with Claude on Amazon Bedrock.

Accepts a merged transcript (merged_transcript.json), a single-track Whisper
transcript (desktop-/microphone-*_transcription.json), or plain text (.txt/.md).
JSON input is rendered as chronological `[Speaker 12.34] text` lines.

The system prompt is a markdown template with two optional placeholders:
`$audience` (who the summary is for) and `$notes` (meeting notes / context).
Unfilled placeholders become empty strings; any other `$word` is left as-is.
Pass either value inline, or prefix with "@" to read it from a file. --notes
can be repeated (e.g. -n @focus.md -n @meeting_notes.md); multiple notes are
joined under "### <filename>" (or "### Note N") headings.

Auth is explicit-only, for IP-sensitive use: the Bedrock API key comes from a
key file and nothing else. Credentials, base URLs, regions, proxies and custom
headers found in the environment are all ignored, so the request goes only to
bedrock-mantle.<region>.api.aws with that one key.

Key file: --key-file, else DEFAULT_KEY_FILE (set below), else an error.
  - *.json: a Claude Code settings file; reads env.AWS_BEARER_TOKEN_BEDROCK
    and env.AWS_REGION (e.g. .claude/settings.local.json).
  - anything else (.env, .txt, .md, ...): KEY=value lines; reads
    AWS_BEARER_TOKEN_BEDROCK=... and AWS_REGION=... ("export " and quotes ok).
Region: --region, else AWS_REGION from the key file, else us-east-1.

Example:
    uv run scripts/summarizer/summarize_bedrock.py run/03_merged/merged_transcript.json \\
        --key-file .claude/settings.local.json \\
        --audience "Nick, consultant leading the solver project" \\
        --notes @run/meeting_notes.md --model sonnet
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from enum import StrEnum
from pathlib import Path
from string import Template

import anthropic
import typer
from loguru import logger
from nanoid import generate

app = typer.Typer(
    add_completion=False,
    help="Summarize a Whisper meeting transcript with Claude on Amazon Bedrock.",
)

# nanoid alphabet kept to lowercase + digits so suffixes are filename-clean
_HASH_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

# --- user config --------------------------------------------------------------
# Key file used whenever --key-file isn't passed, so repeat runs need no flag.
# Must be absolute (~ allowed). None = always require --key-file.
DEFAULT_KEY_FILE: Path | None = None
# e.g. DEFAULT_KEY_FILE = Path("/mnt/c/Users/me/project/.claude/settings.local.json")
# ------------------------------------------------------------------------------

DEFAULT_PROMPT = Path(__file__).resolve().parent / "prompts" / "default.md"
# Names read from the key file only; never from os.environ.
KEY_NAME = "AWS_BEARER_TOKEN_BEDROCK"
REGION_NAME = "AWS_REGION"
FALLBACK_REGION = "us-east-1"
# AWS region shape (e.g. us-east-1); guards the hostname built from the region.
_REGION_RE = re.compile(r"^[a-z]{2}(-[a-z]+)+-\d$")
# KEY=value line in a .env/.txt/.md key file; the name must start the line.
_KV_LINE_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
# Opus 5.5 / Sonnet 5.5 allow 128K output; streaming keeps 64K clear of HTTP timeouts.
MAX_OUTPUT_TOKENS = 64_000


class Model(StrEnum):
    opus = "opus"
    sonnet = "sonnet"


MODEL_IDS = {
    Model.opus: "anthropic.claude-opus-5-5",
    Model.sonnet: "anthropic.claude-sonnet-5-5",
}


class Effort(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"
    max = "max"


def configure_logging(verbose: bool) -> None:
    """Send loguru to stdout so the invoking agent sees live progress."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | {level: <7} | {message}",
        level="DEBUG" if verbose else "INFO",
    )


def resolve_output_path(path: Path, clobber: bool) -> Path:
    """Return a non-colliding output path.

    If `clobber` is False and `path` already exists, insert a short random
    nanoid before the extension (e.g. report.csv -> report_a3k9zd.csv).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if clobber or not path.exists():
        return path
    suffix = generate(_HASH_ALPHABET, 6)
    return path.with_name(f"{path.stem}_{suffix}{path.suffix}")


def combine_notes(values: list[str]) -> str:
    """Read each --notes value; label them by source when there is more than one."""
    if len(values) <= 1:
        return read_value(values[0], "notes") if values else ""
    sections = []
    for i, value in enumerate(values, start=1):
        label = Path(value[1:]).name if value.startswith("@") else f"Note {i}"
        sections.append(f"### {label}\n{read_value(value, 'notes').strip()}")
    return "\n\n".join(sections)


def read_value(value: str, name: str) -> str:
    """Return `value`, or the contents of a file when it is written as "@path"."""
    if not value.startswith("@"):
        return value
    path = Path(value[1:]).expanduser()
    if not path.is_file():
        logger.error(f"--{name} file not found: {path}")
        raise typer.Exit(code=1)
    logger.debug(f"Read --{name} from {path}")
    return path.read_text(encoding="utf-8")


def infer_speaker(transcript_path: Path, metadata: dict) -> str:
    """Guess a single-track speaker label from the filename, then the source audio."""
    candidates = [transcript_path.stem, Path(metadata.get("source_file", "")).stem]
    for name in candidates:
        name = name.lower()
        if name.startswith("desktop"):
            return "Desktop"
        if name.startswith(("microphone", "mic")):
            return "Microphone"
    return "Speaker"


def format_segments(segments: list[dict], timestamps: bool) -> str:
    """Render segments as chronological `[Speaker 12.34] text` lines."""
    lines = []
    for seg in sorted(segments, key=lambda s: s.get("start_time", 0.0)):
        text = seg.get("text", "").strip()
        if not text:
            continue
        speaker = seg["speaker"]
        tag = f"{speaker} {seg.get('start_time', 0.0):.2f}" if timestamps else speaker
        lines.append(f"[{tag}] {text}")
    return "\n".join(lines)


def load_transcript(path: Path, speaker: str | None, timestamps: bool) -> str:
    """Load any supported transcript format and return prompt-ready text."""
    if path.suffix.lower() != ".json":
        logger.info("Plain-text transcript: passing through unchanged")
        return path.read_text(encoding="utf-8").strip()

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("transcript"), list):
        segments = [
            {**seg, "speaker": str(seg.get("source", "speaker")).capitalize()}
            for seg in data["transcript"]
        ]
        speakers = sorted({seg["speaker"] for seg in segments})
        logger.info(f"Merged transcript: {len(segments)} segments from {speakers}")
    elif isinstance(data, dict) and isinstance(data.get("segments"), list):
        label = speaker or infer_speaker(path, data.get("metadata", {}))
        segments = [{**seg, "speaker": label} for seg in data["segments"]]
        logger.info(f"Single-track transcript: {len(segments)} segments as [{label}]")
    else:
        logger.error(
            "Unrecognized JSON: expected a 'transcript' list (merged) "
            "or a 'segments' list (single-track Whisper output)"
        )
        raise typer.Exit(code=1)
    return format_segments(segments, timestamps)


def render_prompt(template_path: Path, audience: str, notes: str) -> str:
    """Fill `$audience` / `$notes`; leave any other `$word` untouched."""
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.safe_substitute(audience=audience.strip(), notes=notes.strip())


def resolve_key_file(cli_path: Path | None) -> tuple[Path, str] | None:
    """Pick the key file: --key-file, then DEFAULT_KEY_FILE, else None."""
    if cli_path is not None:
        return cli_path.expanduser(), "--key-file"
    if DEFAULT_KEY_FILE is not None:
        path = Path(DEFAULT_KEY_FILE).expanduser()
        if not path.is_absolute():
            # A relative default would resolve against whatever cwd the script runs in.
            logger.error(f"DEFAULT_KEY_FILE must be an absolute path: {path}")
            raise typer.Exit(code=1)
        return path, "DEFAULT_KEY_FILE"
    return None


def _reject_duplicate_names(pairs: list[tuple[str, object]]) -> dict:
    """json object_pairs_hook: refuse a key or region name defined twice."""
    names = [name for name, _ in pairs]
    for name in (KEY_NAME, REGION_NAME):
        if names.count(name) > 1:
            raise ValueError(f"{name} is defined more than once")
    return dict(pairs)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def read_key_file(path: Path) -> tuple[str, str | None]:
    """Return (api_key, region or None) from a settings JSON or KEY=value file.

    The key is never logged.
    """
    if not path.is_file():
        logger.error(f"Key file not found: {path}")
        raise typer.Exit(code=1)
    raw = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw, object_pairs_hook=_reject_duplicate_names)
        except ValueError as e:  # JSONDecodeError is a ValueError
            logger.error(f"Key file is not a usable settings JSON ({e}): {path}")
            raise typer.Exit(code=1) from e
        env = data.get("env") if isinstance(data, dict) else None
        if not isinstance(env, dict):
            logger.error(f'Key file has no "env" object: {path}')
            raise typer.Exit(code=1)
        values = {n: env[n] for n in (KEY_NAME, REGION_NAME) if n in env}
        where = "env."
    else:
        values: dict[str, object] = {}
        for lineno, line in enumerate(raw.splitlines(), start=1):
            match = _KV_LINE_RE.match(line)
            if not match or match.group(1) not in (KEY_NAME, REGION_NAME):
                continue
            name = match.group(1)
            if name in values:
                logger.error(
                    f"{name} is defined more than once in {path} (line {lineno})"
                )
                raise typer.Exit(code=1)
            values[name] = _unquote(match.group(2))
        where = ""

    key = values.get(KEY_NAME)
    if not isinstance(key, str) or not key or any(c.isspace() for c in key):
        logger.error(f"No single-line {where}{KEY_NAME} value found in {path}")
        raise typer.Exit(code=1)
    region = values.get(REGION_NAME)
    if region is not None and not isinstance(region, str):
        logger.error(f"{where}{REGION_NAME} must be a string in {path}")
        raise typer.Exit(code=1)
    return key, (region or None)


def resolve_region(cli_region: str | None, file_region: str | None) -> str:
    """--region, then the key file's AWS_REGION, then us-east-1; validated."""
    if cli_region is not None:
        region, source = cli_region, "--region"
    elif file_region is not None:
        region, source = file_region, "key file"
    else:
        region, source = FALLBACK_REGION, "default"
    if not _REGION_RE.match(region):
        logger.error(f"Invalid AWS region from {source}: {region!r}")
        raise typer.Exit(code=1)
    logger.info(f"Region: {region} ({source})")
    return region


def summarize(
    system_prompt: str,
    transcript: str,
    model: Model,
    effort: Effort,
    region: str,
    token: str,
) -> anthropic.types.Message:
    """Stream one Messages API call to Bedrock and return the final message."""
    # The SDK adds headers from this variable; drop it so nothing ambient rides along.
    os.environ.pop("ANTHROPIC_CUSTOM_HEADERS", None)
    # Explicit api_key + base_url: the SDK skips ANTHROPIC_* env credentials,
    # profiles and ANTHROPIC_BASE_URL. trust_env=False ignores proxy env vars and
    # .netrc, so the only connection is directly to Bedrock in `region`.
    client = anthropic.Anthropic(
        base_url=f"https://bedrock-mantle.{region}.api.aws/anthropic",
        api_key=token,
        http_client=anthropic.DefaultHttpxClient(trust_env=False),
    )
    # Thinking is adaptive by default on Opus 5.5 / Sonnet 5.5; effort sets its depth.
    with client.messages.stream(
        model=MODEL_IDS[model],
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Here's the transcript:\n\n{transcript}"}
        ],
        output_config={"effort": effort.value},
    ) as stream:
        return stream.get_final_message()


@app.command()
def main(
    transcript_path: Path = typer.Argument(
        ...,
        help="merged_transcript.json, a single-track *_transcription.json, or .txt/.md.",
    ),
    prompt: Path = typer.Option(
        DEFAULT_PROMPT,
        "--prompt",
        "-p",
        help="System prompt template (.md) using $audience and $notes.",
    ),
    audience: str = typer.Option(
        "",
        "--audience",
        "-a",
        help='Who the summary is for. Inline text, or "@file" to read a file.',
    ),
    notes: list[str] = typer.Option(
        [],
        "--notes",
        "-n",
        help='Meeting notes / context. Inline text, or "@file" to read a file. '
        "Repeatable; multiple notes are labeled by filename.",
    ),
    model: Model = typer.Option(
        Model.opus, "--model", "-m", help="opus = Opus 5.5, sonnet = Sonnet 5.5."
    ),
    effort: Effort = typer.Option(
        Effort.high, "--effort", help="Thinking depth vs. cost."
    ),
    key_file: Path = typer.Option(
        None,
        "--key-file",
        "-k",
        help="File holding AWS_BEARER_TOKEN_BEDROCK (and optionally AWS_REGION): "
        "a Claude settings JSON (env.*) or KEY=value lines (.env/.txt/.md). "
        "Default: DEFAULT_KEY_FILE in the script. Environment variables are "
        "never used.",
    ),
    region: str = typer.Option(
        None,
        "--region",
        help="Bedrock AWS region. Overrides AWS_REGION from the key file; "
        "default us-east-1. Never read from the environment.",
    ),
    speaker: str = typer.Option(
        None,
        "--speaker",
        help="Label for single-track JSON input. Default: inferred from filename.",
    ),
    timestamps: bool = typer.Option(
        True, "--timestamps/--no-timestamps", help="Prefix lines with start time."
    ),
    output_path: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Where to write the summary. Default: <transcript dir>/<stem>_summary.md.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the rendered system prompt and a rough token count, and "
        "check the key file if one is set; no API call.",
    ),
    clobber: bool = typer.Option(
        False, "--clobber", help="Overwrite an existing output file."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable DEBUG-level logging."
    ),
) -> None:
    """Summarize a meeting transcript with Claude on Amazon Bedrock."""
    configure_logging(verbose)

    for path, label in [(transcript_path, "Transcript"), (prompt, "Prompt template")]:
        if not path.is_file():
            logger.error(f"{label} not found: {path}")
            raise typer.Exit(code=1)

    # Resolve credentials first so a bad key file fails before any other work.
    token, file_region = None, None
    chosen = resolve_key_file(key_file)
    if chosen is not None:
        key_path, key_source = chosen
        token, file_region = read_key_file(key_path)
        logger.info(f"Key: {key_path} ({key_source})")
    elif dry_run:
        logger.warning(
            "No key file set; a real run needs --key-file or DEFAULT_KEY_FILE"
        )
    else:
        logger.error(
            "No key file: pass --key-file or set DEFAULT_KEY_FILE in the script "
            "(environment keys are never used)"
        )
        raise typer.Exit(code=1)
    region = resolve_region(region, file_region)

    logger.info(f"Reading {transcript_path}")
    transcript = load_transcript(transcript_path, speaker, timestamps)
    if not transcript:
        logger.error("Transcript is empty; nothing to summarize")
        raise typer.Exit(code=1)

    system_prompt = render_prompt(
        prompt, read_value(audience, "audience"), combine_notes(notes)
    )
    approx_tokens = (len(system_prompt) + len(transcript)) // 4
    logger.info(f"Prompt template: {prompt.name}")
    logger.info(f"Approx. input tokens: ~{approx_tokens:,} (chars / 4)")

    if dry_run:
        preview = "\n".join(transcript.splitlines()[:5])
        print(f"\n===== SYSTEM PROMPT =====\n{system_prompt}")
        print(f"\n===== TRANSCRIPT (first 5 lines) =====\n{preview}\n")
        logger.info("Dry run: no API call made")
        return

    if output_path is None:
        output_path = transcript_path.with_name(f"{transcript_path.stem}_summary.md")

    logger.info(f"Calling {MODEL_IDS[model]} in {region} (effort={effort.value})")
    started = time.monotonic()
    try:
        message = summarize(system_prompt, transcript, model, effort, region, token)
    except anthropic.AuthenticationError as e:
        logger.error(f"Bedrock rejected the API key (401): {e.message}")
        raise typer.Exit(code=1) from e
    except anthropic.PermissionDeniedError as e:
        logger.error(
            f"Access denied (403) - is {MODEL_IDS[model]} enabled under Bedrock "
            f"model access in {region}? {e.message}"
        )
        raise typer.Exit(code=1) from e
    except anthropic.NotFoundError as e:
        logger.error(f"Model or endpoint not found (404): {e.message}")
        raise typer.Exit(code=1) from e
    except anthropic.RateLimitError as e:
        logger.error(f"Rate limited by Bedrock (429): {e.message}")
        raise typer.Exit(code=1) from e
    except anthropic.APIStatusError as e:
        logger.error(f"Bedrock API error ({e.status_code}): {e.message}")
        raise typer.Exit(code=1) from e
    except anthropic.APIConnectionError as e:
        logger.error(f"Could not reach bedrock-mantle.{region}.api.aws: {e}")
        raise typer.Exit(code=1) from e
    elapsed = time.monotonic() - started

    usage = message.usage
    logger.info(
        f"Done in {elapsed:.0f}s: {usage.input_tokens:,} input / "
        f"{usage.output_tokens:,} output tokens (stop: {message.stop_reason})"
    )

    if message.stop_reason == "refusal":
        details = message.stop_details
        category = getattr(details, "category", None)
        explanation = getattr(details, "explanation", None)
        logger.error(
            f"Claude declined the request (category={category}): {explanation}"
        )
        raise typer.Exit(code=1)

    summary = "".join(b.text for b in message.content if b.type == "text").strip()
    if not summary:
        logger.error("Response contained no text")
        raise typer.Exit(code=1)
    if message.stop_reason == "max_tokens":
        logger.warning(
            f"Output hit max_tokens ({MAX_OUTPUT_TOKENS:,}); summary is truncated"
        )

    final_path = resolve_output_path(output_path, clobber)
    final_path.write_text(summary + "\n", encoding="utf-8")
    logger.info(f"Wrote {final_path}")


if __name__ == "__main__":
    app()
