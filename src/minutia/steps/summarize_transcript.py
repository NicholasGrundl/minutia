import json
from pathlib import Path

import tiktoken
from anthropic import Anthropic

from ..config import resolve_anthropic_api_key
from ..logging import logger
from ..prompts import get_filename_prompt

MAX_TOKENS_OUTPUT = (
    8192  # Max model output. Around 3.1K words (6-7 single spaced pages)
)

# Model information
# Pricing source: Anthropic API docs, verified April 29, 2026.
# Convention: per-1k tokens (Anthropic publishes per-MTok; divide by 1000).
# Output is 5x input across the entire current lineup — handy for budgeting.
anthropic_models = {
    # ---- Current generation (Claude 4.x, recommended for new work) ----
    "claude-opus-4-7": {
        "name": "claude-opus-4-7",  # released 2026-04-16, current flagship
        "price_per_1k_input_tokens": 0.005,
        "price_per_1k_output_tokens": 0.025,
    },
    "claude-opus-4-6": {
        "name": "claude-opus-4-6",  # previous flagship, same price as 4.7
        "price_per_1k_input_tokens": 0.005,
        "price_per_1k_output_tokens": 0.025,
    },
    "claude-sonnet-4-6": {
        "name": "claude-sonnet-4-6",  # best price/perf, 1M context at flat rate
        "price_per_1k_input_tokens": 0.003,
        "price_per_1k_output_tokens": 0.015,
    },
    "claude-haiku-4-5": {
        "name": "claude-haiku-4-5-20251001",  # fast/cheap current-gen
        "price_per_1k_input_tokens": 0.001,
        "price_per_1k_output_tokens": 0.005,
    },
    # ---- Legacy (still callable, kept for backward compatibility) ----
    "claude-sonnet-4-5": {
        "name": "claude-sonnet-4-5-20250929",
        "price_per_1k_input_tokens": 0.003,
        "price_per_1k_output_tokens": 0.015,
    },
    "claude-3-7-sonnet": {
        "name": "claude-3-7-sonnet-20250219",
        "price_per_1k_input_tokens": 0.003,
        "price_per_1k_output_tokens": 0.015,
    },
    "claude-3-haiku": {
        "name": "claude-3-haiku-20240307",
        "price_per_1k_input_tokens": 0.00025,
        "price_per_1k_output_tokens": 0.00125,
    },
}


def load_transcript(file_path):
    """Load the merged transcript from a JSON file."""
    try:
        with open(file_path) as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.exception("Error loading transcript: {}", e)
        raise


def prepare_transcript_for_summary(transcript_data):
    """Extract relevant information from the transcript for summarization."""
    transcript_text = ""
    for segment in transcript_data["transcript"]:
        source = segment["source"]
        text = segment["text"]
        transcript_text += f"[{source.capitalize()}] {text}\n"
    return transcript_text


def create_summary_prompt(transcript_text):
    """Create a prompt for the language model to generate a summary."""
    prompt = f"""Please provide a summary of the following meeting transcript. The target audience is a general reader who may not have been present at the meeting but wants to know the technical details discussed.

    <summaryformat>
    Use markdown formatting for headers, bulleted lists, numbered lists and emphasis via bold and italics.

    Try to include around a page or two of notes total balancing brevity with information content.
    </summaryformat>

    <summarydirections>
    First create an executive summary section at the beginning of the summary providing a high level oiverview of who, what, where and when.

    Second reflect critically on the major topics discussed in the meeting and make a numbered list of each of these major topics.

    Third, create a heading section for each major topic and expand on the details focusing on technical content, existing or proposed projects or efforts, decisions, and timelines.

    Fourth, review the existing summary text and add any additional information or relevant notes.

    Finally, end with a action items and conclusion section.
    </summarydirections>


    Here's the transcript:

    <transcript>
    {transcript_text}

    </transcript>

    Please summarize this meeting transcript based on the instructions given in <summaryformat> and <summarydirections>.
    """
    return prompt


def estimate_tokens(text):
    """Estimate the number of tokens in the given text."""
    encoding = tiktoken.encoding_for_model(
        "gpt-3.5-turbo"
    )  # This works for Claude models too
    return len(encoding.encode(text))


def estimate_price(
    input_tokens, output_tokens, price_per_1k_input_tokens, price_per_1k_output_tokens
):
    """Estimate the price for the API call based on input and output tokens."""
    input_price = (input_tokens / 1000) * price_per_1k_input_tokens
    output_price = (output_tokens / 1000) * price_per_1k_output_tokens

    price = input_price + output_price
    return price


