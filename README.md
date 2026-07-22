# Experiment Loop Skill

`experiment-loop` is a GitHub Copilot CLI and Claude Code skill for
agent-mediated experimentation loops. Its `experiment-setup` companion
inspects a target repository, asks one adaptive question at a time, and freezes
an approved, machine-validated brief before costly or unattended runs begin.

Use it when a task benefits from build/run/judge/improve cycles: visual artifacts, code, prompts, UX, documents, data workflows, or any open-ended quality optimization.

This repository is self-contained for review: the worked examples include completed manifests, judge notes, artifacts, and static viewers that can be opened from disk without rerunning the examples.

## What it does

- Defines the optimization target and scorecard.
- Designs parallel experiment tracks.
- Runs build -> execute/render/test -> judge -> improve loops.
- Captures artifacts, judge notes, metadata, and manifest entries.
- Compares variants against a champion.
- Judges interactive artifacts by navigating them (operating tabs, filters, keyboard, and deep-links), not by screenshots alone.
- Gates viewers with an objective check (self-contained, parses, accessible, deterministic, robust) before judging.
- Synthesizes the best lessons into a final pass.
- Produces a local viewer for inspecting the hill-climb.
- Rebuilds that Viewer after every merged Loop and offers a dependency-free local
  `--watch` mode for long-running Experiments.
- Collects Viewer-native human feedback as immutable schema-validated JSON,
  dispositions it against the frozen brief, and traces accepted entries into
  consuming Loop Prompts.
- Explicitly classifies human-use applicability for physical tools, digital
  interfaces, interactive artifacts, and workflows; carries first-principles
  friction and prior-art functional reasoning through Prompts; and judges
  applicable artifacts with qualitative use-friction evidence.
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

Both scripts install the two skills for GitHub Copilot CLI and Claude Code:

```text
~/.copilot/skills/experiment-loop
~/.copilot/skills/experiment-setup
~/.claude/skills/experiment-loop
~/.claude/skills/experiment-setup
```

They do not overwrite an existing skill unless `-Force` / `--force` is provided.
Use `-Runtime Copilot`, `-Runtime Claude`, `--runtime copilot`, or
`--runtime claude` to target one runtime.

## Architecture

- `references/manifest-schema-v1.1.json` defines the enforced Manifest contract.
- `skills/experiment-setup/SKILL.md` defines the guided setup interview,
  independent setup critic, approval, and immutable revision workflow.
- `references/experiment-brief-schema-v1.0.json` (legacy v1.0 plus current v1.1)
  and
  `references/experiment-approval-schema-v1.0.json` define the frozen setup
  contract and exact Prompt/brief hash binding.
- `references/human-judge-schema-v1.0.json` remains the legacy judge export
  contract. `references/human-feedback-*-schema-v1.0.json` defines canonical
  immutable intake and orchestrator disposition sidecars.
- `references/human_feedback.py` and `scripts/validate_human_feedback.py`
  validate the owner-words-to-consuming-Loop chain.
- `references/viewer_renderer` is the deep standalone Viewer module.
- `templates/build-viewer-adapter.py` exposes deterministic one-shot and
  Manifest-only watch builds through the shared Viewer CLI.
- `references/navigation_judge` produces required Navigation Evidence with pinned Chromium.
- `references/evidence_gate` is the single blocking experiment completion gate.
- `scripts/regenerate_examples.py` transactionally regenerates committed snapshots from Example Prompts.
- `scripts/prepare_scratch.py` creates experiment-local scratch space and expands
  unavoidable Windows 8.3 session paths before unattended work.
- `.github/workflows/tests.yml` runs lightweight unit tests on pull requests and `main`.
- `.github/workflows/examples.yml` manually validates refreshed snapshots and optionally publishes valid Viewers with GitHub Pages.

## Start here

- Read `docs\quickstart.md` for the shortest path.
- Invoke `experiment-setup` to create and approve
  `.experiments\<id>\setup\`, then invoke `experiment-loop`.
- On Windows, prepare unattended scratch space under
  `.experiments\<id>\generated\harness\scratch\`; never use a session path that
  still contains an 8.3 component such as `CHRISA~1`.
- Read `docs\concepts.md` for the mental model.
- Read `docs\judging.md` to choose objective, qualitative, or panel judging.
- Read `docs\viewer.md` to understand the expected inspection UI.
- Read `docs\human-feedback.md` for attended intake and disposition.
- Human-operated artifacts require the setup's qualitative human-use/friction
  analysis; independent prior-art browsing remains disabled without explicit
  network approval.
- Read `docs\worked-examples.md` for the completed examples.

## Worked examples

| Example | What it demonstrates | Inspect without rerunning |
| --- | --- | --- |
| `examples\route-optimizer` | Quantitative judging with objective metrics | Open `generated\viewer.html` |
| `examples\visual-design-system` | Qualitative SVG design judging with cross-run synthesis | Open `generated\viewer.html` |
| `examples\multilingual-dad-joke` | Language optimization with multi-model generator and judge panels | Open `generated\viewer.html` |
| `examples\messy-csv-parser` | Objective architecture bake-off | Open `generated\viewer.html` |
| `examples\accessible-mobile-checkout` | Accessibility-first browser/task gates, independent human-use judging, and recovery provenance | Open `generated\viewer.html` |

Regenerate all snapshots manually with `python scripts\regenerate_examples.py`.
Batch skill changes first: ordinary CI does not regenerate Examples or block on
snapshot freshness.

Installed Experiments can run
`python build_viewer.py --data <generated-root> --out <generated-root>\viewer.html --watch`
for local incremental viewing. Ctrl+C stops the watcher; final Viewers remain
self-contained and require the unchanged Navigation Evidence and Evidence Gate.
The watcher also rebuilds for canonical JSON sidecars under `human-feedback\`.

## Dependencies

The Evidence Gate requires Python 3.11+ and pinned `jsonschema`. Navigation
Evidence requires Node.js 20+ and the locked Playwright/Chromium package under
`references\navigation_judge`. Published Viewers remain standalone static files
with no runtime network dependency. `scripts\install_dependencies.py` accepts an
approved npm upstream through `EXPERIMENT_LOOP_NPM_REGISTRY` without persisting
it in repository files.

## License

MIT. See `LICENSE`.

## Governance

This skill includes a human-review gate. If an experiment proposes changes to the skill itself, a rubric, judge policy, approval policy, or reusable agent instruction, the change must be written as a proposal and explicitly approved before it is applied.
