from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent


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
        "scores": {"visual_hierarchy": 4.4, "brand_distinctiveness": 3.6, "information_clarity": 3.9, "system_coherence": 3.6, "polish": 3.8},
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
        "scores": {"visual_hierarchy": 4.7, "brand_distinctiveness": 3.9, "information_clarity": 4.6, "system_coherence": 4.2, "polish": 4.1},
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
        "scores": {"visual_hierarchy": 3.5, "brand_distinctiveness": 4.8, "information_clarity": 3.3, "system_coherence": 3.8, "polish": 4.0},
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
        "scores": {"visual_hierarchy": 4.0, "brand_distinctiveness": 4.7, "information_clarity": 4.0, "system_coherence": 4.4, "polish": 4.2},
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
        "scores": {"visual_hierarchy": 4.6, "brand_distinctiveness": 4.6, "information_clarity": 4.5, "system_coherence": 4.6, "polish": 4.4},
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
        "next": "Stop: the final card has the clearest hierarchy, strongest reusable system, and most polished composition.",
        "palette": {"bg": "#0b1020", "bg2": "#134e4a", "panel": "#fff7ed", "text": "#fff7ed", "ink": "#111827", "muted": "#99f6e4", "accent": "#14b8a6", "accent2": "#f97316"},
        "layout": "polished",
        "scores": {"visual_hierarchy": 4.9, "brand_distinctiveness": 4.8, "information_clarity": 4.8, "system_coherence": 4.9, "polish": 4.9},
    },
]

WEIGHTS = {
    "visual_hierarchy": 1.4,
    "brand_distinctiveness": 1.1,
    "information_clarity": 1.2,
    "system_coherence": 1.0,
    "polish": 1.3,
}


