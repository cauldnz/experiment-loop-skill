#!/usr/bin/env python3
"""Validate an experiment-loop manifest.json against schema v0.2 + evidence rules.

Dependency-free (stdlib only) so it can run anywhere. Turns manifest/evidence
conformance into a blocking gate: a run whose manifest is not schema-complete
cannot be reported as done.

Checks performed:
  1. manifest.json parses as JSON
  2. required top-level keys present; schema_version == "0.2"
  3. each iteration carries every required loop field
  4. decision values are within the allowed enum
  5. artifact paths referenced by the manifest exist on disk (relative to the
     manifest directory)
  6. if a sibling viewer.html exists, any embedded manifest JSON parses
  7. a sibling viewer.html is present for visual or multi-loop runs

Exit code 0 = pass, 1 = fail. Use --json for a machine-readable report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_TOP = ["schema_version", "experiment_id", "title", "goal", "tracks", "iterations"]
REQUIRED_ITER = ["id", "track_id", "parent_id", "hypothesis", "commands",
                 "artifacts", "scores", "changed_files", "lesson", "decision"]
VISUAL_KINDS = {"image", "gif", "video", "screenshot", "contact_sheet", "contact"}
DECISION_ENUM = {"new_best", "reject", "keep_for_synthesis", "needs_human_review", "failed"}


def _report():
    return {"ok": True, "errors": [], "warnings": [], "checks": {}}


def _fail(rep, msg):
    rep["ok"] = False
    rep["errors"].append(msg)


def validate(manifest_path: Path, strict_viewer: bool = False) -> dict:
    rep = _report()
    manifest_path = Path(manifest_path)
    base = manifest_path.parent

    # 1. parses as JSON
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(rep, f"manifest not found: {manifest_path}")
        return rep
    except json.JSONDecodeError as e:
        _fail(rep, f"manifest.json does not parse: {e}")
        return rep
    rep["checks"]["json_parses"] = True

    if not isinstance(data, dict):
        _fail(rep, "manifest root must be a JSON object")
        return rep

    # 2. required top-level keys + schema version
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        _fail(rep, f"missing required top-level keys: {missing}")
    if data.get("schema_version") != "0.2":
        _fail(rep, f"schema_version must be '0.2' (got {data.get('schema_version')!r})")
    rep["checks"]["top_level_keys"] = not missing

    # 3 + 4. iterations
    iterations = data.get("iterations", [])
    if not isinstance(iterations, list):
        _fail(rep, "iterations must be an array")
        iterations = []
    iter_problems = 0
    for i, it in enumerate(iterations):
        if not isinstance(it, dict):
            _fail(rep, f"iteration[{i}] is not an object")
            iter_problems += 1
            continue
        miss = [k for k in REQUIRED_ITER if k not in it]
        if miss:
            _fail(rep, f"iteration '{it.get('id', i)}' missing fields: {miss}")
            iter_problems += 1
        dec = it.get("decision")
        if dec is not None and dec not in DECISION_ENUM:
            _fail(rep, f"iteration '{it.get('id', i)}' has invalid decision {dec!r}")
            iter_problems += 1
    rep["checks"]["iterations_valid"] = iter_problems == 0
    rep["checks"]["iteration_count"] = len(iterations)

    # 5. artifact path existence
    missing_paths = []
    checked_paths = 0
    def _check_artifacts(artifacts):
        nonlocal checked_paths
        for art in artifacts or []:
            if not isinstance(art, dict):
                continue
            for key in ("path", "contact_path"):
                p = art.get(key)
                if not p:
                    continue
                checked_paths += 1
                if not (base / p).exists():
                    missing_paths.append(p)

    for it in iterations:
        if isinstance(it, dict):
            _check_artifacts(it.get("artifacts"))
    for tr in data.get("tracks", []):
        if isinstance(tr, dict):
            _check_artifacts(tr.get("finals"))
    if missing_paths:
        _fail(rep, f"{len(missing_paths)} artifact path(s) do not exist: {missing_paths[:8]}")
    rep["checks"]["artifact_paths_checked"] = checked_paths
    rep["checks"]["artifact_paths_missing"] = len(missing_paths)

    # 6. embedded viewer manifest parses (best-effort)
    viewer = base / "viewer.html"
    if viewer.exists():
        ok, note = _viewer_manifest_parses(viewer)
        rep["checks"]["viewer_manifest_parses"] = ok
        if not ok:
            if strict_viewer:
                _fail(rep, f"viewer.html embedded manifest does not parse: {note}")
            else:
                rep["warnings"].append(f"viewer.html embedded manifest not verified: {note}")

    # 7. viewer presence for visual / multi-loop runs
    kinds = set()
    for it in iterations:
        for art in (it.get("artifacts") or []):
            if isinstance(art, dict) and art.get("kind"):
                kinds.add(str(art.get("kind")).lower())
    expects_viewer = len(iterations) > 1 or bool(kinds & VISUAL_KINDS)
    if expects_viewer:
        rep["checks"]["viewer_present"] = viewer.exists()
        if not viewer.exists():
            msg = "no sibling viewer.html for a visual/multi-loop run"
            if strict_viewer:
                _fail(rep, msg)
            else:
                rep["warnings"].append(msg)

    return rep


def _viewer_manifest_parses(viewer_path: Path) -> tuple[bool, str]:
    text = viewer_path.read_text(encoding="utf-8", errors="replace")
    # pattern A: <script id="manifest" type="application/json"> ... </script>
    m = re.search(
        r'<script[^>]*id=["\']manifest["\'][^>]*>(.*?)</script>',
        text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            json.loads(m.group(1).strip())
            return True, "script-tag JSON ok"
        except json.JSONDecodeError as e:
            return False, f"script-tag JSON invalid: {e}"
    # pattern B: const/var/let MANIFEST = { ... };
    m = re.search(r'(?:const|var|let)\s+MANIFEST\s*=\s*(\{.*?\})\s*;', text, re.DOTALL)
    if m:
        try:
            json.loads(m.group(1))
            return True, "MANIFEST literal ok"
        except json.JSONDecodeError as e:
            return False, f"MANIFEST literal invalid: {e}"
    return True, "no embedded manifest found (skipped)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate an experiment-loop manifest (schema v0.2).")
    ap.add_argument("manifest", help="path to manifest.json")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    ap.add_argument("--strict-viewer", action="store_true", help="fail if embedded viewer manifest is invalid")
    args = ap.parse_args(argv)

    rep = validate(Path(args.manifest), strict_viewer=args.strict_viewer)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        status = "PASS" if rep["ok"] else "FAIL"
        print(f"[{status}] {args.manifest}")
        for e in rep["errors"]:
            print(f"  ERROR: {e}")
        for w in rep["warnings"]:
            print(f"  warn:  {w}")
        print(f"  checks: {json.dumps(rep['checks'])}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
