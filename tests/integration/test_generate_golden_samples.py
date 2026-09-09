import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_generate_golden_samples_discovery(tmp_path):
    """Test that the generate_golden_samples script can discover scenarios."""
    # Create a dummy scenario structure
    scenario_dir = tmp_path / "scenarios" / "test_scenario"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "input.mkv").write_text("fake mkv content")

    # Path to the script
    script_path = (
        Path(__file__).parent.parent / "scripts" / "generate_golden_samples.py"
    )

    # Run the script with --dry-run or similar if we implement it,
    # or just check if it fails when no real mkv is present
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--fixtures-dir",
            str(tmp_path),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Found scenario: test_scenario" in result.stdout