def estimate_tokens_and_price(
    transcript_text, model="claude-sonnet-4-6", max_output_tokens=None
):
    """Estimate tokens and price for summarizing the transcript."""
    if max_output_tokens is None:
        max_output_tokens = MAX_TOKENS_OUTPUT

    if model not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")

    info = anthropic_models[model]
    price_per_1k_input_tokens = info["price_per_1k_input_tokens"]
    price_per_1k_output_tokens = info["price_per_1k_output_tokens"]

    prompt = create_summary_prompt(transcript_text)
    input_tokens = estimate_tokens(prompt)
    output_tokens = max_output_tokens
    total_tokens = input_tokens + output_tokens
    estimated_price = estimate_price(
        input_tokens,
        output_tokens,
        price_per_1k_input_tokens,
        price_per_1k_output_tokens,
    )
    logger.info("Estimating metrics for {}", model)
    logger.info("input tokens: {}", input_tokens)
    logger.info("output tokens: {}", output_tokens)
    logger.info("total tokens: {}", total_tokens)
    logger.info("price: ${:.4f}", estimated_price)

    return total_tokens, estimated_price


def generate_long_summary(
    transcript_text,
    model_name="claude-sonnet-4-6",
    max_output_tokens=None,
    system_prompt=None,
    api_key=None,
    **kwargs,
):
    """Generate a summary using the Anthropic API. Allow multiple continues for length"""
    if max_output_tokens is None:
        max_output_tokens = MAX_TOKENS_OUTPUT

    if model_name not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")
    model = anthropic_models.get(model_name)["name"]

    api_key = api_key or resolve_anthropic_api_key()
    if not api_key:
        raise RuntimeError("Anthropic API key not configured")
    client = Anthropic(api_key=api_key)

    if system_prompt is None:
        # old approach
        prompt = create_summary_prompt(transcript_text)
        messages = [{"role": "user", "content": prompt}]
    else:
        user_prompt = f"Here's the transcript:\n\n{transcript_text}"
        messages = [
            {"role": "user", "content": user_prompt},
        ]

    full_summary = ""
    while True:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_output_tokens,
                temperature=0.1,
                system=system_prompt,
                messages=messages,
                **kwargs,
            )

            summary_part = response.content[0].text
            full_summary += summary_part

            if summary_part.endswith("[CONTINUE]"):
                full_summary = full_summary[:-10]  # Remove the [CONTINUE] tag
                messages.append({"role": "assistant", "content": summary_part})
                messages.append(
                    {"role": "user", "content": "Please continue the summary."}
                )
            else:
                break
        except Exception as e:
            logger.exception("Error generating summary: {}", e)
            raise
    return full_summary


def generate_summary(
    transcript_text,
    model_name="claude-sonnet-4-6",
    max_output_tokens=None,
    system_prompt=None,
    api_key=None,
    **kwargs,
):
    """Generate a summary using the Anthropic API."""
    if max_output_tokens is None:
        max_output_tokens = MAX_TOKENS_OUTPUT

    if model_name not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")
    model = anthropic_models.get(model_name)["name"]

    api_key = api_key or resolve_anthropic_api_key()
    if not api_key:
        raise RuntimeError("Anthropic API key not configured")
    client = Anthropic(api_key=api_key)
    if system_prompt is None:
        # old approach
        prompt = create_summary_prompt(transcript_text)
        messages = [{"role": "user", "content": prompt}]
    else:
        user_prompt = f"Here's the transcript:\n\n{transcript_text}"
        messages = [
            {"role": "user", "content": user_prompt},
        ]

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_output_tokens,
            temperature=0,
            system=system_prompt,
            messages=messages,
            **kwargs,
        )
        return response.content[0].text
    except Exception as e:
        logger.exception("Error generating summary: {}", e)
        raise


def get_filename_from_content(
    content, model_name="claude-sonnet-4-6", api_key=None
) -> str:
    """Use Anthropic to generate a descriptive filename for markdown exports."""
    if model_name not in anthropic_models:
        raise KeyError(f"model must be one of [{list(anthropic_models.keys())}]")
    model = anthropic_models[model_name]["name"]

    api_key = api_key or resolve_anthropic_api_key()
    if not api_key:
        raise RuntimeError("Anthropic API key not configured")
    client = Anthropic(api_key=api_key)

    prompt = get_filename_prompt(content)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.exception("Error generating filename: {}", e)
        raise


def create_markdown_report(
    content,
    output_path,
    model_name="claude-sonnet-4-6",
    api_key=None,
) -> Path:
    """Persist a markdown report using an Anthropic-generated filename."""
    filename = get_filename_from_content(
        content, model_name=model_name, api_key=api_key
    )
    filepath = Path(output_path) / f"{filename}.md"
    logger.info("Writing markdown report to {}", filepath)
    filepath.write_text(content, encoding="utf-8")
    return filepath


def save_summary(summary, output_file):
    """Save the generated summary to a file."""
    try:
        with open(output_file, "w") as f:
            f.write(summary)
        logger.info("Summary saved to {}", output_file)
    except Exception as e:
        logger.exception("Error saving summary: {}", e)
        raise
