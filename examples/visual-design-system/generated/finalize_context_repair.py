#!/usr/bin/env python3
"""Promote synthesis-03 and preserve the rejected context-drift history."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.json"
AGGREGATE_PATH = ROOT / "judges" / "panel-aggregate.json"
AGGREGATE_REPORT_PATH = ROOT / "judges" / "panel-aggregate.md"
EXPECTED_TITLE = "Designing with Feedback Loops"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def digest(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def artifact(
    artifact_id: str,
    kind: str,
    role: str,
    label: str,
    path: str,
    mode: str,
    caption: str,
    *,
    featured: bool = False,
    primary: bool = False,
    alt_text: str | None = None,
    comparison_key: str | None = None,
    **extra: object,
) -> dict[str, object]:
    presentation: dict[str, object] = {
        "mode": mode,
        "featured": featured,
        "primary": primary,
        "caption": caption,
    }
    if alt_text is not None:
        presentation["alt_text"] = alt_text
    if comparison_key is not None:
        presentation["comparison_key"] = comparison_key
    return {
        "id": artifact_id,
        "kind": kind,
        "role": role,
        "label": label,
        "path": path,
        "sha256": digest(path),
        "presentation": presentation,
        **extra,
    }


def update_aggregate() -> None:
    aggregate = json.loads(AGGREGATE_PATH.read_text(encoding="utf-8"))
    aggregate["methodology"]["objective_policy"] = (
        "Independent gate consensus plus recorded metrics. Any svg_validity, "
        "layout_quality, or content_fidelity failure prevents Champion promotion. "
        "Blindness hides candidate identity/order, never the frozen acceptance contract."
    )
    repair_judges = [
        {
            "id": "sonnet-creative-director",
            "model_id": "claude-sonnet-5",
            "role": "creative-director",
        },
        {
            "id": "gpt55-design-systems-critic",
            "model_id": "gpt-5.5",
            "role": "design-systems-critic",
        },
        {
            "id": "opus-accessibility-critic",
            "model_id": "claude-opus-4.8",
            "role": "accessibility-critic",
        },
    ]
    existing_ids = {judge["id"] for judge in aggregate["judges"]}
    aggregate["judges"].extend(
        judge for judge in repair_judges if judge["id"] not in existing_ids
    )

    synthesis_02 = aggregate["loops"]["synthesis-02"]
    synthesis_02["objective_gate_verdict"]["content_fidelity"] = "fail"
    synthesis_02["champion_eligible"] = False
    synthesis_02["decision"] = "reject"
    synthesis_02["dissent"] = (
        "The original panel unanimously preferred the measured layout repair but had "
        "no canonical-content contract or content-fidelity veto. Later human review "
        "found that stress-test copy had replaced the primary headline, so the Loop "
        "is rejected without rewriting its original judge notes."
    )

    score_rows = [
        (
            "sonnet-creative-director",
            "claude-sonnet-5",
            "creative-director",
            {
                "visual_hierarchy": 4.4,
                "brand_distinctiveness": 4.3,
                "information_clarity": 4.5,
                "system_coherence": 4.6,
                "production_polish": 4.3,
            },
            "judges/repair/creative-director-synthesis-03.md",
        ),
        (
            "gpt55-design-systems-critic",
            "gpt-5.5",
            "design-systems-critic",
            {
                "visual_hierarchy": 4.4,
                "brand_distinctiveness": 4.1,
                "information_clarity": 4.5,
                "system_coherence": 4.6,
                "production_polish": 4.3,
            },
            "judges/repair/design-systems-synthesis-03.md",
        ),
        (
            "opus-accessibility-critic",
            "claude-opus-4.8",
            "accessibility-critic",
            {
                "visual_hierarchy": 4.5,
                "brand_distinctiveness": 4.3,
                "information_clarity": 4.5,
                "system_coherence": 4.6,
                "production_polish": 4.4,
            },
            "judges/repair/accessibility-synthesis-03.md",
        ),
    ]
    aggregate["loops"]["synthesis-03"] = {
        "judges": [
            {
                "judge_id": judge_id,
                "model_id": model_id,
                "role": role,
                "scores": scores,
                "objective_gates": {
                    "svg_validity": "pass",
                    "layout_quality": "pass",
                    "content_fidelity": "pass",
                },
                "note": note,
            }
            for judge_id, model_id, role, scores, note in score_rows
        ],
        "panel_median": {
            "visual_hierarchy": 4.4,
            "brand_distinctiveness": 4.3,
            "information_clarity": 4.5,
            "system_coherence": 4.6,
            "production_polish": 4.3,
        },
        "weighted_median_score": 4.417,
        "objective_gate_verdict": {
            "svg_validity": "pass",
            "layout_quality": "pass",
            "content_fidelity": "pass",
        },
        "champion_eligible": True,
        "decision": "new_best",
        "dissent": (
            "All judges pass the repair. They preserve a caveat that the visible title "
            "uses an all-caps typographic treatment while exact mixed-case copy is held "
            "in accessible metadata; localization, RTL, and system-font behavior remain "
            "untested."
        ),
    }
    aggregate["rankings"]["gate_aware_overall"] = [
        "synthesis-03",
        "editorial-02",
        "generative-02",
        "synthesis-01",
        "editorial-01",
        "generative-01",
        "synthesis-02",
    ]
    aggregate["rankings"]["repair_panel"] = {
        "sonnet": ["synthesis-03"],
        "gpt55": ["synthesis-03"],
        "opus": ["synthesis-03"],
    }
    aggregate["synthesis_caveats"] = [
        "Synthesis-02 preserves useful layout evidence but is rejected for primary-content drift that its original judging contract could not detect.",
        "Synthesis-03 restores canonical copy and visibly separates stress content while retaining the width-aware repair.",
        "Exact glyph widths still vary with system fonts; localization, non-Latin scripts, and RTL ordering remain untested.",
    ]
    aggregate["champion"] = "synthesis-03"
    write_json(AGGREGATE_PATH, aggregate)

    AGGREGATE_REPORT_PATH.write_text(
        """# Loop Lab independent panel aggregate

