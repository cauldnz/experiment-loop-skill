from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import build_viewer  # noqa: E402  (local module, single source of truth for viewer.html)


VARIANTS = [
    {
        "id": "loop-01-editorial-poster",
        "title": "Editorial poster baseline",
        "track": "editorial-run",
        "experiment_run": "run-a-editorial-clarity",
        "source_runs": ["run-a-editorial-clarity"],
        "parent_id": None,
        "parent_ids": [],
        "hypothesis": "Run A starts with bold editorial typography to make the event promise instantly clear.",
        "next": "Add reusable modules for agenda, proof points, and call to action.",
        "palette": {"bg": "#0f172a", "bg2": "#172554", "panel": "#f8fafc", "text": "#f8fafc", "ink": "#0f172a", "muted": "#94a3b8", "accent": "#f59e0b", "accent2": "#38bdf8"},
        "layout": "editorial",
        "scores": {"visual_hierarchy": 4.4, "brand_distinctiveness": 3.6, "information_clarity": 3.9, "system_coherence": 3.6, "polish": 3.8, "layout_quality": 3.9},
    },
    {
        "id": "loop-02-editorial-system",
        "title": "Editorial component system",
        "track": "editorial-run",
        "experiment_run": "run-a-editorial-clarity",
        "source_runs": ["run-a-editorial-clarity"],
        "parent_id": "loop-01-editorial-poster",
        "parent_ids": ["loop-01-editorial-poster"],
        "hypothesis": "Run A improves by turning the poster into reusable information modules without losing typographic hierarchy.",
        "next": "Borrow a stronger visual motif from the independent visual-language run.",
        "palette": {"bg": "#111827", "bg2": "#1e293b", "panel": "#f8fafc", "text": "#f8fafc", "ink": "#111827", "muted": "#cbd5e1", "accent": "#f97316", "accent2": "#22d3ee"},
        "layout": "editorial-system",
        "scores": {"visual_hierarchy": 4.7, "brand_distinctiveness": 3.9, "information_clarity": 4.6, "system_coherence": 4.2, "polish": 4.1, "layout_quality": 4.3},
    },
    {
        "id": "loop-01-orbital-identity",
        "title": "Orbital identity study",
        "track": "visual-language-run",
        "experiment_run": "run-b-visual-language",
        "source_runs": ["run-b-visual-language"],
        "parent_id": None,
        "parent_ids": [],
        "hypothesis": "Run B starts with an energetic orbital motif to create a memorable identity, even if information hierarchy is weaker.",
        "next": "Turn the energy into a more structured ribbon system so details are easier to read.",
        "palette": {"bg": "#120a2a", "bg2": "#312e81", "panel": "#faf5ff", "text": "#f5f3ff", "ink": "#1e1b4b", "muted": "#c4b5fd", "accent": "#a78bfa", "accent2": "#34d399"},
        "layout": "orbital",
        "scores": {"visual_hierarchy": 3.5, "brand_distinctiveness": 4.8, "information_clarity": 3.3, "system_coherence": 3.8, "polish": 4.0, "layout_quality": 3.7},
    },
    {
        "id": "loop-02-signal-ribbon-system",
        "title": "Signal ribbon system",
        "track": "visual-language-run",
        "experiment_run": "run-b-visual-language",
        "source_runs": ["run-b-visual-language"],
        "parent_id": "loop-01-orbital-identity",
        "parent_ids": ["loop-01-orbital-identity"],
        "hypothesis": "Run B improves by organizing the orbital energy into reusable signal ribbons and better detail blocks.",
        "next": "Synthesize the ribbon motif with Run A's stronger editorial hierarchy.",
        "palette": {"bg": "#082f49", "bg2": "#164e63", "panel": "#ecfeff", "text": "#ecfeff", "ink": "#083344", "muted": "#a5f3fc", "accent": "#06b6d4", "accent2": "#facc15"},
        "layout": "ribbon",
        "scores": {"visual_hierarchy": 4.0, "brand_distinctiveness": 4.7, "information_clarity": 4.0, "system_coherence": 4.4, "polish": 4.2, "layout_quality": 4.2},
    },
    {
        "id": "loop-03-cross-run-synthesis",
        "title": "Editorial plus signal synthesis",
        "track": "synthesis",
        "experiment_run": "run-c-cross-run-synthesis",
        "source_runs": ["run-a-editorial-clarity", "run-b-visual-language"],
        "parent_id": "loop-02-editorial-system",
        "parent_ids": ["loop-02-editorial-system", "loop-02-signal-ribbon-system"],
        "hypothesis": "The synthesis experiment combines Run A's hierarchy with Run B's signal ribbons to get both clarity and distinctiveness.",
        "next": "Polish spacing, contrast, component rhythm, and CTA treatment.",
        "palette": {"bg": "#111827", "bg2": "#0f766e", "panel": "#f8fafc", "text": "#f8fafc", "ink": "#0f172a", "muted": "#ccfbf1", "accent": "#2dd4bf", "accent2": "#f59e0b"},
        "layout": "synthesis",
        "scores": {"visual_hierarchy": 4.6, "brand_distinctiveness": 4.6, "information_clarity": 4.5, "system_coherence": 4.6, "polish": 4.4, "layout_quality": 4.2},
    },
    {
        "id": "loop-04-production-polish",
        "title": "Production polished system",
        "track": "synthesis",
        "experiment_run": "run-c-cross-run-synthesis",
        "source_runs": ["run-a-editorial-clarity", "run-b-visual-language", "run-c-cross-run-synthesis"],
        "parent_id": "loop-03-cross-run-synthesis",
        "parent_ids": ["loop-03-cross-run-synthesis", "loop-02-editorial-system", "loop-02-signal-ribbon-system"],
        "hypothesis": "A final synthesis loop can make the hybrid feel production-ready while preserving the source-run strengths.",
        "next": "Reject as champion: the process chips collide with body copy, so add an explicit layout-quality gate and reposition the system chips.",
        "palette": {"bg": "#0b1020", "bg2": "#134e4a", "panel": "#fff7ed", "text": "#fff7ed", "ink": "#111827", "muted": "#99f6e4", "accent": "#14b8a6", "accent2": "#f97316"},
        "layout": "polished-collision",
        "scores": {"visual_hierarchy": 4.2, "brand_distinctiveness": 4.8, "information_clarity": 3.6, "system_coherence": 4.4, "polish": 3.4, "layout_quality": 2.2},
    },
    {
        "id": "loop-05-layout-quality-fix",
        "title": "Layout-quality repaired system",
        "track": "synthesis",
        "experiment_run": "run-c-cross-run-synthesis",
        "source_runs": ["run-a-editorial-clarity", "run-b-visual-language", "run-c-cross-run-synthesis"],
        "parent_id": "loop-04-production-polish",
        "parent_ids": ["loop-04-production-polish", "loop-03-cross-run-synthesis"],
        "hypothesis": "A visual-quality gate should reject element collisions, then a repaired layout can keep the synthesis strengths without overlapping content.",
        "next": "Stop: the final card keeps the signal motif, moves process chips into clear whitespace, and passes the layout-quality gate.",
        "palette": {"bg": "#0b1020", "bg2": "#134e4a", "panel": "#fff7ed", "text": "#fff7ed", "ink": "#111827", "muted": "#99f6e4", "accent": "#14b8a6", "accent2": "#f97316"},
        "layout": "polished-safe",
        "scores": {"visual_hierarchy": 4.8, "brand_distinctiveness": 4.7, "information_clarity": 4.9, "system_coherence": 4.8, "polish": 4.8, "layout_quality": 4.9},
    },
]

