"""Command-line interface for minutia.

Re-exports ``main`` — the click command object used by the ``minutia.cli:main`` console entry
point and by ``click.testing.CliRunner`` in tests — so the packaging entry point and callers keep
working after the flat ``cli.py`` became this subpackage.

The Typer application itself is intentionally *not* re-bound as ``minutia.cli.app``: that name
resolves to the ``app`` submodule (so tests can patch module-level names like
``minutia.cli.app.resolve_settings``). The Typer instance lives at ``minutia.cli.app.app``.
"""

from .app import main

__all__ = ["main"]
