# Experiment Loop Skill

`experiment-loop` is a Copilot skill for agent-mediated experimentation loops.

Use it when a task benefits from build/run/judge/improve cycles: visual artifacts, code, prompts, UX, documents, data workflows, or any open-ended quality optimization.

This repository is self-contained for review: the worked examples include completed manifests, judge notes, artifacts, and static viewers that can be opened from disk without rerunning the examples.

## What it does

- Defines the optimization target and scorecard.
- Designs parallel experiment tracks.
- Runs build -> execute/render/test -> judge -> improve loops.
- Captures artifacts, judge notes, metadata, and manifest entries.
- Compares variants against a champion.
- Synthesizes the best lessons into a final pass.
- Produces a local viewer for inspecting the hill-climb.
- Gates durable changes to skills, rubrics, judge policy, and reusable workflow instructions behind explicit human approval.

## Install

Windows PowerShell:

```powershell
.\scripts\install.ps1
```

macOS/Linux:

```bash
bash scripts/install.sh
```

Both scripts install this repository as:

```text
~/.copilot/skills/experiment-loop
```

They do not overwrite an existing skill unless `-Force` / `--force` is provided.

## Contents

```text
.
├── SKILL.md
├── docs
│   ├── concepts.md
│   ├── judging.md
│   ├── quickstart.md
│   ├── viewer.md
│   └── worked-examples.md
├── references
│   └── manifest-schema-v0.2.json
├── templates
│   ├── judge-note-template.md
│   ├── manifest-template.json
│   └── proposal-template.md
├── examples
│   ├── minimal-agent-prompt.md
│   ├── route-optimizer
│   │   ├── manifest.json
│   │   ├── viewer.html
│   │   └── run_example.py
│   ├── visual-design-system
│   │   ├── manifest.json
│   │   ├── viewer.html
│   │   └── run_example.py
│   └── multilingual-dad-joke
│       ├── manifest.json
│       ├── viewer.html
│       └── run_example.py
└── scripts
    ├── install.ps1
    └── install.sh
```

## Start here

- Read `docs\quickstart.md` for the shortest path.
- Read `docs\concepts.md` for the mental model.
- Read `docs\judging.md` to choose objective, qualitative, or panel judging.
- Read `docs\viewer.md` to understand the expected inspection UI.
- Read `docs\worked-examples.md` for the completed examples.

## Worked examples

| Example | What it demonstrates | Inspect without rerunning | Rerun command |
| --- | --- | --- | --- |
| `examples\route-optimizer` | Quantitative judging with objective metrics | Open `viewer.html` | `python run_example.py` |
| `examples\visual-design-system` | Qualitative SVG design judging with cross-run synthesis | Open `viewer.html` | `python run_example.py` |
| `examples\multilingual-dad-joke` | Language-only optimization with multi-model generator and judge panels | Open `viewer.html` | `python run_example.py` |

## Dependencies

The skill itself has no runtime package dependencies. The committed worked examples use only the Python standard library when rerun, and their generated artifacts, manifests, judge notes, and viewers are already included for offline inspection.

## License

MIT. See `LICENSE`.

## Governance

This skill includes a human-review gate. If an experiment proposes changes to the skill itself, a rubric, judge policy, approval policy, or reusable agent instruction, the change must be written as a proposal and explicitly approved before it is applied.
