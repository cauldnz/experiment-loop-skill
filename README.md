# Experiment Loop Skill

`experiment-loop` is a Copilot skill for agent-mediated experimentation loops.

Use it when a task benefits from build/run/judge/improve cycles: visual artifacts, code, prompts, UX, documents, data workflows, or any open-ended quality optimization.

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
├── references
│   └── manifest-schema-v0.2.json
├── templates
│   ├── judge-note-template.md
│   ├── manifest-template.json
│   └── proposal-template.md
├── examples
│   └── minimal-agent-prompt.md
└── scripts
    ├── install.ps1
    └── install.sh
```

## Dependencies

The skill itself has no runtime package dependencies. Individual experiments may need tools such as Python, Node.js, Blender, ImageMagick, cloud CLIs, test runners, or domain-specific tooling.

## Governance

This skill includes a human-review gate. If an experiment proposes changes to the skill itself, a rubric, judge policy, approval policy, or reusable agent instruction, the change must be written as a proposal and explicitly approved before it is applied.
