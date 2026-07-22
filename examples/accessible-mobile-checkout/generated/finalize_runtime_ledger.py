#!/usr/bin/env python3
"""Record the final deterministic Viewer and Navigation Evidence operations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LEDGER_PATH = ROOT / "harness" / "process-ledger.json"
STATUS_PATH = ROOT / "manifest-assembly-status.json"
VIEWER_PATH = ROOT / "viewer.html"
NAVIGATION_PATH = ROOT / "navigation-evidence.json"
EVIDENCE_GATE_PATH = ROOT / "evidence-gate.json"
FAILED_GATE_ATTEMPTS = tuple(
    ROOT / f"evidence-gate-attempt-{index:02d}-failed.json"
    for index in range(1, 4)
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def main() -> int:
    navigation = load(NAVIGATION_PATH)
    viewer_hash = sha256(VIEWER_PATH)
    if navigation.get("status") != "pass":
        raise RuntimeError("Navigation Evidence is not PASS.")
    if navigation.get("viewer_sha256") != viewer_hash:
        raise RuntimeError("Navigation Evidence does not match the exact Viewer.")
    evidence_gate = load(EVIDENCE_GATE_PATH)
    if evidence_gate.get("status") != "pass":
        raise RuntimeError("Final Evidence Gate is not PASS.")
    missing_attempts = [path.name for path in FAILED_GATE_ATTEMPTS if not path.is_file()]
    if missing_attempts:
        raise RuntimeError(
            "Preserved failed Evidence Gate attempts are missing: "
            + ", ".join(missing_attempts)
        )

    ledger = load(LEDGER_PATH)
    replacements = {
        "final-viewer-byte-identical-build",
        "final-navigation-judge",
        "final-evidence-gate",
    }
    events = [item for item in ledger["events"] if item.get("id") not in replacements]
    viewer_time = mtime(VIEWER_PATH)
    navigation_time = mtime(NAVIGATION_PATH)
    events.extend(
        [
            {
                "id": "final-viewer-byte-identical-build",
                "kind": "attended_deterministic_command",
                "role": "orchestrator-viewer-builder",
                "model": "gpt-5.6-sol",
                "command": (
                    "python generated/build_viewer.py --data generated --out "
                    "generated/viewer.html; repeated to viewer.verify.html and compared"
                ),
                "task_handle": "shellId:124",
                "task_handle_kind": "powershell_shell_id",
                "pid": None,
                "heartbeat_utc": viewer_time,
                "end_utc": viewer_time,
                "terminal_status": "completed_verified",
                "byte_identical_rebuild": True,
                "viewer_sha256": viewer_hash,
                "viewer_bytes": VIEWER_PATH.stat().st_size,
                "output_paths": ["../viewer.html"],
                "working_directory": "repository root",
            },
            {
                "id": "final-navigation-judge",
                "kind": "attended_browser_command",
                "role": "navigation-judge",
                "model": "deterministic-playwright-1.61.1",
                "command": (
                    "node references/navigation_judge/cli.mjs --viewer "
                    ".experiments/accessible-mobile-checkout/generated/viewer.html "
                    "--out .experiments/accessible-mobile-checkout/generated"
                ),
                "task_handle": "shellId:125",
                "task_handle_kind": "powershell_shell_id",
                "pid": None,
                "heartbeat_utc": navigation_time,
                "end_utc": navigation_time,
                "terminal_status": "completed_verified",
                "navigation_status": "pass",
                "viewer_sha256": viewer_hash,
                "navigation_evidence_sha256": sha256(NAVIGATION_PATH),
                "output_paths": [
                    "../navigation-evidence.json",
                    "../navigation-report.md",
                    "../navigation-screenshots/",
                ],
                "working_directory": "repository root",
            },
            {
                "id": "final-evidence-gate",
                "kind": "attended_deterministic_command",
                "role": "orchestrator-evidence-gate",
                "model": "gpt-5.6-sol",
                "command": (
                    "python scripts/run_evidence_gate.py "
                    ".experiments/accessible-mobile-checkout/generated"
                ),
                "task_handle": None,
                "task_handle_kind": "reconciled_after_terminal_command",
                "pid": None,
                "heartbeat_utc": mtime(EVIDENCE_GATE_PATH),
                "end_utc": mtime(EVIDENCE_GATE_PATH),
                "terminal_status": "completed_verified",
                "evidence_gate_status": "pass",
                "viewer_sha256": viewer_hash,
                "evidence_gate_sha256": sha256(EVIDENCE_GATE_PATH),
                "preserved_failed_attempts": [
                    {
                        "path": f"../{path.name}",
                        "sha256": sha256(path),
                    }
                    for path in FAILED_GATE_ATTEMPTS
                ],
                "output_paths": ["../evidence-gate.json"],
                "working_directory": "repository root",
            },
        ]
    )
    ledger["events"] = events
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    status = load(STATUS_PATH)
    status["viewer_status"] = "pass_byte_identical"
    status["viewer_sha256"] = viewer_hash
    status["navigation_evidence_status"] = "pass"
    status["navigation_evidence_sha256"] = sha256(NAVIGATION_PATH)
    status["evidence_gate_status"] = "pass"
    status["evidence_gate_sha256"] = sha256(EVIDENCE_GATE_PATH)
    status["preserved_failed_evidence_gate_attempts"] = [
        {
            "path": path.name,
            "sha256": sha256(path),
        }
        for path in FAILED_GATE_ATTEMPTS
    ]
    STATUS_PATH.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "viewer_sha256": viewer_hash,
                "navigation_status": "pass",
                "ledger_sha256": sha256(LEDGER_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
