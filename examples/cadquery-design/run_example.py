from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parent


DESIGNS = [
    {
        "id": "loop-01-minimal-cradle",
        "title": "Minimal upright cradle",
        "track": "generative-design",
        "experiment_run": "run-a-utility-cradle",
        "source_runs": ["run-a-utility-cradle"],
        "parent_id": None,
        "parent_ids": [],
        "hypothesis": "Run A starts with the smallest obvious cradle to establish a clear, printable baseline.",
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
        "experiment_run": "run-a-utility-cradle",
        "source_runs": ["run-a-utility-cradle"],
        "parent_id": "loop-01-minimal-cradle",
        "parent_ids": ["loop-01-minimal-cradle"],
        "hypothesis": "Run A tests whether cable access and a wider footprint improve utility enough to offset visual bulk.",
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
        "id": "loop-01-compact-braced",
        "title": "Compact braced printability run",
        "track": "bracing-run",
        "experiment_run": "run-b-printable-bracing",
        "source_runs": ["run-b-printable-bracing"],
        "parent_id": None,
        "parent_ids": [],
        "hypothesis": "Run B explores whether triangular side braces can make a compact stand feel stable without first solving cable access.",
        "params": {
            "width": 68,
            "depth": 56,
            "base_thickness": 6,
            "back_height": 80,
            "back_thickness": 7,
            "lip_height": 10,
            "lip_depth": 9,
            "side_braces": True,
            "cable_channel_width": 0,
        },
        "next": "Add cable access to the braced compact concept and check whether the footprint remains acceptable.",
    },
    {
        "id": "loop-02-printable-braced-cable",
        "title": "Braced cable-access run",
        "track": "bracing-run",
        "experiment_run": "run-b-printable-bracing",
        "source_runs": ["run-b-printable-bracing"],
        "parent_id": "loop-01-compact-braced",
        "parent_ids": ["loop-01-compact-braced"],
        "hypothesis": "Run B adds the charging cut-out to the braced concept, trading a little desk footprint for a more complete functional candidate.",
        "params": {
            "width": 84,
            "depth": 74,
            "base_thickness": 6,
            "back_height": 94,
            "back_thickness": 7,
            "lip_height": 12,
            "lip_depth": 10,
            "side_braces": True,
            "cable_channel_width": 14,
        },
        "next": "Synthesize Run A's cable affordance with Run B's side-braced stability into a cross-run hybrid.",
    },
    {
        "id": "loop-03-braced-synthesis",
        "title": "Cross-run braced cable synthesis",
        "track": "synthesis",
        "experiment_run": "run-c-cross-run-synthesis",
        "source_runs": ["run-a-utility-cradle", "run-b-printable-bracing"],
        "parent_id": "loop-02-cable-dock",
        "parent_ids": ["loop-02-cable-dock", "loop-02-printable-braced-cable"],
        "hypothesis": "The synthesis experiment combines Run A's cable-dock affordance with Run B's side-braced stability to make a less bulky hybrid.",
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
        "next": "Refine the hybrid by trimming footprint while preserving the cable channel and brace support.",
    },
    {
        "id": "loop-04-refined-hybrid",
        "title": "Refined cross-run champion",
        "track": "synthesis",
        "experiment_run": "run-c-cross-run-synthesis",
        "source_runs": ["run-a-utility-cradle", "run-b-printable-bracing", "run-c-cross-run-synthesis"],
        "parent_id": "loop-03-braced-synthesis",
        "parent_ids": ["loop-03-braced-synthesis", "loop-02-cable-dock", "loop-02-printable-braced-cable"],
        "hypothesis": "A second synthesis loop can build on both source experiments and the first hybrid to reduce footprint without losing stability or cable usability.",
        "params": {
            "width": 78,
            "depth": 68,
            "base_thickness": 6,
            "back_height": 92,
            "back_thickness": 7,
            "lip_height": 12,
            "lip_depth": 10,
            "side_braces": True,
            "cable_channel_width": 16,
        },
        "next": "Stop: the refined hybrid is the best cross-run synthesis candidate while keeping all objective gates green.",
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
    width = float(params["width"])
    depth = float(params["depth"])
    base_t = float(params["base_thickness"])
    back_h = float(params["back_height"])
    back_t = float(params["back_thickness"])
    lip_h = float(params["lip_height"])
    lip_d = float(params["lip_depth"])
    cable_w = float(params["cable_channel_width"])
    side_braces = bool(params["side_braces"])

    w = width / 2
    d = depth / 2
    origin_x = 380
    origin_y = 318
    scale = 2.65

    def project(x: float, y: float, z: float) -> tuple[float, float]:
        return (
            origin_x + (x * scale) - (y * 1.08),
            origin_y + (y * 0.46) - (z * 2.05),
        )

    def points(values: list[tuple[float, float, float]]) -> str:
        return " ".join(f"{project(x, y, z)[0]:.1f},{project(x, y, z)[1]:.1f}" for x, y, z in values)

    def polygon(values: list[tuple[float, float, float]], fill: str, stroke: str = "#475569", stroke_width: int = 2) -> str:
        return f"<polygon points=\"{points(values)}\" fill=\"{fill}\" stroke=\"{stroke}\" stroke-width=\"{stroke_width}\"/>"

    def path_line(values: list[tuple[float, float, float]], stroke: str, stroke_width: int = 4) -> str:
        projected = [project(*value) for value in values]
        commands = " ".join(("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}" for index, (x, y) in enumerate(projected))
        return f"<path d=\"{commands}\" fill=\"none\" stroke=\"{stroke}\" stroke-width=\"{stroke_width}\" stroke-linecap=\"round\"/>"

    phone_w = min(46, width - 22)
    phone_bottom = base_t + 14
    phone_top = min(back_h - 9, phone_bottom + 68)
    brace_h = back_h * 0.58
    front_y = -d + lip_d + 8
    back_y = d - back_t
    gap = cable_w / 2 if cable_w else 0
    lip_segments = [(-w, -gap), (gap, w)] if cable_w else [(-w, w)]

    parts = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"760\" height=\"420\" viewBox=\"0 0 760 420\">",
        "<rect width=\"760\" height=\"420\" fill=\"#fbfbf7\"/>",
        f"<text x=\"28\" y=\"34\" font-family=\"Segoe UI, Arial\" font-size=\"22\" font-weight=\"700\" fill=\"#111827\">{html.escape(title)}</text>",
        f"<text x=\"28\" y=\"58\" font-family=\"Segoe UI, Arial\" font-size=\"13\" fill=\"#475569\">Footprint {m['footprint_mm2']} mm2; stability ratio {m['stability_ratio']}; material proxy {m['material_proxy']}</text>",
        f"<text x=\"28\" y=\"78\" font-family=\"Segoe UI, Arial\" font-size=\"13\" fill=\"#475569\">Dimensions: W {width:.0f} mm x D {depth:.0f} mm x H {back_h:.0f} mm; lip {lip_h:.0f} mm; cable {cable_w:.0f} mm; braces {'yes' if side_braces else 'no'}</text>",
        polygon([(-w, -d, base_t), (w, -d, base_t), (w, d, base_t), (-w, d, base_t)], "#dbeafe"),
        polygon([(-w, d - back_t, base_t), (w, d - back_t, base_t), (w, d, back_h), (-w, d, back_h)], "#bfdbfe"),
        polygon([(-phone_w / 2, d - back_t - 3, phone_bottom), (phone_w / 2, d - back_t - 3, phone_bottom), (phone_w / 2, d - back_t - 3, phone_top), (-phone_w / 2, d - back_t - 3, phone_top)], "#1f293326", "#33415599", 1),
    ]

    for x0, x1 in lip_segments:
        parts.append(polygon([(x0, -d, base_t), (x1, -d, base_t), (x1, -d, base_t + lip_h), (x0, -d, base_t + lip_h)], "#93c5fd"))

    if cable_w:
        parts.append(path_line([(0, -d - 12, 0), (0, -d - 1, base_t + lip_h / 2), (0, d - back_t - 4, phone_bottom + 8)], "#2563eb", 5))

    if side_braces:
        parts.append(polygon([(-w + 9, front_y, base_t), (-w + 9, back_y, base_t), (-w + 9, back_y, base_t + brace_h)], "#60a5fa"))
        parts.append(polygon([(w - 9, front_y, base_t), (w - 9, back_y, base_t), (w - 9, back_y, base_t + brace_h)], "#60a5fa"))

    parts.extend([
        "<line x1=\"54\" y1=\"352\" x2=\"214\" y2=\"352\" stroke=\"#94a3b8\" stroke-width=\"2\"/>",
        f"<text x=\"54\" y=\"370\" font-family=\"Segoe UI, Arial\" font-size=\"12\" fill=\"#475569\">W {width:.0f} / D {depth:.0f} / H {back_h:.0f}</text>",
        "<text x=\"28\" y=\"388\" font-family=\"Segoe UI, Arial\" font-size=\"13\" fill=\"#475569\">Included artifacts: CadQuery STEP, CadQuery SVG projection, concept SVG preview, metrics, panel notes</text>",
        "</svg>",
    ])
    path.write_text("\n".join(parts), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text_export(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(
        r"(FILE_NAME\('Open CASCADE Shape Model',')[^']*(')",
        r"\g<1>2026-01-01T00:00:00\g<2>",
        text,
    )
    lines = text.splitlines()
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


def _legacy_viewer_html(manifest: dict[str, object]) -> str:
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


def viewer_html(manifest: dict[str, object]) -> str:
    data = json.dumps(manifest, indent=2).replace("</", "<\\/")
    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f4ef; color: #1f2933; }
header { background: #172554; color: white; padding: 28px 36px; }
main { padding: 24px 36px 48px; }
a { color: #1d4ed8; }
.summary, .card { background: white; border: 1px solid #d6d3d1; border-radius: 14px; padding: 18px; box-shadow: 0 8px 24px rgba(15,23,42,.06); }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(320px, .8fr); gap: 18px; margin: 18px 0; }
.controls { display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }
select { padding: 8px 10px; border-radius: 8px; border: 1px solid #a8a29e; }
.cards { display: grid; gap: 18px; }
.card img { width: 100%; max-width: 760px; border: 1px solid #d6d3d1; border-radius: 10px; background: #fff; }
.artifact-previews { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; align-items: start; }
.artifact-preview-title { margin: 0 0 6px; color: #57534e; font-size: 13px; font-weight: 700; }
.meta { color: #57534e; font-size: 14px; }
.pill { display: inline-block; padding: 4px 9px; border-radius: 999px; background: #dbeafe; color: #1e40af; font-size: 12px; margin-right: 6px; }
.new_best { background: #dcfce7; color: #166534; }
.reject, .failed { background: #fee2e2; color: #991b1b; }
.keep_for_synthesis { background: #fef3c7; color: #92400e; }
.needs_human_review { background: #ede9fe; color: #5b21b6; }
pre { white-space: pre-wrap; overflow: auto; background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
td, th { border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: left; vertical-align: top; }
summary { cursor: pointer; font-weight: 700; }
.graph-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
#graph { min-width: 860px; width: 100%; height: 260px; display: block; }
.timeline { display: grid; gap: 8px; }
.bar-row { display: grid; grid-template-columns: 220px 1fr 52px; gap: 10px; align-items: center; }
.bar-track { height: 14px; border-radius: 999px; background: #e7e5e4; overflow: hidden; }
.bar { height: 100%; border-radius: 999px; background: #2563eb; }
.json-panel { max-height: 520px; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <p>__GOAL__</p>
</header>
<main>
  <section class="summary">
    <div><strong>Best</strong><br><span id="best"></span></div>
    <div><strong>Iterations</strong><br><span id="iterationCount"></span></div>
    <div><strong>Tracks</strong><br><span id="trackCount"></span></div>
    <div><strong>Judging</strong><br><span id="scorerSummary"></span></div>
  </section>
  <section class="grid">
    <div class="card">
      <h2>Experiment graph</h2>
      <p class="meta">Lineage comes from each iteration's <code>parent_id</code>; colors show decisions and the star marks the champion.</p>
      <div class="graph-wrap"><svg id="graph" role="img" aria-label="Experiment lineage graph"></svg></div>
    </div>
    <div class="card">
      <h2>Score timeline</h2>
      <div class="timeline" id="timeline"></div>
    </div>
  </section>
  <section class="card">
    <h2>Scorecard</h2>
    <table><tbody id="scorecard"></tbody></table>
  </section>
  <div class="controls">
    <label>Decision <select id="decision"><option value="all">all</option></select></label>
    <label>Track <select id="track"><option value="all">all</option></select></label>
  </div>
  <section class="cards" id="cards"></section>
  <details class="card">
    <summary>Raw manifest JSON</summary>
    <pre class="json-panel" id="manifestJson"></pre>
  </details>
</main>
<script>
const manifest = __MANIFEST_JSON__;
const bestId = manifest.best && manifest.best.iteration_id;
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const scoreFor = iteration => {
  const preferred = (iteration.scores || []).find(score => score.scorer_id === 'design-panel' && typeof score.value === 'number');
  const numeric = preferred || (iteration.scores || []).find(score => typeof score.value === 'number');
  return numeric ? numeric.value : null;
};
const primaryArtifact = iteration =>
  (iteration.artifacts || []).find(a => a.label === 'Preview SVG') ||
  (iteration.artifacts || []).find(a => a.label === 'CadQuery projection SVG') ||
  (iteration.artifacts || []).find(a => a.kind === 'image');
document.getElementById('best').textContent = manifest.best ? `${manifest.best.iteration_id} - score ${manifest.best.score} (${manifest.best.why})` : 'none';
document.getElementById('iterationCount').textContent = manifest.iterations.length;
document.getElementById('trackCount').textContent = manifest.tracks.map(t => t.label || t.id).join(', ');
document.getElementById('scorerSummary').textContent = (manifest.scorers || []).map(s => `${s.id} (${s.type}${s.primary ? ', primary' : ''})`).join('; ') || 'none';
document.getElementById('manifestJson').textContent = JSON.stringify(manifest, null, 2);
document.getElementById('scorecard').innerHTML = manifest.scorecard.map(c => `<tr><th>${esc(c.label)}</th><td>weight ${esc(c.weight)}</td><td><code>${esc(c.id)}</code></td></tr>`).join('');
for (const value of [...new Set(manifest.iterations.map(i => i.decision))]) {
  decision.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
}
for (const value of manifest.tracks.map(t => t.id)) {
  track.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
}
function renderGraph() {
  const tracks = manifest.tracks.map(t => t.id);
  const nodeById = new Map();
  const width = Math.max(920, manifest.iterations.length * 230 + 120);
  const height = Math.max(220, tracks.length * 105 + 90);
  manifest.iterations.forEach((iteration, index) => {
    nodeById.set(iteration.id, { iteration, x: 90 + index * 230, y: 62 + Math.max(0, tracks.indexOf(iteration.track_id)) * 105 });
  });
  const color = decision => ({ new_best: '#16a34a', keep_for_synthesis: '#d97706', reject: '#dc2626', failed: '#991b1b', needs_human_review: '#7c3aed' }[decision] || '#2563eb');
  const lines = [];
  const nodes = [];
  for (const node of nodeById.values()) {
    const parentIds = node.iteration.parent_ids || (node.iteration.parent_id ? [node.iteration.parent_id] : []);
    for (const parentId of parentIds) {
      const parent = nodeById.get(parentId);
      if (parent) lines.push(`<line x1="${parent.x + 72}" y1="${parent.y}" x2="${node.x - 72}" y2="${node.y}" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>`);
    }
    const score = scoreFor(node.iteration);
    nodes.push(`<g>
      <rect x="${node.x - 74}" y="${node.y - 34}" width="148" height="68" rx="12" fill="#fff" stroke="${color(node.iteration.decision)}" stroke-width="3"/>
      <text x="${node.x}" y="${node.y - 12}" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a">${esc(node.iteration.id.replace(/^loop-/, ''))}</text>
      <text x="${node.x}" y="${node.y + 7}" text-anchor="middle" font-size="11" fill="#57534e">${esc(node.iteration.track_id)}</text>
      <text x="${node.x}" y="${node.y + 24}" text-anchor="middle" font-size="11" fill="#57534e">${score === null ? 'no score' : `score ${score}`}${node.iteration.id === bestId ? ' *' : ''}</text>
    </g>`);
  }
  graph.setAttribute('viewBox', `0 0 ${width} ${height}`);
  graph.innerHTML = `<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#64748b"/></marker></defs>${lines.join('')}${nodes.join('')}`;
}
function renderTimeline() {
  const maxScore = Math.max(5, ...manifest.iterations.map(i => scoreFor(i) || 0));
  timeline.innerHTML = manifest.iterations.map(i => {
    const score = scoreFor(i) || 0;
    const width = Math.max(2, Math.round(score / maxScore * 100));
    return `<div class="bar-row"><div><code>${esc(i.id)}</code></div><div class="bar-track"><div class="bar" style="width:${width}%"></div></div><div>${esc(score)}</div></div>`;
  }).join('');
}
function render() {
  const d = decision.value;
  const t = track.value;
  cards.innerHTML = manifest.iterations
    .filter(i => (d === 'all' || i.decision === d) && (t === 'all' || i.track_id === t))
    .map(i => {
      const art = primaryArtifact(i);
      const projection = (i.artifacts || []).find(a => a.label === 'CadQuery projection SVG');
      const step = (i.artifacts || []).find(a => a.label === 'CadQuery STEP');
      const parents = i.parent_ids && i.parent_ids.length ? i.parent_ids : (i.parent_id ? [i.parent_id] : ['root']);
      const artifacts = (i.artifacts || []).map(a => `<tr><td>${esc(a.kind)}</td><td>${esc(a.label)}</td><td><a href="${esc(a.path)}">${esc(a.path)}</a></td><td><code>${esc((a.sha256 || '').slice(0, 16))}</code></td></tr>`).join('');
      const scores = (i.scores || []).map(s => `<tr><td>${esc(s.scorer_id)}</td><td>${esc(s.type)}</td><td>${esc(s.value)}</td><td><pre>${esc(JSON.stringify(s.per_criterion || {}, null, 2))}</pre></td></tr>`).join('');
      const previewCards = [art, projection && (!art || projection.path !== art.path) ? projection : null]
        .filter(Boolean)
        .map(a => `<div class="artifact-preview"><p class="artifact-preview-title">${esc(a.label)}</p><img src="${esc(a.path)}" alt="${esc(a.label)}"></div>`)
        .join('');
      return `<article class="card">
        <h2>${esc(i.id)} ${i.id === bestId ? '*' : ''}</h2>
        <p><span class="pill ${esc(i.decision)}">${esc(i.decision)}</span><span class="pill">${esc(i.track_id)}</span><span class="pill">run: ${esc(i.experiment_run || i.track_id)}</span><span class="pill">parents: ${esc(parents.join(', '))}</span></p>
        <p>${esc(i.hypothesis)}</p>
        ${previewCards ? `<div class="artifact-previews">${previewCards}</div>` : ''}
        ${step ? `<p class="meta">STEP artifact: <a href="${esc(step.path)}">${esc(step.path)}</a></p>` : ''}
        <h3>Lesson</h3><pre>${esc(i.lesson.trigger)}\nAction: ${esc(i.lesson.action)}\nEvidence: ${esc(i.lesson.evidence)}\nConfidence: ${esc(i.lesson.confidence)}</pre>
        <details open>
          <summary>Metadata and provenance</summary>
          <table><tbody>
            <tr><th>Build</th><td>${esc(i.commands.build)}</td></tr>
            <tr><th>Run</th><td>${esc(i.commands.run)}</td></tr>
            <tr><th>Judge</th><td>${esc(i.commands.judge)}</td></tr>
            <tr><th>Changed files</th><td>${esc((i.changed_files || []).join(', '))}</td></tr>
            <tr><th>Stop reason</th><td>${esc(i.stop_reason || '')}</td></tr>
          </tbody></table>
          <h4>Artifacts</h4><table><thead><tr><th>Kind</th><th>Label</th><th>Path</th><th>SHA-256</th></tr></thead><tbody>${artifacts}</tbody></table>
          <h4>Scores</h4><table><thead><tr><th>Scorer</th><th>Type</th><th>Value</th><th>Per criterion</th></tr></thead><tbody>${scores}</tbody></table>
          <h4>Raw iteration JSON</h4><pre>${esc(JSON.stringify(i, null, 2))}</pre>
        </details>
      </article>`;
    }).join('');
}
decision.addEventListener('change', render);
track.addEventListener('change', render);
renderGraph();
renderTimeline();
render();
</script>
</body>
</html>
"""
    return (
        template.replace("__TITLE__", html.escape(str(manifest["title"])))
        .replace("__GOAL__", html.escape(str(manifest["goal"])))
        .replace("__MANIFEST_JSON__", data)
    )


def main() -> None:
    best_score = -1.0
    best_id = ""
    iterations = []

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
                "experiment_run": design["experiment_run"],
                "source_runs": design["source_runs"],
                "parent_id": design["parent_id"],
                "parent_ids": design["parent_ids"],
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
                "stop_reason": "Cross-run synthesis reached the best weighted score." if design["id"] == "loop-04-refined-hybrid" else None,
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "cadquery-design-worked-example",
        "title": "CadQuery Phone Stand Worked Example",
        "goal": "Run two independent CadQuery phone-stand experiments, then synthesize their best lessons into a third cross-run experiment.",
        "created_at": "2026-07-03T00:00:00Z",
        "budget": {"max_iters": 6, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 180},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["generative-design/**", "bracing-run/**", "synthesis/**", "manifest.json", "viewer.html"],
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
                "label": "Run A - utility cradle",
                "hypothesis": "A conventional cradle path can optimize cable access and obvious usability.",
            },
            {
                "id": "bracing-run",
                "label": "Run B - printable bracing",
                "hypothesis": "A separate bracing-first path can optimize stability and printability before synthesis.",
            },
            {
                "id": "synthesis",
                "label": "Run C - cross-run synthesis",
                "hypothesis": "A third experiment can build from both Run A and Run B rather than continuing only one lineage.",
            },
        ],
        "iterations": iterations,
        "best": {
            "iteration_id": best_id,
            "score": best_score,
            "why": "Best qualitative panel score while passing all objective gates and combining lessons from both source runs.",
        },
        "rules": [
            {
                "trigger": "Qualitative CAD design has hard constraints and taste tradeoffs.",
                "action": "Use objective gates first, then independent qualitative judges for champion selection.",
                "confidence": "high",
            }
        ],
        "synthesis": "Run A proved the value of a visible cable dock but became visually heavy. Run B proved side braces could preserve stability and printability, but needed the utility affordance from Run A. Run C synthesized both branches, then refined the hybrid to reduce footprint while keeping the cable channel and brace support.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "viewer.html").write_text(viewer_html(manifest), encoding="utf-8")
    print(f"Best design: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
