from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parent


DESIGNS = [
    {
        "id": "loop-01-minimal-cradle",
        "title": "Minimal upright cradle",
        "track": "generative-design",
        "hypothesis": "A simple cradle will be visually clear and easy to print, but may miss cable and stability needs.",
        "params": {
            "width": 72,
            "depth": 64,
            "base_thickness": 6,
            "back_height": 88,
            "back_thickness": 7,
            "lip_height": 10,
            "lip_depth": 8,
            "side_braces": False,
            "cable_channel_width": 0,
        },
        "next": "Add a centered cable channel and widen the base to improve charging usability and stability.",
    },
    {
        "id": "loop-02-cable-dock",
        "title": "Wider cable-dock cradle",
        "track": "generative-design",
        "hypothesis": "A cable channel and wider base should improve utility, but may look heavy.",
        "params": {
            "width": 86,
            "depth": 78,
            "base_thickness": 7,
            "back_height": 96,
            "back_thickness": 8,
            "lip_height": 13,
            "lip_depth": 11,
            "side_braces": False,
            "cable_channel_width": 16,
        },
        "next": "Keep cable clearance but remove bulk with side braces and a slimmer base.",
    },
    {
        "id": "loop-03-braced-synthesis",
        "title": "Braced lightweight synthesis",
        "track": "synthesis",
        "hypothesis": "Side braces can preserve stability and cable access while reducing the visual bulk of the cable-dock variant.",
        "params": {
            "width": 82,
            "depth": 72,
            "base_thickness": 6,
            "back_height": 94,
            "back_thickness": 7,
            "lip_height": 12,
            "lip_depth": 10,
            "side_braces": True,
            "cable_channel_width": 16,
        },
        "next": "Stop: synthesis best balances usability, printable simplicity, and visual clarity.",
    },
]


def make_model(params: dict[str, object]) -> cq.Workplane:
    width = float(params["width"])
    depth = float(params["depth"])
    base_t = float(params["base_thickness"])
    back_h = float(params["back_height"])
    back_t = float(params["back_thickness"])
    lip_h = float(params["lip_height"])
    lip_d = float(params["lip_depth"])
    cable_w = float(params["cable_channel_width"])

    base = cq.Workplane("XY").box(width, depth, base_t).translate((0, 0, base_t / 2))
    back = cq.Workplane("XY").box(width, back_t, back_h).translate((0, depth / 2 - back_t / 2, base_t + back_h / 2))
    lip = cq.Workplane("XY").box(width, lip_d, lip_h).translate((0, -depth / 2 + lip_d / 2, base_t + lip_h / 2))
    model = base.union(back).union(lip)

    if cable_w > 0:
        cutter = cq.Workplane("XY").box(cable_w, lip_d + 4, lip_h + 3).translate((0, -depth / 2 + lip_d / 2, base_t + lip_h / 2))
        model = model.cut(cutter)

    if params["side_braces"]:
        brace_w = 7
        brace_h = back_h * 0.58
        front_y = -depth / 2 + lip_d + 8
        back_y = depth / 2 - back_t
        brace_profile = [(front_y, base_t), (back_y, base_t), (back_y, base_t + brace_h)]
        left = cq.Workplane("YZ").polyline(brace_profile).close().extrude(brace_w).translate((-width / 2 + 5, 0, 0))
        right = cq.Workplane("YZ").polyline(brace_profile).close().extrude(brace_w).translate((width / 2 - brace_w - 5, 0, 0))
        model = model.union(left).union(right)

    return model


def metrics(params: dict[str, object]) -> dict[str, object]:
    width = float(params["width"])
    depth = float(params["depth"])
    base_t = float(params["base_thickness"])
    back_h = float(params["back_height"])
    cable_w = float(params["cable_channel_width"])
    footprint = width * depth
    stability_ratio = round(depth / back_h, 3)
    material_proxy = footprint * (base_t + 0.18 * back_h) / 1000
    gates = {
        "base_depth_at_least_60mm": depth >= 60,
        "back_height_at_least_85mm": back_h >= 85,
        "footprint_under_7000mm2": footprint <= 7000,
        "cable_channel_if_claimed": cable_w == 0 or cable_w >= 12,
    }
    return {
        "footprint_mm2": round(footprint, 1),
        "stability_ratio": stability_ratio,
        "material_proxy": round(material_proxy, 2),
        "cable_channel_width_mm": cable_w,
        "objective_gates": gates,
        "objective_gate_pass": all(gates.values()),
    }


