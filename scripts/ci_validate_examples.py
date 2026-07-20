#!/usr/bin/env python3
"""Rerun Navigation Evidence and the Evidence Gate for every Generated Example."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from references.evidence_gate import validate_experiment  # noqa: E402


def main() -> int:
    failures = 0
    judge = ROOT / "references" / "navigation_judge" / "cli.mjs"
    for prompt in sorted((ROOT / "examples").glob("*/prompt.md")):
        name = prompt.parent.name
        generated = prompt.parent / "generated"
        viewer = generated / "viewer.html"
        with tempfile.TemporaryDirectory(prefix=f"navigation-{name}-") as temp_dir:
            navigation = subprocess.run(
                [
                    "node",
                    str(judge),
                    "--viewer",
                    str(viewer),
                    "--out",
                    temp_dir,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if navigation.returncode != 0:
                print(f"[FAIL] {name}: navigation judge")
                print((navigation.stdout + navigation.stderr)[-2000:])
                failures += 1
                continue
            evidence = json.loads(
                (Path(temp_dir) / "navigation-evidence.json").read_text(
                    encoding="utf-8"
                )
            )
            if evidence.get("status") != "pass":
                print(f"[FAIL] {name}: navigation status is not pass")
                failures += 1
                continue

        gate = validate_experiment(generated)
        if gate.passed:
            print(f"[ok] {name}")
        else:
            print(f"[FAIL] {name}: Evidence Gate")
            for check in gate.checks:
                if check.status != "pass":
                    print(f"  {check.status}: {check.name}: {check.detail}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
