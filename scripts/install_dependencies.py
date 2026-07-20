#!/usr/bin/env python3
"""Install required dependencies with optional runtime-only npm registry injection."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent


def _registry(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("npm registry must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("npm registry URL must not contain credentials")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npm-registry",
        help=(
            "npm upstream for this process only; defaults to "
            "EXPERIMENT_LOOP_NPM_REGISTRY, then NPM_CONFIG_REGISTRY"
        ),
    )
    args = parser.parse_args(argv)

    registry = _registry(
        args.npm_registry
        or os.environ.get("EXPERIMENT_LOOP_NPM_REGISTRY")
        or os.environ.get("NPM_CONFIG_REGISTRY")
    )
    npm_env = os.environ.copy()
    if registry:
        npm_env["NPM_CONFIG_REGISTRY"] = registry
        print("Using a runtime-injected npm registry (not persisted).")
    else:
        print("Using npm's existing registry configuration.")

    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    npx = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    if not npm or not npx:
        print("npm and npx must be available on PATH.", file=sys.stderr)
        return 1

    commands = [
        (
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            ROOT,
            os.environ.copy(),
        ),
        (
            [npm, "ci"],
            ROOT / "references" / "navigation_judge",
            npm_env,
        ),
        (
            [npx, "playwright", "install", "chromium"],
            ROOT / "references" / "navigation_judge",
            npm_env,
        ),
    ]
    for command, cwd, env in commands:
        result = subprocess.run(command, cwd=cwd, env=env, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