def weighted_score(scores: dict[str, float]) -> float:
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS) / sum(WEIGHTS.values()), 2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_card_svg(variant: dict[str, object], path: Path) -> None:
    p = variant["palette"]
    layout = variant["layout"]
    title = variant["title"]
    show_orbits = layout in {"orbital", "synthesis", "polished"}
    show_ribbons = layout in {"ribbon", "synthesis", "polished"}
    show_modules = layout in {"editorial-system", "ribbon", "synthesis", "polished"}
    dense_polish = layout == "polished"
    orbital_opacity = "0.55" if layout == "orbital" else "0.28"
    ribbon_opacity = "0.9" if layout in {"ribbon", "polished"} else "0.55"
    title_size = 82 if layout in {"editorial", "editorial-system"} else 70
    hero_y = 178 if show_modules else 206

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

    panel_x = 596 if show_modules else 614
    panel_w = 270 if show_modules else 240
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
        module_x = 372
        module_y = 326 if dense_polish else 346
        modules = [("01", "Frame goal"), ("02", "Run variants"), ("03", "Synthesize")]
        for index, (num, label) in enumerate(modules):
            y = module_y + index * 44
            parts.extend(
                [
                    f'<rect x="{module_x}" y="{y}" width="178" height="32" rx="16" fill="#ffffff" opacity="{0.16 if dense_polish else 0.12}"/>',
                    f'<text x="{module_x + 16}" y="{y + 22}" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="800" fill="{p["accent2"]}">{num}</text>',
                    f'<text x="{module_x + 52}" y="{y + 22}" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="650" fill="{p["text"]}">{label}</text>',
                ]
            )

    parts.extend(
        [
            f'<text x="86" y="456" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="700" fill="{p["muted"]}">VARIANT / {html.escape(str(title)).upper()}</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(parts), encoding="utf-8")


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
    path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def write_judge_notes(loop_dir: Path, variant: dict[str, object], total: float, decision: str) -> None:
    scores = variant["scores"]
    fast = f"""# Judge: fast-critic for {variant['id']}

## Evidence inspected
- `card.svg`
- `tokens.json`

## Scores
- visual_hierarchy: {scores['visual_hierarchy']} - scan path and title clarity.
- information_clarity: {scores['information_clarity']} - event details and CTA readability.

## Rationale
The card is {'ready to promote' if total >= 4.6 else 'useful but still has a visible tradeoff'} for quick visual review.
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
    aggregate = f"""# Judge: aggregate for {variant['id']}

## What changed
- {variant['hypothesis']}

## Evidence inspected
- `card.svg`
- `tokens.json`
- independent fast/design critic notes

## Scores
- visual_hierarchy: {scores['visual_hierarchy']}
- brand_distinctiveness: {scores['brand_distinctiveness']}
- information_clarity: {scores['information_clarity']}
- system_coherence: {scores['system_coherence']}
- polish: {scores['polish']}
- weighted_total: {total}

## Judge mode
- panel, with objective SVG validity checks as supporting gates.

## Panel notes
- fast-critic: focused on scan path, event detail clarity, and CTA visibility.
- design-critic: focused on identity, component reuse, and visual finish.
- dissent / disagreement: none material; both critics agree this is `{decision}`.

## What improved
- {variant['next']}

## What failed / regressed
- {'No material regression versus the previous champion.' if decision == 'new_best' else 'Did not beat the current champion, but remains useful synthesis input.'}

## Next hypothesis
- {variant['next']}
"""
    (loop_dir / "judge-fast-critic.md").write_text(fast, encoding="utf-8")
    (loop_dir / "judge-design-critic.md").write_text(design, encoding="utf-8")
    (loop_dir / "judge-aggregate.md").write_text(aggregate, encoding="utf-8")


def viewer_html(manifest: dict[str, object]) -> str:
    data = json.dumps(manifest, indent=2).replace("</", "<\\/")
    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f7f7fb; color: #172033; }
header { background: #0b1020; color: white; padding: 30px 38px; }
main { padding: 24px 38px 54px; }
a { color: #0f766e; }
.summary, .card { background: white; border: 1px solid #dde3ee; border-radius: 16px; padding: 18px; box-shadow: 0 10px 30px rgba(15,23,42,.07); }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr); gap: 18px; margin: 18px 0; }
.controls { display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }
select { padding: 8px 10px; border-radius: 8px; border: 1px solid #b8c2d6; }
.cards { display: grid; gap: 18px; }
.artifact-previews { display: grid; gap: 12px; }
.artifact-preview-title { margin: 0 0 6px; color: #5b6475; font-size: 13px; font-weight: 750; }
.card img { width: 100%; max-width: 960px; border: 1px solid #dde3ee; border-radius: 14px; background: #fff; }
.meta { color: #5b6475; font-size: 14px; }
.pill { display: inline-block; padding: 4px 9px; border-radius: 999px; background: #ccfbf1; color: #115e59; font-size: 12px; margin-right: 6px; }
.new_best { background: #dcfce7; color: #166534; }
.reject, .failed { background: #fee2e2; color: #991b1b; }
.keep_for_synthesis { background: #fef3c7; color: #92400e; }
.needs_human_review { background: #ede9fe; color: #5b21b6; }
pre { white-space: pre-wrap; overflow: auto; background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
td, th { border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: left; vertical-align: top; }
summary { cursor: pointer; font-weight: 750; }
.graph-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
#graph { min-width: 1080px; width: 100%; height: 330px; display: block; }
.timeline { display: grid; gap: 8px; }
.bar-row { display: grid; grid-template-columns: 230px 1fr 52px; gap: 10px; align-items: center; }
.bar-track { height: 14px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
.bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #14b8a6, #f97316); }
.json-panel { max-height: 520px; }
@media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
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
      <p class="meta">Lineage comes from <code>parent_ids</code>; colors show decisions and the star marks the champion.</p>
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
const primaryArtifact = iteration => (iteration.artifacts || []).find(a => a.label === 'Card SVG') || (iteration.artifacts || []).find(a => a.kind === 'image');
document.getElementById('best').textContent = manifest.best ? `${manifest.best.iteration_id} - score ${manifest.best.score} (${manifest.best.why})` : 'none';
document.getElementById('iterationCount').textContent = manifest.iterations.length;
document.getElementById('trackCount').textContent = manifest.tracks.map(t => t.label || t.id).join(', ');
document.getElementById('scorerSummary').textContent = (manifest.scorers || []).map(s => `${s.id} (${s.type}${s.primary ? ', primary' : ''})`).join('; ') || 'none';
document.getElementById('manifestJson').textContent = JSON.stringify(manifest, null, 2);
document.getElementById('scorecard').innerHTML = manifest.scorecard.map(c => `<tr><th>${esc(c.label)}</th><td>weight ${esc(c.weight)}</td><td><code>${esc(c.id)}</code></td></tr>`).join('');
for (const value of [...new Set(manifest.iterations.map(i => i.decision))]) decision.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
for (const value of manifest.tracks.map(t => t.id)) track.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
function renderGraph() {
  const tracks = manifest.tracks.map(t => t.id);
  const nodeById = new Map();
  const width = Math.max(1080, manifest.iterations.length * 210 + 160);
  const height = Math.max(300, tracks.length * 92 + 92);
  manifest.iterations.forEach((iteration, index) => nodeById.set(iteration.id, { iteration, x: 96 + index * 205, y: 62 + Math.max(0, tracks.indexOf(iteration.track_id)) * 92 }));
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
      <text x="${node.x}" y="${node.y + 7}" text-anchor="middle" font-size="11" fill="#5b6475">${esc(node.iteration.track_id)}</text>
      <text x="${node.x}" y="${node.y + 24}" text-anchor="middle" font-size="11" fill="#5b6475">${score === null ? 'no score' : `score ${score}`}${node.iteration.id === bestId ? ' *' : ''}</text>
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
      const tokens = (i.artifacts || []).find(a => a.label === 'Design tokens');
      const parents = i.parent_ids && i.parent_ids.length ? i.parent_ids : (i.parent_id ? [i.parent_id] : ['root']);
      const artifacts = (i.artifacts || []).map(a => `<tr><td>${esc(a.kind)}</td><td>${esc(a.label)}</td><td><a href="${esc(a.path)}">${esc(a.path)}</a></td><td><code>${esc((a.sha256 || '').slice(0, 16))}</code></td></tr>`).join('');
      const scores = (i.scores || []).map(s => `<tr><td>${esc(s.scorer_id)}</td><td>${esc(s.type)}</td><td>${esc(s.value)}</td><td><pre>${esc(JSON.stringify(s.per_criterion || {}, null, 2))}</pre></td></tr>`).join('');
      return `<article class="card">
        <h2>${esc(i.id)} ${i.id === bestId ? '*' : ''}</h2>
        <p><span class="pill ${esc(i.decision)}">${esc(i.decision)}</span><span class="pill">${esc(i.track_id)}</span><span class="pill">run: ${esc(i.experiment_run || i.track_id)}</span><span class="pill">parents: ${esc(parents.join(', '))}</span></p>
        <p>${esc(i.hypothesis)}</p>
        ${art ? `<div class="artifact-previews"><p class="artifact-preview-title">${esc(art.label)}</p><img src="${esc(art.path)}" alt="${esc(art.label)}"></div>` : ''}
        ${tokens ? `<p class="meta">Tokens: <a href="${esc(tokens.path)}">${esc(tokens.path)}</a></p>` : ''}
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
    for variant in VARIANTS:
        loop_dir = ROOT / variant["track"] / variant["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        card_path = loop_dir / "card.svg"
        tokens_path = loop_dir / "tokens.json"
        write_card_svg(variant, card_path)
        write_tokens(variant, tokens_path)
        valid_svg = validate_svg(card_path)
        total = weighted_score(variant["scores"]) if valid_svg else 0.0
        decision = "new_best" if total > best_score else "keep_for_synthesis"
        if decision == "new_best":
            best_score = total
            best_id = variant["id"]
        write_judge_notes(loop_dir, variant, total, decision)
        artifacts = [
            {"kind": "image", "label": "Card SVG", "path": f"{variant['track']}/{variant['id']}/card.svg", "sha256": sha256(card_path)},
            {"kind": "data", "label": "Design tokens", "path": f"{variant['track']}/{variant['id']}/tokens.json", "sha256": sha256(tokens_path)},
        ]
        for name in ["judge-fast-critic.md", "judge-design-critic.md", "judge-aggregate.md"]:
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
                    "judge": "Validate SVG, then aggregate independent qualitative judge notes.",
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
                        "scorer_id": "design-panel",
                        "type": "llm_rubric",
                        "judge_panel": "design-panel",
                        "value": total,
                        "per_criterion": variant["scores"],
                        "notes": "Aggregated from fast-critic and design-critic judge notes.",
                    },
                ],
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": variant["hypothesis"],
                    "action": variant["next"],
                    "evidence": f"{variant['track']}/{variant['id']}/card.svg, tokens.json, and panel notes",
                    "confidence": "high" if decision == "new_best" else "medium",
                },
                "decision": decision,
                "stop_reason": "Cross-run synthesis reached production-polish target." if variant["id"] == "loop-04-production-polish" else None,
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "visual-design-system-worked-example",
        "title": "SVG Visual Design System Worked Example",
        "goal": "Run two independent SVG visual design experiments, then synthesize their best lessons into a polished event-card system.",
        "created_at": "2026-07-06T00:00:00Z",
        "budget": {"max_iters": 6, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 60},
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
        ],
        "scorers": [
            {"id": "svg-validity", "type": "objective_command", "command": "python run_example.py", "primary": True, "weight": 1},
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
        "best": {"iteration_id": best_id, "score": best_score, "why": "Best panel score while passing SVG validity gates and combining both source-run strengths."},
        "rules": [
            {
                "trigger": "Qualitative visual work still needs auditable artifacts.",
                "action": "Commit the generated SVG, tokens, judge notes, manifest, and viewer so the design can be inspected without rerunning.",
                "confidence": "high",
            }
        ],
        "synthesis": "Run A provided the strongest hierarchy and information clarity. Run B provided a more distinctive visual language. Run C combined the editorial card system with signal ribbons, then polished spacing, contrast, and component rhythm into the final champion.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "viewer.html").write_text(viewer_html(manifest), encoding="utf-8")
    print(f"Best design: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