WEIGHTS = {
    "visual_hierarchy": 1.4,
    "brand_distinctiveness": 1.1,
    "information_clarity": 1.2,
    "system_coherence": 1.0,
    "polish": 1.3,
    "layout_quality": 1.5,
}


def weighted_score(scores: dict[str, float]) -> float:
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS) / sum(WEIGHTS.values()), 2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def layout_settings(variant: dict[str, object]) -> dict[str, object]:
    layout = str(variant["layout"])
    show_orbits = layout in {"orbital", "synthesis", "polished-collision", "polished-safe"}
    show_ribbons = layout in {"ribbon", "synthesis", "polished-collision", "polished-safe"}
    show_modules = layout in {"editorial-system", "ribbon", "synthesis", "polished-collision", "polished-safe"}
    dense_polish = layout in {"polished-collision", "polished-safe"}
    title_size = 82 if layout in {"editorial", "editorial-system"} else 70
    hero_y = 178 if show_modules else 206
    panel_x = 596 if show_modules else 614
    panel_w = 270 if show_modules else 240
    modules = [("01", "Frame goal"), ("02", "Run variants"), ("03", "Synthesize")]
    if not show_modules:
        module_positions = []
    elif layout == "polished-collision":
        module_positions = [(372, 326, 178), (372, 370, 178), (372, 414, 178)]
    else:
        module_y = 395 if dense_polish else 402
        module_positions = [(88 + index * 148, module_y, 136) for index in range(len(modules))]
    return {
        "layout": layout,
        "show_orbits": show_orbits,
        "show_ribbons": show_ribbons,
        "show_modules": show_modules,
        "dense_polish": dense_polish,
        "title_size": title_size,
        "hero_y": hero_y,
        "panel_x": panel_x,
        "panel_w": panel_w,
        "modules": modules,
        "module_positions": module_positions,
    }


