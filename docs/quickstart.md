# Quickstart

Use `experiment-loop` when the answer is not obvious up front and you want agents to improve an artifact through evidence-backed iterations.

## 1. Install the skill

From this repository root:

```powershell
.\scripts\install.ps1
```

On macOS or Linux:

```bash
bash scripts/install.sh
```

Restart GitHub Copilot CLI or Claude Code, or reload skills after installation.

## 2. Freeze the Experiment setup

For unattended, high-cost, deployment, telemetry, external-user, service, or
real-data work, invoke `experiment-setup` first. It inspects the repository,
asks one adaptive question at a time, runs an independent setup critic, and
writes:

```text
.experiments/<experiment-id>/setup/
  prompt.md
  experiment-brief.json
  setup-review.md
  approval.json
```

Review the exact Prompt, brief, and critic findings before approving them. An
approval binds the exact Prompt and brief hashes. Revise approved setup through
a new numbered revision rather than editing it in place.

For unattended Windows runs, keep scratch files under the Experiment rather
than in `%TEMP%` or a session scratchpad:

```powershell
python <experiment-loop-skill>\scripts\prepare_scratch.py `
  --generated-root .experiments\<experiment-id>\generated
```

Use the printed path for every agent. If a tool forces use of an existing
session scratch directory, pass it with `--session-scratch`; the helper expands
8.3 components such as `CHRISA~1` to a long path or fails before the run starts.

## 3. Start the Experiment

After approval, ask the agent to invoke `experiment-loop` with the setup
directory. Small, supervised, low-cost experiments may start directly with a
compact prompt:

```text
Use the experiment-loop skill.

Goal: Improve <artifact> until it satisfies <quality target>.

Scorecard:
- correctness: what a correct result must do
- quality: what a better result looks like
- reproducibility: evidence and commands exist for every loop

Topology:
- Run 2 or 3 tracks.
- Each track runs 2 or 3 loops.
- Keep a Manifest, judge notes, Artifacts, and a standalone Viewer.
```

If you already know the exact implementation, do not use the skill. Use normal engineering work instead.

## 4. Require observable evidence

Every loop should leave behind:

- the artifact that was produced;
- objective command output, metrics, renders, screenshots, or drafts;
- judge notes tied to the scorecard;
- the next hypothesis;
- a manifest entry.

The manifest is the source of truth. Chat history is not.
After merging each Loop entry, immediately rebuild `viewer.html`. For a local
live view, run the standard adapter with `--watch`; it rebuilds when the Manifest
or standard fragments change and stops with Ctrl+C.

## 5. Pick the judging mode

Use objective commands when correctness can be measured, for example tests, route length, benchmarks, or schema validation.

Use independent qualitative judges when the target is visual quality, UX, writing, prompt quality, or design taste. The generator should not be the only judge of its own work if a result is promoted as the champion.

## 6. Inspect the result

Open `viewer.html` during the run to inspect all Loops merged so far. An interim
Viewer labels itself in progress and does not claim final gate completion. Every
completed experiment must contain at least two Loops and a final Viewer. Run the
navigation judge and Evidence Gate before treating it as complete.

For complete examples, see:

- `examples\route-optimizer` for quantitative judging;
- `examples\visual-design-system` for qualitative design judging with SVG artifacts;
- `examples\multilingual-dad-joke` for language optimization with multi-model experiment and judge panels.
