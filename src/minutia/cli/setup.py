"""The ``minutia setup`` command — run the config wizard unconditionally.

Thin wrapper over the wizard's setup flow. The wizard (and thus ``rich``) is imported **lazily**
inside the command so ``--help`` / ``--version`` / ``info`` never pull it.
"""

import typer


def setup_command(ctx: typer.Context) -> None:
    """Configure minutia — set your recordings folder and Anthropic API key."""
    from .wizard import run_setup

    try:
        run_setup(ctx.obj["config"])
    except KeyboardInterrupt:
        typer.echo("\nCancelled.")