The original three-judge panel correctly assessed visual and layout quality but
shared an incomplete acceptance contract: no canonical headline and no
content-fidelity veto. Human review therefore rejected `synthesis-02` without
rewriting its historical judge notes. A new three-role panel judged the
context-preserving repair against a frozen brief.

| Loop | Hierarchy ×2 | Brand | Clarity | Coherence | Polish | Weighted median | SVG | Layout | Content | Decision |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| editorial-01 | 4 | 4 | 3 | 4 | 3 | 3.667 | pass | fail | n/a | reject |
| editorial-02 | 5 | 4 | 5 | 5 | 5 | 4.833 | pass | pass | n/a | keep_for_synthesis |
| generative-01 | 2 | 4 | 2 | 2 | 2 | 2.333 | pass | fail | n/a | reject |
| generative-02 | 4 | 5 | 4 | 3 | 4 | 4.000 | pass | pass | n/a | keep_for_synthesis |
| synthesis-01 | 4 | 5 | 4 | 3 | 3 | 3.833 | pass | fail | n/a | reject |
| synthesis-02 | 5 | 5 | 5 | 5 | 4 | 4.833 | pass | pass | **fail** | **reject** |
| synthesis-03 | 4.4 | 4.3 | 4.5 | 4.6 | 4.3 | 4.417 | pass | pass | **pass** | **new_best** |

## Why the original panel missed the drift

All three judges saw the same generator-authored Prompt chain, layout metrics,
and required-content declaration, but no frozen canonical-content source.
Blindness kept their opinions independent; it did not make the acceptance
contract independent. They therefore rewarded the changed title as successful
stress evidence. `context-drift-postmortem.md` records the full causal chain.

## Repair-panel verdict

Claude Sonnet 5 (creative-director), GPT-5.5 (design-systems-critic), and Claude
Opus 4.8 (accessibility-critic) independently pass SVG validity, layout quality,
and content fidelity for `synthesis-03`.

## Preserved dissent

The visible title uses an all-caps editorial treatment while exact mixed-case
copy remains in accessible SVG metadata. Localization, RTL, and system-font
behavior remain untested.

## Champion

