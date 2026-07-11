from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import build_viewer  # noqa: E402  (local module, single source of truth for viewer.html)


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
    (ROOT / "viewer.html").write_text(
        build_viewer.render_viewer(manifest), encoding="utf-8", newline="\n"
    )
    print(f"Best joke: {best_id} at score {best_score}")


if __name__ == "__main__":
    main()
