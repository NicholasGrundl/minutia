"""Cut a release: bump -> commit -> tag -> push.

    uv run python scripts/release.py {patch|minor|major} [-n]

Pushing the v* tag triggers .github/workflows/release.yml, whose guard
requires the tag to equal v$(uv version --short); the ordering here
guarantees that.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

LEVELS = ("patch", "minor", "major")


def run(cmd: list[str], *, capture: bool = False) -> str:
    print("+", " ".join(cmd))
    result = subprocess.run(
        cmd, text=True, capture_output=capture
    )  # shell=False (default)
    if result.returncode != 0:
        sys.exit(f"error: command failed: {' '.join(cmd)}")
    return (result.stdout or "").strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump the version, commit, tag, and push."
    )
    parser.add_argument(
        "level", choices=LEVELS, help="which part of the version to bump"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="preview the tag; write and push nothing",
    )
    args = parser.parse_args()
    level = args.level

    # check if git has uncommitted changes
    dirty = run(["git", "status", "--porcelain"], capture=True)

    # check what tags would be bumped and what exist now
    version = run(
        ["uv", "version", "--bump", level, "--dry-run", "--short"], capture=True
    )
    tag = f"v{version}"
    exists = run(["git", "tag", "--list", tag], capture=True)

    print(f"\nrelease plan: {level} bump -> {tag}")
    if args.dry_run:
        if dirty:
            print("warning: working tree is not clean")
        if exists:
            print(f"warning: tag {tag} already exists")
        print("dry run - nothing written.")
        return

    if dirty:
        sys.exit("error: working tree not clean — commit or stash first")
    if exists:
        sys.exit(f"error: tag {tag} already exists")

    # workflow's guard checks. Each step is a fixed command list.
    run(["uv", "version", "--bump", level])
    run(["git", "add", "pyproject.toml", "uv.lock"])
    run(["git", "commit", "-m", f"chore: release {tag}"])
    run(["git", "tag", tag])
    run(["git", "push"])
    run(["git", "push", "origin", tag])
    print(f"\nreleased {tag}")


if __name__ == "__main__":
    main()
