from __future__ import annotations

import hashlib
import html
import json
import math
import random
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parent

STOPS = [
    ("Depot", 50, 50),
    ("Museum", 18, 78),
    ("Bakery", 28, 32),
    ("Clinic", 38, 86),
    ("Library", 55, 72),
    ("School", 68, 88),
    ("Market", 82, 58),
    ("Harbor", 90, 24),
    ("Stadium", 64, 18),
    ("Garden", 42, 12),
    ("Station", 15, 15),
    ("Gallery", 75, 42),
]


def distance(a: int, b: int) -> float:
    _, ax, ay = STOPS[a]
    _, bx, by = STOPS[b]
    return math.hypot(ax - bx, ay - by)


def route_length(route: list[int]) -> float:
    return sum(distance(route[i], route[i + 1]) for i in range(len(route) - 1))


def is_valid(route: list[int]) -> bool:
    return route[0] == 0 and route[-1] == 0 and sorted(route[1:-1]) == list(range(1, len(STOPS)))


def nearest_neighbor() -> list[int]:
    route = [0]
    remaining = set(range(1, len(STOPS)))
    while remaining:
        current = route[-1]
        nxt = min(remaining, key=lambda idx: (distance(current, idx), STOPS[idx][0]))
        route.append(nxt)
        remaining.remove(nxt)
    route.append(0)
    return route


def two_opt(route: list[int]) -> tuple[list[int], int]:
    best = route[:]
    improvements = 0
    improved = True
    while improved:
        improved = False
        best_len = route_length(best)
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                if j - i == 1:
                    continue
                candidate = best[:i] + best[i:j][::-1] + best[j:]
                candidate_len = route_length(candidate)
                if candidate_len + 1e-9 < best_len:
                    best = candidate
                    improvements += 1
                    improved = True
                    break
            if improved:
                break
    return best, improvements


def multistart_two_opt() -> tuple[list[int], dict[str, float]]:
    rng = random.Random(42)
    candidates: list[tuple[float, list[int]]] = []
    starts = [nearest_neighbor()]
    for _ in range(35):
        middle = list(range(1, len(STOPS)))
        rng.shuffle(middle)
        starts.append([0] + middle + [0])
    for start in starts:
        improved, _ = two_opt(start)
        candidates.append((route_length(improved), improved))
    candidates.sort(key=lambda item: item[0])
    lengths = [item[0] for item in candidates]
    return candidates[0][1], {
        "starts": len(starts),
        "best_start_length": round(min(route_length(s) for s in starts), 2),
        "median_final_length": round(statistics.median(lengths), 2),
    }


def write_route_svg(route: list[int], path: Path, title: str) -> None:
    width, height = 760, 520
    margin = 52
    scale_x = (width - margin * 2) / 100
    scale_y = (height - margin * 2) / 100

    def xy(idx: int) -> tuple[float, float]:
        _, x, y = STOPS[idx]
        return margin + x * scale_x, height - margin - y * scale_y

    points = " ".join(f"{xy(idx)[0]:.1f},{xy(idx)[1]:.1f}" for idx in route)
    parts = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"760\" height=\"520\" viewBox=\"0 0 760 520\">",
        "<rect width=\"760\" height=\"520\" fill=\"#fbfbf7\"/>",
        f"<text x=\"32\" y=\"34\" font-family=\"Segoe UI, Arial\" font-size=\"22\" font-weight=\"700\" fill=\"#1f2933\">{html.escape(title)}</text>",
        f"<text x=\"32\" y=\"58\" font-family=\"Segoe UI, Arial\" font-size=\"14\" fill=\"#52606d\">Distance: {route_length(route):.2f}; valid: {str(is_valid(route)).lower()}</text>",
        f"<polyline points=\"{points}\" fill=\"none\" stroke=\"#2563eb\" stroke-width=\"4\" stroke-linejoin=\"round\" stroke-linecap=\"round\" opacity=\"0.88\"/>",
    ]
    for order, idx in enumerate(route[:-1]):
        x, y = xy(idx)
        name = STOPS[idx][0]
        color = "#dc2626" if idx == 0 else "#111827"
        radius = 11 if idx == 0 else 8
        parts.append(f"<circle cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"{radius}\" fill=\"{color}\" stroke=\"#ffffff\" stroke-width=\"3\"/>")
        parts.append(f"<text x=\"{x + 12:.1f}\" y=\"{y - 10:.1f}\" font-family=\"Segoe UI, Arial\" font-size=\"12\" fill=\"#1f2933\">{order}. {html.escape(name)}</text>")
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_from_length(length: float, baseline: float) -> float:
    improvement = (baseline - length) / baseline
    return round(min(5.0, 2.0 + improvement * 10.0), 2)


