"""
Anthropic model registry: CLI/config choices and pricing in one place.

This module has no intra-package imports so it can be used from steps, the
pipeline orchestrator, config validation, and the CLI without import cycles.
"""

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

DEFAULT_SUMMARY_MODEL = "claude-sonnet-4-6"

__all__ = ["anthropic_models", "DEFAULT_SUMMARY_MODEL"]
