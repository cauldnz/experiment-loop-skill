# Multilingual dad-joke Experiment

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
node ..\.github\skills\experiment-loop\references\navigation_judge\cli.mjs --viewer viewer.html --out .
python -m references.evidence_gate .
```

Run the final two commands from the repository root with the skill root on `PYTHONPATH`, or set `EXPERIMENT_LOOP_SKILL_ROOT` for the Viewer adapter.

## Feature surface demonstrated

**Viewer capabilities:** fixed Overview, Topology, and Compare views; authored milestones; multi-parent lineage; per-Loop Artifact inspection; full prompt/input-feedback/judge-feedback/next-prompt chains; criterion timelines; blind-panel dissent; evidence-linked Champion reasons and caveats; structured generation provenance; native-script rendering; objective gate state; and offline deterministic rebuilds.

**Manifest capabilities:** schema v1.1 Problem framing with exact original Prompt evidence; authoritative generation fields and actual model IDs; explicit scorer semantics and a blocking objective gate; blind judge panels; comparable scorecards; structured Artifact presentation metadata; eight Loops with `parent_ids`; multi-parent synthesis; authored story milestones; and evidence-linked Champion decisions.
