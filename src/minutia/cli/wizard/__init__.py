"""The minutia wizard — full-screen interactive chrome.

``tui.py`` is the presentation layer (drawing + key handling); ``flow.py`` holds the setup +
guided-run flows and their pure cores. The public surface is the two flows.
"""

from .flow import RunPlan, run_guided, run_setup

__all__ = ["RunPlan", "run_guided", "run_setup"]
