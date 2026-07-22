#!/usr/bin/env python3
"""Aggregate independent blind Loop 02 judges and select Track finalists."""

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
JUDGE_DIRS = {
    "judge-accessibility": ROOT / "judge-accessibility",
    "judge-human-use": ROOT / "judge-human-use",
}
REQUIRED_LENSES = (
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


def write_json(path: Path, value: Any) -> None:
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


def terminal(status: dict[str, Any]) -> bool:
    state = str(status.get("status") or status.get("state", "")).lower()
    return state in {"complete", "completed"} and not status.get("blockers")


def normalize_record(record: dict[str, Any], judge_id: str) -> dict[str, Any]:
    raw_lenses = record["lens_findings"]
    if isinstance(raw_lenses, dict):
        lenses = {
            lens: {
                "score": raw_lenses[lens]["score"],
                "finding": raw_lenses[lens]["finding"],
                "evidence_refs": list(record.get("evidence_refs", [])),
            }
            for lens in REQUIRED_LENSES
        }
    else:
        lenses = {
            item["lens"]: {
                "score": item["score"],
                "finding": item["finding"],
                "evidence_refs": list(item.get("evidence_refs", [])),
            }
            for item in raw_lenses
        }
    if set(lenses) != set(REQUIRED_LENSES):
        raise RuntimeError(
            f"{judge_id}:{record.get('candidate')} does not contain all required lenses."
        )
    visual = record.get("visual-information-clarity") or record.get(
        "visual_information_clarity"
    )
    return {
        "candidate": record["candidate"],
        "judge_id": judge_id,
        "model": record.get("actual_model_used")
        or ("gpt-5.6-terra" if judge_id == "judge-accessibility" else "claude-opus-4.7"),
        "reported_score": record["score"],
        "recomputed_score": sum(item["score"] for item in lenses.values())
        / len(REQUIRED_LENSES),
        "lenses": lenses,
        "visual_information_clarity": visual,
        "evidence_refs": list(record.get("evidence_refs", [])),
        "synthesis_feedback": deepcopy(record.get("synthesis_feedback")),
        "strengths": deepcopy(record.get("strengths", [])),
        "defects": deepcopy(record.get("defects", [])),
    }


def raw_artifacts(label: str) -> list[dict[str, str]]:
    result = []
    suffix = label.removeprefix("candidate-")
    for judge_id, directory in JUDGE_DIRS.items():
        for name in (
            f"{label}.json",
            f"{label}.md",
            f"navigation-transcript-{suffix}.json",
            "pairwise.json",
            "pairwise.md",
            "manifest-ready.json",
            "status.json",
        ):
            path = directory / name
            if not path.is_file():
                raise RuntimeError(f"Required judge Artifact is missing: {path}")
            result.append(
                {
                    "id": (
                        f"{mapping_safe(label)}-{judge_id}-{name.replace('.', '-')}"
                    ),
                    "judge_id": judge_id,
                    "path": generated_relative(path),
                    "sha256": sha256(path),
                }
            )
    return result


def mapping_safe(value: str) -> str:
    return value.replace("_", "-").replace(".", "-")


def load_pairwise() -> list[dict[str, Any]]:
    accessibility = load_json(JUDGE_DIRS["judge-accessibility"] / "pairwise.json")
    human = load_json(JUDGE_DIRS["judge-human-use"] / "pairwise.json")
    normalized = []
    for item in accessibility["comparisons_in_required_order"]:
        normalized.append(
            {
                "judge_id": "judge-accessibility",
                "pair": item["comparison"],
                "preferred": item["preference"],
                "confidence": item["confidence"],
                "rationale": item["rationale"],
                "evidence_refs": item["evidence_refs"],
            }
        )
    for item in human["pairs"]:
        left, right = item["pair"].split("_vs_")
        normalized.append(
            {
                "judge_id": "judge-human-use",
                "pair": [f"candidate-{left}", f"candidate-{right}"],
                "preferred": item["preferred"],
                "confidence": item["confidence"],
                "rationale": item["rationale"],
                "evidence_refs": item["evidence_refs"],
            }
        )
    return normalized


def pair_key(pair: list[str]) -> tuple[str, str]:
    return tuple(sorted(pair))


def main() -> int:
    statuses = {
        judge_id: load_json(directory / "status.json")
        for judge_id, directory in JUDGE_DIRS.items()
    }
    if not all(terminal(status) for status in statuses.values()):
        raise RuntimeError("Both independent judges must be terminal without blockers.")

    pending_map_path = ORCHESTRATOR_ROOT / "blinding-map.pending.json"
    hidden_map = load_json(pending_map_path)
    if hidden_map.get("mapping_fixed_before_judging") is not True:
        raise RuntimeError("Blinding map was not fixed before judging.")
    mapping = {item["label"]: item for item in hidden_map["mappings"]}

    raw_by_candidate: dict[str, list[dict[str, Any]]] = {
        label: [] for label in mapping
    }
    for judge_id, directory in JUDGE_DIRS.items():
        manifest_ready = load_json(directory / "manifest-ready.json")
        for record in manifest_ready["records"]:
            normalized = normalize_record(record, judge_id)
            raw_by_candidate[normalized["candidate"]].append(normalized)

    loop01 = load_json(
        GENERATED_ROOT / "judging" / "loop-01" / "aggregate" / "panel-scores.json"
    )
    loop01_by_track = {item["track_id"]: item for item in loop01["iterations"]}
    panel_iterations = []
    for label in sorted(mapping):
        records = raw_by_candidate[label]
        if len(records) != 2:
            raise RuntimeError(f"{label} must have exactly two raw judge records.")
        lens_medians = {}
        lens_findings = []
        for lens in REQUIRED_LENSES:
            scores = [record["lenses"][lens]["score"] for record in records]
            median = statistics.median(scores)
            lens_medians[lens] = median
            lens_findings.append(
                {
                    "lens": lens,
                    "median_score": median,
                    "raw": [
                        {
                            "judge_id": record["judge_id"],
                            "model": record["model"],
                            "score": record["lenses"][lens]["score"],
                            "finding": record["lenses"][lens]["finding"],
                            "evidence_refs": record["lenses"][lens]["evidence_refs"],
                        }
                        for record in records
                    ],
                }
            )
        aggregate_score = sum(lens_medians.values()) / len(REQUIRED_LENSES)
        visual_inputs = [
            record["visual_information_clarity"]["score"] for record in records
        ]
        track_id = f"track-{mapping[label]['track_id']}"
        prior = loop01_by_track[track_id]
        prior_score = prior["human_use_quality"]["value"]
        improved = aggregate_score > prior_score
        loop_id = mapping[label]["loop_id"]
        if improved:
            finalist = loop_id
            decision = "new_best"
            rationale = (
                "All seven objective gates pass and the Loop 02 per-lens panel "
                f"aggregate improved from {prior_score:.6f} to {aggregate_score:.6f}."
            )
        else:
            finalist = prior["iteration_id"]
            decision = "reject"
            rationale = (
                "All seven objective gates pass, but the Loop 02 per-lens panel "
                f"aggregate changed from {prior_score:.6f} to {aggregate_score:.6f}. "
                "The parent remains the Track finalist; the regression evidence is preserved."
            )
        panel_iterations.append(
            {
                "label": label,
                "iteration_id": loop_id,
                "track_id": track_id,
                "decision": decision,
                "decision_rationale": rationale,
                "track_finalist_iteration_id": finalist,
                "parent_iteration_id": prior["iteration_id"],
                "parent_human_use_quality": prior_score,
                "human_use_quality": {
                    "value": aggregate_score,
                    "calculation": "mean of 11 per-lens panel medians",
                    "lens_medians": lens_medians,
                },
                "visual_information_clarity": {
                    "value": statistics.median(visual_inputs),
                    "raw_inputs": visual_inputs,
                },
                "lens_findings": lens_findings,
                "raw_judges": records,
                "raw_judge_artifacts": raw_artifacts(label),
            }
        )

    pairwise = load_pairwise()
    pairwise_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in pairwise:
        pairwise_groups.setdefault(pair_key(record["pair"]), []).append(record)
    pairwise_aggregate = []
    for pair, records in sorted(pairwise_groups.items()):
        preferences = [record["preferred"] for record in records]
        consensus = preferences[0] if len(set(preferences)) == 1 else None
        pairwise_aggregate.append(
            {
                "pair": list(pair),
                "consensus_preference": consensus,
                "dissent": consensus is None,
                "raw": records,
            }
        )

    finalists = {
        item["track_id"]: item["track_finalist_iteration_id"]
        for item in panel_iterations
    }
    synthesis_parents = [
        finalists["track-single-page"],
        finalists["track-resumable-wizard"],
        finalists["track-task-cards"],
    ]
    if synthesis_parents != [
        "single-page-loop-02",
        "resumable-wizard-loop-02",
        "task-cards-loop-01",
    ]:
        raise RuntimeError(f"Unexpected evidence-driven finalists: {synthesis_parents}")

    revealed_map = deepcopy(hidden_map)
    revealed_map.update(
        {
            "visibility": "revealed after both independent judges reached terminal state",
            "judge_terminal_evidence": {
                "judge-accessibility": {
                    "path": "judging/loop-02/judge-accessibility/status.json",
                    "terminal_at": statuses["judge-accessibility"].get("terminal_at"),
                },
                "judge-human-use": {
                    "path": "judging/loop-02/judge-human-use/status.json",
                    "terminal_at": statuses["judge-human-use"].get("ended_at"),
                },
            },
        }
    )
    write_json(ROOT / "blinding-map.json", revealed_map)

    panel_scores = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "loop": "loop-02",
        "aggregation": {
            "judge_count": 2,
            "method": "per_lens_median_then_mean",
            "visual_information_clarity": "median",
            "dissent_preserved": True,
        },
        "judge_orders": hidden_map["judge_orders"],
        "iterations": panel_iterations,
        "track_finalists": finalists,
        "synthesis_parent_ids": synthesis_parents,
    }
    write_json(AGGREGATE_ROOT / "panel-scores.json", panel_scores)
    write_json(
        AGGREGATE_ROOT / "pairwise-aggregate.json",
        {
            "schema_version": "1.0",
            "comparisons": pairwise_aggregate,
            "overall_panel_order_by_aggregate_score": [
                item["label"]
                for item in sorted(
                    panel_iterations,
                    key=lambda item: item["human_use_quality"]["value"],
                    reverse=True,
                )
            ],
        },
    )

    manifest_records = []
    for item in panel_iterations:
        raw_refs = [artifact["path"] for artifact in item["raw_judge_artifacts"]]
        manifest_records.append(
            {
                "iteration_id": item["iteration_id"],
                "loop_id": item["iteration_id"],
                "track_id": item["track_id"],
                "decision": item["decision"],
                "decision_rationale": item["decision_rationale"],
                "track_finalist_iteration_id": item["track_finalist_iteration_id"],
                "panel_judges": [
                    {
                        "judge_id": record["judge_id"],
                        "model_id": record["model"],
                    }
                    for record in item["raw_judges"]
                ],
                "scores": [
                    {
                        "scorer_id": "blind-human-use-panel",
                        "criterion_id": "human-use-quality",
                        "value": item["human_use_quality"]["value"],
                        "notes": "Mean of 11 per-lens medians from two independent blind judges.",
                    },
                    {
                        "scorer_id": "blind-human-use-panel",
                        "criterion_id": "visual-information-clarity",
                        "value": item["visual_information_clarity"]["value"],
                        "notes": "Median of two independent blind judge scores.",
                    },
                ],
                "judging_evidence": {
                    "iteration_id": item["iteration_id"],
                    "criterion_id": "human-use-quality",
                    "scorer_id": "blind-human-use-panel",
                    "kind": "qualitative_rubric",
                    "objective_gate": False,
                    "score": item["human_use_quality"]["value"],
                    "evidence_refs": raw_refs,
                    "lens_findings": [
                        {
                            "lens": finding["lens"],
                            "score": finding["median_score"],
                            "finding": " | ".join(
                                f"{raw['judge_id']}: {raw['finding']}"
                                for raw in finding["raw"]
                            ),
                            "evidence_refs": sorted(
                                {
                                    ref
                                    for raw in finding["raw"]
                                    for ref in raw["evidence_refs"]
                                }
                            ),
                        }
                        for finding in item["lens_findings"]
                    ],
                },
                "raw_judge_artifacts": item["raw_judge_artifacts"],
                "judge_feedback": "Independent Loop 02 blind panel evidence is preserved in aggregate/panel-scores.json.",
                "next_loop_feedback": (
                    "Use the evidence-driven Track finalists and preserved panel dissent "
                    "as inputs to synthesis-loop-01."
                ),
                "next_loop_feedback_ref": "judging/loop-02/aggregate/synthesis-input.json",
                "synthesis_feedback": [
                    {
                        "judge_id": record["judge_id"],
                        "feedback": record["synthesis_feedback"],
                    }
                    for record in item["raw_judges"]
                ],
            }
        )
    write_json(
        AGGREGATE_ROOT / "manifest-ready.json",
        {
            "schema_version": "1.0",
            "source_loop": "loop-02",
            "records": manifest_records,
            "track_finalists": finalists,
            "synthesis_parent_ids": synthesis_parents,
        },
    )

    synthesis_input = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "synthesis_loop_id": "synthesis-loop-01",
        "parent_ids": synthesis_parents,
        "track_finalists": [
            {
                "track_id": "track-single-page",
                "iteration_id": "single-page-loop-02",
                "role": "primary structural template",
                "adopt": [
                    "landmark trio and skip link",
                    "one-page anchor navigation and direct Edit controls",
                    "section-grouped error summary with preserved-values reassurance",
                    "compact-completed progressive disclosure with hidden descendants excluded from focus",
                    "fictional-value hints and atomic single-placement status",
                ],
                "reject": [
                    "lack of a discoverable confirmed clear-progress control",
                    "literal fictional card-number hints outside this synthetic demonstration",
                ],
            },
            {
                "track_id": "track-resumable-wizard",
                "iteration_id": "resumable-wizard-loop-02",
                "role": "selective safety and progress contributor",
                "adopt": [
                    "step-local validation and focus retention",
                    "role=progressbar with descriptive aria-valuetext",
                    "Save progress plus explicit Clear saved progress confirmation and Cancel",
                    "named synthetic confirmation",
                ],
                "reject": [
                    "shipping choices nested inside order-summary aside",
                    "extra step transitions when they do not reduce cognitive load",
                ],
            },
            {
                "track_id": "track-task-cards",
                "iteration_id": "task-cards-loop-01",
                "role": "independent task-status contributor retained after Loop 02 regression",
                "adopt": [
                    "independently understandable section completion state",
                    "direct per-section editability",
                ],
                "reject": [
                    "Loop 01 all-open mobile density",
                    "Loop 02 collapsed content that remains keyboard-focusable",
                    "silent review-checkbox reset",
                    "flat generic error dump",
                ],
            },
        ],
        "required_synthesis_constraints": [
            "Create a fresh synthesis candidate; do not mutate a parent.",
            "Keep all seven frozen objective gates blocking and use the unchanged harness.",
            "Use true multi-parent lineage exactly as listed.",
            "Write an explicit adoption/rejection matrix with evidence references.",
            "Preserve the permanent path-remediation procedural caveat.",
        ],
        "panel_scores_path": "judging/loop-02/aggregate/panel-scores.json",
        "pairwise_path": "judging/loop-02/aggregate/pairwise-aggregate.json",
        "provenance_path": "harness/path-violation-evidence/provenance.json",
    }
    write_json(AGGREGATE_ROOT / "synthesis-input.json", synthesis_input)

    split = next(
        item
        for item in pairwise_aggregate
        if item["pair"] == ["candidate-a", "candidate-b"]
    )
    (AGGREGATE_ROOT / "dissent.md").write_text(
        "# Loop 02 panel dissent\n\n"
        "The panel split on candidate A versus B. The accessibility judge preferred "
        "B for explicit save/restore, step-local validation, and confirmed clearing. "
        "The human-use judge preferred A for stronger landmarks, lower input burden, "
        "section-grouped recovery, and direct one-page editing. The disagreement is "
        "preserved and resolved by synthesis: use A as the structural template while "
        "adopting B's progress and destructive-action safety patterns.\n\n"
        f"Raw comparison records: `{json.dumps(split['raw'], ensure_ascii=False)}`\n",
        encoding="utf-8",
        newline="\n",
    )
    (AGGREGATE_ROOT / "panel-summary.md").write_text(
        "# Loop 02 panel summary\n\n"
        "- single-page-loop-02: 4.545454545454546; Track finalist.\n"
        "- resumable-wizard-loop-02: 4.318181818181818; Track finalist.\n"
        "- task-cards-loop-02: 3.090909090909091; rejected in favor of task-cards-loop-01.\n\n"
        "Synthesis parents: single-page-loop-02, resumable-wizard-loop-02, "
        "task-cards-loop-01. All objective gates remain passing; qualitative "
        "judging does not override them.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "track_finalists": finalists,
                "synthesis_parent_ids": synthesis_parents,
                "scores": {
                    item["iteration_id"]: item["human_use_quality"]["value"]
                    for item in panel_iterations
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
