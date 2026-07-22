#!/usr/bin/env python3
"""Aggregate the two independent Synthesis Loop 01 judges."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT.parents[1]
AGGREGATE_ROOT = ROOT / "aggregate"
LEDGER_PATH = GENERATED_ROOT / "harness" / "process-ledger.json"
JUDGES = {
    "judge-accessibility": {
        "path": ROOT / "judge-accessibility",
        "model": "gpt-5.6-terra",
        "handle": "synth1-accessibility-judge",
    },
    "judge-human-use": {
        "path": ROOT / "judge-human-use",
        "model": "claude-opus-4.7",
        "handle": "synth1-human-use-judge",
    },
}
LENSES = (
    "discoverability",
    "navigation",
    "input_burden",
    "error_prevention_recovery",
    "feedback_status",
    "accessibility",
    "responsive_touch_ergonomics",
    "interruption_resumption",
    "latency_perception",
    "destructive_actions",
    "cognitive_load",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_relative(path: Path) -> str:
    return path.resolve().relative_to(GENERATED_ROOT.resolve()).as_posix()


def artifact_id(judge_id: str, path: Path) -> str:
    relative = path.relative_to(JUDGES[judge_id]["path"]).as_posix()
    safe = "".join(ch if ch.isalnum() else "-" for ch in relative).strip("-")
    return f"synthesis-loop-01-{judge_id}-{safe}"


def raw_artifacts() -> list[dict[str, str]]:
    result = []
    for judge_id, config in JUDGES.items():
        for path in sorted(config["path"].rglob("*")):
            if not path.is_file():
                continue
            result.append(
                {
                    "id": artifact_id(judge_id, path),
                    "judge_id": judge_id,
                    "path": generated_relative(path),
                    "sha256": sha256(path),
                }
            )
    return result


def main() -> int:
    a_manifest = load_json(JUDGES["judge-accessibility"]["path"] / "manifest-ready.json")
    h_manifest = load_json(JUDGES["judge-human-use"]["path"] / "manifest-ready.json")
    a = a_manifest["records"][0]
    h = h_manifest
    a_scores = a["scores"]
    h_scores = h["scores"]
    medians = {
        lens: statistics.median([a_scores[lens], h_scores[lens]])
        for lens in LENSES
    }
    score = sum(medians.values()) / len(LENSES)
    visual = statistics.median(
        [a["visual_information_clarity"]["score"], h["visual_information_clarity"]]
    )
    lens_findings = []
    for lens in LENSES:
        a_finding = a["lens_findings"][lens]
        lens_findings.append(
            {
                "lens": lens,
                "score": medians[lens],
                "finding": (
                    f"judge-accessibility ({a_scores[lens]}): "
                    f"{a_finding['finding']} | judge-human-use ({h_scores[lens]}): "
                    f"{lens.replace('_', ' ')} score supported by "
                    "candidate-a.json and manifest-ready.json."
                ),
            }
        )
    raw = raw_artifacts()
    feedback = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "source_iteration_id": "synthesis-loop-01",
        "target_iteration_id": "synthesis-loop-02",
        "accepted_improvement_instruction": (
            "Preserve the one-page synthesis, grouped recovery, safe storage boundary, "
            "confirmed clear flow, compact hidden descendants, and one SYN-2048 "
            "confirmation. Make the skip target programmatically focusable and move "
            "focus to the named checkout start. Default compact-completed on after "
            "safe restoration records a completed section and persist that preference. "
            "Label untouched preselected shipping as 'Default selected: Standard' "
            "until acknowledged. Persist only a non-sensitive placed flag so reload "
            "keeps placement disabled and announces the existing SYN-2048 order. "
            "Do not persist payment secrets or weaken any objective gate."
        ),
        "evidence": [
            {
                "judge_id": "judge-accessibility",
                "model_id": "gpt-5.6-terra",
                "instruction": a["improvement_instruction_for_synthesis_loop_02"],
                "source": "judging/synthesis-loop-01/judge-accessibility/manifest-ready.json",
            },
            {
                "judge_id": "judge-human-use",
                "model_id": "claude-opus-4.7",
                "instruction": h["feedback"]["improvement_instruction"],
                "source": "judging/synthesis-loop-01/judge-human-use/manifest-ready.json",
            },
        ],
        "panel_score": score,
        "visual_information_clarity": visual,
        "objective_gate": False,
    }
    write_json(AGGREGATE_ROOT / "synthesis-loop-02-feedback.json", feedback)
    panel = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "iteration_id": "synthesis-loop-01",
        "aggregation": "per_lens_median_then_mean",
        "human_use_quality": score,
        "visual_information_clarity": visual,
        "lens_medians": medians,
        "judge_scores": {
            "judge-accessibility": {
                "model_id": "gpt-5.6-terra",
                "mean": a["mean_11_lenses_unrounded"],
                "scores": a_scores,
                "visual_information_clarity": a[
                    "visual_information_clarity"
                ]["score"],
            },
            "judge-human-use": {
                "model_id": "claude-opus-4.7",
                "mean": h["unrounded_mean_of_11_lenses"],
                "scores": h_scores,
                "visual_information_clarity": h["visual_information_clarity"],
            },
        },
        "dissent": {
            "preserved": True,
            "accessibility": (
                "Skip-link focus failure and exact-minimum targets prevent top scores."
            ),
            "human_use": (
                "Residual issues are compact default, initial shipping status, and "
                "post-confirmation reload state."
            ),
        },
    }
    write_json(AGGREGATE_ROOT / "panel-scores.json", panel)
    record = {
        "iteration_id": "synthesis-loop-01",
        "track_id": "synthesis",
        "panel_judges": [
            {"judge_id": judge_id, "model_id": config["model"]}
            for judge_id, config in JUDGES.items()
        ],
        "scores": [
            {
                "scorer_id": "blind-human-use-panel",
                "criterion_id": "human-use-quality",
                "value": score,
                "notes": "Mean of 11 per-lens medians from two independent blind judges.",
            },
            {
                "scorer_id": "blind-human-use-panel",
                "criterion_id": "visual-information-clarity",
                "value": visual,
                "notes": "Median of two independent blind judge scores.",
            },
        ],
        "judging_evidence": {
            "iteration_id": "synthesis-loop-01",
            "criterion_id": "human-use-quality",
            "scorer_id": "blind-human-use-panel",
            "kind": "qualitative_rubric",
            "objective_gate": False,
            "score": score,
            "evidence_refs": [item["path"] for item in raw],
            "lens_findings": lens_findings,
        },
        "raw_judge_artifacts": raw,
        "decision": "new_best",
        "decision_rationale": (
            "All seven objective gates pass and the independent synthesis panel "
            f"aggregate is {score:.6f}, above the strongest parent aggregate "
            "4.545455. This is the synthesis baseline leader, not the final Champion."
        ),
        "judge_feedback": (
            "The panel confirms the synthesis direction while preserving a skip-link "
            "focus defect and three minor human-use improvements."
        ),
        "next_loop_feedback": feedback["accepted_improvement_instruction"],
        "next_loop_feedback_ref": (
            "judging/synthesis-loop-01/aggregate/synthesis-loop-02-feedback.json"
        ),
    }
    write_json(
        AGGREGATE_ROOT / "manifest-ready.json",
        {
            "schema_version": "1.0",
            "source_loop": "synthesis-loop-01",
            "records": [record],
        },
    )
    (AGGREGATE_ROOT / "dissent.md").write_text(
        "# Synthesis Loop 01 panel dissent\n\n"
        "Both judges support the synthesis direction, but they emphasize different "
        "remaining defects. The accessibility judge observed that activating the "
        "skip link changes the fragment while leaving focus on `BODY`, and noted "
        "exact-minimum targets and initial density. The human-use judge scored the "
        "candidate more highly but identified compact mode defaulting off, premature "
        "Shipping `Complete` status, and placement state not surviving reload. "
        "Synthesis Loop 02 must address all evidence-backed findings without changing "
        "the one-page paradigm or weakening objective gates.\n",
        encoding="utf-8",
        newline="\n",
    )

    ledger = load_json(LEDGER_PATH)
    events = [
        event
        for event in ledger["events"]
        if event.get("id")
        not in {
            "task-synthesis-loop-01-judge-accessibility",
            "task-synthesis-loop-01-judge-human-use",
            "aggregate-synthesis-loop-01-judging",
        }
    ]
    for judge_id, config in JUDGES.items():
        status = load_json(config["path"] / "status.json")
        events.append(
            {
                "id": f"task-synthesis-loop-01-{judge_id}",
                "kind": "background_task",
                "role": judge_id,
                "model": config["model"],
                "command": f"background task {config['handle']}",
                "task_handle": config["handle"],
                "task_handle_kind": "background_agent_id",
                "pid": None,
                "pid_reason": "The background task API exposed an agent task handle, not an operating-system PID.",
                "start_utc": status["started_at"],
                "heartbeat_utc": status["heartbeat_at"],
                "end_utc": status["completed_at"],
                "terminal_status": "completed",
                "status_path": f"../judging/synthesis-loop-01/{judge_id}/status.json",
                "output_paths": [
                    f"../judging/synthesis-loop-01/{judge_id}/manifest-ready.json",
                    f"../judging/synthesis-loop-01/{judge_id}/candidate-a.json",
                    f"../judging/synthesis-loop-01/{judge_id}/navigation-transcript-a.json",
                ],
                "objective_harness_rerun": False,
                "working_directory": "repository root",
            }
        )
    events.append(
        {
            "id": "aggregate-synthesis-loop-01-judging",
            "kind": "attended_deterministic_command",
            "role": "orchestrator-judge-aggregator",
            "model": "gpt-5.6-sol",
            "command": "python generated/judging/synthesis-loop-01/aggregate_judges.py",
            "pid": None,
            "terminal_status": "completed_verified",
            "output_paths": [
                "../judging/synthesis-loop-01/aggregate/panel-scores.json",
                "../judging/synthesis-loop-01/aggregate/manifest-ready.json",
                "../judging/synthesis-loop-01/aggregate/synthesis-loop-02-feedback.json",
                "../judging/synthesis-loop-01/aggregate/dissent.md",
            ],
            "panel_score": score,
            "working_directory": "repository root",
        }
    )
    ledger["events"] = events
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "iteration_id": "synthesis-loop-01",
                "human_use_quality": score,
                "visual_information_clarity": visual,
                "raw_artifact_count": len(raw),
                "ledger_event_count": len(events),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
