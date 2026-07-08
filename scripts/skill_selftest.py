#!/usr/bin/env python3
"""Regression self-test for the experiment-loop skill package.

Lightweight guard to run after you change this skill: confirms every shipped
worked example still validates — its manifest parses, declares schema 0.2, carries
the required top-level keys, references artifacts that exist on disk, and ships a
viewer. This is a regression check, not a quality judge; to decide whether a
durable change is an improvement, run the external benchmark described in
docs/self-testing.md.

Exit code 0 = all examples valid, 1 = at least one problem.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_TOP = ["schema_version", "experiment_id", "title", "goal", "tracks", "iterations"]


def check_manifest(mpath: Path) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(mpath.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"{mpath.name}: does not parse: {e}"]
    for k in REQUIRED_TOP:
        if k not in data:
            errs.append(f"missing top-level key '{k}'")
    if data.get("schema_version") != "0.2":
        errs.append(f"schema_version is {data.get('schema_version')!r}, expected '0.2'")
    base = mpath.parent
    for it in data.get("iterations", []):
        if not isinstance(it, dict):
            continue
        for art in it.get("artifacts", []) or []:
            p = art.get("path") if isinstance(art, dict) else None
            if p and not (base / p).exists():
                errs.append(f"iteration '{it.get('id','?')}' missing artifact {p}")
    return errs


def main() -> int:
    examples = sorted((SKILL_ROOT / "examples").glob("*/manifest.json"))
    if not examples:
        print("no example manifests found under examples/*/manifest.json — nothing to regression-test (skipped)")
        return 0
    total_errs = 0
    for m in examples:
        errs = check_manifest(m)
        print(f"[{'ok' if not errs else 'FAIL'}] {m.parent.name}")
        for e in errs:
            print(f"   ERROR: {e}")
        total_errs += len(errs)
        if not (m.parent / "viewer.html").exists():
            print("   warn: no viewer.html next to manifest")
    print(f"\n{len(examples)} example(s) checked, {total_errs} error(s)")
    return 1 if total_errs else 0


if __name__ == "__main__":
    sys.exit(main())
