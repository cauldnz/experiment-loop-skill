#!/usr/bin/env python3
"""Validate canonical human-feedback sidecars and their Manifest consumption chain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from references.human_feedback import validate_feedback_directory  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest_path = args.data / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot parse manifest.json: {exc}")
        return 1
    if not isinstance(manifest, dict):
        print("ERROR: manifest.json root must be an object")
        return 1
    errors = validate_feedback_directory(args.data, manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("HUMAN FEEDBACK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