def overlaps(a: dict[str, float], b: dict[str, float], padding: float = 8) -> bool:
    return not (
        a["x"] + a["w"] + padding <= b["x"]
        or b["x"] + b["w"] + padding <= a["x"]
        or a["y"] + a["h"] + padding <= b["y"]
        or b["y"] + b["h"] + padding <= a["y"]
    )


def layout_quality_metrics(variant: dict[str, object]) -> dict[str, object]:
    settings = layout_settings(variant)
    hero_y = float(settings["hero_y"])
    panel_x = float(settings["panel_x"])
    panel_w = float(settings["panel_w"])
    boxes = [
        {"id": "body-copy", "x": 88.0, "y": hero_y + 120, "w": 470.0, "h": 66.0},
        {"id": "detail-panel", "x": panel_x, "y": 250.0, "w": panel_w, "h": 178.0},
        {"id": "variant-caption", "x": 86.0, "y": 442.0, "w": 360.0, "h": 24.0},
    ]
    for index, (x, y, width) in enumerate(settings["module_positions"]):
        boxes.append({"id": f"process-chip-{index + 1}", "x": float(x), "y": float(y), "w": float(width), "h": 32.0})

    collisions = []
    for index, first in enumerate(boxes):
        for second in boxes[index + 1 :]:
            if overlaps(first, second):
                collisions.append({"a": first["id"], "b": second["id"]})

    return {
        "passes_layout_gate": not collisions,
        "score": 5.0 if not collisions else max(1.0, round(3.0 - 0.6 * (len(collisions) - 1), 2)),
        "checked_boxes": boxes,
        "collisions": collisions,
    }


def write_layout_metrics(variant: dict[str, object], path: Path) -> dict[str, object]:
    metrics = layout_quality_metrics(variant)
    write_text_lf(path, json.dumps(metrics, indent=2))
    return metrics


def prompt_feedback(variant: dict[str, object], decision: str, layout_metrics: dict[str, object]) -> dict[str, str]:
    collisions = ", ".join(f"{item['a']} over {item['b']}" for item in layout_metrics["collisions"]) or "none"
    parent_text = ", ".join(variant["parent_ids"]) if variant["parent_ids"] else "none - first loop in this run"
    return {
        "track_prompt": (
            f"Create the next SVG event-card candidate for {variant['experiment_run']}. "
            f"Optimize the scorecard while preserving this track's hypothesis: {variant['hypothesis']}"
        ),
        "input_feedback": (
            f"Parent evidence: {parent_text}. Use prior judge notes and artifacts as constraints; "
            f"do not overwrite another track's visual direction."
        ),
        "judge_feedback": (
            f"Decision: {decision}. Layout gate: {'pass' if layout_metrics['passes_layout_gate'] else 'fail'}; "
            f"collisions: {collisions}. Next recommendation: {variant['next']}"
        ),
        "next_prompt": variant["next"],
    }


