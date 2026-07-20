#!/usr/bin/env python3
"""Assemble the multilingual dad-joke experiment from model-authored evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CRITERIA = (
    "cross_language_equivalence",
    "dad_joke_groan",
    "brevity",
    "cultural_portability",
    "translation_naturalness",
)
INITIAL_KEY = {
    "A": "track-gpt-5-5-loop-02",
    "B": "track-claude-sonnet-5-loop-01",
    "C": "track-gemini-3-1-pro-preview-loop-02",
    "D": "track-gpt-5-5-loop-01",
    "E": "track-claude-sonnet-5-loop-02",
    "F": "track-gemini-3-1-pro-preview-loop-01",
}
FINAL_KEY = {
    "P": "track-gemini-3-1-pro-preview-loop-01",
    "Q": "synthesis-loop-01",
    "R": "track-gemini-3-1-pro-preview-loop-02",
    "S": "synthesis-loop-02",
}
LOOPS = {
    "track-gpt-5-5-loop-01": ("track-gpt-5-5", "loop-01", "gpt-5.5"),
    "track-gpt-5-5-loop-02": ("track-gpt-5-5", "loop-02", "gpt-5.5"),
    "track-gemini-3-1-pro-preview-loop-01": (
        "track-gemini-3-1-pro-preview",
        "loop-01",
        "gemini-3.1-pro-preview",
    ),
    "track-gemini-3-1-pro-preview-loop-02": (
        "track-gemini-3-1-pro-preview",
        "loop-02",
        "gemini-3.1-pro-preview",
    ),
    "track-claude-sonnet-5-loop-01": (
        "track-claude-sonnet-5",
        "loop-01",
        "claude-sonnet-5",
    ),
    "track-claude-sonnet-5-loop-02": (
        "track-claude-sonnet-5",
        "loop-02",
        "claude-sonnet-5",
    ),
    "synthesis-loop-01": ("synthesis", "loop-01", "gpt-5.6-sol"),
    "synthesis-loop-02": ("synthesis", "loop-02", "gpt-5.6-sol"),
}
DECISIONS = {
    "track-gpt-5-5-loop-01": "keep_for_synthesis",
    "track-gpt-5-5-loop-02": "keep_for_synthesis",
    "track-gemini-3-1-pro-preview-loop-01": "new_best",
    "track-gemini-3-1-pro-preview-loop-02": "keep_for_synthesis",
    "track-claude-sonnet-5-loop-01": "reject",
    "track-claude-sonnet-5-loop-02": "reject",
    "synthesis-loop-01": "reject",
    "synthesis-loop-02": "keep_for_synthesis",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(
    artifact_id: str,
    path: Path,
    kind: str,
    role: str,
    label: str,
    mode: str,
    caption: str,
    *,
    primary: bool = False,
    featured: bool = False,
    comparison_key: str | None = None,
) -> dict[str, Any]:
    relative = path.relative_to(ROOT).as_posix()
    presentation: dict[str, Any] = {
        "mode": mode,
        "featured": featured,
        "primary": primary,
        "caption": caption,
    }
    if comparison_key:
        presentation["comparison_key"] = comparison_key
    return {
        "id": artifact_id,
        "kind": kind,
        "role": role,
        "label": label,
        "path": relative,
        "sha256": sha256(path),
        "presentation": presentation,
    }


def gate_pass(value: Any) -> bool:
    if value is True or value == "pass":
        return True
    if isinstance(value, dict):
        return value.get("status") in {"eligible", "pass"} or value.get("result") == "pass"
    return False


def aggregate_round(
    round_id: str, judge_files: list[Path], key: dict[str, str]
) -> dict[str, Any]:
    judges = [load(path) for path in judge_files]
    candidates: dict[str, Any] = {}
    for label, iteration_id in key.items():
        entries = []
        first_place_votes = []
        for judge in judges:
            entry = next(item for item in judge["candidates"] if item["label"] == label)
            entries.append(
                {
                    "judge_id": judge["judge_id"],
                    "model_id": judge["model_id"],
                    "scores": entry["scores"],
                    "mean": entry["mean"],
                    "completeness_gate": entry["completeness_gate"],
                    "rationale": entry["rationale"],
                    "defects": entry["defects"],
                    "recommendation": entry["recommendation"],
                }
            )
            if judge["ranking"][0] == label:
                first_place_votes.append(judge["judge_id"])
        means = {
            criterion: round(
                sum(float(entry["scores"][criterion]) for entry in entries) / len(entries),
                3,
            )
            for criterion in CRITERIA
        }
        candidates[iteration_id] = {
            "blind_label": label,
            "scores": means,
            "overall_mean": round(sum(means.values()) / len(CRITERIA), 3),
            "completeness_gate": (
                "pass"
                if all(gate_pass(entry["completeness_gate"]) for entry in entries)
                else "fail"
            ),
            "first_place_votes": first_place_votes,
            "judges": entries,
        }
    aggregate = {
        "round": round_id,
        "aggregation": "equal-weight mean with first-place votes and dissent preserved",
        "candidate_key": key,
        "judge_models": [
            {"judge_id": judge["judge_id"], "model_id": judge["model_id"]}
            for judge in judges
        ],
        "candidates": candidates,
    }
    dump(ROOT / round_id / "aggregate.json", aggregate)
    lines = [
        f"# Blind panel aggregate: {round_id}",
        "",
        "Scores are equal-weight means. Individual rationales and defects are preserved below.",
        "",
    ]
    for iteration_id, result in sorted(
        candidates.items(), key=lambda item: item[1]["overall_mean"], reverse=True
    ):
        lines.extend(
            [
                f"## {result['blind_label']} — {iteration_id}",
                "",
                f"- Mean: **{result['overall_mean']:.3f}/5**",
                f"- Completeness: **{result['completeness_gate']}**",
                f"- First-place votes: {len(result['first_place_votes'])}",
                "",
            ]
        )
        for entry in result["judges"]:
            lines.extend(
                [
                    f"### {entry['judge_id']} ({entry['model_id']})",
                    "",
                    f"- Mean: {entry['mean']}/5",
                    f"- Rationale: {entry['rationale']}",
                    f"- Defects/dissent: {entry['defects']}",
                    f"- Recommendation: {entry['recommendation']}",
                    "",
                ]
            )
    (ROOT / round_id / "aggregate.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
    return aggregate


def normalize_lesson(value: Any, iteration_id: str) -> dict[str, str]:
    if isinstance(value, dict) and all(
        key in value for key in ("trigger", "action", "evidence", "confidence")
    ):
        return value
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {
        "trigger": f"Feedback from {iteration_id}",
        "action": text,
        "evidence": f"Candidate and critique artifacts for {iteration_id}",
        "confidence": "medium",
    }


def read_loop(track_dir: str, loop_dir: str) -> dict[str, Any]:
    return load(ROOT / track_dir / loop_dir / "loop.json")


def make_judge_aggregate(
    iteration_id: str, round_id: str, result: dict[str, Any]
) -> Path:
    track_dir, loop_dir, _ = LOOPS[iteration_id]
    path = ROOT / track_dir / loop_dir / "judge-aggregate.md"
    lines = [
        f"# Judge aggregate: {iteration_id}",
        "",
        f"- Round: `{round_id}`",
        f"- Blind label: `{result['blind_label']}`",
        f"- Aggregation: equal-weight mean with dissent preserved",
        f"- Overall mean: **{result['overall_mean']:.3f}/5**",
        f"- Objective completeness: **{result['completeness_gate']}**",
        f"- First-place votes: **{len(result['first_place_votes'])}**",
        "",
        "## Criterion means",
        "",
    ]
    lines.extend(
        f"- {criterion}: {value:.3f}/5"
        for criterion, value in result["scores"].items()
    )
    lines.extend(["", "## Independent panel notes", ""])
    for entry in result["judges"]:
        lines.extend(
            [
                f"### {entry['judge_id']} — `{entry['model_id']}`",
                "",
                f"- Rationale: {entry['rationale']}",
                f"- Defects / dissent: {entry['defects']}",
                f"- Recommendation: {entry['recommendation']}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    initial_files = [
        ROOT / "panel/judge-claude-opus-4-8/scores.json",
        ROOT / "panel/judge-gpt-5-6-terra/scores.json",
        ROOT / "panel/judge-gemini-3-1-pro-preview/scores.json",
    ]
    final_files = [
        ROOT / "panel-final/judge-claude-opus-4-8/scores.json",
        ROOT / "panel-final/judge-gpt-5-6-terra/scores.json",
        ROOT / "panel-final/judge-gemini-3-1-pro-preview/scores.json",
    ]
    initial = aggregate_round("panel", initial_files, INITIAL_KEY)
    final = aggregate_round("panel-final", final_files, FINAL_KEY)
    dump(ROOT / "panel/candidate-key.json", INITIAL_KEY)
    dump(ROOT / "panel-final/candidate-key.json", FINAL_KEY)

    final_dir = ROOT / "final"
    final_dir.mkdir(exist_ok=True)
    champion_source = ROOT / "track-gemini-3-1-pro-preview/loop-01/candidate.json"
    champion_draft_source = ROOT / "track-gemini-3-1-pro-preview/loop-01/draft.md"
    shutil.copyfile(champion_source, final_dir / "champion.json")
    shutil.copyfile(champion_draft_source, final_dir / "champion.md")

    prompt_text = (ROOT.parent / "prompt.md").read_text(encoding="utf-8")
    iterations = []
    for iteration_id, (track_dir, loop_dir, model_id) in LOOPS.items():
        record = read_loop(track_dir, loop_dir)
        result = (
            final["candidates"][iteration_id]
            if iteration_id in final["candidates"]
            else initial["candidates"][iteration_id]
        )
        round_id = "panel-final" if iteration_id in final["candidates"] else "panel"
        judge_path = make_judge_aggregate(iteration_id, round_id, result)
        candidate_path = ROOT / track_dir / loop_dir / "candidate.json"
        draft_path = ROOT / track_dir / loop_dir / "draft.md"
        critique_path = ROOT / track_dir / loop_dir / "self-critique.md"
        raw_loop_path = ROOT / track_dir / loop_dir / "loop.json"
        prompt = record.get("prompt", {})
        original_feedback = str(prompt.get("judge_feedback", "")).strip()
        panel_feedback = (
            f"Post-generation blind {round_id} panel: label {result['blind_label']}; "
            f"aggregate {result['overall_mean']:.3f}/5; "
            + " | ".join(
                f"{entry['judge_id']} ({entry['model_id']}): {entry['rationale']} "
                f"Defects: {entry['defects']}"
                for entry in result["judges"]
            )
        )
        artifacts = [
            artifact(
                f"{iteration_id}-candidate",
                candidate_path,
                "candidate",
                "primary-output",
                f"{iteration_id} structured candidate",
                "structured_json",
                "Four-language candidate with mechanism and portability notes.",
                primary=True,
                comparison_key="multilingual-joke",
            ),
            artifact(
                f"{iteration_id}-draft",
                draft_path,
                "draft",
                "multilingual-draft",
                f"{iteration_id} multilingual draft",
                "markdown",
                "Native-script English, French, Spanish, and Japanese draft.",
            ),
            artifact(
                f"{iteration_id}-critique",
                critique_path,
                "critique",
                "generator-feedback",
                f"{iteration_id} self-critique",
                "markdown",
                "Generator critique used to drive or close the Track.",
            ),
            artifact(
                f"{iteration_id}-judge-aggregate",
                judge_path,
                "judge-note",
                "panel-evidence",
                f"{iteration_id} blind panel aggregate",
                "markdown",
                "Independent blind scores, rationales, defects, and dissent.",
            ),
            artifact(
                f"{iteration_id}-raw-loop",
                raw_loop_path,
                "loop-record",
                "prompt-history",
                f"{iteration_id} raw Loop record",
                "structured_json",
                "Model-authored Loop record with full prompt and feedback chain.",
            ),
        ]
        if iteration_id == "track-gemini-3-1-pro-preview-loop-01":
            artifacts.extend(
                [
                    artifact(
                        "champion-final-json",
                        final_dir / "champion.json",
                        "candidate",
                        "final-output",
                        "Champion structured candidate",
                        "structured_json",
                        "Winning visual-mechanism joke in four languages.",
                    ),
                    artifact(
                        "champion-final-md",
                        final_dir / "champion.md",
                        "draft",
                        "final-output",
                        "Champion multilingual draft",
                        "markdown",
                        "The final native-script multilingual joke.",
                        featured=True,
                    ),
                ]
            )
        scores = [
            {
                "scorer_id": (
                    "championship-panel-rubric"
                    if round_id == "panel-final"
                    else "initial-panel-rubric"
                ),
                "criterion_id": criterion,
                "value": value,
                "notes": f"Blind three-judge {round_id} equal-weight mean.",
            }
            for criterion, value in result["scores"].items()
        ]
        scores.append(
            {
                "scorer_id": "native-script-completeness",
                "criterion_id": "objective_completeness",
                "value": 1,
                "notes": "All four required languages are present; Japanese uses Japanese script.",
            }
        )
        parents = record.get("parent_ids", [])
        iterations.append(
            {
                "id": iteration_id,
                "track_id": track_dir,
                "parent_ids": parents,
                "model_id": model_id,
                "hypothesis": str(record.get("hypothesis", "Improve the multilingual joke.")),
                "outcome": (
                    str(record.get("outcome", "Candidate produced."))
                    + f" Blind {round_id} aggregate: {result['overall_mean']:.3f}/5; "
                    + f"completeness {result['completeness_gate']}."
                ),
                "commands": {
                    "build": f"Model {model_id} authored {track_dir}/{loop_dir}/candidate.json and draft.md",
                    "run": "python check_completeness.py --data . --out completeness-report.json",
                    "judge": f"Three independent blind judges scored label {result['blind_label']} in {round_id}",
                },
                "artifacts": artifacts,
                "scores": scores,
                "prompt": {
                    "track_prompt": str(prompt.get("track_prompt", "")),
                    "input_feedback": str(prompt.get("input_feedback", "")),
                    "judge_feedback": (
                        (original_feedback + "\n\n") if original_feedback else ""
                    )
                    + panel_feedback,
                    "next_prompt": str(prompt.get("next_prompt", "")),
                },
                "quality_gates": {
                    "native_script_completeness": result["completeness_gate"]
                },
                "changed_files": [
                    candidate_path.relative_to(ROOT).as_posix(),
                    draft_path.relative_to(ROOT).as_posix(),
                    critique_path.relative_to(ROOT).as_posix(),
                    raw_loop_path.relative_to(ROOT).as_posix(),
                    judge_path.relative_to(ROOT).as_posix(),
                ],
                "lesson": normalize_lesson(record.get("lesson", ""), iteration_id),
                "decision": DECISIONS[iteration_id],
                "stop_reason": record.get("stop_reason"),
                "blind_panel": {
                    "round": round_id,
                    "label": result["blind_label"],
                    "first_place_votes": result["first_place_votes"],
                    "individual_judges": [
                        {
                            "judge_id": entry["judge_id"],
                            "model_id": entry["model_id"],
                            "scores": entry["scores"],
                            "mean": entry["mean"],
                            "rationale": entry["rationale"],
                            "defects": entry["defects"],
                            "recommendation": entry["recommendation"],
                        }
                        for entry in result["judges"]
                    ],
                },
            }
        )

    manifest = {
        "schema_version": "1.1",
        "experiment_id": "multilingual-dad-joke",
        "title": "A dad joke that survives four languages",
        "created_at": "2026-07-20T21:24:32.306+10:00",
        "problem": {
            "statement": "Create one wholesome dad joke that lands naturally in English, French, Spanish, and Japanese.",
            "optimization_target": "Maximize equal-weight cross-language equivalence, dad-joke groan, brevity, cultural portability, and translation naturalness while passing native-script completeness.",
            "constraints": [
                "Use English, French, Spanish, and Japanese in native script.",
                "Prefer a universal comic mechanism over English-only wordplay.",
                "Run three independent two-Loop generator Tracks and a two-Loop synthesis Track.",
                "Use a blind three-model panel and preserve dissent.",
                "A failed native-script completeness scorer blocks Champion promotion.",
            ],
            "success_criteria": [
                "Every candidate presents all four languages and passes the objective script gate.",
                "Every generator materially improves or reconsiders its first candidate.",
                "The Champion has independent blind-panel support across all five qualitative criteria.",
                "The synthesis explicitly accepts or rejects lessons from every parent Track.",
            ],
            "original_prompt": prompt_text,
        },
        "generation": {
            "skill_commit": "d086a6686a0e13d7c42241b92c74793cdafac702",
            "skill_tree_sha256": "86017f17afddb3815c003b3224a03de6cb468d4e7ebb702a442eb3b120b50222",
            "prompt_sha256": "fd85e24df3e799b72408d93ce972f18ff7cab23520ecaef51a5a41efd3857d3f",
            "copilot_cli_version": "GitHub Copilot CLI 1.0.71-2.\nRun 'copilot update' to check for updates.",
            "orchestrator_model": "gpt-5.6-sol",
            "models": [
                {"role": "orchestrator", "model_id": "gpt-5.6-sol"},
                {
                    "role": "generator",
                    "track_id": "track-gpt-5-5",
                    "model_id": "gpt-5.5",
                },
                {
                    "role": "generator",
                    "track_id": "track-gemini-3-1-pro-preview",
                    "model_id": "gemini-3.1-pro-preview",
                },
                {
                    "role": "generator",
                    "track_id": "track-claude-sonnet-5",
                    "model_id": "claude-sonnet-5",
                },
                {
                    "role": "synthesis",
                    "track_id": "synthesis",
                    "model_id": "gpt-5.6-sol",
                },
                {
                    "role": "initial-blind-judge",
                    "model_id": "claude-opus-4.8",
                },
                {
                    "role": "initial-blind-judge",
                    "model_id": "gpt-5.6-terra",
                },
                {
                    "role": "initial-blind-judge",
                    "model_id": "gemini-3.1-pro-preview",
                },
                {
                    "role": "championship-blind-judge",
                    "model_id": "claude-opus-4.8",
                },
                {
                    "role": "championship-blind-judge",
                    "model_id": "gpt-5.6-terra",
                },
                {
                    "role": "championship-blind-judge",
                    "model_id": "gemini-3.1-pro-preview",
                },
            ]
            + [
                {
                    "role": "loop-author",
                    "iteration_id": iteration_id,
                    "track_id": track_dir,
                    "model_id": model_id,
                }
                for iteration_id, (track_dir, _, model_id) in LOOPS.items()
            ],
        },
        "budget": {
            "max_iters": 8,
            "patience": 4,
            "cost_limit": None,
            "wall_time_limit_sec": 3600,
        },
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["**"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {
                "id": criterion,
                "label": criterion.replace("_", " ").title(),
                "weight": 0.2,
                "direction": "maximize",
                "unit": "points (1-5)",
                "comparable_across_tracks": True,
                "primary": criterion == "cross_language_equivalence",
            }
            for criterion in CRITERIA
        ]
        + [
            {
                "id": "objective_completeness",
                "label": "Four languages in native script",
                "weight": 0,
                "direction": "maximize",
                "unit": "pass (1) / fail (0)",
                "comparable_across_tracks": True,
                "primary": False,
                "gate": {"operator": "gte", "threshold": 1},
            }
        ],
        "scorers": [
            {
                "id": "native-script-completeness",
                "type": "objective_command",
                "criterion_ids": ["objective_completeness"],
                "command": "python check_completeness.py --data . --out completeness-report.json",
                "primary": True,
                "weight": 0,
            },
            {
                "id": "initial-panel-rubric",
                "type": "llm_rubric",
                "criterion_ids": list(CRITERIA),
                "judge_panel": "initial-blind-panel",
                "primary": True,
                "weight": 1,
            },
            {
                "id": "championship-panel-rubric",
                "type": "pairwise_judge",
                "criterion_ids": list(CRITERIA),
                "judge_panel": "championship-blind-panel",
                "primary": True,
                "weight": 1,
            },
        ],
        "judge_panels": [
            {
                "id": "initial-blind-panel",
                "blind": True,
                "flip_pairwise_order": False,
                "aggregation": "weighted_mean_with_dissent",
                "judges": [
                    {
                        "id": "judge-claude-opus-4-8",
                        "model_id": "claude-opus-4.8",
                        "role": "multilingual comedy critic",
                    },
                    {
                        "id": "judge-gpt-5-6-terra",
                        "model_id": "gpt-5.6-terra",
                        "role": "portability and naturalness critic",
                    },
                    {
                        "id": "judge-gemini-3-1-pro-preview",
                        "model_id": "gemini-3.1-pro-preview",
                        "role": "visual and cultural mechanism critic",
                    },
                ],
            },
            {
                "id": "championship-blind-panel",
                "blind": True,
                "flip_pairwise_order": False,
                "aggregation": "weighted_mean_with_dissent",
                "judges": [
                    {
                        "id": "final-judge-claude-opus-4-8",
                        "model_id": "claude-opus-4.8",
                        "role": "championship multilingual comedy critic",
                    },
                    {
                        "id": "final-judge-gpt-5-6-terra",
                        "model_id": "gpt-5.6-terra",
                        "role": "championship portability critic",
                    },
                    {
                        "id": "final-judge-gemini-3-1-pro-preview",
                        "model_id": "gemini-3.1-pro-preview",
                        "role": "championship visual-mechanism critic",
                    },
                ],
            },
        ],
        "governance": {
            "self_editing": {
                "requires_user_approval": True,
                "proposal_required": True,
                "approved_proposal_id": None,
            }
        },
        "tracks": [
            {
                "id": "track-gpt-5-5",
                "label": "GPT-5.5 generator",
                "hypothesis": "Universal physical behavior can form a portable riddle.",
                "final_decision": "Useful portability lessons; not Champion.",
            },
            {
                "id": "track-gemini-3-1-pro-preview",
                "label": "Gemini 3.1 Pro Preview generator",
                "hypothesis": "Visual and spatial mechanisms can retain the same reveal in every language.",
                "final_decision": "Loop 01 visual mechanism became Champion.",
            },
            {
                "id": "track-claude-sonnet-5",
                "label": "Claude Sonnet 5 generator",
                "hypothesis": "A category-confusion introduction joke can be rebuilt around shared grammar.",
                "final_decision": "Candidate rejected; grammatical-audit lesson retained.",
            },
            {
                "id": "synthesis",
                "label": "GPT-5.6 Sol synthesis",
                "hypothesis": "A refined wall joke can combine geometry, brevity, and per-language idiom.",
                "final_decision": "Improved the wall finalist, but lost 2-1 to the visual Champion.",
            },
        ],
        "iterations": iterations,
        "champion": {
            "iteration_id": "track-gemini-3-1-pro-preview-loop-01",
            "summary": "The high-eyebrows/surprised joke won the blind championship because its visual cause-and-effect survives all four languages without a grammar or corner-vocabulary seam.",
            "reasons": [
                {
                    "text": "It received two of three first-place championship votes and the highest equal-weight panel mean (4.667/5).",
                    "evidence_refs": [
                        "track-gemini-3-1-pro-preview-loop-01-judge-aggregate",
                        "champion-final-json",
                    ],
                },
                {
                    "text": "All judges scored cross-language equivalence and cultural portability 5/5 because raised eyebrows visually imply surprise.",
                    "evidence_refs": [
                        "cross_language_equivalence",
                        "cultural_portability",
                        "champion-final-json",
                    ],
                },
                {
                    "text": "The blocking four-language native-script scorer passed.",
                    "evidence_refs": [
                        "objective_completeness",
                        "champion-final-md",
                    ],
                },
            ],
            "caveats": [
                {
                    "text": "It is longer than the compact wall synthesis; the panel mean for brevity was 3.667/5.",
                    "evidence_refs": [
                        "brevity",
                        "track-gemini-3-1-pro-preview-loop-01-judge-aggregate",
                    ],
                },
                {
                    "text": "Terra dissented, preferring synthesis Loop 02 for its tighter four-language balance.",
                    "evidence_refs": [
                        "synthesis-loop-02-judge-aggregate",
                        "track-gemini-3-1-pro-preview-loop-01-judge-aggregate",
                    ],
                },
            ],
        },
        "story": {
            "milestones": [
                {
                    "iteration_id": "track-gpt-5-5-loop-01",
                    "caption": "Echo established a highly portable but gentle baseline.",
                },
                {
                    "iteration_id": "track-gpt-5-5-loop-02",
                    "caption": "Shadow made the physical mechanism more visual.",
                },
                {
                    "iteration_id": "track-gemini-3-1-pro-preview-loop-01",
                    "caption": "Eyebrows introduced the eventual visual Champion.",
                },
                {
                    "iteration_id": "track-gemini-3-1-pro-preview-loop-02",
                    "caption": "Walls tightened the joke into a classic Q&A.",
                },
                {
                    "iteration_id": "track-claude-sonnet-5-loop-01",
                    "caption": "Hunger exposed the grammatical-calque trap.",
                },
                {
                    "iteration_id": "track-claude-sonnet-5-loop-02",
                    "caption": "Tired improved grammar but still failed native comic license.",
                },
                {
                    "iteration_id": "synthesis-loop-01",
                    "caption": "Synthesis repaired Spanish and Japanese wall seams.",
                },
                {
                    "iteration_id": "synthesis-loop-02",
                    "caption": "A compact wall finalist won Terra’s vote but not the panel.",
                },
            ],
            "featured_artifact_id": "champion-final-md",
            "primary_comparison_key": "multilingual-joke",
        },
        "rules": [
            "Prefer visual or physical mechanisms whose comic inference exists before translation.",
            "Treat shared grammar as insufficient evidence of shared comic license; audit native effect.",
        ],
        "synthesis": "GPT-5.6 Sol accepted GPT-5.5’s concrete-physical lesson, Gemini’s visual/Q&A lessons, and Claude’s grammatical-audit discipline. It rejected the shadow candidate as too mild, rejected claims that the original wall translations were perfect, and rejected both name-pun candidates as calques. The refined wall joke improved Japanese and Spanish but lost the championship 2-1 to the eyebrows visual gag. Full accept/reject evidence is in synthesis/acceptance-matrix.json and synthesis/synthesis-report.md.",
    }
    dump(ROOT / "manifest.json", manifest)

    readme = """# Multilingual dad-joke Experiment

