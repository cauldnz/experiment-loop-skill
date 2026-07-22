#!/usr/bin/env python3
"""Record reconciled Loop 02 judge tasks and deterministic aggregation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT.parents[1]
LEDGER_PATH = GENERATED_ROOT / "harness" / "process-ledger.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def replace_event(events: list[dict[str, Any]], event: dict[str, Any]) -> None:
    events[:] = [item for item in events if item.get("id") != event["id"]]
    events.append(event)


def judge_event(
    *,
    event_id: str,
    judge_id: str,
    model: str,
    agent_id: str,
    task_call_id: str,
) -> dict[str, Any]:
    judge_root = ROOT / judge_id
    status_path = judge_root / "status.json"
    status = load_json(status_path)
    status_mtime = iso_mtime(status_path)
    return {
        "id": event_id,
        "kind": "background_task",
        "role": judge_id,
        "model": model,
        "command": f"background task {judge_id}-loop-02",
        "task_handle": agent_id,
        "task_handle_kind": "background_agent_id",
        "task_call_id": task_call_id,
        "pid": None,
        "pid_reason": "The background task API exposed an agent task handle, not an operating-system PID.",
        "working_directory": "repository root",
        "start_utc": datetime.fromtimestamp(
            status_path.stat().st_ctime, timezone.utc
        ).isoformat(),
        "start_source": "observed status Artifact creation time",
        "heartbeat_utc": status_mtime,
        "heartbeat_source": "observed terminal status Artifact modification time",
        "end_utc": status_mtime,
        "end_source": "observed terminal status Artifact modification time",
        "terminal_status": "completed",
        "status_path": f"../judging/loop-02/{judge_id}/status.json",
        "status_reported_timestamps": {
            key: status[key]
            for key in (
                "started_at",
                "last_heartbeat",
                "heartbeat",
                "completed_at",
                "terminal_at",
                "ended_at",
            )
            if key in status
        },
        "status_timestamp_caveat": (
            "Task-authored status timestamps are later than the observed filesystem "
            "times and are preserved as claims, not used as ledger chronology."
        ),
        "output_paths": [
            f"../judging/loop-02/{judge_id}/manifest-ready.json",
            f"../judging/loop-02/{judge_id}/pairwise.json",
            f"../judging/loop-02/{judge_id}/status.json",
        ],
    }


def main() -> int:
    ledger = load_json(LEDGER_PATH)
    events = ledger["events"]
    replace_event(
        events,
        judge_event(
            event_id="task-accessibility-judge-loop-02",
            judge_id="judge-accessibility",
            model="gpt-5.6-terra",
            agent_id="task_hZNGNFU7nFaBf9jm7dHA8KjA",
            task_call_id="call_prGWVqR5vGwKRwF644kxNN9f",
        ),
    )
    replace_event(
        events,
        judge_event(
            event_id="task-human-use-judge-loop-02",
            judge_id="judge-human-use",
            model="claude-opus-4.7",
            agent_id="task_qAtIi3mWZfpTY4NgIbPVyKrl",
            task_call_id="call_CRZ0nyj71gOYYh4GBOmx1vfv",
        ),
    )
    output_paths = [
        ROOT / "blinding-map.json",
        ROOT / "aggregate" / "panel-scores.json",
        ROOT / "aggregate" / "pairwise-aggregate.json",
        ROOT / "aggregate" / "manifest-ready.json",
        ROOT / "aggregate" / "synthesis-input.json",
        ROOT / "aggregate" / "dissent.md",
        ROOT / "aggregate" / "panel-summary.md",
    ]
    for path in output_paths:
        if not path.is_file():
            raise RuntimeError(f"Missing aggregation output: {path}")
    completed_at = max(iso_mtime(path) for path in output_paths)
    replace_event(
        events,
        {
            "id": "aggregate-blind-judging-loop-02",
            "kind": "attended_deterministic_command",
            "role": "orchestrator-judge-aggregator",
            "model": "gpt-5.6-sol",
            "command": "python generated/judging/loop-02/aggregate_loop02_judges.py",
            "pid": None,
            "pid_reason": "Short attended deterministic command completed within its process call.",
            "working_directory": "repository root",
            "start_utc": completed_at,
            "start_source": "aggregation output modification times",
            "heartbeat_utc": completed_at,
            "heartbeat_source": "aggregation output modification times",
            "end_utc": completed_at,
            "end_source": "all aggregation outputs written and hashed",
            "terminal_status": "completed_verified",
            "mapping_revealed_after_both_judges_terminal": True,
            "track_finalists": [
                "single-page-loop-02",
                "resumable-wizard-loop-02",
                "task-cards-loop-01",
            ],
            "output_paths": [
                "../" + str(path.relative_to(GENERATED_ROOT)).replace("\\", "/")
                for path in output_paths
            ],
            "output_sha256": {
                str(path.relative_to(GENERATED_ROOT)).replace("\\", "/"): sha256(path)
                for path in output_paths
            },
        },
    )
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "ledger": str(LEDGER_PATH),
                "event_count": len(events),
                "sha256": sha256(LEDGER_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
