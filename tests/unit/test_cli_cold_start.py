"""Cold-start discipline: the cheap CLI surfaces must not import the ML/AI stack.

`--version`, `--help`, and `config` are read-only / introspection-only and are hit constantly
(including shell completion and scripts). They must stay fast, which means never importing
torch/whisper (transcription) or anthropic (summarization). Those load lazily, behind dispatch,
only when a command that actually runs a step is invoked.

Run in a fresh subprocess so the assertion sees a clean `sys.modules` — the in-process test
session has almost certainly imported torch already via other tests.
"""

import subprocess
import sys

# Import the package + run the cheap surfaces, then report which heavy deps got pulled in.
_PROBE = """
import sys
from click.testing import CliRunner

import minutia.cli

runner = CliRunner()
for args in (["--version"], ["--help"], ["config"]):
    runner.invoke(minutia.cli.main, args, env={"MINUTIA_OUTPUT_DIR": "/tmp/minutia-cold-start"})

heavy = [name for name in ("torch", "whisper", "anthropic") if name in sys.modules]
print("HEAVY:" + ",".join(heavy))
"""


def test_cheap_cli_surfaces_do_not_import_heavy_deps():
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=True,
    )
    marker = next(
        line for line in result.stdout.splitlines() if line.startswith("HEAVY:")
    )
    loaded = marker.removeprefix("HEAVY:").strip()
    assert loaded == "", (
        f"--version/--help/config imported heavy deps ({loaded}); a module-level import "
        "regressed cold-start discipline. stdout:\n" + result.stdout
    )