**synthesis-03.** It restores **Designing with Feedback Loops**, confines the
long replacement title to a visibly labelled stress fixture, and preserves the
measured width-aware layout repair from `synthesis-02`.
""",
        encoding="utf-8",
        newline="\n",
    )


def update_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    problem = manifest["problem"]
    problem["constraints"] = [
        (
            "Use exactly three tracks with at least two loops each and preserve the "
            "specified model and multi-parent lineage; audited repair loops may extend "
            "a track after human review."
            if constraint.startswith("Use exactly three tracks with two loops each")
            else constraint
        )
        for constraint in problem["constraints"]
    ]
    invariant_constraint = (
        "The primary Champion headline is exactly 'Designing with Feedback Loops'; "
        "stress-test copy must remain visibly labelled secondary evidence."
    )
    if invariant_constraint not in problem["constraints"]:
        problem["constraints"].append(invariant_constraint)
    success = (
        "The Champion passes an external content-fidelity gate against the frozen "
        "canonical brief."
    )
    if success not in problem["success_criteria"]:
        problem["success_criteria"].append(success)

    if not any(item["id"] == "content_fidelity" for item in manifest["scorecard"]):
        manifest["scorecard"].append(
            {
                "id": "content_fidelity",
                "label": "Canonical content fidelity — objective gate (1 pass / 0 fail)",
                "weight": 1,
                "direction": "maximize",
                "unit": "binary: 1=pass, 0=fail",
                "comparable_across_tracks": False,
                "primary": False,
                "gate": {"operator": "gte", "threshold": 1},
            }
        )
    objective = next(
        scorer for scorer in manifest["scorers"] if scorer["id"] == "objective-command"
    )
    if "content_fidelity" not in objective["criterion_ids"]:
        objective["criterion_ids"].append("content_fidelity")

    repair_scorer_id = "context-repair-panel"
    if not any(scorer["id"] == repair_scorer_id for scorer in manifest["scorers"]):
        manifest["scorers"].append(
            {
                "id": repair_scorer_id,
                "type": "llm_rubric",
                "criterion_ids": [
                    "visual_hierarchy",
                    "brand_distinctiveness",
                    "information_clarity",
                    "system_coherence",
                    "production_polish",
                ],
                "judge_panel": "context-repair-panel",
                "primary": False,
                "weight": 1,
            }
        )
    if not any(
        panel["id"] == "context-repair-panel" for panel in manifest["judge_panels"]
    ):
        manifest["judge_panels"].append(
            {
                "id": "context-repair-panel",
                "blind": True,
                "independent": True,
                "flip_pairwise_order": False,
                "aggregation": "criterion_median_then_weighted_mean_with_dissent",
                "dissent_preserved": True,
                "frozen_acceptance_contract": {
                    "primary_headline": EXPECTED_TITLE,
                    "stress_fixture_policy": "secondary and visibly labelled",
                    "content_mismatch": "blocking veto",
                },
                "judges": [
                    {
                        "id": "sonnet-creative-director",
                        "model_id": "claude-sonnet-5",
                        "role": "creative-director",
                        "weight": 1,
                    },
                    {
                        "id": "gpt55-design-systems-critic",
                        "model_id": "gpt-5.5",
                        "role": "design-systems-critic",
                        "weight": 1,
                    },
                    {
                        "id": "opus-accessibility-critic",
                        "model_id": "claude-opus-4.8",
                        "role": "accessibility-critic",
                        "weight": 1,
                    },
                ],
                "calculation": (
                    "Take the median of the three independent criterion scores, then "
                    "apply scorecard weights. Any failed objective gate vetoes promotion."
                ),
            }
        )

    synthesis_02 = next(
        item for item in manifest["iterations"] if item["id"] == "synthesis-02"
    )
    synthesis_02["quality_gates"]["content_fidelity"] = "fail"
    if not any(
        score["criterion_id"] == "content_fidelity"
        for score in synthesis_02["scores"]
    ):
        synthesis_02["scores"].append(
            {
                "scorer_id": "objective-command",
                "criterion_id": "content_fidelity",
                "value": 0,
                "notes": (
                    "Later human review found that stress-test copy replaced the "
                    "primary headline. The original panel had no canonical-content gate."
                ),
            }
        )
    later_review = (
        "Later human review rejected primary-content drift: the stress-test title "
        "had replaced the intended headline."
    )
    if later_review not in synthesis_02["outcome"]:
        synthesis_02["outcome"] += f" {later_review}"
    synthesis_02["decision"] = "reject"
    synthesis_02["stop_reason"] = (
        "Rejected after human review: content_fidelity failed even though the original "
        "SVG and layout gates passed."
    )
    synthesis_02["artifacts"] = [
        item
        for item in synthesis_02["artifacts"]
        if item["role"] != "panel-aggregate"
    ]

    loop = ROOT / "track-synthesis" / "loop-03"
    if not loop.is_dir():
        raise RuntimeError("repair_context_drift.py must create loop-03 first")
    loop_03_artifacts = [
        artifact(
            "synthesis-03-card",
            "svg",
            "primary-output",
            "Synthesis 03 context-preserving Champion card",
            "track-synthesis/loop-03/card.svg",
            "svg",
            "Canonical headline restored without losing the measured width-aware layout repair.",
            featured=True,
            primary=True,
            alt_text=(
                "Cream Loop Lab card for Designing with Feedback Loops. A large "
                "two-line navy serif title and event details sit left; a dark paired-loop "
                "routing diagram sits right; a dark blue Register Now button sits below."
            ),
            comparison_key="event-card",
            required_content={
                "title": EXPECTED_TITLE,
                "date": "NOV 19, 2026",
                "time": "13:00–16:30",
                "venue": "INNOVATION HUB + ONLINE",
                "cta": "REGISTER NOW →",
            },
        ),
        artifact(
            "synthesis-03-tokens",
            "json",
            "design-tokens",
            "synthesis-03 design tokens",
            "track-synthesis/loop-03/tokens.json",
            "structured_json",
            "Design tokens with an explicit immutable canonical-event contract.",
        ),
        artifact(
            "synthesis-03-metrics",
            "json",
            "layout-metrics",
            "synthesis-03 objective layout metrics",
            "track-synthesis/loop-03/layout-metrics.json",
            "metric_set",
            "Rendered geometry, contrast, clipping, and context-fidelity evidence.",
        ),
        artifact(
            "synthesis-03-content-fidelity",
            "json",
            "context-fidelity",
            "synthesis-03 canonical-content gate",
            "track-synthesis/loop-03/context-fidelity.json",
            "key_value",
            "External expected-versus-actual primary-copy gate.",
        ),
        artifact(
            "synthesis-03-prompt-chain",
            "json",
            "prompt-chain",
            "synthesis-03 prompt chain",
            "track-synthesis/loop-03/prompt-chain.json",
            "structured_json",
            "Repair Prompt, human feedback, objective result, and prevention rule.",
        ),
        artifact(
            "synthesis-03-notes",
            "markdown",
            "synthesis-notes",
            "synthesis-03 synthesis notes",
            "track-synthesis/loop-03/synthesis-notes.md",
            "markdown",
            "Context-preserving repair decisions and prevention lesson.",
        ),
        artifact(
            "synthesis-03-variants",
            "svg",
            "variant-system-sheet",
            "synthesis-03 variant and stress-fixture sheet",
            "track-synthesis/loop-03/variants.svg",
            "svg",
            "Three compact variants; alternate long-title content is visibly marked as a stress fixture.",
            featured=True,
            primary=False,
            alt_text=(
                "Three compact Loop Lab cards. The first is visibly labelled Stress "
                "Fixture and uses the long alternate title; two event variants follow."
            ),
            comparison_key="variant-system",
        ),
        artifact(
            "synthesis-03-card-preview",
            "image",
            "render-evidence",
            "synthesis-03 rendered primary card",
            "track-synthesis/loop-03/card-preview.png",
            "image",
            "Inkscape 1200×630 render inspected by the repair panel.",
            dimensions={"width": 1200, "height": 630},
        ),
        artifact(
            "synthesis-03-variants-preview",
            "image",
            "render-evidence",
            "synthesis-03 rendered variant sheet",
            "track-synthesis/loop-03/variants-preview.png",
            "image",
            "Inkscape 1200×630 render proving visible stress-fixture separation.",
            dimensions={"width": 1200, "height": 630},
        ),
        artifact(
            "synthesis-03-judge-creative",
            "markdown",
            "independent-judge-note",
            "Claude Sonnet 5 creative-director note",
            "judges/repair/creative-director-synthesis-03.md",
            "markdown",
            "Independent creative-direction scores, gates, and dissent.",
        ),
        artifact(
            "synthesis-03-judge-systems",
            "markdown",
            "independent-judge-note",
            "GPT-5.5 design-systems note",
            "judges/repair/design-systems-synthesis-03.md",
            "markdown",
            "Independent design-system scores, gates, and dissent.",
        ),
        artifact(
            "synthesis-03-judge-accessibility",
            "markdown",
            "independent-judge-note",
            "Claude Opus 4.8 accessibility note",
            "judges/repair/accessibility-synthesis-03.md",
            "markdown",
            "Independent accessibility scores, gates, and dissent.",
        ),
        artifact(
            "synthesis-03-human-review",
            "markdown",
            "human-review",
            "Human context-drift review",
            "judges/repair/human-context-review.md",
            "markdown",
            "Human rejection of synthesis-02 and required repair scope.",
        ),
        artifact(
            "context-drift-postmortem",
            "markdown",
            "postmortem",
            "Context-drift causal analysis",
            "context-drift-postmortem.md",
            "markdown",
            "Why synthesis drifted and why three independent judges missed it.",
        ),
        artifact(
            "panel-aggregate-json",
            "json",
            "panel-aggregate",
            "Independent panel aggregate data",
            "judges/panel-aggregate.json",
            "structured_json",
            "Historical panel results plus the content-aware repair-panel verdict.",
        ),
        artifact(
            "panel-aggregate-md",
            "markdown",
            "panel-aggregate",
            "Independent panel aggregate report",
            "judges/panel-aggregate.md",
            "markdown",
            "Readable gate-aware ranking, judge-miss analysis, and revised Champion.",
        ),
    ]

    scores = {
        "visual_hierarchy": 4.4,
        "brand_distinctiveness": 4.3,
        "information_clarity": 4.5,
        "system_coherence": 4.6,
        "production_polish": 4.3,
    }
    panel_notes = (
        "Criterion median from Claude Sonnet 5, GPT-5.5, and Claude Opus 4.8. "
        "All judges passed content fidelity and preserved case-transform, "
        "localization/RTL, and system-font caveats."
    )
    loop_03 = {
        "id": "synthesis-03",
        "track_id": "track-synthesis",
        "parent_ids": ["synthesis-02"],
        "model_id": "gpt-5.6-sol",
        "hypothesis": (
            "Restoring the canonical primary headline while retaining synthesis-02's "
            "width-aware layout, and visibly separating stress content, will repair "
            "context drift without regressing visual or layout quality."
        ),
        "outcome": (
            "Restored 'Designing with Feedback Loops' in the primary card, retained "
            "the measured metadata and routing-module repairs, visibly labelled the "
            "alternate long title as a stress fixture, and added an external "
            "content-fidelity gate. Three independent judges pass all gates."
        ),
        "commands": {
            "build": "python repair_context_drift.py",
            "run": (
                "Render both SVGs with Inkscape; query title geometry; compare "
                "context-fidelity.json expected and actual primary content."
            ),
            "judge": "Independent context-repair-panel with a blocking content_fidelity veto.",
        },
        "artifacts": loop_03_artifacts,
        "scores": [
            {
                "scorer_id": repair_scorer_id,
                "criterion_id": criterion,
                "value": value,
                "notes": panel_notes,
            }
            for criterion, value in scores.items()
        ]
        + [
            {
                "scorer_id": "objective-command",
                "criterion_id": criterion,
                "value": 1,
                "notes": notes,
            }
            for criterion, notes in (
                ("svg_validity", "Both standalone SVGs parse and contain accessible metadata."),
                ("layout_quality", "Rendered bounds, contrast, clipping, and safe-zone checks pass."),
                (
                    "content_fidelity",
                    "Expected and actual primary headline match; alternate copy is a visibly labelled secondary stress fixture.",
                ),
            )
        ],
        "prompt": json.loads(
            (loop / "prompt-chain.json").read_text(encoding="utf-8")
        )
        | {},
        "quality_gates": {
            "svg_validity": "pass",
            "layout_quality": "pass",
            "content_fidelity": "pass",
        },
        "changed_files": [
            "track-synthesis/loop-03/card.svg",
            "track-synthesis/loop-03/variants.svg",
            "track-synthesis/loop-03/tokens.json",
            "track-synthesis/loop-03/layout-metrics.json",
            "track-synthesis/loop-03/context-fidelity.json",
            "track-synthesis/loop-03/prompt-chain.json",
            "track-synthesis/loop-03/synthesis-notes.md",
            "track-synthesis/loop-03/card-preview.png",
            "track-synthesis/loop-03/variants-preview.png",
        ],
        "lesson": {
            "trigger": (
                "Human review found that a stress-test Prompt had changed primary copy "
                "and that three judges promoted it."
            ),
            "action": (
                "Freeze canonical content outside the candidate, inject it into every "
                "repair and judge Prompt, visibly separate stress fixtures, and make "
                "content fidelity a blocking objective gate."
            ),
            "evidence": (
                "synthesis-02 lacks the canonical title but was previously new_best; "
                "synthesis-03 context-fidelity.json passes and all three repair judges "
                "confirm the visible separation."
            ),
            "confidence": "high",
        },
        "decision": "new_best",
        "stop_reason": (
            "All three objective gates pass and the independent repair panel selects "
            "synthesis-03 as Champion."
        ),
    }
    loop_03["prompt"].pop("iteration", None)
    loop_03["prompt"].pop("model_id", None)
    iterations = [
        item for item in manifest["iterations"] if item["id"] != "synthesis-03"
    ]
    iterations.append(loop_03)
    manifest["iterations"] = iterations

    for track in manifest["tracks"]:
        if track["id"] == "track-synthesis":
            track["final_decision"] = (
                "synthesis-03 selected after restoring canonical content and passing "
                "the new content-fidelity gate"
            )
    milestones = [
        item
        for item in manifest["story"]["milestones"]
        if item["iteration_id"] != "synthesis-03"
    ]
    for item in milestones:
        if item["iteration_id"] == "synthesis-02":
            item["caption"] = (
                "Repaired the measured overset but was later rejected because stress "
                "copy had replaced the primary headline."
            )
    milestones.append(
        {
            "iteration_id": "synthesis-03",
            "caption": (
                "Restored canonical content, visibly separated the stress fixture, "
                "added a blocking fidelity gate, and became Champion."
            ),
        }
    )
    manifest["story"]["milestones"] = milestones
    manifest["story"]["featured_artifact_id"] = "synthesis-03-card"
    manifest["champion"] = {
        "iteration_id": "synthesis-03",
        "summary": (
            "Synthesis-03 is the context-preserving Champion: it restores the canonical "
            "headline, visibly separates stress content, retains the measured layout "
            "repair, and passes SVG, layout, and content-fidelity gates."
        ),
        "reasons": [
            {
                "text": "The primary Artifact again uses 'Designing with Feedback Loops'.",
                "evidence_refs": [
                    "content_fidelity",
                    "synthesis-03-card",
                    "synthesis-03-content-fidelity",
                ],
            },
            {
                "text": "Long-title capacity evidence remains available only as a visibly labelled stress fixture.",
                "evidence_refs": [
                    "content_fidelity",
                    "synthesis-03-variants",
                    "synthesis-03-variants-preview",
                ],
            },
            {
                "text": "The width-aware metadata and routing-module layout repair remains intact.",
                "evidence_refs": [
                    "layout_quality",
                    "synthesis-03-metrics",
                    "synthesis-03-card-preview",
                ],
            },
            {
                "text": "Three independent repair judges pass every objective gate.",
                "evidence_refs": [
                    "panel-aggregate-json",
                    "synthesis-03-judge-creative",
                    "synthesis-03-judge-systems",
                    "synthesis-03-judge-accessibility",
                ],
            },
        ],
        "caveats": [
            {
                "text": "Visible all-caps display treatment is accepted while exact mixed-case copy remains in accessible metadata.",
                "evidence_refs": [
                    "synthesis-03-judge-creative",
                    "synthesis-03-judge-accessibility",
                ],
            },
            {
                "text": "Localization, non-Latin scripts, RTL ordering, and cross-environment font substitution remain untested.",
                "evidence_refs": [
                    "production_polish",
                    "synthesis-03-judge-systems",
                    "synthesis-03-judge-accessibility",
                ],
            },
        ],
    }
    new_rule = (
        "Freeze primary-content invariants outside candidate artifacts; stress fixtures "
        "must remain visibly labelled secondary evidence and invariant failures block promotion."
    )
    if new_rule not in manifest["rules"]:
        manifest["rules"].append(new_rule)
    manifest["synthesis"] = (
        "Editorial-02 contributed hierarchy and accessibility discipline; generative-02 "
        "contributed the routing language. Synthesis-01 combined them but exposed a "
        "venue overset. Synthesis-02 repaired the layout yet promoted stress-test copy "
        "into the primary card because no content invariant existed. Human review caught "
        "the drift. Synthesis-03 preserves the useful repair, restores canonical copy, "
        "visibly labels the stress fixture, and passes a new external fidelity gate."
    )
    write_json(MANIFEST_PATH, manifest)


def main() -> int:
    update_aggregate()
    update_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
