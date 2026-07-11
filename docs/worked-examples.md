# Worked examples

This repository includes four completed experiment runs. They are intentionally small enough to read, rerun, and adapt.

All examples are self-contained for review: generated artifacts, judge notes, `manifest.json`, and `viewer.html` are committed. Rerunning is optional.

## Quantitative: route optimizer

Path: `examples\route-optimizer`

This example optimizes a small delivery route. The primary scorer is objective: route length must go down while every stop is visited exactly once. The run compares input order, nearest-neighbor construction, 2-opt local search, and deterministic multi-start 2-opt.

Open:

- `examples\route-optimizer\README.md` for the story;
- `examples\route-optimizer\prompt.md` for the kickoff prompt;
- `examples\route-optimizer\manifest.json` for the source of truth;
- `examples\route-optimizer\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\route-optimizer
python run_example.py
```

## Qualitative: SVG visual design system

Path: `examples\visual-design-system`

This example explores a browser-native event-card design system. It produces SVG cards, design tokens, layout-quality metrics, and judge notes. Objective gates check SVG validity and visual overlap, while champion selection also depends on qualitative design judgement. It demonstrates two independent design runs followed by a cross-run synthesis experiment with multi-parent graph lineage.

Open:

- `examples\visual-design-system\README.md` for the story;
- `examples\visual-design-system\prompt.md` for the kickoff prompt;
- `examples\visual-design-system\manifest.json` for the source of truth;
- `examples\visual-design-system\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\visual-design-system
python run_example.py
```

## Language: multilingual dad joke

Path: `examples\multilingual-dad-joke`

This example creates a wholesome dad joke that works in English, French, Spanish, and Japanese. It demonstrates a multi-model experiment panel where GPT-style, Gemini-style, and Claude-style generator tracks compete, then a multi-model judge panel preserves dissent before a synthesis loop polishes the winner.

Open:

- `examples\multilingual-dad-joke\README.md` for the story;
- `examples\multilingual-dad-joke\prompt.md` for the kickoff prompt;
- `examples\multilingual-dad-joke\manifest.json` for the source of truth;
- `examples\multilingual-dad-joke\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\multilingual-dad-joke
python run_example.py
```

## Objective bake-off: messy CSV parser

Path: `examples\messy-csv-parser`

This example hand-rolls a parser for a messy vendor CSV dialect and lets an objective correctness suite settle an architecture bake-off. A line-based regex track competes with a character state-machine track; a quoted field that spans two lines is a must-pass core sample that the regex architecture structurally cannot represent, so that track is rejected. The hardened state machine wins, and a synthesis loop merges it with the regex track's concise field-finalisation helper. A single deep-critic judge scores only error clarity and maintainability and never overrides the objective result.

Open:

- `examples\messy-csv-parser\README.md` for the story;
- `examples\messy-csv-parser\prompt.md` for the kickoff prompt;
- `examples\messy-csv-parser\manifest.json` for the source of truth;
- `examples\messy-csv-parser\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\messy-csv-parser
python run_example.py
```