def write_judge_note(path: Path, loop_id: str, title: str, metrics: dict[str, object], next_hypothesis: str) -> None:
    path.write_text(
        f"""# Judge: quantitative route loop {loop_id}

## What changed
- {title}

## Evidence inspected
- `route.svg`
- `metrics.json`

## Scores
- route_length: {metrics["distance"]} total units.
- validity: {"pass" if metrics["valid"] else "fail"}.
- reproducibility: deterministic script and fixed stop list.
- explainability: route SVG and metrics show the change.

## Judge mode
- single with primary objective command.

## What improved
- Improvement versus baseline: {metrics["improvement_pct"]}%.

## What failed / regressed
- {metrics["regression_note"]}

## Next hypothesis
- {next_hypothesis}
""",
        encoding="utf-8",
    )


def _legacy_viewer_html(manifest: dict[str, object]) -> str:
    data = json.dumps(manifest, indent=2)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{html.escape(manifest["title"])}</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f5f7fa; color: #1f2933; }}
header {{ background: #111827; color: white; padding: 28px 36px; }}
main {{ padding: 24px 36px 48px; }}
.summary, .card {{ background: white; border: 1px solid #d9e2ec; border-radius: 14px; padding: 18px; box-shadow: 0 8px 24px rgba(15,23,42,.06); }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }}
.controls {{ display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }}
select {{ padding: 8px 10px; border-radius: 8px; border: 1px solid #bcccdc; }}
.cards {{ display: grid; gap: 18px; }}
.card img {{ width: 100%; max-width: 760px; border: 1px solid #d9e2ec; border-radius: 10px; background: #fff; }}
.meta {{ color: #52606d; font-size: 14px; }}
.pill {{ display: inline-block; padding: 4px 9px; border-radius: 999px; background: #e0f2fe; color: #075985; font-size: 12px; margin-right: 6px; }}
.new_best {{ background: #dcfce7; color: #166534; }}
.reject {{ background: #fee2e2; color: #991b1b; }}
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
    <div><strong>Judging</strong><br>Objective command primary</div>
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
      const art = i.artifacts.find(a => a.kind === 'image');
      const metric = i.scores.find(s => s.scorer_id === 'route-metrics');
      return `<article class=\"card\">
        <h2>${{i.id}}</h2>
        <p><span class=\"pill ${{i.decision}}\">${{i.decision}}</span><span class=\"pill\">${{i.track_id}}</span></p>
        <p>${{i.hypothesis}}</p>
        <p class=\"meta\">Distance: ${{metric.raw.distance}}; improvement: ${{metric.raw.improvement_pct}}%; route: ${{metric.raw.route_names.join(' -> ')}}</p>
        ${{art ? `<img src=\"${{art.path}}\" alt=\"${{art.label}}\">` : ''}}
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
body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f5f7fa; color: #1f2933; }
header { background: #111827; color: white; padding: 28px 36px; }
main { padding: 24px 36px 48px; }
a { color: #1d4ed8; }
.summary, .card { background: white; border: 1px solid #d9e2ec; border-radius: 14px; padding: 18px; box-shadow: 0 8px 24px rgba(15,23,42,.06); }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(320px, .8fr); gap: 18px; margin: 18px 0; }
.controls { display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }
select { padding: 8px 10px; border-radius: 8px; border: 1px solid #bcccdc; }
.cards { display: grid; gap: 18px; }
.card img { width: 100%; max-width: 760px; border: 1px solid #d9e2ec; border-radius: 10px; background: #fff; }
.meta { color: #52606d; font-size: 14px; }
.pill { display: inline-block; padding: 4px 9px; border-radius: 999px; background: #e0f2fe; color: #075985; font-size: 12px; margin-right: 6px; }
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
.bar-track { height: 14px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
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
  const numeric = (iteration.scores || []).find(score => typeof score.value === 'number');
  return numeric ? numeric.value : null;
};
const primaryArtifact = iteration =>
  (iteration.artifacts || []).find(a => a.label === 'Route SVG' || a.label === 'Preview SVG') ||
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
    const parent = node.iteration.parent_id ? nodeById.get(node.iteration.parent_id) : null;
    if (parent) lines.push(`<line x1="${parent.x + 72}" y1="${parent.y}" x2="${node.x - 72}" y2="${node.y}" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>`);
    const score = scoreFor(node.iteration);
    nodes.push(`<g>
      <rect x="${node.x - 74}" y="${node.y - 34}" width="148" height="68" rx="12" fill="#fff" stroke="${color(node.iteration.decision)}" stroke-width="3"/>
      <text x="${node.x}" y="${node.y - 12}" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a">${esc(node.iteration.id.replace(/^loop-/, ''))}</text>
      <text x="${node.x}" y="${node.y + 7}" text-anchor="middle" font-size="11" fill="#475569">${esc(node.iteration.track_id)}</text>
      <text x="${node.x}" y="${node.y + 24}" text-anchor="middle" font-size="11" fill="#475569">${score === null ? 'no score' : `score ${score}`}${node.iteration.id === bestId ? ' *' : ''}</text>
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
      const metric = i.scores.find(s => s.scorer_id === 'route-metrics') || i.scores[0] || {};
      const artifacts = (i.artifacts || []).map(a => `<tr><td>${esc(a.kind)}</td><td>${esc(a.label)}</td><td><a href="${esc(a.path)}">${esc(a.path)}</a></td><td><code>${esc((a.sha256 || '').slice(0, 16))}</code></td></tr>`).join('');
      const scores = (i.scores || []).map(s => `<tr><td>${esc(s.scorer_id)}</td><td>${esc(s.type)}</td><td>${esc(s.value)}</td><td><pre>${esc(JSON.stringify(s.per_criterion || {}, null, 2))}</pre></td></tr>`).join('');
      return `<article class="card">
        <h2>${esc(i.id)} ${i.id === bestId ? '*' : ''}</h2>
        <p><span class="pill ${esc(i.decision)}">${esc(i.decision)}</span><span class="pill">${esc(i.track_id)}</span><span class="pill">parent: ${esc(i.parent_id || 'root')}</span></p>
        <p>${esc(i.hypothesis)}</p>
        ${metric.raw ? `<p class="meta">Distance: ${esc(metric.raw.distance)}; improvement: ${esc(metric.raw.improvement_pct)}%; route: ${esc((metric.raw.route_names || []).join(' -> '))}</p>` : ''}
        ${art ? `<img src="${esc(art.path)}" alt="${esc(art.label)}">` : ''}
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
    loops = [
        {
            "id": "loop-01-baseline-order",
            "track": "quantitative-search",
            "title": "Baseline input-order route",
            "route": list(range(len(STOPS))) + [0],
            "hypothesis": "A baseline route establishes the objective distance to beat.",
            "next": "Try a greedy construction heuristic that chooses the nearest unvisited stop.",
        },
        {
            "id": "loop-02-nearest-neighbor",
            "track": "quantitative-search",
            "title": "Nearest-neighbor construction",
            "route": nearest_neighbor(),
            "hypothesis": "Choosing the nearest unvisited stop should cut obvious cross-town jumps.",
            "next": "Apply local edge swaps to remove route crossings left by the greedy heuristic.",
        },
    ]
    opt_route, improvements = two_opt(nearest_neighbor())
    loops.append(
        {
            "id": "loop-03-two-opt",
            "track": "quantitative-search",
            "title": f"2-opt local search ({improvements} edge improvements)",
            "route": opt_route,
            "hypothesis": "2-opt should shorten the route by reversing crossed or inefficient segments.",
            "next": "Use deterministic restarts to check whether the local optimum is robust.",
        }
    )
    synthesis_route, synthesis_meta = multistart_two_opt()
    loops.append(
        {
            "id": "loop-04-multistart-synthesis",
            "track": "synthesis",
            "title": "Deterministic multi-start 2-opt synthesis",
            "route": synthesis_route,
            "hypothesis": "Multiple deterministic starts should avoid over-trusting one local optimum.",
            "next": "Stop: deterministic restarts did not find a shorter valid route than the current champion.",
            "extra": synthesis_meta,
        }
    )

    baseline_length = route_length(loops[0]["route"])
    best_length = float("inf")
    best_id = None
    iterations = []

    for loop in loops:
        loop_dir = ROOT / loop["track"] / loop["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        route = loop["route"]
        length = route_length(route)
        valid = is_valid(route)
        if valid and length < best_length - 1e-9:
            decision = "new_best"
            best_length = length
            best_id = loop["id"]
            regression_note = "No regression; objective distance improved."
        elif valid:
            decision = "keep_for_synthesis"
            regression_note = "Valid but did not improve the current champion."
        else:
            decision = "reject"
            regression_note = "Rejected because the route failed the validity gate."
        metrics = {
            "distance": round(length, 2),
            "valid": valid,
            "improvement_pct": round((baseline_length - length) / baseline_length * 100, 2),
            "route": route,
            "route_names": [STOPS[idx][0] for idx in route],
            "regression_note": regression_note,
        }
        metrics.update(loop.get("extra", {}))
        metrics_path = loop_dir / "metrics.json"
        route_path = loop_dir / "route.svg"
        judge_path = loop_dir / "judge.md"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        write_route_svg(route, route_path, loop["title"])
        write_judge_note(judge_path, loop["id"], loop["title"], metrics, loop["next"])
        iterations.append(
            {
                "id": loop["id"],
                "track_id": loop["track"],
                "parent_id": None if len(iterations) == 0 else iterations[-1]["id"],
                "hypothesis": loop["hypothesis"],
                "commands": {
                    "build": "Select deterministic route-construction or route-improvement variant.",
                    "run": "python run_example.py",
                    "judge": "Read metrics.json; enforce validity gate; compare route_length to champion.",
                },
                "artifacts": [
                    {
                        "kind": "image",
                        "label": "Route SVG",
                        "path": f"{loop['track']}/{loop['id']}/route.svg",
                        "sha256": sha256(route_path),
                    },
                    {
                        "kind": "data",
                        "label": "Metrics JSON",
                        "path": f"{loop['track']}/{loop['id']}/metrics.json",
                        "sha256": sha256(metrics_path),
                    },
                    {
                        "kind": "markdown",
                        "label": "Judge note",
                        "path": f"{loop['track']}/{loop['id']}/judge.md",
                        "sha256": sha256(judge_path),
                    },
                ],
                "scores": [
                    {
                        "scorer_id": "route-metrics",
                        "type": "objective_command",
                        "value": score_from_length(length, baseline_length) if valid else 0,
                        "per_criterion": {
                            "route_length": round(length, 2),
                            "validity": 5 if valid else 0,
                            "reproducibility": 5,
                            "explainability": 4.5,
                        },
                        "notes": regression_note,
                        "raw": metrics,
                    }
                ],
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": loop["hypothesis"],
                    "action": loop["next"],
                    "evidence": f"{loop['track']}/{loop['id']}/route.svg and metrics.json",
                    "confidence": "high" if valid else "low",
                },
                "decision": decision,
                "stop_reason": None if loop["id"] != "loop-04-multistart-synthesis" else "Patience exhausted: no deterministic restart beat 2-opt champion.",
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "route-optimizer-worked-example",
        "title": "Route Optimizer Worked Example",
        "goal": "Minimize a deterministic delivery route while preserving validity and reproducibility.",
        "created_at": "2026-07-03T00:00:00Z",
        "budget": {"max_iters": 4, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 60},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["quantitative-search/**", "synthesis/**", "manifest.json", "viewer.html"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {"id": "route_length", "label": "Route length", "weight": 3},
            {"id": "validity", "label": "Visits every stop exactly once", "weight": 3},
            {"id": "reproducibility", "label": "Deterministic and rerunnable", "weight": 1},
            {"id": "explainability", "label": "Artifacts explain the improvement", "weight": 1},
        ],
        "scorers": [
            {
                "id": "route-metrics",
                "type": "objective_command",
                "command": "python run_example.py",
                "primary": True,
                "weight": 3,
            }
        ],
        "judge_panels": [],
        "governance": {
            "self_editing": {
                "requires_user_approval": True,
                "proposal_required": True,
                "approved_proposal_id": None,
            }
        },
        "tracks": [
            {
                "id": "quantitative-search",
                "label": "Quantitative route search",
                "hypothesis": "Simple deterministic heuristics can rapidly improve a route when objective distance is measurable.",
            },
            {
                "id": "synthesis",
                "label": "Synthesis and robustness check",
                "hypothesis": "Deterministic restarts test whether the local-search champion is robust.",
            },
        ],
        "iterations": iterations,
        "best": {
            "iteration_id": best_id,
            "score": round(score_from_length(best_length, baseline_length), 2),
            "why": f"Shortest valid route at {best_length:.2f} units.",
        },
        "rules": [
            {
                "trigger": "A primary objective metric exists.",
                "action": "Use it as a gate before qualitative explanation.",
                "confidence": "high",
            }
        ],
        "synthesis": "Nearest-neighbor removed obvious waste, 2-opt made the largest objective improvement, and deterministic restarts confirmed the champion rather than replacing it.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "viewer.html").write_text(viewer_html(manifest), encoding="utf-8")
    print(f"Best route: {best_id} at {best_length:.2f} units")


if __name__ == "__main__":
    main()
