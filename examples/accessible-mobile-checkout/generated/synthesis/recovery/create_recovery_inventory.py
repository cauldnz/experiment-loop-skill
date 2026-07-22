#!/usr/bin/env python3
"""Hash the immutable Synthesis Loop 01 outputs recovered after reboot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RECOVERY_ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = RECOVERY_ROOT.parents[1]
EXPERIMENT_ROOT = GENERATED_ROOT.parent
LOOP_ROOT = GENERATED_ROOT / "synthesis" / "loop-01"
OUTPUT = RECOVERY_ROOT / "recovery-inventory.json"

IMMUTABLE_PATHS = (
    "synthesis/loop-01/index.html",
    "synthesis/loop-01/styles.css",
    "synthesis/loop-01/app.js",
    "synthesis/loop-01/process.json",
    "synthesis/loop-01/evidence/objective-report.json",
    "synthesis/loop-01/evidence/objective-report.txt",
    "synthesis/loop-01/evidence/initial.png",
    "synthesis/loop-01/evidence/keyboard-completion.png",
    "synthesis/loop-01/evidence/final.png",
    "synthesis/loop-01/evidence/viewport-320x568.png",
    "synthesis/loop-01/evidence/viewport-360x800.png",
    "synthesis/loop-01/evidence/viewport-390x844.png",
    "synthesis/loop-01/adoption-rejection-matrix.json",
    "synthesis/loop-01/adoption-rejection-matrix.md",
)

FROZEN_PATHS = (
    "setup/experiment-brief.json",
    "setup/prompt.md",
    "setup/approval.json",
    "generated/harness/canonical-fixture.json",
    "generated/harness/run_checkout_gates.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path, relative_to: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": sha256(path),
        "bytes": stat.st_size,
        "created_utc": datetime.fromtimestamp(
            stat.st_ctime, timezone.utc
        ).isoformat(),
        "modified_utc": datetime.fromtimestamp(
            stat.st_mtime, timezone.utc
        ).isoformat(),
    }


def main() -> int:
    immutable = []
    for relative in IMMUTABLE_PATHS:
        path = GENERATED_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Missing recovered immutable output: {relative}")
        immutable.append(record(path, GENERATED_ROOT))

    frozen = []
    for relative in FROZEN_PATHS:
        path = EXPERIMENT_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Missing frozen input: {relative}")
        frozen.append(record(path, EXPERIMENT_ROOT))

    process = json.loads(
        (LOOP_ROOT / "process.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (LOOP_ROOT / "evidence" / "objective-report.json").read_text(
            encoding="utf-8"
        )
    )
    run = process["objective_runs"][0]
    if (
        run["terminal_state"] != "completed"
        or run["exit_code"] != 0
        or run["failed_gate_ids"]
        or report["blocking_failure"]
        or report["failed_gate_ids"]
        or any(gate["status"] != "pass" for gate in report["gates"])
    ):
        raise RuntimeError("Persisted objective evidence is not a terminal pass.")
    if run["fixture_sha256"] != report["fixture_sha256"]:
        raise RuntimeError("Process and objective report fixture hashes differ.")

    payload = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "loop_id": "synthesis-loop-01",
        "recovery_classification": "agent_interrupted_after_terminal_objective_pass",
        "approval_binding_validation": {
            "validator": "scripts/validate_experiment_setup.py",
            "require_approved": True,
            "result": "EXPERIMENT SETUP: PASS",
            "installed_skill_validator_caveat": (
                "The current user-installed skill validator targets a newer brief "
                "schema and rejected the frozen repository brief's human_use field. "
                "The repository-pinned validator was used because it is part of the "
                "approved revision-1 contract."
            ),
        },
        "objective_terminal_evidence": {
            "terminal_state": run["terminal_state"],
            "exit_code": run["exit_code"],
            "end_utc": run["end_utc"],
            "pid": run["process_pid"],
            "blocking_failure": report["blocking_failure"],
            "failed_gate_ids": report["failed_gate_ids"],
            "gate_states": {
                gate["id"]: gate["status"] for gate in report["gates"]
            },
            "external_request_count": len(report["external_requests"]),
            "rerun_authorized": False,
        },
        "immutable_outputs": immutable,
        "frozen_inputs": frozen,
        "missing_outputs_at_recovery": [
            "synthesis/loop-01/metadata.json",
            "synthesis/loop-01/synthesis-report.md",
            "synthesis/manifest-fragment.json",
            "terminal synthesis/loop-01/status.json",
            "process-ledger synthesis reconciliation event",
        ],
        "reboot_provenance": {
            "persisted_status_state": "running",
            "persisted_status_heartbeat": "2026-07-21T09:02:38.916Z",
            "agent_handle": "synthesis-loop-01",
            "agent_handle_after_reboot": "not_found",
            "recorded_objective_pid_alive_after_reboot": False,
            "active_shell_sessions_after_reboot": 0,
            "active_background_agents_after_reboot": 0,
            "writes_outside_generated_synthesis_after_launch": [],
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output": OUTPUT.relative_to(GENERATED_ROOT).as_posix(),
                "sha256": sha256(OUTPUT),
                "immutable_output_count": len(immutable),
                "frozen_input_count": len(frozen),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
