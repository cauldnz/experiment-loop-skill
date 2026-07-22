#!/usr/bin/env python3
"""Append the verified reboot reconciliation sidecar to the process ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


RECOVERY_ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = RECOVERY_ROOT.parents[1]
LEDGER_PATH = GENERATED_ROOT / "harness" / "process-ledger.json"
SIDECAR_PATH = RECOVERY_ROOT / "reconciliation-ledger-event.json"
VERIFICATION_PATH = RECOVERY_ROOT / "post-recovery-verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    sidecar = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))
    verification = json.loads(VERIFICATION_PATH.read_text(encoding="utf-8"))
    if verification.get("result") != "PASS":
        raise RuntimeError("Post-recovery verification is not PASS.")
    expected = {
        item["path"]: item["sha256"]
        for item in verification["new_required_records_verification"]["records"]
    }
    sidecar_relative = "synthesis/recovery/reconciliation-ledger-event.json"
    if expected.get(sidecar_relative) != sha256(SIDECAR_PATH):
        raise RuntimeError("Reconciliation sidecar hash does not match verification.")
    if not verification["immutable_outputs_verification"]["all_match_launch_inventory"]:
        raise RuntimeError("Immutable synthesis outputs do not match recovery inventory.")

    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    event = {
        "id": "task-synthesis-loop-01-reboot-reconciliation",
        "kind": "background_task_recovery",
        "role": "synthesizer",
        "model": sidecar["model_id"],
        "command": "background task synthesis-loop-01 followed by explicitly authorized continuation synthesis-loop-01-recovery",
        "task_handle": sidecar["original_agent_handle"],
        "continuation_task_handle": sidecar["continuation_task_identity"],
        "task_handle_kind": "background_agent_id",
        "pid": sidecar["objective_run"]["process_pid"],
        "start_utc": sidecar["objective_run"]["start_utc"],
        "heartbeat_utc": sidecar["recovery_window"]["heartbeat_utc"],
        "end_utc": sidecar["recovery_window"]["end_utc"],
        "terminal_status": sidecar["terminal_status"],
        "interruption_classification": sidecar["interruption_classification"],
        "objective_run": sidecar["objective_run"],
        "reboot_provenance": sidecar["reboot_provenance"],
        "output_paths": [
            "../synthesis/loop-01/metadata.json",
            "../synthesis/loop-01/synthesis-report.md",
            "../synthesis/loop-01/status.json",
            "../synthesis/manifest-fragment.json",
            "../synthesis/recovery/recovery-inventory.json",
            "../synthesis/recovery/reconciliation-ledger-event.json",
            "../synthesis/recovery/post-recovery-verification.json",
        ],
        "output_sha256": {
            **{
                item["path"]: item["sha256"]
                for item in verification[
                    "new_required_records_verification"
                ]["records"]
            },
            "synthesis/recovery/post-recovery-verification.json": sha256(
                VERIFICATION_PATH
            ),
            "synthesis/recovery/recovery-inventory.json": verification[
                "immutable_inventory"
            ]["current_sha256"],
        },
        "objective_command_rerun": False,
        "immutable_output_count": verification[
            "immutable_outputs_verification"
        ]["count"],
        "immutable_outputs_unchanged": True,
        "working_directory": "repository root",
    }
    events = [
        item
        for item in ledger["events"]
        if item.get("id") != event["id"]
    ]
    events.append(event)
    ledger["events"] = events
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "event_id": event["id"],
                "event_count": len(events),
                "ledger_sha256": sha256(LEDGER_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
