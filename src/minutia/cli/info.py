"""The ``minutia info`` command group — read-only introspection.

Bare ``minutia info`` prints the resolved settings and where each value came from (the former
top-level ``config`` command); ``info config`` is an explicit alias; ``info recordings`` lists the
newest ``.mkv`` files in the configured recordings dir. All of this is cheap — no heavy imports —
so it stays cold-start friendly.
"""

from collections.abc import Iterable
from pathlib import Path

import click
import typer

from ..config import MinutiaSettings

RECORDINGS_LIST_LIMIT = 10


def _list_recordings(recordings_dir: Path) -> list[Path]:
    """Return the ``.mkv`` files in ``recordings_dir``, newest first (by mtime)."""
    return sorted(
        recordings_dir.glob("*.mkv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _show_config(ctx: typer.Context) -> None:
    """Print resolved configuration values and where each came from."""
    resolution = ctx.obj["settings_resolution"]
    config: MinutiaSettings = resolution.settings
    rows: Iterable[tuple[str, object]] = (
        ("whisper_model", config.whisper_model),
        ("summary_model", config.summary_model),
        ("mic_track", config.mic_track),
        ("desktop_track", config.desktop_track),
        ("base_output_dir", config.base_output_dir),
        ("recordings_dir", config.recordings_dir),
        ("personal_info_path", config.personal_info_path),
        ("log_level", config.log_level),
        ("cleanup_policy", config.cleanup_policy.value),
        ("anthropic_api_key", config.masked_anthropic_key),
    )
    for name, value in rows:
        source = resolution.sources.get(name, "default")
        typer.echo(f"{name} = {value if value is not None else '<unset>'}  [{source}]")
    typer.echo(f"\ninvocation directory: {resolution.invocation_dir}")
    typer.echo(
        "contextual env file: "
        f"{resolution.context_env_file if resolution.context_env_file else '<none>'}"
    )
    typer.echo(f"user config file: {resolution.user_config_file}")
    typer.echo(
        "precedence: CLI flag > environment > contextual .env > user config > default"
    )


info_app = typer.Typer(
    name="info",
    help="Show resolved settings, provenance, and available recordings.",
    add_completion=False,
    invoke_without_command=True,
)


@info_app.callback(invoke_without_command=True)
def info_main(ctx: typer.Context) -> None:
    """Bare `info` shows resolved settings + provenance (same as `info config`)."""
    if ctx.invoked_subcommand is not None:
        return
    _show_config(ctx)


@info_app.command("config")
def config_cmd(ctx: typer.Context) -> None:
    """Show resolved configuration values and where each came from."""
    _show_config(ctx)


@info_app.command("recordings")
def recordings_cmd(ctx: typer.Context) -> None:
    """List the newest recordings in the configured recordings dir."""
    config: MinutiaSettings = ctx.obj["config"]
    if config.recordings_dir is None:
        raise click.ClickException(
            "No recordings directory configured. Set MINUTIA_RECORDINGS_DIR "
            "(e.g. in the user config) or run `minutia setup`."
        )
    recordings_dir = Path(config.recordings_dir).expanduser()
    if not recordings_dir.is_dir():
        raise click.ClickException(
            f"Recordings directory does not exist: {recordings_dir}"
        )
    recordings = _list_recordings(recordings_dir)
    if not recordings:
        typer.echo(f"No .mkv files found in {recordings_dir}")
        return
    typer.echo(f"Recordings in {recordings_dir} (newest first):")
    for index, path in enumerate(recordings[:RECORDINGS_LIST_LIMIT], start=1):
        typer.echo(f"  {index}. {path.name}")
    if len(recordings) > RECORDINGS_LIST_LIMIT:
        typer.echo(f"  … and {len(recordings) - RECORDINGS_LIST_LIMIT} more")
