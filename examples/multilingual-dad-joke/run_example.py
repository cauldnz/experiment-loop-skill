from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


CRITERIA = {
    "cross_language_equivalence": 1.5,
    "dad_joke_groan": 1.0,
    "brevity": 0.9,
    "cultural_portability": 1.2,
    "translation_naturalness": 1.4,
}


CANDIDATES = [
    {
        "id": "loop-01-gpt-virus",
        "title": "Computer virus",
        "track": "gpt-generator",
        "experiment_run": "run-a-gpt-5-5-generator",
        "model_source": "gpt-5.5",
        "parent_id": None,
        "parent_ids": [],
        "source_models": ["gpt-5.5"],
        "hypothesis": "A globally adopted technical double meaning can survive all four languages with minimal localization loss.",
        "concept": "Object personification plus literal computer-virus/medical-virus double meaning.",
        "joke": {
            "en": "Why did the computer go to the doctor? It had a virus.",
            "fr": "Pourquoi l'ordinateur est-il allé chez le médecin ? Il avait un virus.",
            "es": "¿Por qué fue la computadora al médico? Tenía un virus.",
            "ja": "なぜコンピューターはお医者さんに行ったの？ウイルスにかかったから。",
        },
        "lesson_action": "Keep globally standardized double meanings, but polish native-script translations and reduce fixture-style romanization.",
        "panel_scores": {
            "gpt-5.5-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 4, "translation_naturalness": 4},
            "gemini-3.1-pro-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
            "claude-sonnet-4.6-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
        },
        "dissent": "Strongest aggregate equivalence, but some risk that the joke is familiar and less fresh.",
        "decision_hint": "new_best",
    },
    {
        "id": "loop-02-gemini-wall-corner",
        "title": "Meet at the corner",
        "track": "gemini-generator",
        "experiment_run": "run-b-gemini-generator",
        "model_source": "gemini-3.1-pro-preview",
        "parent_id": None,
        "parent_ids": [],
        "source_models": ["gemini-3.1-pro-preview"],
        "hypothesis": "A universal spatial setup can avoid language-specific puns and still feel dad-joke simple.",
        "concept": "Anthropomorphized walls meet at a corner, which is both architectural geometry and a meeting place.",
        "joke": {
            "en": "What did one wall say to the other wall? I'll meet you at the corner.",
            "fr": "Que dit un mur à un autre mur ? « On se retrouve au coin. »",
            "es": "¿Qué le dice una pared a otra pared? « Nos vemos en la esquina. »",
            "ja": "ひとつの壁がもうひとつの壁に何と言った？「角で待ち合わせよう。」",
        },
        "lesson_action": "Preserve the wall/corner idea as a charming runner-up; watch for corner-word nuance across languages.",
        "panel_scores": {
            "gpt-5.5-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
            "gemini-3.1-pro-judge": {"cross_language_equivalence": 4, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 4},
            "claude-sonnet-4.6-judge": {"cross_language_equivalence": 4, "dad_joke_groan": 3, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 4},
        },
        "dissent": "One judge preferred this candidate for charm and universality, but two judges saw slightly weaker translation equivalence.",
        "decision_hint": "keep_for_synthesis",
    },
    {
        "id": "loop-03-claude-two-places",
        "title": "Two places",
        "track": "claude-generator",
        "experiment_run": "run-c-claude-generator",
        "model_source": "claude-sonnet-4.6",
        "parent_id": None,
        "parent_ids": [],
        "source_models": ["claude-sonnet-4.6"],
        "hypothesis": "A conceptual ambiguity between body locations and geographic locations can work without phonetic wordplay.",
        "concept": "The doctor interprets 'two places' as travel destinations instead of fracture locations.",
        "joke": {
            "en": "I told my doctor I broke my arm in two places. He told me to stop going to those places.",
            "fr": "J'ai dit à mon médecin que je m'étais cassé le bras en deux endroits. Il m'a dit d'arrêter d'aller dans ces endroits.",
            "es": "Le dije al médico que me había roto el brazo en dos lugares. Me dijo que dejara de ir a esos lugares.",
            "ja": "「先生、2か所で腕を骨折しました」と言ったら、「じゃあ、その場所には行かないようにしなさい」と言われました。",
        },
        "lesson_action": "Keep conceptual ambiguity in mind, but avoid long setups that become forced in Japanese and Romance-language translations.",
        "panel_scores": {
            "gpt-5.5-judge": {"cross_language_equivalence": 4, "dad_joke_groan": 4, "brevity": 3, "cultural_portability": 4, "translation_naturalness": 3},
            "gemini-3.1-pro-judge": {"cross_language_equivalence": 3, "dad_joke_groan": 5, "brevity": 3, "cultural_portability": 4, "translation_naturalness": 3},
            "claude-sonnet-4.6-judge": {"cross_language_equivalence": 4, "dad_joke_groan": 5, "brevity": 3, "cultural_portability": 4, "translation_naturalness": 3},
        },
        "dissent": "Best groan factor, but weakest brevity and naturalness across the four languages.",
        "decision_hint": "keep_for_synthesis",
    },
    {
        "id": "loop-04-synthesis-polished-virus",
        "title": "Polished universal-virus joke",
        "track": "synthesis",
        "experiment_run": "run-d-cross-model-synthesis",
        "model_source": "synthesis-from-panel",
        "parent_id": "loop-01-gpt-virus",
        "parent_ids": ["loop-01-gpt-virus", "loop-02-gemini-wall-corner", "loop-03-claude-two-places"],
        "source_models": ["gpt-5.5", "gemini-3.1-pro-preview", "claude-sonnet-4.6"],
        "hypothesis": "Use the panel's aggregate winner, keep the globally shared virus double meaning, and polish the wording into native scripts.",
        "concept": "A computer gets medical advice because it has a virus; the biological/digital double meaning is shared across all target languages.",
        "joke": {
            "en": "Why did the computer go to the doctor? It had a virus.",
            "fr": "Pourquoi l'ordinateur est-il allé chez le médecin ? Il avait un virus.",
            "es": "¿Por qué fue la computadora al médico? Tenía un virus.",
            "ja": "なぜコンピューターはお医者さんに行ったの？ウイルスにかかったから。",
        },
        "lesson_action": "Stop: the candidate is brief, globally portable, and equally legible after native-script polishing.",
        "panel_scores": {
            "gpt-5.5-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
            "gemini-3.1-pro-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
            "claude-sonnet-4.6-judge": {"cross_language_equivalence": 5, "dad_joke_groan": 4, "brevity": 5, "cultural_portability": 5, "translation_naturalness": 5},
        },
        "dissent": "Panel consensus after polishing: the joke is not the freshest, but it is the most equal across all four languages.",
        "decision_hint": "new_best",
    },
]


