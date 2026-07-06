# Worked example: CadQuery phone stand

This is a completed qualitative experiment-loop run. It explores a small parametric phone stand with a cable pass-through.

The completed run is self-contained for review: STEP files, previews, metrics, judge notes, the manifest, and the static viewer are already included. CadQuery is only needed if you want to rerun or adapt the generator.

## Goal

Create a simple desk phone stand concept that is stable, printable, visually clean, and usable while charging.

## What the loop tried

1. Minimal upright cradle.
2. Wider cable-dock cradle.
3. Braced lightweight synthesis with cable clearance.

## Why this is a good qualitative example

The script produces objective constraint checks and real CadQuery STEP files, but the champion is selected by a qualitative design panel. The final design wins because it balances stability, cable access, visual clarity, and printability better than the alternatives.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly. Each loop folder contains:

- `model.step`
- `preview.svg`
- `cadquery-projection.svg`
- `metrics.json`
- panel judge notes

## Rerun

```powershell
pip install -r requirements.txt
python run_example.py
```

Dependency: CadQuery.