def write_card_svg(variant: dict[str, object], path: Path) -> None:
    p = variant["palette"]
    settings = layout_settings(variant)
    layout = settings["layout"]
    title = variant["title"]
    show_orbits = bool(settings["show_orbits"])
    show_ribbons = bool(settings["show_ribbons"])
    show_modules = bool(settings["show_modules"])
    dense_polish = bool(settings["dense_polish"])
    orbital_opacity = "0.55" if layout == "orbital" else "0.28"
    ribbon_opacity = "0.9" if layout in {"ribbon", "polished-collision", "polished-safe"} else "0.55"
    title_size = int(settings["title_size"])
    hero_y = int(settings["hero_y"])

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p["bg"]}"/><stop offset="100%" stop-color="{p["bg2"]}"/></linearGradient>',
        f'<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{p["accent"]}"/><stop offset="100%" stop-color="{p["accent2"]}"/></linearGradient>',
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#020617" flood-opacity="0.22"/></filter>',
        "</defs>",
        '<rect width="960" height="540" rx="34" fill="url(#bg)"/>',
        f'<circle cx="816" cy="82" r="190" fill="{p["accent"]}" opacity="0.08"/>',
        f'<circle cx="116" cy="474" r="160" fill="{p["accent2"]}" opacity="0.10"/>',
    ]
    if show_orbits:
        parts.extend(
            [
                f'<ellipse cx="700" cy="172" rx="210" ry="58" fill="none" stroke="{p["accent2"]}" stroke-width="3" opacity="{orbital_opacity}" transform="rotate(-18 700 172)"/>',
                f'<ellipse cx="700" cy="172" rx="138" ry="38" fill="none" stroke="{p["accent"]}" stroke-width="8" opacity="{orbital_opacity}" transform="rotate(22 700 172)"/>',
                f'<circle cx="814" cy="124" r="12" fill="{p["accent2"]}"/>',
                f'<circle cx="604" cy="214" r="8" fill="{p["accent"]}"/>',
            ]
        )
    if show_ribbons:
        parts.extend(
            [
                f'<path d="M520 392 C610 328 730 350 880 272" fill="none" stroke="{p["accent"]}" stroke-width="34" stroke-linecap="round" opacity="{ribbon_opacity}"/>',
                f'<path d="M500 430 C630 392 760 430 912 352" fill="none" stroke="{p["accent2"]}" stroke-width="12" stroke-linecap="round" opacity="0.92"/>',
            ]
        )

    parts.extend(
        [
            '<rect x="54" y="54" width="852" height="432" rx="28" fill="#ffffff" opacity="0.07" stroke="#ffffff" stroke-opacity="0.18"/>',
            f'<text x="86" y="104" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" letter-spacing="4" fill="{p["muted"]}">LOOP LAB</text>',
            f'<text x="86" y="{hero_y}" font-family="Segoe UI, Arial, sans-serif" font-size="{title_size}" font-weight="800" letter-spacing="-4" fill="{p["text"]}">Design</text>',
            f'<text x="86" y="{hero_y + 74}" font-family="Segoe UI, Arial, sans-serif" font-size="{title_size}" font-weight="800" letter-spacing="-4" fill="{p["text"]}">Systems</text>',
            f'<rect x="88" y="{hero_y + 98}" width="238" height="8" rx="4" fill="url(#accent)"/>',
            f'<text x="88" y="{hero_y + 142}" font-family="Segoe UI, Arial, sans-serif" font-size="25" font-weight="650" fill="{p["text"]}">Build. Judge. Improve.</text>',
            f'<text x="88" y="{hero_y + 176}" font-family="Segoe UI, Arial, sans-serif" font-size="17" fill="{p["muted"]}">A hands-on workshop for experiment-driven product teams.</text>',
        ]
    )

    panel_x = int(settings["panel_x"])
    panel_w = int(settings["panel_w"])
    parts.extend(
        [
            f'<g filter="url(#softShadow)"><rect x="{panel_x}" y="250" width="{panel_w}" height="178" rx="22" fill="{p["panel"]}"/></g>',
            f'<text x="{panel_x + 26}" y="292" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="800" fill="{p["ink"]}">Workshop Sprint</text>',
            f'<text x="{panel_x + 26}" y="324" font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="{p["ink"]}" opacity="0.76">Tue 14 Jul / 10:00</text>',
            f'<text x="{panel_x + 26}" y="352" font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="{p["ink"]}" opacity="0.76">Studio 3 + remote</text>',
            f'<rect x="{panel_x + 26}" y="378" width="112" height="34" rx="17" fill="{p["accent"]}"/>',
            f'<text x="{panel_x + 48}" y="400" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="800" fill="{p["ink"]}">JOIN RUN</text>',
        ]
    )

    if show_modules:
        modules = settings["modules"]
        module_positions = settings["module_positions"]
        for index, (num, label) in enumerate(modules):
            x, y, width = module_positions[index]
            parts.extend(
                [
                    f'<rect x="{x}" y="{y}" width="{width}" height="32" rx="16" fill="#ffffff" opacity="{0.18 if dense_polish else 0.12}"/>',
                    f'<text x="{x + 16}" y="{y + 22}" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="800" fill="{p["accent2"]}">{num}</text>',
                    f'<text x="{x + 52}" y="{y + 22}" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="650" fill="{p["text"]}">{label}</text>',
                ]
            )

    parts.extend(
        [
            f'<text x="86" y="456" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="700" fill="{p["muted"]}">VARIANT / {html.escape(str(title)).upper()}</text>',
            "</svg>",
        ]
    )
    write_text_lf(path, "\n".join(parts))


