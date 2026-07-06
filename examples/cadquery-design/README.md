# Worked example: CadQuery phone stand

This is a completed qualitative experiment-loop run. It explores a small parametric phone stand with a cable pass-through.

The completed run is self-contained for review: STEP files, previews, metrics, judge notes, the manifest, and the static viewer are already included. CadQuery is only needed if you want to rerun or adapt the generator.

## Goal

Create a simple desk phone stand concept that is stable, printable, visually clean, and usable while charging.

## What the loop tried

1. Run A: a conventional utility-cradle path, from minimal cradle to wider cable dock.
2. Run B: a separate printability/bracing path, from compact braced stand to cable-capable braced stand.
3. Run C: a cross-run synthesis experiment that combines Run A's cable affordance with Run B's side-braced stability, then refines the hybrid.

## Why this is a good qualitative example

The script produces objective constraint checks and real CadQuery STEP files, but the champion is selected by a qualitative design panel. It also demonstrates multi-parent experiment lineage: the synthesis branch builds from both independent source runs instead of continuing a single linear chain.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly. Each loop folder contains:

- `model.step`
- `preview.svg`
- `cadquery-projection.svg`
- `metrics.json`
- panel judge notes

The viewer includes the experiment graph, score timeline, per-loop metadata/provenance, artifact inventory, raw iteration JSON, and raw manifest JSON.

## Rerun

```powershell
pip install -r requirements.txt
python run_example.py
```

Dependency: CadQuery.
