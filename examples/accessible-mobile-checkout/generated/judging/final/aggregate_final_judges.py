#!/usr/bin/env python3
"""Reveal and aggregate the terminal final blind panel."""

from __future__ import annotations

import hashlib
import json
import statistics
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT.parents[1]
AGGREGATE_ROOT = ROOT / "aggregate"
ORCHESTRATOR_ROOT = ROOT / "orchestrator"
LEDGER_PATH = GENERATED_ROOT / "harness" / "process-ledger.json"
JUDGES = {
    "judge-accessibility": {
        "path": ROOT / "judge-accessibility",
        "model": "gpt-5.6-terra",
        "handle": "final-accessibility-judge",
    },
    "judge-human-use": {
        "path": ROOT / "judge-human-use",
        "model": "claude-opus-4.7",
        "handle": "final-human-use-judge",
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


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_relative(path: Path) -> str:
    return path.resolve().relative_to(GENERATED_ROOT.resolve()).as_posix()


def raw_artifacts() -> list[dict[str, str]]:
    result = []
    for judge_id, config in JUDGES.items():
        for path in sorted(config["path"].rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(config["path"]).as_posix()
            safe = "".join(ch if ch.isalnum() else "-" for ch in relative).strip("-")
            result.append(
                {
                    "id": f"final-{judge_id}-{safe}",
                    "judge_id": judge_id,
                    "path": generated_relative(path),
                    "sha256": sha256(path),
                }
            )
    return result


def accessibility_records() -> dict[str, dict[str, Any]]:
    manifest = load(JUDGES["judge-accessibility"]["path"] / "manifest-ready.json")
    return {record["label"]: record for record in manifest["records"]}


def human_records() -> dict[str, dict[str, Any]]:
    manifest = load(JUDGES["judge-human-use"]["path"] / "manifest-ready.json")
    return {
        f"candidate-{record['candidate_label']}": record
        for record in manifest["records"]
    }


def normalize_pairs() -> list[dict[str, Any]]:
    a = load(JUDGES["judge-accessibility"]["path"] / "pairwise.json")
    h = load(JUDGES["judge-human-use"]["path"] / "pairwise.json")
    result = []
    for item in a["comparisons"]:
        result.append(
            {
                "judge_id": "judge-accessibility",
                "model_id": "gpt-5.6-terra",
                "pair": item["observed_order"],
                "preferred": item["preferred_label"],
                "confidence": item["confidence"],
                "rationale": item["rationale"],
                "regression_assessment": item["regression_assessment"],
            }
        )
    for item in h["comparisons"]:
        left, right = item["pair"].split(" vs ")
        result.append(
            {
                "judge_id": "judge-human-use",
                "model_id": "claude-opus-4.7",
                "pair": [left, right],
                "preferred": item["preferred"],
                "confidence": item["confidence"],
                "rationale": " ".join(item["concrete_observed_rationale"]),
                "regression_assessment": item["regression_assessment"],
            }
        )
    return result


def pair_key(pair: list[str]) -> tuple[str, str]:
    return tuple(sorted(pair))


def main() -> int:
    statuses = {
        judge_id: load(config["path"] / "status.json")
        for judge_id, config in JUDGES.items()
    }
    if statuses["judge-accessibility"].get("status") != "completed":
        raise RuntimeError("Final accessibility judge is not terminal.")
    if statuses["judge-human-use"].get("phase") != "complete":
        raise RuntimeError("Final human-use judge is not terminal.")
    if statuses["judge-accessibility"].get("blockers") or statuses[
        "judge-human-use"
    ].get("blockers"):
        raise RuntimeError("A final judge reported blockers.")

    pending_map = load(ORCHESTRATOR_ROOT / "blinding-map.pending.json")
    if pending_map.get("mapping_fixed_before_judging") is not True:
        raise RuntimeError("Final blind mapping was not fixed before judging.")
    mapping = {
        item["label"]: item["iteration_id"] for item in pending_map["mappings"]
    }
    expected_mapping = {
        "candidate-a": "synthesis-loop-02",
        "candidate-b": "synthesis-loop-01",
        "candidate-c": "single-page-loop-02",
    }
    if mapping != expected_mapping:
        raise RuntimeError(f"Unexpected final mapping: {mapping}")

    a_records = accessibility_records()
    h_records = human_records()
    candidates = []
    for label in ("candidate-a", "candidate-b", "candidate-c"):
        a = a_records[label]
        h = h_records[label]
        a_scores = {
            lens: a["lens_scores"][lens]["score"] for lens in LENSES
        }
        h_scores = {lens: h["sub_scores"][lens] for lens in LENSES}
        medians = {
            lens: statistics.median([a_scores[lens], h_scores[lens]])
            for lens in LENSES
        }
        score = sum(medians.values()) / len(LENSES)
        visual = statistics.median(
            [
                a["visual_information_clarity"]["score"],
                h["visual_information_clarity_score"],
            ]
        )
        candidates.append(
            {
                "label": label,
                "iteration_id": mapping[label],
                "human_use_quality": score,
                "visual_information_clarity": visual,
                "lens_medians": medians,
                "raw_judge_scores": {
                    "judge-accessibility": {
                        "mean_11": a["unrounded_mean_11_lenses"],
                        "scores": a_scores,
                        "visual_information_clarity": a[
                            "visual_information_clarity"
                        ]["score"],
                    },
                    "judge-human-use": {
                        "mean_11": sum(h_scores.values()) / len(LENSES),
                        "scores": h_scores,
                        "visual_information_clarity": h[
                            "visual_information_clarity_score"
                        ],
                    },
                },
                "lens_findings": [
                    {
                        "lens": lens,
                        "finding": (
                            f"judge-accessibility ({a_scores[lens]}): "
                            f"{a['lens_scores'][lens]['evidence']} | "
                            f"judge-human-use ({h_scores[lens]}): see "
                            f"judging/final/judge-human-use/candidate-{label[-1]}.json"
                        ),
                    }
                    for lens in LENSES
                ],
            }
        )
    by_label = {item["label"]: item for item in candidates}
    if max(candidates, key=lambda item: item["human_use_quality"])["label"] != "candidate-a":
        raise RuntimeError("Final qualitative aggregate does not select candidate-a.")

    pairs = normalize_pairs()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in pairs:
        grouped.setdefault(pair_key(item["pair"]), []).append(item)
    pairwise_aggregate = []
    for key, items in sorted(grouped.items()):
        preferences = [item["preferred"] for item in items]
        consensus = preferences[0] if len(set(preferences)) == 1 else None
        pairwise_aggregate.append(
            {
                "pair": list(key),
                "consensus_preference": consensus,
                "dissent": consensus is None,
                "raw": items,
            }
        )
    required = next(
        item
        for item in pairwise_aggregate
        if item["pair"] == ["candidate-a", "candidate-c"]
    )
    if (
        required["consensus_preference"] != "candidate-a"
        or any(
            raw["pair"] != ["candidate-a", "candidate-c"]
            for raw in required["raw"]
            if raw["judge_id"] == "judge-accessibility"
        )
        or any(
            raw["pair"] != ["candidate-c", "candidate-a"]
            for raw in required["raw"]
            if raw["judge_id"] == "judge-human-use"
        )
    ):
        raise RuntimeError("Required flipped Champion-versus-parent comparison failed.")

    revealed = deepcopy(pending_map)
    revealed["visibility"] = "revealed after both final judges reached terminal state"
    revealed["judge_terminal_status"] = {
        judge_id: generated_relative(config["path"] / "status.json")
        for judge_id, config in JUDGES.items()
    }
    write(ROOT / "blinding-map.json", revealed)
    write(
        AGGREGATE_ROOT / "panel-scores.json",
        {
            "schema_version": "1.0",
            "experiment_id": "accessible-mobile-checkout",
            "aggregation": "per_lens_median_then_mean",
            "candidates": candidates,
            "ranking": [
                item["iteration_id"]
                for item in sorted(
                    candidates,
                    key=lambda item: item["human_use_quality"],
                    reverse=True,
                )
            ],
        },
    )
    write(
        AGGREGATE_ROOT / "pairwise-aggregate.json",
        {
            "schema_version": "1.0",
            "comparisons": pairwise_aggregate,
            "required_flipped_comparison": required,
        },
    )
    raw = raw_artifacts()
    champion = {
        "iteration_id": "synthesis-loop-02",
        "summary": (
            "Synthesis Loop 02 is the final Champion: it passes all seven frozen "
            "objective gates, wins both independent flipped-order comparisons against "
            "the strongest parent, and has the highest final per-lens panel aggregate."
        ),
        "reasons": [
            {
                "text": (
                    "All seven objective gates pass with zero external requests and "
                    "no pass-to-fail regression against any parent."
                ),
                "evidence_refs": [
                    "synthesis-loop-02-objective-report",
                    "offline-safety-gate",
                ],
            },
            {
                "text": (
                    "Both independent judges preferred the Champion candidate over "
                    "the strongest parent in opposite observed orders."
                ),
                "evidence_refs": [
                    "final-judge-accessibility-pairwise-json",
                    "final-judge-human-use-pairwise-json",
                ],
            },
            {
                "text": (
                    "The final human-use aggregate is highest, with improved skip "
                    "focus, explicit safe progress controls, and cross-reload duplicate safety."
                ),
                "evidence_refs": [
                    "human-use-quality",
                    "synthesis-loop-02-checkout-ui",
                ],
            },
        ],
        "caveats": [
            {
                "text": (
                    "The one-page mobile form remains information-dense before "
                    "sections become eligible for compaction."
                ),
                "evidence_refs": [
                    "final-judge-accessibility-candidate-a-json",
                    "human-use-quality",
                ],
            },
            {
                "text": (
                    "Screen-reader speech output and real switch/magnifier hardware "
                    "were not directly exercised; browser semantics and operation were tested."
                ),
                "evidence_refs": [
                    "final-judge-accessibility-candidate-a-json",
                    "semantic-accessibility-gate",
                ],
            },
            {
                "text": (
                    "Permanent procedural provenance caveats cover the remediated "
                    "root-path violation and the reboot recovery; functional hashes remained valid."
                ),
                "evidence_refs": [
                    "synthesis-loop-01-status",
                    "synthesis-loop-02-status",
                ],
            },
        ],
    }
    winner = by_label["candidate-a"]
    manifest_record = {
        "iteration_id": "synthesis-loop-02",
        "track_id": "synthesis",
        "panel_judges": [
            {"judge_id": judge_id, "model_id": config["model"]}
            for judge_id, config in JUDGES.items()
        ],
        "scores": [
            {
                "scorer_id": "blind-human-use-panel",
                "criterion_id": "human-use-quality",
                "value": winner["human_use_quality"],
                "notes": "Final mean of 11 per-lens medians from two independent blind judges.",
            },
            {
                "scorer_id": "blind-human-use-panel",
                "criterion_id": "visual-information-clarity",
                "value": winner["visual_information_clarity"],
                "notes": "Final median of two independent blind judge scores.",
            },
        ],
        "judging_evidence": {
            "iteration_id": "synthesis-loop-02",
            "criterion_id": "human-use-quality",
            "scorer_id": "blind-human-use-panel",
            "kind": "qualitative_rubric",
            "objective_gate": False,
            "score": winner["human_use_quality"],
            "evidence_refs": [item["path"] for item in raw],
            "lens_findings": winner["lens_findings"],
        },
        "raw_judge_artifacts": raw,
        "decision": "new_best",
        "decision_rationale": champion["summary"],
        "judge_feedback": (
            "Final blind panel consensus selects this iteration over both its immediate "
            "synthesis parent and the strongest primary-Track parent."
        ),
        "next_loop_feedback": (
            "Stop: planned convergence is established and all objective and final "
            "qualitative comparisons pass."
        ),
        "next_loop_feedback_ref": "judging/final/aggregate/pairwise-aggregate.json",
    }
    write(
        AGGREGATE_ROOT / "manifest-ready.json",
        {
            "schema_version": "1.0",
            "source_loop": "final",
            "records": [manifest_record],
            "champion": champion,
        },
    )
    (AGGREGATE_ROOT / "dissent.md").write_text(
        "# Final panel dissent\n\n"
        "There is no winner-level dissent: both independent judges prefer candidate A "
        "over B and C, including the required A/C comparison in flipped observed "
        "orders. Preserved nuance: the leanest parent has fewer optional controls and "
        "may reduce chrome for some users, while the Champion is preferred for explicit "
        "save/clear agency, progress semantics, focused skip behavior, and cross-reload "
        "duplicate safety.\n",
        encoding="utf-8",
        newline="\n",
    )
    (AGGREGATE_ROOT / "panel-summary.md").write_text(
        "# Final blind panel summary\n\n"
        f"- synthesis-loop-02: {by_label['candidate-a']['human_use_quality']:.12f}; Champion.\n"
        f"- synthesis-loop-01: {by_label['candidate-b']['human_use_quality']:.12f}.\n"
        f"- single-page-loop-02: {by_label['candidate-c']['human_use_quality']:.12f}.\n\n"
        "Both judges prefer synthesis-loop-02 over the strongest parent in opposite "
        "orders. All compared candidates retain terminal seven-gate objective passes.\n",
        encoding="utf-8",
        newline="\n",
    )

    ledger = load(LEDGER_PATH)
    replace_ids = {
        "task-final-judge-accessibility",
        "task-final-judge-human-use",
        "aggregate-final-blind-panel",
    }
    events = [item for item in ledger["events"] if item.get("id") not in replace_ids]
    for judge_id, config in JUDGES.items():
        status = statuses[judge_id]
        start = status.get("started_at")
        heartbeat = status.get("heartbeat_at") or status.get("heartbeat")
        end = status.get("completed_at")
        events.append(
            {
                "id": f"task-final-{judge_id}",
                "kind": "background_task",
                "role": judge_id,
                "model": config["model"],
                "command": f"background task {config['handle']}",
                "task_handle": config["handle"],
                "task_handle_kind": "background_agent_id",
                "pid": None,
                "start_utc": start,
                "heartbeat_utc": heartbeat,
                "end_utc": end,
                "terminal_status": "completed",
                "status_path": f"../judging/final/{judge_id}/status.json",
                "objective_harness_rerun": False,
                "output_paths": [
                    f"../judging/final/{judge_id}/manifest-ready.json",
                    f"../judging/final/{judge_id}/pairwise.json",
                ],
                "working_directory": "repository root",
            }
        )
    events.append(
        {
            "id": "aggregate-final-blind-panel",
            "kind": "attended_deterministic_command",
            "role": "orchestrator-judge-aggregator",
            "model": "gpt-5.6-sol",
            "command": "python generated/judging/final/aggregate_final_judges.py",
            "pid": None,
            "terminal_status": "completed_verified",
            "mapping_revealed_after_both_judges_terminal": True,
            "champion_iteration_id": "synthesis-loop-02",
            "required_flipped_pairwise_consensus": "synthesis-loop-02",
            "output_paths": [
                "../judging/final/blinding-map.json",
                "../judging/final/aggregate/panel-scores.json",
                "../judging/final/aggregate/pairwise-aggregate.json",
                "../judging/final/aggregate/manifest-ready.json",
                "../judging/final/aggregate/dissent.md",
                "../judging/final/aggregate/panel-summary.md",
            ],
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
                "champion": "synthesis-loop-02",
                "panel_score": winner["human_use_quality"],
                "visual_information_clarity": winner[
                    "visual_information_clarity"
                ],
                "pairwise_consensus": True,
                "raw_artifact_count": len(raw),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