def validate_svg(path: Path) -> bool:
    try:
        ElementTree.fromstring(path.read_text(encoding="utf-8"))
        return True
    except ElementTree.ParseError:
        return False


def write_tokens(variant: dict[str, object], path: Path) -> None:
    tokens = {
        "name": variant["id"],
        "layout": variant["layout"],
        "palette": variant["palette"],
        "type_scale": {"eyebrow": 18, "hero": 82 if variant["layout"] in {"editorial", "editorial-system"} else 70, "body": 17, "caption": 12},
        "components": ["hero", "signal_ribbon", "detail_panel", "cta", "process_chips"],
        "source_runs": variant["source_runs"],
    }
    write_text_lf(path, json.dumps(tokens, indent=2))


def write_judge_notes(loop_dir: Path, variant: dict[str, object], total: float, decision: str, layout_metrics: dict[str, object]) -> None:
    scores = variant["scores"]
    layout_passes = bool(layout_metrics["passes_layout_gate"])
    collision_summary = ", ".join(f"{item['a']} over {item['b']}" for item in layout_metrics["collisions"]) or "none"
    fast = f"""# Judge: fast-critic for {variant['id']}

## Evidence inspected
- `card.svg`
- `tokens.json`

## Scores
- visual_hierarchy: {scores['visual_hierarchy']} - scan path and title clarity.
- information_clarity: {scores['information_clarity']} - event details and CTA readability.
- layout_quality: {scores['layout_quality']} - checked for content/control overlap and clear whitespace.

## Rationale
The card is {'ready to promote' if total >= 4.6 and layout_passes else 'blocked by a layout-quality issue' if not layout_passes else 'useful but still has a visible tradeoff'} for quick visual review.
"""
    design = f"""# Judge: design-critic for {variant['id']}

## Evidence inspected
- `card.svg`
- `tokens.json`

## Scores
- brand_distinctiveness: {scores['brand_distinctiveness']} - memorable visual language.
- system_coherence: {scores['system_coherence']} - reusable components and token consistency.
- polish: {scores['polish']} - spacing, rhythm, and production finish.

## Rationale
The design {'balances identity and system reuse well' if total >= 4.6 else 'contributes a useful direction for synthesis'}.
"""
    layout = f"""# Judge: layout-critic for {variant['id']}

## Evidence inspected
- `card.svg`
- `layout-quality.json`

## Scores
- layout_quality: {scores['layout_quality']} - visual element separation, whitespace, and collision risk.

## Rationale
Layout gate: {'pass' if layout_passes else 'fail'}.

Detected collisions: {collision_summary}.
"""
    aggregate = f"""# Judge: aggregate for {variant['id']}

## What changed
- {variant['hypothesis']}

## Evidence inspected
- `card.svg`
- `tokens.json`
- independent fast/design/layout critic notes

## Scores
- visual_hierarchy: {scores['visual_hierarchy']}
- brand_distinctiveness: {scores['brand_distinctiveness']}
- information_clarity: {scores['information_clarity']}
- system_coherence: {scores['system_coherence']}
- polish: {scores['polish']}
- layout_quality: {scores['layout_quality']}
- weighted_total: {total}

## Judge mode
- panel, with objective SVG validity and layout-overlap checks as supporting gates.

## Panel notes
- fast-critic: focused on scan path, event detail clarity, and CTA visibility.
- design-critic: focused on identity, component reuse, and visual finish.
- layout-critic: focused on element collisions, whitespace, and whether the card is visually usable.
- dissent / disagreement: {'layout critic blocks champion promotion because ' + collision_summary if not layout_passes else 'none material; critics agree this is `' + decision + '`.'}

## What improved
- {variant['next']}

## What failed / regressed
- {'No material regression versus the previous champion.' if decision == 'new_best' else 'Did not beat the current champion, but remains useful synthesis input.'}

## Next hypothesis
- {variant['next']}
"""
    write_text_lf(loop_dir / "judge-fast-critic.md", fast)
    write_text_lf(loop_dir / "judge-design-critic.md", design)
    write_text_lf(loop_dir / "judge-layout-critic.md", layout)
    write_text_lf(loop_dir / "judge-aggregate.md", aggregate)


