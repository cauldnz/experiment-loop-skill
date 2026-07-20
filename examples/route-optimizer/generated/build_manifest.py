#!/usr/bin/env python3
"""Build the deterministic Manifest v1.1 from measured experiment evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACK = ROOT / "track-quantitative"
LENGTHS = [81.425571978, 42.530641862, 38.066195605, 37.576644306]
EXPLAINABILITY = [5, 4, 4, 5]
STRATEGIES = ["baseline", "nearest", "two_opt", "multi_start"]
HYPOTHESES = [
    "Measure a deterministic alphabetical tour to establish the unoptimized reference.",
    "A nearest-neighbor construction will sharply reduce distance while preserving both hard gates.",
    "A deterministic 2-opt pass will remove avoidable long edges from the constructed tour.",
    "Multi-start nearest-neighbor plus 2-opt will escape the single-start local optimum.",
]
TRACK_PROMPTS = [
    "Generate the measured baseline: sort all 12 named stops alphabetically, wrap the route with Central Depot, run it three times, validate it, measure Euclidean length, and render its route map.",
    "Generate a deterministic construction candidate on the unchanged fixed input: repeatedly choose the nearest unvisited stop with a lexical tie-break, return to the depot, run three times, validate, measure, and render.",
    "Improve the nearest-neighbor candidate with deterministic best-improvement 2-opt until no improving reversal remains; preserve the fixed input and objective gates, repeat three times, measure, and render.",
    "Synthesize the strongest candidate by forcing each possible first stop, applying nearest-neighbor plus 2-opt, and choosing the shortest tour with deterministic tie-breaking. Verify it independently with the Held-Karp exact oracle.",
]
NEXT_PROMPTS = [
    "Use a deterministic nearest-neighbor construction on the identical fixed data and compare it with the 81.425571978 km baseline.",
    "Apply deterministic 2-opt local search to the nearest-neighbor route and retain the validity and reproducibility gates.",
    "Run nearest-neighbor plus 2-opt from every possible first stop, retain the shortest deterministic result, and ask an independent exact oracle whether it is globally optimal.",
    "For a future experiment, test scalability on larger fixed instances and compare the heuristic against a tractable lower bound.",
]
OUTCOMES = [
    "The valid, reproducible alphabetical baseline measured 81.425571978 km.",
    "Nearest-neighbor passed both gates and reduced length by 38.894930116 km to 42.530641862 km.",
    "2-opt passed both gates and reduced length by another 4.464446257 km to 38.066195605 km.",
    "Multi-start passed both gates, reached 37.576644306 km, and the independent exact oracle certified a zero optimality gap.",
]
CAPTIONS = [
    "Measured baseline: valid but geometry-blind",
    "Construction heuristic: nearest-neighbor removes 47.77%",
    "Local search: 2-opt removes avoidable long edges",
    "Final synthesis: multi-start reaches the certified optimum",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(
    artifact_id: str,
    kind: str,
    role: str,
    label: str,
    path: str,
    mode: str,
    caption: str,
    comparison_key: str,
    *,
    primary: bool = False,
    featured: bool = False,
    alt_text: str | None = None,
) -> dict[str, object]:
    presentation: dict[str, object] = {
        "mode": mode,
        "featured": featured,
        "primary": primary,
        "caption": caption,
        "comparison_key": comparison_key,
    }
    if alt_text is not None:
        presentation["alt_text"] = alt_text
    return {
        "id": artifact_id,
        "kind": kind,
        "role": role,
        "label": label,
        "path": path,
        "sha256": sha(ROOT / path),
        "presentation": presentation,
    }


def loop_artifacts(number: int) -> list[dict[str, object]]:
    prefix = f"track-quantitative/loop-{number:02d}"
    strategy_label = STRATEGIES[number - 1].replace("_", " ").title()
    items = [
        artifact(
            f"loop-{number:03d}-map",
            "route-map",
            "primary-output",
            f"{strategy_label} route map",
            f"{prefix}/route-map.svg",
            "svg",
            f"{strategy_label} tour on the fixed 12-stop Cartesian instance.",
            "route-map",
            primary=True,
            featured=number == 4,
            alt_text=(
                f"Map of the Loop {number} {strategy_label} tour, beginning and "
                f"ending at Central Depot; measured length {LENGTHS[number - 1]:.9f} km."
            ),
        ),
        artifact(
            f"loop-{number:03d}-metrics",
            "objective-metrics",
            "measurement-evidence",
            f"Loop {number} objective metrics",
            f"{prefix}/metrics.json",
            "metric_set",
            (
                f"Measured route length, validity gate, and three-run "
                f"reproducibility gate for Loop {number}."
            ),
            "objective-metrics",
        ),
        artifact(
            f"loop-{number:03d}-route",
            "route-record",
            "candidate-output",
            f"Loop {number} ordered route",
            f"{prefix}/route.json",
            "structured_json",
            f"Ordered depot-to-depot route generated in Loop {number}.",
            "route-record",
        ),
        artifact(
            f"loop-{number:03d}-judge",
            "judge-note",
            "independent-judgment",
            f"Loop {number} independent judge note",
            f"{prefix}/judge.md",
            "markdown",
            f"Independent claude-sonnet-5 explanation judgment for Loop {number}.",
            "judge-note",
        ),
    ]
    if number == 1:
        items.extend(
            [
                artifact(
                    "fixed-stop-data",
                    "input-data",
                    "fixed-input",
                    "Fixed depot and 12 named stops",
                    "stops.json",
                    "structured_json",
                    "The immutable Cartesian-kilometer input shared by every candidate.",
                    "fixed-input",
                ),
                artifact(
                    "optimizer-source",
                    "source-code",
                    "runnable-code",
                    "Candidate optimizer source",
                    "optimizer.py",
                    "code",
                    "Runnable deterministic baseline, nearest-neighbor, 2-opt, and multi-start implementations.",
                    "optimizer-code",
                ),
                artifact(
                    "original-prompt-evidence",
                    "prompt",
                    "prompt-evidence",
                    "Exact original Experiment Prompt",
                    "original-prompt.md",
                    "markdown",
                    "Verbatim Experiment Prompt used to frame and evaluate this run.",
                    "original-prompt",
                ),
            ]
        )
    if number == 4:
        items.extend(
            [
                artifact(
                    "exact-oracle-result",
                    "objective-proof",
                    "optimality-evidence",
                    "Held-Karp exact oracle result",
                    f"{prefix}/oracle.json",
                    "metric_set",
                    "Independent exhaustive oracle proof: the Champion has zero optimality gap.",
                    "optimality-proof",
                ),
                artifact(
                    "exact-oracle-source",
                    "source-code",
                    "runnable-code",
                    "Independent exact oracle source",
                    "objective_oracle.py",
                    "code",
                    "Runnable Held-Karp dynamic program independent of candidate generation.",
                    "oracle-code",
                ),
            ]
        )
    return items


def main() -> int:
    original_prompt = (ROOT / "original-prompt.md").read_text(encoding="utf-8")
    judge_notes = [
        (TRACK / f"loop-{number:02d}" / "judge.md").read_text(encoding="utf-8")
        for number in range(1, 5)
    ]
    iterations = []
    for index in range(4):
        number = index + 1
        previous_feedback = (
            "No prior Loop; the exact original Experiment Prompt is the input."
            if index == 0
            else judge_notes[index - 1]
        )
        scores = [
            {
                "scorer_id": "objective-route-scorer",
                "criterion_id": "route-length",
                "value": LENGTHS[index],
                "notes": "Total Euclidean depot-to-depot tour length from metrics.json.",
            },
            {
                "scorer_id": "objective-gate-scorer",
                "criterion_id": "validity",
                "value": 1,
                "notes": "All 12 stops visited exactly once; route starts and ends at Central Depot.",
            },
            {
                "scorer_id": "objective-gate-scorer",
                "criterion_id": "reproducibility",
                "value": 1,
                "notes": "Three repeated runs produced an identical ordered route.",
            },
            {
                "scorer_id": "independent-explanation-judge",
                "criterion_id": "explainability",
                "value": EXPLAINABILITY[index],
                "notes": "Independent qualitative score by claude-sonnet-5; non-overriding.",
            },
        ]
        iterations.append(
            {
                "id": f"loop-{number:03d}",
                "track_id": "quantitative-route",
                "parent_ids": [] if index == 0 else [f"loop-{number - 1:03d}"],
                "model_id": "gpt-5.6-sol",
                "hypothesis": HYPOTHESES[index],
                "outcome": OUTCOMES[index],
                "commands": {
                    "build": f"Implement/select the {STRATEGIES[index]} strategy in generated/optimizer.py.",
                    "run": (
                        f"python generated/optimizer.py --data generated/stops.json "
                        f"--strategy {STRATEGIES[index]} --out "
                        f"generated/track-quantitative/loop-{number:02d}"
                        + (
                            " && python generated/objective_oracle.py --data "
                            "generated/stops.json --candidate "
                            "generated/track-quantitative/loop-04/route.json --out "
                            "generated/track-quantitative/loop-04/oracle.json"
                            if number == 4
                            else ""
                        )
                    ),
                    "judge": (
                        f"claude-sonnet-5 independently inspects Loop {number} route, "
                        "metrics, map, source, and prior evidence; objective scorers retain authority."
                    ),
                },
                "artifacts": loop_artifacts(number),
                "scores": scores,
                "prompt": {
                    "track_prompt": TRACK_PROMPTS[index],
                    "input_feedback": previous_feedback,
                    "judge_feedback": judge_notes[index],
                    "next_prompt": NEXT_PROMPTS[index],
                },
                "quality_gates": {
                    "validity": "pass",
                    "reproducibility": "pass",
                    "global_optimality": "pass" if number == 4 else "not_run",
                },
                "changed_files": [
                    "generated/optimizer.py",
                    f"generated/track-quantitative/loop-{number:02d}/route.json",
                    f"generated/track-quantitative/loop-{number:02d}/metrics.json",
                    f"generated/track-quantitative/loop-{number:02d}/route-map.svg",
                    f"generated/track-quantitative/loop-{number:02d}/judge.md",
                ]
                + (
                    [
                        "generated/objective_oracle.py",
                        "generated/track-quantitative/loop-04/oracle.json",
                    ]
                    if number == 4
                    else []
                ),
                "lesson": {
                    "trigger": (
                        "Measured fixed-input evidence"
                        if number == 1
                        else f"Loop {number - 1} judge feedback and route-length result"
                    ),
                    "action": NEXT_PROMPTS[index],
                    "evidence": OUTCOMES[index],
                    "confidence": "high",
                },
                "decision": "new_best",
                "stop_reason": (
                    "Certified global optimum reached for the fixed input."
                    if number == 4
                    else None
                ),
            }
        )

    manifest = {
        "schema_version": "1.1",
        "experiment_id": "fixed-12-stop-route-optimizer",
        "title": "From Alphabetical Tour to Certified-Optimal Delivery Route",
        "created_at": "2026-07-20T20:45:33.373+10:00",
        "problem": {
            "statement": (
                "Find a short closed delivery tour through a fixed depot and 12 named "
                "stops, while making each improvement auditable to a technically curious reader."
            ),
            "optimization_target": (
                "Minimize total Euclidean route length in kilometers; route length is "
                "the primary ranking metric after validity and reproducibility pass."
            ),
            "constraints": [
                "Start at Central Depot and return to Central Depot.",
                "Visit every one of the 12 named stops exactly once.",
                "Use the identical immutable Cartesian input in generated/stops.json for every Loop.",
                "A route that misses or duplicates a stop cannot become Champion.",
                "A route that differs across three repeated runs cannot become Champion.",
                "The independent explanation judge cannot override objective gates or route length.",
            ],
            "success_criteria": [
                "Beat the measured 81.425571978 km baseline on the fixed input.",
                "Pass validity at exactly 1 and reproducibility at exactly 1.",
                "Provide an inline route map, rendered objective metrics, and independent explanation note for every Loop.",
                "Use an independent exact oracle to determine the Champion's global-optimality gap.",
            ],
            "original_prompt": original_prompt,
        },
        "generation": {
            "skill_commit": "d086a6686a0e13d7c42241b92c74793cdafac702",
            "skill_tree_sha256": "86017f17afddb3815c003b3224a03de6cb468d4e7ebb702a442eb3b120b50222",
            "prompt_sha256": "d60b7e2b891670a164c220b319d7045b9051541ad0c6a5a9d5a3228dad3a7d9d",
            "copilot_cli_version": "GitHub Copilot CLI 1.0.71-2.\nRun 'copilot update' to check for updates.",
            "orchestrator_model": "gpt-5.6-sol",
            "models": [
                {"role": "orchestrator", "model_id": "gpt-5.6-sol"},
                *[
                    {
                        "role": "candidate-generator",
                        "model_id": "gpt-5.6-sol",
                        "track_id": "quantitative-route",
                        "iteration_id": f"loop-{number:03d}",
                    }
                    for number in range(1, 5)
                ],
                {
                    "role": "synthesis-generator",
                    "model_id": "gpt-5.6-sol",
                    "track_id": "quantitative-route",
                    "iteration_id": "loop-004",
                },
                *[
                    {
                        "role": "independent-explanation-judge",
                        "model_id": "claude-sonnet-5",
                        "track_id": "quantitative-route",
                        "iteration_id": f"loop-{number:03d}",
                    }
                    for number in range(1, 5)
                ],
                {
                    "role": "objective-oracle",
                    "model_id": "non-LLM: Held-Karp dynamic programming",
                    "track_id": "quantitative-route",
                    "iteration_id": "loop-004",
                },
            ],
        },
        "budget": {
            "max_iters": 4,
            "patience": 4,
            "cost_limit": None,
            "wall_time_limit_sec": 3600,
        },
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["generated/**"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {
                "id": "route-length",
                "label": "Route length",
                "weight": 1.0,
                "direction": "minimize",
                "unit": "km",
                "comparable_across_tracks": True,
                "primary": True,
                "baseline": {
                    "value": LENGTHS[0],
                    "unit": "km",
                    "source_artifact_id": "loop-001-metrics",
                },
            },
            {
                "id": "validity",
                "label": "Validity",
                "weight": 0.0,
                "direction": "maximize",
                "unit": "pass (1) / fail (0)",
                "comparable_across_tracks": True,
                "primary": False,
                "baseline": {
                    "value": 1,
                    "unit": "pass (1) / fail (0)",
                    "source_artifact_id": "loop-001-metrics",
                },
                "gate": {"operator": "eq", "threshold": 1},
            },
            {
                "id": "reproducibility",
                "label": "Reproducibility",
                "weight": 0.0,
                "direction": "maximize",
                "unit": "pass (1) / fail (0)",
                "comparable_across_tracks": True,
                "primary": False,
                "baseline": {
                    "value": 1,
                    "unit": "pass (1) / fail (0)",
                    "source_artifact_id": "loop-001-metrics",
                },
                "gate": {"operator": "eq", "threshold": 1},
            },
            {
                "id": "explainability",
                "label": "Explainability",
                "weight": 0.0,
                "direction": "maximize",
                "unit": "points (1-5)",
                "comparable_across_tracks": True,
                "primary": False,
                "baseline": {
                    "value": EXPLAINABILITY[0],
                    "unit": "points (1-5)",
                    "source_artifact_id": "loop-001-judge",
                },
            },
        ],
        "scorers": [
            {
                "id": "objective-route-scorer",
                "type": "objective_command",
                "criterion_ids": ["route-length"],
                "command": "python generated/optimizer.py --data generated/stops.json --strategy <strategy> --out <loop-dir>",
                "primary": True,
                "weight": 1.0,
            },
            {
                "id": "objective-gate-scorer",
                "type": "objective_command",
                "criterion_ids": ["validity", "reproducibility"],
                "command": "python generated/optimizer.py --data generated/stops.json --strategy <strategy> --out <loop-dir>",
                "primary": False,
                "weight": 1.0,
            },
            {
                "id": "independent-explanation-judge",
                "type": "llm_rubric",
                "criterion_ids": ["explainability"],
                "judge_panel": "explanation-panel",
                "primary": False,
                "weight": 0.0,
            },
        ],
        "judge_panels": [
            {
                "id": "explanation-panel",
                "blind": False,
                "flip_pairwise_order": False,
                "aggregation": "single_independent_judge",
                "judges": [
                    {
                        "id": "explanation-critic",
                        "model_id": "claude-sonnet-5",
                        "role": "Explain metrics and assess auditability without overriding objective evidence.",
                    }
                ],
            }
        ],
        "governance": {
            "objective_precedence": (
                "Validity and reproducibility are hard gates; among passing candidates, "
                "lower route length wins. Explainability cannot override either rule."
            )
        },
        "tracks": [
            {
                "id": "quantitative-route",
                "label": "Quantitative route optimization",
                "hypothesis": (
                    "Construction, local search, and deterministic multi-start can "
                    "monotonically reduce the fixed-input route while preserving hard gates."
                ),
                "final_decision": "Adopt Loop 004: exact oracle confirms global optimality.",
            }
        ],
        "iterations": iterations,
        "champion": {
            "iteration_id": "loop-004",
            "summary": (
                "The multi-start synthesis is valid, reproducible, 53.848927672 km "
                "shorter than baseline, and independently certified globally optimal."
            ),
            "reasons": [
                {
                    "text": "37.576644306 km is the shortest eligible route and a 53.848927672 km (66.13%) baseline reduction.",
                    "evidence_refs": ["route-length", "loop-004-metrics", "loop-004-map"],
                },
                {
                    "text": "The route passes the exact-once depot tour validity gate and the three-run reproducibility gate.",
                    "evidence_refs": ["validity", "reproducibility", "loop-004-metrics"],
                },
                {
                    "text": "Independent Held-Karp dynamic programming proves a zero optimality gap on the fixed input.",
                    "evidence_refs": ["exact-oracle-result", "exact-oracle-source"],
                },
                {
                    "text": "The independent claude-sonnet-5 judge rated the explanation 5/5 without overriding objective evidence.",
                    "evidence_refs": ["explainability", "loop-004-judge"],
                },
            ],
            "caveats": [
                {
                    "text": "Global optimality is certified only for this fixed 12-stop instance; heuristic performance does not generalize automatically.",
                    "evidence_refs": ["fixed-stop-data", "exact-oracle-result"],
                },
                {
                    "text": "Held-Karp has exponential scaling and is used here as a small-instance oracle, not as the production heuristic.",
                    "evidence_refs": ["exact-oracle-source", "loop-004-judge"],
                },
            ],
        },
        "story": {
            "milestones": [
                {"iteration_id": f"loop-{number:03d}", "caption": CAPTIONS[number - 1]}
                for number in range(1, 5)
            ],
            "featured_artifact_id": "loop-004-map",
            "primary_comparison_key": "route-map",
        },
        "rules": [
            "Never promote a candidate that fails validity or reproducibility.",
            "Rank eligible candidates by measured Euclidean route length, not judge preference.",
        ],
        "synthesis": (
            "Alphabetical baseline -> nearest-neighbor construction -> 2-opt local "
            "search -> deterministic multi-start. Every step shortened the route, "
            "and the final 37.576644306 km result matches the independent exact optimum."
        ),
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
