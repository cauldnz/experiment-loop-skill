#!/usr/bin/env python3
"""Fail when a Generated Example is stale against its skill or Example Prompt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.example_regeneration._provenance import (  # noqa: E402
    file_sha256,
    tree_sha256,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "examples",
        nargs="*",
        help="optional Example names to check; the default checks every Example",
    )
    args = parser.parse_args(argv)
    expected_skill = tree_sha256(ROOT)
    failures = 0
    if args.examples:
        prompts = [ROOT / "examples" / name / "prompt.md" for name in args.examples]
    else:
        prompts = sorted((ROOT / "examples").glob("*/prompt.md"))
    for prompt in prompts:
        if not prompt.is_file():
            print(f"[FAIL] {prompt.parent.name}: prompt.md is missing")
            failures += 1
            continue
        manifest_path = prompt.parent / "generated" / "manifest.json"
        if not manifest_path.exists():
            print(f"[FAIL] {prompt.parent.name}: generated/manifest.json is missing")
            failures += 1
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[FAIL] {prompt.parent.name}: {exc}")
            failures += 1
            continue
        generation = manifest.get("generation", {})
        reasons = []
        if generation.get("skill_tree_sha256") != expected_skill:
            reasons.append("skill source changed")
        if generation.get("prompt_sha256") != file_sha256(prompt):
            reasons.append("Example Prompt changed")
        if reasons:
            print(f"[FAIL] {prompt.parent.name}: {', '.join(reasons)}")
            failures += 1
        else:
            print(f"[ok] {prompt.parent.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