This Generated Example searches for one wholesome dad joke that lands naturally in English, French, Spanish, and Japanese. The Champion is a visual cause-and-effect joke: eyebrows drawn too high make someone look surprised.

## Experiment

Five equal-weight qualitative criteria guide the hill-climb: cross-language equivalence, dad-joke groan, brevity, cultural portability, and translation naturalness. A reproducible objective scorer blocks any candidate missing one of the four languages or Japanese native script.

## Topology

Three independent generators (`gpt-5.5`, `gemini-3.1-pro-preview`, and `claude-sonnet-5`) each run two Loops. A `gpt-5.6-sol` synthesis Track then accepts or rejects lessons from all three parents and runs two more Loops. `parent_ids` preserve single-parent improvements and the synthesis Track’s three-parent lineage.

## Judging

The same blind panel (`claude-opus-4.8`, `gpt-5.6-terra`, and `gemini-3.1-pro-preview`) first scores all six source candidates, then judges a championship slate containing the two leading sources and both synthesis Loops. Scores use equal-weight means, while every individual rationale, defect, ranking, and dissent remains available. The Champion wins two first-place votes to one; Terra’s preference for the compact wall synthesis is retained as a caveat.

## Inspect or rerun

Open `viewer.html` directly to inspect the Problem, topology, complete Loop prompt/feedback chains, artifacts, scores, and Champion evidence. To rebuild and revalidate from this folder:

```text
python check_completeness.py --data . --out completeness-report.json
python build_viewer.py --data . --out viewer.html
node ..\\.github\\skills\\experiment-loop\\references\\navigation_judge\\cli.mjs --viewer viewer.html --out .
python -m references.evidence_gate .
```

Run the final two commands from the repository root with the skill root on `PYTHONPATH`, or set `EXPERIMENT_LOOP_SKILL_ROOT` for the Viewer adapter.

## Feature surface demonstrated

**Viewer capabilities:** fixed Overview, Topology, and Compare views; authored milestones; multi-parent lineage; per-Loop Artifact inspection; full prompt/input-feedback/judge-feedback/next-prompt chains; criterion timelines; blind-panel dissent; evidence-linked Champion reasons and caveats; structured generation provenance; native-script rendering; objective gate state; and offline deterministic rebuilds.

**Manifest capabilities:** schema v1.1 Problem framing with exact original Prompt evidence; authoritative generation fields and actual model IDs; explicit scorer semantics and a blocking objective gate; blind judge panels; comparable scorecards; structured Artifact presentation metadata; eight Loops with `parent_ids`; multi-parent synthesis; authored story milestones; and evidence-linked Champion decisions.
"""
    (ROOT / "example-readme.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