JUDGE_RATIONALES = {
    "gpt-5.5-judge": {
        "winner": "loop-02-gemini-wall-corner before synthesis; accepted loop-04 after native-script polish.",
        "rationale": "Wall/corner had the most charm, but the polished virus joke became more translation-stable while staying short.",
    },
    "gemini-3.1-pro-judge": {
        "winner": "loop-01-gpt-virus and loop-04-synthesis-polished-virus",
        "rationale": "The virus double meaning is globally standardized and requires the least language-specific forcing.",
    },
    "claude-sonnet-4.6-judge": {
        "winner": "loop-01-gpt-virus and loop-04-synthesis-polished-virus",
        "rationale": "Computer virus is familiar, but it survives across all four languages with high naturalness and brevity.",
    },
}


def average_scores(panel_scores: dict[str, dict[str, float]]) -> dict[str, float]:
    return {
        criterion: round(sum(scores[criterion] for scores in panel_scores.values()) / len(panel_scores), 2)
        for criterion in CRITERIA
    }


def weighted_score(scores: dict[str, float]) -> float:
    return round(sum(scores[k] * CRITERIA[k] for k in CRITERIA) / sum(CRITERIA.values()), 2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete(candidate: dict[str, object]) -> bool:
    joke = candidate["joke"]
    return all(isinstance(joke.get(language), str) and bool(joke[language].strip()) for language in ["en", "fr", "es", "ja"])


def write_joke_markdown(candidate: dict[str, object], path: Path) -> None:
    joke = candidate["joke"]
    text = f"""# {candidate['title']}

## Concept

{candidate['concept']}

## English

{joke['en']}

## French

{joke['fr']}

## Spanish

{joke['es']}

## Japanese

{joke['ja']}
"""
    path.write_text(text, encoding="utf-8")


def write_candidate_json(candidate: dict[str, object], path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": candidate["id"],
                "title": candidate["title"],
                "model_source": candidate["model_source"],
                "source_models": candidate["source_models"],
                "concept": candidate["concept"],
                "joke": candidate["joke"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_judge_notes(loop_dir: Path, candidate: dict[str, object], averaged: dict[str, float], total: float, decision: str) -> list[str]:
    written = []
    for judge_id, scores in candidate["panel_scores"].items():
        note = f"""# Judge: {judge_id} for {candidate['id']}

## Evidence inspected
- `joke.md`
- `candidate.json`

## Scores
{chr(10).join(f"- {criterion}: {value}" for criterion, value in scores.items())}

## Rationale
{JUDGE_RATIONALES[judge_id]['rationale']}

## Winner tendency
{JUDGE_RATIONALES[judge_id]['winner']}
"""
        path = loop_dir / f"judge-{judge_id}.md"
        path.write_text(note, encoding="utf-8")
        written.append(path.name)

    aggregate = f"""# Judge: aggregate for {candidate['id']}

## What changed
- {candidate['hypothesis']}

## Evidence inspected
- `joke.md`
- `candidate.json`
- three independent model-judge notes

## Scores
{chr(10).join(f"- {criterion}: {value}" for criterion, value in averaged.items())}
- weighted_total: {total}

## Judge mode
- panel: three model-backed judges with preserved dissent.

## Panel notes
- gpt-5.5-judge: initially preferred the wall/corner joke for charm.
- gemini-3.1-pro-judge: preferred the virus joke for global semantic portability.
- claude-sonnet-4.6-judge: preferred the virus joke for translation naturalness and brevity.
- dissent / disagreement: {candidate['dissent']}

## What improved
- {candidate['lesson_action']}

## What failed / regressed
- {'No material regression; this candidate improves the current champion.' if decision == 'new_best' else 'Useful evidence, but did not beat the current champion on aggregate weighted score.'}

## Next hypothesis
- {candidate['lesson_action']}
"""
    aggregate_path = loop_dir / "judge-aggregate.md"
    aggregate_path.write_text(aggregate, encoding="utf-8")
    written.append(aggregate_path.name)
    return written


def viewer_html(manifest: dict[str, object]) -> str:
    data = json.dumps(manifest, indent=2, ensure_ascii=False).replace("</", "<\\/")
    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f8fafc; color: #172033; }
header { background: #111827; color: white; padding: 30px 38px; }
main { padding: 24px 38px 54px; }
a { color: #0f766e; }
.summary, .card { background: white; border: 1px solid #dde3ee; border-radius: 16px; padding: 18px; box-shadow: 0 10px 30px rgba(15,23,42,.07); }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(320px, .9fr); gap: 18px; margin: 18px 0; }
.controls { display: flex; gap: 12px; align-items: center; margin: 18px 0; flex-wrap: wrap; }
select { padding: 8px 10px; border-radius: 8px; border: 1px solid #b8c2d6; }
.cards { display: grid; gap: 18px; }
.translations { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 14px 0; }
.translation { border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; background: #f8fafc; }
.translation strong { display: block; color: #475569; margin-bottom: 8px; }
.meta { color: #5b6475; font-size: 14px; }
.pill { display: inline-block; padding: 4px 9px; border-radius: 999px; background: #ccfbf1; color: #115e59; font-size: 12px; margin-right: 6px; margin-bottom: 4px; }
.new_best { background: #dcfce7; color: #166534; }
.reject, .failed { background: #fee2e2; color: #991b1b; }
.keep_for_synthesis { background: #fef3c7; color: #92400e; }
.needs_human_review { background: #ede9fe; color: #5b21b6; }
pre { white-space: pre-wrap; overflow: auto; background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
td, th { border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: left; vertical-align: top; }
summary { cursor: pointer; font-weight: 750; }
.graph-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
#graph { min-width: 980px; width: 100%; height: 330px; display: block; }
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
    <div><strong>Model experiment panel</strong><br><span id="modelPanel"></span></div>
    <div><strong>Judging</strong><br><span id="scorerSummary"></span></div>
  </section>
  <section class="grid">
    <div class="card">
      <h2>Experiment graph</h2>
      <p class="meta">Lineage comes from <code>parent_ids</code>; the synthesis node has all model candidates as parents.</p>
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
  const preferred = (iteration.scores || []).find(score => score.scorer_id === 'multi-model-judge-panel' && typeof score.value === 'number');
  const numeric = preferred || (iteration.scores || []).find(score => typeof score.value === 'number');
  return numeric ? numeric.value : null;
};
document.getElementById('best').textContent = manifest.best ? `${manifest.best.iteration_id} - score ${manifest.best.score} (${manifest.best.why})` : 'none';
document.getElementById('iterationCount').textContent = manifest.iterations.length;
document.getElementById('modelPanel').textContent = (manifest.model_experiment_panels || []).map(p => `${p.id}: ${p.models.join(', ')}`).join('; ');
document.getElementById('scorerSummary').textContent = (manifest.scorers || []).map(s => `${s.id} (${s.type}${s.primary ? ', primary' : ''})`).join('; ') || 'none';
document.getElementById('manifestJson').textContent = JSON.stringify(manifest, null, 2);
document.getElementById('scorecard').innerHTML = manifest.scorecard.map(c => `<tr><th>${esc(c.label)}</th><td>weight ${esc(c.weight)}</td><td><code>${esc(c.id)}</code></td></tr>`).join('');
for (const value of [...new Set(manifest.iterations.map(i => i.decision))]) decision.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
for (const value of manifest.tracks.map(t => t.id)) track.insertAdjacentHTML('beforeend', `<option value="${esc(value)}">${esc(value)}</option>`);
function renderGraph() {
  const tracks = manifest.tracks.map(t => t.id);
  const nodeById = new Map();
  const width = 1040;
  const height = Math.max(300, tracks.length * 78 + 86);
  manifest.iterations.forEach((iteration, index) => {
    const isSynthesis = iteration.track_id === 'synthesis';
    nodeById.set(iteration.id, { iteration, x: isSynthesis ? 850 : 150 + index * 210, y: 60 + Math.max(0, tracks.indexOf(iteration.track_id)) * 78 });
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
      <rect x="${node.x - 82}" y="${node.y - 34}" width="164" height="68" rx="12" fill="#fff" stroke="${color(node.iteration.decision)}" stroke-width="3"/>
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
      const candidate = i.output || {};
      const joke = candidate.joke || {};
      const parents = i.parent_ids && i.parent_ids.length ? i.parent_ids : (i.parent_id ? [i.parent_id] : ['root']);
      const artifacts = (i.artifacts || []).map(a => `<tr><td>${esc(a.kind)}</td><td>${esc(a.label)}</td><td><a href="${esc(a.path)}">${esc(a.path)}</a></td><td><code>${esc((a.sha256 || '').slice(0, 16))}</code></td></tr>`).join('');
      const scores = (i.scores || []).map(s => `<tr><td>${esc(s.scorer_id)}</td><td>${esc(s.type)}</td><td>${esc(s.value)}</td><td><pre>${esc(JSON.stringify(s.per_criterion || {}, null, 2))}</pre></td></tr>`).join('');
      return `<article class="card">
        <h2>${esc(i.id)} ${i.id === bestId ? '*' : ''}</h2>
        <p><span class="pill ${esc(i.decision)}">${esc(i.decision)}</span><span class="pill">${esc(i.track_id)}</span><span class="pill">source: ${esc(i.model_source || '')}</span><span class="pill">parents: ${esc(parents.join(', '))}</span></p>
        <p>${esc(i.hypothesis)}</p>
        <div class="translations">
          <div class="translation"><strong>English</strong>${esc(joke.en)}</div>
          <div class="translation"><strong>French</strong>${esc(joke.fr)}</div>
          <div class="translation"><strong>Spanish</strong>${esc(joke.es)}</div>
          <div class="translation"><strong>Japanese</strong>${esc(joke.ja)}</div>
        </div>
        <p class="meta"><strong>Concept:</strong> ${esc(candidate.concept || '')}</p>
        <h3>Lesson</h3><pre>${esc(i.lesson.trigger)}\nAction: ${esc(i.lesson.action)}\nEvidence: ${esc(i.lesson.evidence)}\nConfidence: ${esc(i.lesson.confidence)}</pre>
        <details open>
          <summary>Metadata and provenance</summary>
          <table><tbody>
            <tr><th>Build</th><td>${esc(i.commands.build)}</td></tr>
            <tr><th>Run</th><td>${esc(i.commands.run)}</td></tr>
            <tr><th>Judge</th><td>${esc(i.commands.judge)}</td></tr>
            <tr><th>Source models</th><td>${esc((i.source_models || []).join(', '))}</td></tr>
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

    for candidate in CANDIDATES:
        loop_dir = ROOT / candidate["track"] / candidate["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        joke_path = loop_dir / "joke.md"
        candidate_path = loop_dir / "candidate.json"
        write_joke_markdown(candidate, joke_path)
        write_candidate_json(candidate, candidate_path)

        is_complete = complete(candidate)
        averaged = average_scores(candidate["panel_scores"])
        total = weighted_score(averaged) if is_complete else 0.0
        decision = "new_best" if total > best_score else "keep_for_synthesis"
        if decision == "new_best":
            best_score = total
            best_id = candidate["id"]

        note_names = write_judge_notes(loop_dir, candidate, averaged, total, decision)
        artifacts = [
            {"kind": "markdown", "label": "Joke draft", "path": f"{candidate['track']}/{candidate['id']}/joke.md", "sha256": sha256(joke_path)},
            {"kind": "data", "label": "Candidate JSON", "path": f"{candidate['track']}/{candidate['id']}/candidate.json", "sha256": sha256(candidate_path)},
        ]
        for note_name in note_names:
            note_path = loop_dir / note_name
            artifacts.append({"kind": "markdown", "label": note_name, "path": f"{candidate['track']}/{candidate['id']}/{note_name}", "sha256": sha256(note_path)})

        iterations.append(
            {
                "id": candidate["id"],
                "track_id": candidate["track"],
                "experiment_run": candidate["experiment_run"],
                "model_source": candidate["model_source"],
                "source_models": candidate["source_models"],
                "parent_id": candidate["parent_id"],
                "parent_ids": candidate["parent_ids"],
                "hypothesis": candidate["hypothesis"],
                "commands": {
                    "build": "Generate or synthesize a multilingual joke candidate from the model experiment panel.",
                    "run": "python run_example.py",
                    "judge": "Check text completeness, then aggregate independent multi-model judge notes.",
                },
                "artifacts": artifacts,
                "output": {
                    "title": candidate["title"],
                    "concept": candidate["concept"],
                    "joke": candidate["joke"],
                },
                "scores": [
                    {
                        "scorer_id": "language-completeness",
                        "type": "objective_command",
                        "value": 5 if is_complete else 0,
                        "per_criterion": {language: bool(candidate["joke"][language]) for language in ["en", "fr", "es", "ja"]},
                        "notes": "All four language variants are present." if is_complete else "One or more language variants are missing.",
                    },
                    {
                        "scorer_id": "multi-model-judge-panel",
                        "type": "llm_rubric",
                        "judge_panel": "multilingual-joke-panel",
                        "value": total,
                        "per_criterion": averaged,
                        "notes": candidate["dissent"],
                    },
                ],
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": candidate["hypothesis"],
                    "action": candidate["lesson_action"],
                    "evidence": f"{candidate['track']}/{candidate['id']}/joke.md, candidate.json, and model judge notes",
                    "confidence": "high" if decision == "new_best" else "medium",
                },
                "decision": decision,
                "stop_reason": "Synthesis reached the best cross-language equality score." if candidate["id"] == "loop-04-synthesis-polished-virus" else None,
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "multilingual-dad-joke-worked-example",
        "title": "Multilingual Dad Joke Worked Example",
        "goal": "Use a multi-model experiment panel and multi-model judge panel to create a dad joke that works in English, French, Spanish, and Japanese.",
        "created_at": "2026-07-06T00:00:00Z",
        "budget": {"max_iters": 4, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 60},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["gpt-generator/**", "gemini-generator/**", "claude-generator/**", "synthesis/**", "manifest.json", "viewer.html"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {"id": "cross_language_equivalence", "label": "Cross-language equivalence", "weight": CRITERIA["cross_language_equivalence"]},
            {"id": "dad_joke_groan", "label": "Dad-joke groan", "weight": CRITERIA["dad_joke_groan"]},
            {"id": "brevity", "label": "Brevity", "weight": CRITERIA["brevity"]},
            {"id": "cultural_portability", "label": "Cultural portability", "weight": CRITERIA["cultural_portability"]},
            {"id": "translation_naturalness", "label": "Translation naturalness", "weight": CRITERIA["translation_naturalness"]},
        ],
        "scorers": [
            {"id": "language-completeness", "type": "objective_command", "command": "python run_example.py", "primary": True, "weight": 1},
            {"id": "multi-model-judge-panel", "type": "llm_rubric", "judge_panel": "multilingual-joke-panel", "weight": 2},
        ],
        "model_experiment_panels": [
            {
                "id": "generator-panel",
                "harness": "GitHub Copilot task agents with model overrides",
                "models": ["gpt-5.5", "gemini-3.1-pro-preview", "claude-sonnet-4.6"],
                "purpose": "Generate competing candidates from model-diverse language strategies before synthesis.",
            }
        ],
        "judge_panels": [
            {
                "id": "multilingual-joke-panel",
                "blind": True,
                "flip_pairwise_order": False,
                "aggregation": "weighted_mean_with_dissent",
                "judges": [
                    {"id": "gpt-5.5-judge", "model": "gpt-5.5", "role": "cross-language equivalence and concise joke structure"},
                    {"id": "gemini-3.1-pro-judge", "model": "gemini-3.1-pro-preview", "role": "semantic portability and translation naturalness"},
                    {"id": "claude-sonnet-4.6-judge", "model": "claude-sonnet-4.6", "role": "groan factor, brevity, and tradeoff analysis"},
                ],
            }
        ],
        "governance": {"self_editing": {"requires_user_approval": True, "proposal_required": True, "approved_proposal_id": None}},
        "tracks": [
            {"id": "gpt-generator", "label": "Run A - GPT-style generator", "hypothesis": "Globally standardized double meanings can be robust across languages."},
            {"id": "gemini-generator", "label": "Run B - Gemini-style generator", "hypothesis": "Universal physical setups can avoid language-specific puns."},
            {"id": "claude-generator", "label": "Run C - Claude-style generator", "hypothesis": "Conceptual ambiguity can produce stronger dad-joke misdirection."},
            {"id": "synthesis", "label": "Run D - cross-model synthesis", "hypothesis": "Judge dissent can guide a polished final candidate."},
        ],
        "iterations": iterations,
        "best": {"iteration_id": best_id, "score": best_score, "why": "Best weighted panel score while passing the four-language completeness gate."},
        "rules": [
            {
                "trigger": "Multilingual language tasks can reward stale but highly portable jokes.",
                "action": "Record judge dissent explicitly so readers can see the tradeoff between freshness and cross-language equality.",
                "confidence": "high",
            }
        ],
        "synthesis": "The generator panel produced three different strategies: a globally shared virus double meaning, a universal wall/corner spatial joke, and a stronger-groan doctor ambiguity. The judge panel disagreed, with one model preferring the wall/corner candidate for charm and two models preferring the virus candidate for equal translation. The synthesis loop accepted the aggregate winner and polished the Japanese into native script while preserving the exact joke mechanic.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "viewer.html").write_text(viewer_html(manifest), encoding="utf-8")
    print(f"Best joke: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
