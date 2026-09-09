"""Slow tier: full-pipeline tests that call the *real* Anthropic API.

Tests placed in this directory are auto-marked ``slow`` by the directory-based
marker in the root ``tests/conftest.py`` and are excluded from the default and
``unit``/``integration`` runs. They execute only under ``-m slow`` (see the
``test-all`` recipe) and only when a real key is present.

Isolation caveat: the root autouse ``_scrub_minutia_environment`` strips
``ANTHROPIC_API_KEY`` before every test. We therefore capture the real key at
import (collection) time — before any per-test scrub runs — and, for slow tests
only, re-inject it past the scrub. Without a real key the whole tier skips, so
CI and offline runs never spend money.
"""

import os

import pytest

# Captured at collection time, before the per-test env-scrub deletes it.
_REAL_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def _looks_real(key: str) -> bool:
    """A real Anthropic key is ``sk-ant-…``; the test baseline key is not."""
    return key.startswith("sk-ant-")


@pytest.fixture(autouse=True)
def _require_real_anthropic_key(monkeypatch):
    """Skip the slow tier without a real key; restore it past the env-scrub."""
    if not _looks_real(_REAL_ANTHROPIC_KEY):
        pytest.skip("slow tier needs a real ANTHROPIC_API_KEY (sk-ant-…)")
    monkeypatch.setenv("ANTHROPIC_API_KEY", _REAL_ANTHROPIC_KEY)
