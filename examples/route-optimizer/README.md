# Worked example: route optimizer

This is a completed quantitative experiment-loop run. It optimizes a small delivery route with objective scoring.

## Goal

Find a short route that starts and ends at the depot, visits every stop exactly once, and remains easy to reproduce.

## What the loop tried

1. Baseline input order.
2. Nearest-neighbor construction.
3. 2-opt local search from the nearest-neighbor route.
4. Deterministic multi-start 2-opt synthesis.

## Why this is a good quantitative example

The primary scorer is a command-generated metric: total route distance. Validity is a gate. Qualitative comments exist only to explain readability and reproducibility; they do not override the objective result.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly.

## Rerun

```powershell
python run_example.py
```

The script rewrites the loop artifacts, manifest, and viewer.
