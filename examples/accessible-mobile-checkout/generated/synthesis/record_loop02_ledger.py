#!/usr/bin/env python3
"""Record the terminal Synthesis Loop 02 task in the process ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SYNTHESIS_ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = SYNTHESIS_ROOT.parent
LOOP_ROOT = SYNTHESIS_ROOT / "loop-02"
LEDGER_PATH = GENERATED_ROOT / "harness" / "process-ledger.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    status = load(LOOP_ROOT / "status.json")
    process = load(LOOP_ROOT / "process.json")
    report = load(LOOP_ROOT / "evidence" / "objective-report.json")
    run = process["runs"][0]
    if (
        status["state"] != "complete"
        or status["objective_status"] != "pass"
        or run["terminal_state"] != "exited"
        or run["exit_code"] != 0
        or report["blocking_failure"]
        or report["failed_gate_ids"]
        or any(gate["status"] != "pass" for gate in report["gates"])
    ):
        raise RuntimeError("Synthesis Loop 02 is not a verified terminal pass.")
    for relative, expected in status["output_hashes"].items():
        path = (LOOP_ROOT / relative).resolve()
        if relative == "../manifest-fragment.json":
            path = SYNTHESIS_ROOT / "manifest-fragment.json"
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"Loop 02 output hash mismatch: {relative}")

    ledger = load(LEDGER_PATH)
    event = {
        "id": "task-synthesis-loop-02",
        "kind": "background_task",
        "role": "synthesizer",
        "model": "claude-opus-4.8",
        "command": "background task synthesis-loop-02",
        "task_handle": "synthesis-loop-02",
        "task_handle_kind": "background_agent_id",
        "pid": run["process_handle_pid"],
        "pid_scope": "terminal objective harness subprocess",
        "start_utc": status["start"],
        "heartbeat_utc": status["heartbeat"],
        "end_utc": status["end"],
        "terminal_status": "completed",
        "status_path": "../synthesis/loop-02/status.json",
        "objective_run": run,
        "objective_gate_states": {
            gate["id"]: gate["status"] for gate in report["gates"]
        },
        "objective_command_rerun": False,
        "repair_attempts": 0,
        "external_requests": 0,
        "output_paths": [
            "../synthesis/loop-02/metadata.json",
            "../synthesis/loop-02/evidence/objective-report.json",
            "../synthesis/loop-02/synthesis-report.md",
            "../synthesis/loop-02/status.json",
            "../synthesis/manifest-fragment.json",
        ],
        "output_sha256": {
            **{
                f"synthesis/loop-02/{relative}": value
                for relative, value in status["output_hashes"].items()
                if not relative.startswith("../")
            },
            "synthesis/loop-02/status.json": sha256(LOOP_ROOT / "status.json"),
            "synthesis/manifest-fragment.json": sha256(
                SYNTHESIS_ROOT / "manifest-fragment.json"
            ),
        },
        "working_directory": "repository root",
    }
    ledger["events"] = [
        item for item in ledger["events"] if item.get("id") != event["id"]
    ] + [event]
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "event_id": event["id"],
                "ledger_sha256": sha256(LEDGER_PATH),
                "status_sha256": event["output_sha256"][
                    "synthesis/loop-02/status.json"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
