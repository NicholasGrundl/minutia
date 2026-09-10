"""Top-level Typer application for minutia.

Thin wiring layer: the ``--env-file`` / ``--no-env-file`` / ``--version`` top-level options and the
settings-resolution callback live here, plus the read-only ``config`` command. Pipeline execution
lives under the ``run`` group (:mod:`.run`); the heavy work stays behind dispatch for cold start.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Annotated

import click
import typer

from ..config import ConfigurationError, resolve_settings
from ..logging import configure_logging, logger
from .info import info_app
from .run import run_app

app = typer.Typer(
    name="minutia",
    help="OBS Video Processing CLI",
    add_completion=False,
)

EnvFileOption = Annotated[
    Path | None,
    typer.Option(
        "--env-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Use this contextual .env file instead of automatic discovery",
    ),
]
NoEnvFileOption = Annotated[
    bool,
    typer.Option(
        "--no-env-file",
        help="Disable contextual .env discovery (the user config still loads)",
    ),
]


def _package_version() -> str:
    """Installed package version, or ``unknown`` when running from an unbuilt tree."""
    try:
        return _pkg_version("minutia")
    except PackageNotFoundError:
        return "unknown"


def _version_callback(value: bool) -> None:
    """Eager ``--version``: print and exit before any settings/logging work runs."""
    if value:
        typer.echo(_package_version())
        raise typer.Exit()


VersionOption = Annotated[
    bool,
    typer.Option(
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
]


@app.callback()
def main_callback(
    ctx: typer.Context,
    env_file: EnvFileOption = None,
    no_env_file: NoEnvFileOption = False,
    version: VersionOption = False,
):
    """OBS Video Processing CLI"""
    if env_file is not None and no_env_file:
        raise click.ClickException(
            "--env-file and --no-env-file cannot be used together"
        )
    try:
        resolution = resolve_settings(
            env_file=env_file,
            discover_dotenv=not no_env_file,
        )
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    config = resolution.settings
    configure_logging(level=config.log_level)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["settings_resolution"] = resolution
    logger.info(
        "CLI initialised with whisper_model={}, summary_model={}, output_dir={}, anthropic_key={}",
        config.whisper_model,
        config.summary_model,
        config.base_output_dir,
        config.masked_anthropic_key,
    )


app.add_typer(run_app, name="run")
app.add_typer(info_app, name="info")


# Click-compatible command object: keeps the console-script entry point
# (minutia.cli:main), the package re-export, and click.testing.CliRunner working.
main = typer.main.get_command(app)

if __name__ == "__main__":
    main()