def main() -> None:
    best_score = -1.0
    best_id = ""
    iterations = []
    for variant in VARIANTS:
        loop_dir = ROOT / variant["track"] / variant["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        card_path = loop_dir / "card.svg"
        tokens_path = loop_dir / "tokens.json"
        layout_path = loop_dir / "layout-quality.json"
        write_card_svg(variant, card_path)
        write_tokens(variant, tokens_path)
        layout_metrics = write_layout_metrics(variant, layout_path)
        valid_svg = validate_svg(card_path)
        total = weighted_score(variant["scores"]) if valid_svg else 0.0
        if not valid_svg:
            decision = "failed"
        elif not layout_metrics["passes_layout_gate"]:
            decision = "reject"
        else:
            decision = "new_best" if total > best_score else "keep_for_synthesis"
        if decision == "new_best":
            best_score = total
            best_id = variant["id"]
        write_judge_notes(loop_dir, variant, total, decision, layout_metrics)
        prompt_chain = prompt_feedback(variant, decision, layout_metrics)
        artifacts = [
            {"kind": "image", "label": "Card SVG", "path": f"{variant['track']}/{variant['id']}/card.svg", "sha256": sha256(card_path)},
            {"kind": "data", "label": "Design tokens", "path": f"{variant['track']}/{variant['id']}/tokens.json", "sha256": sha256(tokens_path)},
            {"kind": "data", "label": "Layout quality metrics", "path": f"{variant['track']}/{variant['id']}/layout-quality.json", "sha256": sha256(layout_path)},
        ]
        for name in ["judge-fast-critic.md", "judge-design-critic.md", "judge-layout-critic.md", "judge-aggregate.md"]:
            note_path = loop_dir / name
            artifacts.append({"kind": "markdown", "label": name, "path": f"{variant['track']}/{variant['id']}/{name}", "sha256": sha256(note_path)})
        iterations.append(
            {
                "id": variant["id"],
                "track_id": variant["track"],
                "experiment_run": variant["experiment_run"],
                "source_runs": variant["source_runs"],
                "parent_id": variant["parent_id"],
                "parent_ids": variant["parent_ids"],
                "hypothesis": variant["hypothesis"],
                "commands": {
                    "build": "Generate SVG card and design tokens from deterministic design parameters.",
                    "run": "python run_example.py",
                    "judge": "Validate SVG and layout quality, then aggregate independent qualitative judge notes.",
                },
                "artifacts": artifacts,
                "scores": [
                    {
                        "scorer_id": "svg-validity",
                        "type": "objective_command",
                        "value": 5 if valid_svg else 0,
                        "per_criterion": {"svg_parses": valid_svg, "has_tokens": tokens_path.exists(), "has_card": card_path.exists()},
                        "notes": "SVG parses and required artifacts exist." if valid_svg else "SVG failed XML parsing.",
                    },
                    {
                        "scorer_id": "layout-quality",
                        "type": "objective_command",
                        "value": layout_metrics["score"],
                        "per_criterion": {
                            "passes_layout_gate": layout_metrics["passes_layout_gate"],
                            "collisions": layout_metrics["collisions"],
                        },
                        "notes": "No layout collisions detected." if layout_metrics["passes_layout_gate"] else "Layout collisions block champion promotion.",
                    },
                    {
                        "scorer_id": "design-panel",
                        "type": "llm_rubric",
                        "judge_panel": "design-panel",
                        "value": total,
                        "per_criterion": variant["scores"],
                        "notes": "Aggregated from fast-critic, design-critic, and layout-critic judge notes.",
                    },
                ],
                "prompt": prompt_chain,
                "layout_quality": layout_metrics,
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": variant["hypothesis"],
                    "action": variant["next"],
                    "evidence": f"{variant['track']}/{variant['id']}/card.svg, tokens.json, and panel notes",
                    "confidence": "high" if decision == "new_best" else "low" if decision in {"reject", "failed"} else "medium",
                },
                "decision": decision,
                "stop_reason": (
                    "Rejected because the layout-quality gate detected overlapping process chips and body copy."
                    if variant["id"] == "loop-04-production-polish"
                    else "Cross-run synthesis reached production-polish target without layout collisions."
                    if variant["id"] == "loop-05-layout-quality-fix"
                    else None
                ),
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "visual-design-system-worked-example",
        "title": "SVG Visual Design System Worked Example",
        "goal": "Run two independent SVG visual design experiments, then synthesize their best lessons into a polished event-card system.",
        "created_at": "2026-07-06T00:00:00Z",
        "budget": {"max_iters": 7, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 60},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["editorial-run/**", "visual-language-run/**", "synthesis/**", "manifest.json", "viewer.html"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {"id": "visual_hierarchy", "label": "Visual hierarchy", "weight": 1.4},
            {"id": "brand_distinctiveness", "label": "Brand distinctiveness", "weight": 1.1},
            {"id": "information_clarity", "label": "Information clarity", "weight": 1.2},
            {"id": "system_coherence", "label": "Reusable system coherence", "weight": 1.0},
            {"id": "polish", "label": "Production polish", "weight": 1.3},
            {"id": "layout_quality", "label": "Layout quality and non-overlap", "weight": 1.5},
        ],
        "scorers": [
            {"id": "svg-validity", "type": "objective_command", "command": "python run_example.py", "primary": True, "weight": 1},
            {"id": "layout-quality", "type": "objective_command", "command": "python run_example.py", "primary": True, "weight": 2},
            {"id": "design-panel", "type": "llm_rubric", "judge_panel": "design-panel", "weight": 2},
        ],
        "judge_panels": [
            {
                "id": "design-panel",
                "blind": False,
                "flip_pairwise_order": False,
                "aggregation": "weighted_mean_with_dissent",
                "judges": [
                    {"id": "fast-critic", "role": "scan path, readability, and CTA clarity"},
                    {"id": "design-critic", "role": "brand identity, component reuse, and visual polish"},
                    {"id": "layout-critic", "role": "element collisions, whitespace, and visual usability"},
                ],
            }
        ],
        "governance": {"self_editing": {"requires_user_approval": True, "proposal_required": True, "approved_proposal_id": None}},
        "tracks": [
            {"id": "editorial-run", "label": "Run A - editorial clarity", "hypothesis": "A typographic route can optimize hierarchy and information clarity."},
            {"id": "visual-language-run", "label": "Run B - visual language", "hypothesis": "A generative visual route can optimize distinctiveness and energy."},
            {"id": "synthesis", "label": "Run C - cross-run synthesis", "hypothesis": "A synthesis run can combine editorial clarity with distinctive signal motifs."},
        ],
        "iterations": iterations,
        "best": {"iteration_id": best_id, "score": best_score, "why": "Best panel score while passing SVG validity and layout-quality gates."},
        "rules": [
            {
                "trigger": "Qualitative visual work still needs auditable artifacts.",
                "action": "Commit the generated SVG, tokens, judge notes, manifest, and viewer so the design can be inspected without rerunning.",
                "confidence": "high",
            },
            {
                "trigger": "A visually valid SVG can still be a poor design if elements overlap.",
                "action": "Add a layout-quality gate and show prompt/feedback history so rejected visual decisions remain visible.",
                "confidence": "high",
            }
        ],
        "synthesis": "Run A provided the strongest hierarchy and information clarity. Run B provided a more distinctive visual language. Run C combined the editorial card system with signal ribbons. The first production polish loop looked attractive but failed the new layout-quality gate because process chips overlapped the body copy. The final loop moved those chips into clear whitespace and became the champion.",
    }
    write_text_lf(ROOT / "manifest.json", json.dumps(manifest, indent=2))
    write_text_lf(ROOT / "viewer.html", build_viewer.render_viewer(manifest))
    print(f"Best design: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