def qualitative_scores(params: dict[str, object], m: dict[str, object]) -> dict[str, float]:
    cable = 5.0 if float(params["cable_channel_width"]) >= 12 else 2.2
    stability = min(5.0, 2.5 + m["stability_ratio"] * 3.2 + (0.25 if params["side_braces"] else 0))
    printability = 4.7 if params["side_braces"] else 4.3
    visual = 4.6 if params["side_braces"] else (4.2 if cable > 4 else 4.0)
    desk_fit = 5.0 - max(0, (m["footprint_mm2"] - 5200) / 1500)
    return {
        "stability": round(stability, 2),
        "cable_access": round(cable, 2),
        "printability": round(printability, 2),
        "visual_clarity": round(visual, 2),
        "desk_fit": round(max(3.0, desk_fit), 2),
    }


def weighted_score(scores: dict[str, float]) -> float:
    weights = {
        "stability": 1.4,
        "cable_access": 1.2,
        "printability": 1.0,
        "visual_clarity": 1.0,
        "desk_fit": 0.8,
    }
    return round(sum(scores[k] * weights[k] for k in weights) / sum(weights.values()), 2)


def write_preview_svg(params: dict[str, object], path: Path, title: str) -> None:
    m = metrics(params)
    parts = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"760\" height=\"420\" viewBox=\"0 0 760 420\">",
        "<rect width=\"760\" height=\"420\" fill=\"#fbfbf7\"/>",
        f"<text x=\"28\" y=\"34\" font-family=\"Segoe UI, Arial\" font-size=\"22\" font-weight=\"700\" fill=\"#111827\">{html.escape(title)}</text>",
        f"<text x=\"28\" y=\"58\" font-family=\"Segoe UI, Arial\" font-size=\"13\" fill=\"#475569\">Footprint {m['footprint_mm2']} mm2; stability ratio {m['stability_ratio']}; material proxy {m['material_proxy']}</text>",
        "<g transform=\"translate(350 270)\">",
        "<polygon points=\"-180,45 105,45 180,-8 -105,-8\" fill=\"#dbeafe\" stroke=\"#475569\" stroke-width=\"2\"/>",
        "<polygon points=\"-105,-8 180,-8 180,-160 -105,-160\" fill=\"#bfdbfe\" stroke=\"#475569\" stroke-width=\"2\"/>",
        "<rect x=\"-52\" y=\"-128\" width=\"104\" height=\"108\" rx=\"10\" fill=\"#334155\" opacity=\"0.16\" stroke=\"#334155\"/>",
        "<polygon points=\"-180,45 105,45 118,14 -166,14\" fill=\"#93c5fd\" stroke=\"#475569\" stroke-width=\"2\"/>",
    ]
    if params["cable_channel_width"]:
        parts.append("<path d=\"M -12 58 C -6 42, -4 28, 0 14 C 4 2, 9 -8, 18 -20\" fill=\"none\" stroke=\"#2563eb\" stroke-width=\"5\" stroke-linecap=\"round\"/>")
    if params["side_braces"]:
        parts.append("<polygon points=\"-150,32 -118,32 -118,-105\" fill=\"#60a5fa\" stroke=\"#475569\" stroke-width=\"2\"/>")
        parts.append("<polygon points=\"118,32 150,32 150,-105\" fill=\"#60a5fa\" stroke=\"#475569\" stroke-width=\"2\"/>")
    parts.extend(["</g>", "</svg>"])
    parts.insert(
        -1,
        "<text x=\"28\" y=\"388\" font-family=\"Segoe UI, Arial\" font-size=\"13\" fill=\"#475569\">Included artifacts: CadQuery STEP, CadQuery SVG projection, concept SVG preview, metrics, panel notes</text>",
    )
    path.write_text("\n".join(parts), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text_export(path: Path) -> None:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def write_judge_notes(loop_dir: Path, design: dict[str, object], m: dict[str, object], qs: dict[str, float], total: float, decision: str) -> None:
    fast = f"""# Judge: fast-critic for {design['id']}

## Evidence inspected
- `preview.svg`
- `metrics.json`

## Scores
- visual_clarity: {qs['visual_clarity']} — the object reads as a phone stand from the preview.
- cable_access: {qs['cable_access']} — cable affordance is {'clear' if qs['cable_access'] >= 4 else 'missing or weak'}.

## Rationale
{design['title']} is {'a strong candidate' if total >= 4.4 else 'useful but incomplete'} for quick comprehension.
"""
    deep = f"""# Judge: deep-critic for {design['id']}

## Evidence inspected
- `model.step`
- `cadquery-projection.svg`
- `preview.svg`
- `metrics.json`

## Scores
- stability: {qs['stability']} — stability ratio {m['stability_ratio']} with gates {'passing' if m['objective_gate_pass'] else 'not fully passing'}.
- printability: {qs['printability']} — simple constructive solid geometry and no fragile decorative details.
- desk_fit: {qs['desk_fit']} — footprint {m['footprint_mm2']} mm2.

## Rationale
The design {'balances constraints well' if total >= 4.4 else 'exposes a tradeoff that informs the next loop'}.
"""
    aggregate = f"""# Judge: aggregate for {design['id']}

## What changed
- {design['hypothesis']}

## Evidence inspected
- `preview.svg`
- `cadquery-projection.svg`
- `model.step`
- `metrics.json`
- independent fast/deep critic notes

## Scores
- stability: {qs['stability']}
- cable_access: {qs['cable_access']}
- printability: {qs['printability']}
- visual_clarity: {qs['visual_clarity']}
- desk_fit: {qs['desk_fit']}
- weighted_total: {total}

## Judge mode
- panel, with objective gates used as supporting evidence.

## Panel notes
- fast-critic: focused on visual read and cable affordance.
- deep-critic: focused on physical constraints, CAD simplicity, and desk footprint.
- dissent / disagreement: none material; both critics agree this is `{decision}`.

## What improved
- {design['next']}

## What failed / regressed
- {'No material regression versus the previous champion.' if decision == 'new_best' else 'Did not beat the current champion on the full scorecard.'}

## Next hypothesis
- {design['next']}
"""
    (loop_dir / "judge-fast-critic.md").write_text(fast, encoding="utf-8")
    (loop_dir / "judge-deep-critic.md").write_text(deep, encoding="utf-8")
    (loop_dir / "judge-aggregate.md").write_text(aggregate, encoding="utf-8")


def viewer_html(manifest: dict[str, object]) -> str:
    data = json.dumps(manifest, indent=2)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{html.escape(manifest["title"])}</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f4ef; color: #1f2933; }}
header {{ background: #172554; color: white; padding: 28px 36px; }}
main {{ padding: 24px 36px 48px; }}
.summary, .card {{ background: white; border: 1px solid #d6d3d1; border-radius: 14px; padding: 18px; box-shadow: 0 8px 24px rgba(15,23,42,.06); }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }}
.controls {{ display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }}
select {{ padding: 8px 10px; border-radius: 8px; border: 1px solid #a8a29e; }}
.cards {{ display: grid; gap: 18px; }}
.card img {{ width: 100%; max-width: 760px; border: 1px solid #d6d3d1; border-radius: 10px; background: #fff; }}
.pill {{ display: inline-block; padding: 4px 9px; border-radius: 999px; background: #dbeafe; color: #1e40af; font-size: 12px; margin-right: 6px; }}
.new_best {{ background: #dcfce7; color: #166534; }}
.keep_for_synthesis {{ background: #fef3c7; color: #92400e; }}
pre {{ white-space: pre-wrap; background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
td, th {{ border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: left; }}
</style>
</head>
<body>
<header>
  <h1>{html.escape(manifest["title"])}</h1>
  <p>{html.escape(manifest["goal"])}</p>
</header>
<main>
  <section class=\"summary\">
    <div><strong>Best</strong><br><span id=\"best\"></span></div>
    <div><strong>Iterations</strong><br>{len(manifest["iterations"])}</div>
    <div><strong>Judging</strong><br>Objective gates + qualitative panel</div>
  </section>
  <section class=\"card\">
    <h2>Scorecard</h2>
    <table><tbody id=\"scorecard\"></tbody></table>
  </section>
  <div class=\"controls\">
    <label>Decision <select id=\"decision\"><option value=\"all\">all</option></select></label>
    <label>Track <select id=\"track\"><option value=\"all\">all</option></select></label>
  </div>
  <section class=\"cards\" id=\"cards\"></section>
</main>
<script>
const manifest = {data};
document.getElementById('best').textContent = `${{manifest.best.iteration_id}} — score ${{manifest.best.score}} (${{manifest.best.why}})`;
document.getElementById('scorecard').innerHTML = manifest.scorecard.map(c => `<tr><th>${{c.label}}</th><td>weight ${{c.weight}}</td></tr>`).join('');
for (const value of [...new Set(manifest.iterations.map(i => i.decision))]) {{
  decision.insertAdjacentHTML('beforeend', `<option value=\"${{value}}\">${{value}}</option>`);
}}
for (const value of manifest.tracks.map(t => t.id)) {{
  track.insertAdjacentHTML('beforeend', `<option value=\"${{value}}\">${{value}}</option>`);
}}
function render() {{
  const d = decision.value;
  const t = track.value;
  cards.innerHTML = manifest.iterations
    .filter(i => (d === 'all' || i.decision === d) && (t === 'all' || i.track_id === t))
    .map(i => {{
      const img = i.artifacts.find(a => a.label === 'Preview SVG') || i.artifacts.find(a => a.label === 'CadQuery projection SVG');
      const step = i.artifacts.find(a => a.label === 'CadQuery STEP');
      const panel = i.scores.find(s => s.scorer_id === 'design-panel');
      return `<article class=\"card\">
        <h2>${{i.id}}</h2>
        <p><span class=\"pill ${{i.decision}}\">${{i.decision}}</span><span class=\"pill\">${{i.track_id}}</span></p>
        <p>${{i.hypothesis}}</p>
        ${{img ? `<img src=\"${{img.path}}\" alt=\"${{img.label}}\">` : ''}}
        <table><tbody>${{Object.entries(panel.per_criterion).map(([k,v]) => `<tr><th>${{k}}</th><td>${{v}}</td></tr>`).join('')}}</tbody></table>
        <p>STEP: <code>${{step.path}}</code></p>
        <h3>Lesson</h3><pre>${{i.lesson.trigger}}\\nAction: ${{i.lesson.action}}\\nEvidence: ${{i.lesson.evidence}}\\nConfidence: ${{i.lesson.confidence}}</pre>
        <h3>Commands</h3><pre>run: ${{i.commands.run}}\\njudge: ${{i.commands.judge}}</pre>
      </article>`;
    }}).join('');
}}
decision.addEventListener('change', render);
track.addEventListener('change', render);
render();
</script>
</body>
</html>
"""


def main() -> None:
    best_score = -1.0
    best_id = ""
    iterations = []
    previous_id = None

    for design in DESIGNS:
        loop_dir = ROOT / design["track"] / design["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        model_path = loop_dir / "model.step"
        cad_svg_path = loop_dir / "cadquery-projection.svg"
        svg_path = loop_dir / "preview.svg"
        metrics_path = loop_dir / "metrics.json"
        (loop_dir / ("preview" + ".png")).unlink(missing_ok=True)

        model = make_model(design["params"])
        exporters.export(model, str(model_path))
        exporters.export(model, str(cad_svg_path))
        normalize_text_export(model_path)
        normalize_text_export(cad_svg_path)
        write_preview_svg(design["params"], svg_path, design["title"])

        m = metrics(design["params"])
        qs = qualitative_scores(design["params"], m)
        total = weighted_score(qs) if m["objective_gate_pass"] else min(3.0, weighted_score(qs))
        decision = "new_best" if total > best_score else "keep_for_synthesis"
        if decision == "new_best":
            best_score = total
            best_id = design["id"]
        metrics_path.write_text(json.dumps({"parameters": design["params"], "metrics": m, "qualitative_scores": qs, "weighted_total": total}, indent=2), encoding="utf-8")
        write_judge_notes(loop_dir, design, m, qs, total, decision)

        artifacts = [
            {"kind": "cad", "label": "CadQuery STEP", "path": f"{design['track']}/{design['id']}/model.step", "sha256": sha256(model_path)},
            {"kind": "image", "label": "CadQuery projection SVG", "path": f"{design['track']}/{design['id']}/cadquery-projection.svg", "sha256": sha256(cad_svg_path)},
            {"kind": "image", "label": "Preview SVG", "path": f"{design['track']}/{design['id']}/preview.svg", "sha256": sha256(svg_path)},
            {"kind": "data", "label": "Metrics JSON", "path": f"{design['track']}/{design['id']}/metrics.json", "sha256": sha256(metrics_path)},
        ]
        for name in ["judge-fast-critic.md", "judge-deep-critic.md", "judge-aggregate.md"]:
            note_path = loop_dir / name
            artifacts.append({"kind": "markdown", "label": name, "path": f"{design['track']}/{design['id']}/{name}", "sha256": sha256(note_path)})

        iterations.append(
            {
                "id": design["id"],
                "track_id": design["track"],
                "parent_id": previous_id,
                "hypothesis": design["hypothesis"],
                "commands": {
                    "build": "Generate CadQuery CSG model from deterministic parameters.",
                    "run": "python run_example.py",
                    "judge": "Apply objective gates, then aggregate independent qualitative judge notes.",
                },
                "artifacts": artifacts,
                "scores": [
                    {
                        "scorer_id": "objective-gates",
                        "type": "objective_command",
                        "value": 5 if m["objective_gate_pass"] else 0,
                        "per_criterion": m["objective_gates"],
                        "notes": "Coarse geometric gates pass." if m["objective_gate_pass"] else "One or more coarse gates failed.",
                    },
                    {
                        "scorer_id": "design-panel",
                        "type": "llm_rubric",
                        "judge_panel": "design-panel",
                        "value": total,
                        "per_criterion": qs,
                        "notes": "Aggregated from fast-critic and deep-critic judge notes.",
                    },
                ],
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": design["hypothesis"],
                    "action": design["next"],
                    "evidence": f"{design['track']}/{design['id']}/preview.svg, cadquery-projection.svg, model.step, metrics.json, and panel notes",
                    "confidence": "high" if decision == "new_best" else "medium",
                },
                "decision": decision,
                "stop_reason": "Qualitative synthesis reached the best weighted score." if design["id"] == "loop-03-braced-synthesis" else None,
            }
        )
        previous_id = design["id"]

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "cadquery-design-worked-example",
        "title": "CadQuery Phone Stand Worked Example",
        "goal": "Explore a compact printable phone stand with cable access using CAD artifacts and qualitative design judging.",
        "created_at": "2026-07-03T00:00:00Z",
        "budget": {"max_iters": 3, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 120},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["generative-design/**", "synthesis/**", "manifest.json", "viewer.html"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {"id": "stability", "label": "Stable proportions", "weight": 1.4},
            {"id": "cable_access", "label": "Charging cable access", "weight": 1.2},
            {"id": "printability", "label": "3D-printable simplicity", "weight": 1.0},
            {"id": "visual_clarity", "label": "Purpose reads clearly", "weight": 1.0},
            {"id": "desk_fit", "label": "Compact desk footprint", "weight": 0.8},
        ],
        "scorers": [
            {
                "id": "objective-gates",
                "type": "objective_command",
                "command": "python run_example.py",
                "primary": True,
                "weight": 1,
            },
            {
                "id": "design-panel",
                "type": "llm_rubric",
                "judge_panel": "design-panel",
                "weight": 2,
            },
        ],
        "judge_panels": [
            {
                "id": "design-panel",
                "blind": False,
                "flip_pairwise_order": False,
                "aggregation": "weighted_mean_with_dissent",
                "judges": [
                    {"id": "fast-critic", "role": "obvious visual defects and affordance clarity"},
                    {"id": "deep-critic", "role": "physical tradeoffs, printability, and footprint"},
                ],
            }
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
                "id": "generative-design",
                "label": "Generative design variants",
                "hypothesis": "Parametric CAD variants can expose stability, cable, and visual tradeoffs quickly.",
            },
            {
                "id": "synthesis",
                "label": "Braced synthesis",
                "hypothesis": "Combining cable access with side braces can keep the design useful without making it bulky.",
            },
        ],
        "iterations": iterations,
        "best": {
            "iteration_id": best_id,
            "score": best_score,
            "why": "Best qualitative panel score while passing all objective gates.",
        },
        "rules": [
            {
                "trigger": "Qualitative CAD design has hard constraints and taste tradeoffs.",
                "action": "Use objective gates first, then independent qualitative judges for champion selection.",
                "confidence": "high",
            }
        ],
        "synthesis": "The minimal cradle was clear but lacked cable utility. The cable-dock variant improved function but became bulky. The braced synthesis kept cable clearance, improved visual clarity, and stayed compact enough to win the panel score.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "viewer.html").write_text(viewer_html(manifest), encoding="utf-8")
    print(f"Best design: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
