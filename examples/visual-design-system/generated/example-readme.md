# Loop Lab event-card experiment

This experiment hill-climbs a reusable SVG event-card system through exactly
three Tracks, with a seventh audited repair Loop added after human review:

- **Editorial Typography:** establishes a print-led hierarchy, then repairs a
  measured contrast failure.
- **Generative Visual Language:** discovers a modular routing motif, then zones
  it away from live content.
- **Multi-parent Synthesis:** combines both parent winners, exposes a 3.358px
  variant overset, repairs it with width-aware metadata, then records and fixes
  a primary-content context drift without rewriting the rejected history.

The original independent panel comprises GPT-5.6 Terra, Claude Opus 4.8, and
Gemini 3.1 Pro Preview. A context-aware repair panel uses Claude Sonnet 5,
GPT-5.5, and Claude Opus 4.8. Criterion-wise medians are weighted with visual
hierarchy counted twice, while individual scores, dissent, the judge-miss
postmortem, and anonymous Human Review remain inspectable.

**Champion:** `synthesis-03`. It restores **Designing with Feedback Loops**,
keeps alternate long-title content in a visibly labelled stress fixture,
preserves the measured width-aware layout repair, and passes SVG, layout, and
external content-fidelity gates. Remaining caveats are system-font variance and
untested localization/non-Latin/RTL behavior.

## Inspect and rerun

Open `viewer.html` directly in a browser. From the repository root, rebuild and
gate it with:

```powershell
python generated\build_viewer.py --data generated --out generated\viewer.html
Set-Location generated
python validate_artifacts.py --manifest manifest.json
Set-Location ..
node .github\skills\experiment-loop\references\navigation_judge\cli.mjs --viewer generated\viewer.html --out generated
$env:PYTHONPATH=".github\skills\experiment-loop"
python -m references.evidence_gate generated
```

If the navigation judge dependencies are absent, first run:

```powershell
npm ci --prefix .github\skills\experiment-loop\references\navigation_judge
```

## Feature surface demonstrated

- **Viewer:** Overview, Topology/lineage, Compare, complete prompt chain,
  objective gates, preserved dissent, evidence-linked Champion, anonymous human
  export, provenance, and deterministic build.
- **Manifest:** exactly three Tracks and seven Loops, true multi-parent lineage,
  preserved rejection history, independent panel medians, content-fidelity and
  layout gates, inspectable Artifact hashes, authored milestones, and
  evidence-linked Champion reasons and caveats.
