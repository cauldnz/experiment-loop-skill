# Worked example: messy CSV parser

This is a completed experiment-loop run that settles an architecture bake-off with objective tests. It hand-rolls a parser for a messy vendor CSV dialect and lets a correctness suite — not a judge — decide which design wins.

The completed run is self-contained for review: the two competing tracks, the synthesis loop, their per-loop parser snapshots, test results, judge notes, the manifest, and the static viewer are already included. Rerunning only needs Python.

## Goal

Hand-roll a parser for a messy vendor CSV dialect (quoted commas, embedded newlines, doubled-quote escaping, BOM, comment and blank lines, ragged rows, whitespace rules) without importing the standard-library `csv` module. Use objective sample tests to settle the architecture bake-off and a single deep-critic judge only for maintainability.

## What the loop tried

Two architectures compete in parallel tracks, then a synthesis loop merges the winner with a helper borrowed from the loser:

1. **Line-based regex track** — `loop-01-naive-split`: split each line on commas (baseline); `loop-02-regex-quoted`: a per-line regex that understands quotes. **Rejected** — an objective test (a quoted field spanning two lines) proves a line-based design structurally cannot represent embedded newlines.
2. **Character state-machine track** — `loop-01-scanner`: a character scanner with a quote state that crosses line boundaries; `loop-02-hardened`: add the vendor-dialect niceties (BOM, comments, blank lines, trimming) and clean `ParseError` reporting.
3. **Synthesis** — `loop-03-merged`: merge the hardened state machine with the regex track's concise field-finalisation helper. Champion.

## Why this is a good example

The bake-off is decided objectively. The primary scorer runs the correctness suite over 15 committed samples, and a small set of **must-pass core samples** (embedded commas, embedded newlines, doubled-quote escaping) act as a hard gate: a variant that fails one cannot become champion, and a track whose architecture can *never* pass one is rejected outright. A separate robustness suite requires every malformed fixture to raise `ParseError`. The deep-critic judge only scores error-message clarity and maintainability; it never overrides the objective result. This is the example to read for **objective, test-driven judging of competing designs** and a **dead-end rejection driven by a structural limit**.

## Results

| Loop | Track | Correctness | Robustness | Value | Decision |
| --- | --- | --- | --- | --- | --- |
| `loop-01-naive-split` | regex | 8/15 | 0/3 | 2.39 | new_best (baseline) |
| `loop-02-regex-quoted` | regex | 13/15 | 0/3 | 3.03 | reject (dead end) |
| `loop-01-scanner` | state machine | core pass | 0/3 | 3.14 | new_best |
| `loop-02-hardened` | state machine | 15/15 | 3/3 | 4.67 | new_best |
| `loop-03-merged` | synthesis | 15/15 | 3/3 | 4.83 | new_best (champion) |

The champion is the only variant that passes all 15 samples and all 3 malformed inputs with the clearest code, so it wins the weighted scorecard.

## Inspect the completed run

Open `viewer.html` in a browser, or read `manifest.json` directly. Each loop folder contains:

- `parser.py` — the parser snapshot for that variant;
- `test-results.json` — per-sample and per-criterion scores;
- `judge.md` — the deep-critic note.

The champion parser and its suite are also promoted to the example root as `parser.py` and `test_parser.py`.

## Rerun

```powershell
python run_example.py
```

The script rewrites the sample corpus, runs every suite, re-derives the decisions, and regenerates the loop artifacts, manifest, and viewer. Dependency: Python standard library only.
