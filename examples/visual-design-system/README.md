# Worked example: SVG visual design system

This is a completed qualitative experiment-loop run for visual design. It creates a small event-card design system using only self-contained SVG, JSON, Markdown, and HTML.

The completed run is self-contained for review: generated SVG cards, design tokens, judge notes, the manifest, and the static viewer are already included. Rerunning only needs Python.

## Goal

Design a polished, reusable visual identity for a fictional "Loop Lab" workshop card that clearly communicates the event and demonstrates qualitative design judging.

## What the loop tried

1. Run A: an editorial/typographic path that optimizes hierarchy and clarity.
2. Run B: a generative visual-language path that optimizes distinctiveness and energy.
3. Run C: a cross-run synthesis path that combines Run A's clarity with Run B's visual language, then polishes the result.

## Why this is a good qualitative example

The output is visual and subjective, but the run still records evidence: every loop has an SVG artifact, design tokens, objective SVG checks, independent judge notes, scores, lineage metadata, and a manifest. The synthesis loops use multiple parents so the graph shows how one experiment can build on two earlier runs.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly. Each loop folder contains:

- `card.svg`
- `tokens.json`
- `judge-fast-critic.md`
- `judge-design-critic.md`
- `judge-aggregate.md`

The viewer includes the experiment graph, score timeline, per-loop metadata/provenance, artifact inventory, raw iteration JSON, and raw manifest JSON.

## Rerun

```powershell
python run_example.py
```

Dependency: Python standard library only.
