# Worked example: multilingual dad joke

This is a completed language-only experiment-loop run. It uses a multi-model generation panel to produce candidate dad jokes, then uses a multi-model judging panel to choose and polish the joke that works most evenly in English, French, Spanish, and Japanese.

The completed run is self-contained for review: generated joke drafts, candidate JSON, judge notes, the manifest, and the static viewer are already included. Rerunning only needs Python.

## Goal

Create a wholesome dad joke that lands as consistently as possible across four languages without relying on an English-only pun.

## What the loop tried

1. A GPT-style generator proposed a globally portable computer-virus joke.
2. A Gemini-style generator proposed a wall/corner joke based on shared physical geometry.
3. A Claude-style generator proposed a doctor joke based on "two places" ambiguity.
4. A synthesis loop resolved judge-panel dissent and polished the strongest cross-language candidate.

## Why this is a good language example

It shows that experiment loops are not limited to images, code, or CAD. The artifact is text, but the run still records evidence: every loop has multilingual outputs, model provenance, independent judge notes, scores, lineage metadata, and a manifest. It also demonstrates a second kind of panel: not just several agents judging one artifact, but several model-backed generators competing as an experiment panel.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly. Each loop folder contains:

- `joke.md`
- `candidate.json`
- judge notes

The viewer includes the experiment graph, score timeline, candidate translations, model-panel provenance, judge-panel dissent, artifact inventory, raw iteration JSON, and raw manifest JSON.

## Rerun

```powershell
python run_example.py
```

Dependency: Python standard library only.
