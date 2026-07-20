#!/usr/bin/env python3
"""Run the unified Evidence Gate over every committed Generated Example."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from references.evidence_gate import validate_experiment  # noqa: E402


def main() -> int:
    prompts = sorted((SKILL_ROOT / "examples").glob("*/prompt.md"))
    if not prompts:
        print("no Example Prompts found under examples/*/prompt.md")
        return 1

    failed = 0
    for prompt in prompts:
        generated = prompt.parent / "generated"
        if not generated.exists():
            print(f"[FAIL] {prompt.parent.name}: generated/ is missing")
            failed += 1
            continue
        report = validate_experiment(generated)
        print(f"[{'ok' if report.passed else 'FAIL'}] {prompt.parent.name}")
        for check in report.checks:
            if check.status != "pass":
                print(f"   {check.status}: {check.name}: {check.detail}")
        failed += 0 if report.passed else 1
    print(f"\n{len(prompts)} Generated Example(s) checked, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
