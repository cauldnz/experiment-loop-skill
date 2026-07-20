#!/usr/bin/env python3
"""Regenerate committed Generated Examples from their Example Prompts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.example_regeneration import regenerate_examples  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", nargs="*", help="example names; default is all")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--model", default="gpt-5.6-sol")
    args = parser.parse_args(argv)
    result = regenerate_examples(
        ROOT,
        names=tuple(args.examples),
        jobs=args.jobs,
        orchestrator_model=args.model,
    )
    print(f"EXAMPLE REGENERATION: {result.status.upper()}")
    for example in result.examples:
        print(f"  [{example.status.upper()}] {example.name}: {example.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
