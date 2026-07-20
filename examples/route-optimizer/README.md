# Certified-optimal delivery route experiment

## Experiment

This Example hill-climbs a closed Euclidean delivery tour over one fixed depot
and 12 named stops. Route length is the primary metric. Validity (start and end
at the depot, visit every stop exactly once) and three-run reproducibility are
hard objective gates. The independent `claude-sonnet-5` judge scores how well
the evidence explains each result, but cannot override a gate or a measured
distance.

The four authored Loops progress from an alphabetical measured baseline through
nearest-neighbor construction and 2-opt local search to deterministic
multi-start synthesis. The final candidate is checked independently by a
Held-Karp dynamic-programming oracle.

## Topology and judging

`quantitative-route` is one linear Track:

1. `loop-001`: measured alphabetical baseline.
2. `loop-002`: nearest-neighbor construction.
3. `loop-003`: 2-opt local-search improvement.
4. `loop-004`: multi-start synthesis plus exact-oracle certification.

Each Loop's `parent_ids` points to its predecessor. Objective `metrics.json`
files record route length and gate evidence on the same input hash. Independent
Markdown judge notes explain the measurements and assign the non-overriding
explainability score. The Champion is globally optimal for this fixed instance:
37.576644306 km with zero oracle gap.

## Inspect and rerun

Open `generated/viewer.html` directly in a browser. The Overview frames the
Problem and Champion, Topology exposes lineage and the complete prompt/feedback
chain, and Compare charts metric progression and embeds route maps side by side.
`generated/manifest.json` is the authoritative Manifest v1.1 record.

From the repository root, rerun a candidate and the exact check with:

```text
python generated/optimizer.py --data generated/stops.json --strategy multi_start --out generated/track-quantitative/loop-04
python generated/objective_oracle.py --data generated/stops.json --candidate generated/track-quantitative/loop-04/route.json --out generated/track-quantitative/loop-04/oracle.json
python generated/build_manifest.py
python generated/build_viewer.py --data generated --out generated/viewer.html
```

The other strategy names are `baseline`, `nearest`, and `two_opt`. Rebuilding
the Viewer is deterministic. Navigation Evidence and the unified gate are
stored in `navigation-evidence.json` and `evidence-gate.json`.

## Feature surface demonstrated

- **Shared standalone Viewer:** offline Overview, Topology, and Compare views;
  embedded SVG route maps; rendered metric sets; keyboard navigation; deep
  links; Artifact dialogs; filters; provenance; and the full feedback chain.
- **Manifest v1.1:** structured Problem framing and exact Prompt evidence;
  scorecard direction, units, baselines, gates, and comparability; `parent_ids`
  lineage; stable Artifact presentation metadata; authored milestones; actual
  generator/judge/synthesis model IDs; and evidence-linked Champion reasons and
  caveats.
