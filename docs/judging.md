# Judging

Good experiments separate objective scoring from qualitative judgement.

## Objective scorers

Use an objective scorer when a command can produce a reproducible signal:

- tests pass or fail;
- schema validation passes or fails;
- benchmark time improves;
- route length decreases;
- model constraints are satisfied;
- lint or static analysis reports no regressions.

If a primary objective scorer fails, the loop should not become champion unless a human explicitly overrides the gate.

## Qualitative judges

Use qualitative judges for taste, clarity, UX, style, usefulness, and design tradeoffs. Record the exact evidence inspected and write short rationale against each criterion.

For subjective work, avoid self-approval. A generator can propose that a loop is promising, but an independent judge or panel should confirm before promotion to `new_best`.

### Human-operated artifacts

When the setup says human use is applicable, every Loop receives the frozen
friction analysis and is scored through a qualitative use-friction criterion.
Human-operated systems include physical tools, digital interfaces, interactive
artifacts, and workflows. Record evidence-backed findings for every selected
lens. Relevant physical findings can include:

- sharp and hand-contact edges;
- comfort across the declared grips and repetitive-use contexts;
- insertion/removal and inversion/retention;
- qualitative strength confidence under intended loads;
- operability, assembly/disassembly, misuse, accessibility, and safety contexts;
- failed, skipped, or degraded fillet/chamfer/cosmetic operations.

Relevant digital/interaction findings can include:

- discoverability, navigation, and input burden;
- error prevention/recovery and feedback/status;
- accessibility and responsive/touch ergonomics;
- interruption/resumption and latency perception;
- destructive actions and cognitive load.

Treat degraded physical or digital operations as real defects whenever they
affect use quality or confidence. Do not replace this rubric with mandatory
numeric edge, force, load, torque, latency, or interaction gates. Objective
safety/correctness gates may coexist only when separately justified by the
approved setup.

## Navigation-based judging for interactive artifacts

When the artifact is *interactive* — a viewer, dashboard, SPA, prototype, or any UI with tabs, filters, keyboard controls, or deep-links — a static screenshot is not sufficient evidence. Judges must **operate** the artifact and score from observed behaviour, not appearance.

Each judge, or a shared navigation harness that every judge runs, should:

- exercise every discoverable control (click each tab, select each filter option, toggle each checkbox);
- record, per interaction, whether the view actually changed;
- keyboard-operate the primary control group (focus, Arrow keys, Enter/Space);
- round-trip any URL-hash / deep-link view state;
- capture a screenshot per interaction state plus a transcript of actions to outcomes and any console errors.

Score interactivity, hierarchy, and robustness from that transcript, citing the concrete interaction observed. A control that is visibly present but does nothing — a nav link that only scrolls, a dead filter, a non-operable tablist — is a defect, not something to credit from a screenshot. Prefer a shared, reproducible harness so every judge exercises the same states and the evidence is auditable.

`references/navigation_judge` is the required harness. Install its pinned
Playwright/Chromium dependency once, then run:

```text
node references/navigation_judge/cli.mjs --viewer <run>/viewer.html --out <run>
```

It executes the Viewer's embedded interaction contract, fails on uncovered
controls, tests keyboard operation and hash deep-links, and writes
`navigation-evidence.json`, screenshots, and `navigation-report.md`.

## Panel judging

Use a small panel when the output is subjective or high-value. A practical default is three judges:

- fast critic for obvious defects;
- deep critic for tradeoffs and correctness;
- style or domain critic for audience fit.

Preserve dissent. If judges disagree strongly, run a synthesis loop that tests the competing hypotheses instead of hiding the disagreement in an average.

## Model experiment panels

Judge panels evaluate evidence. Model experiment panels create competing evidence.

When the harness supports model selection, you can deliberately run separate generator tracks with different models, then preserve the model source in each loop's metadata:

```json
{
  "model_experiment_panels": [
    {
      "id": "generator-panel",
      "harness": "GitHub Copilot task agents with model overrides",
      "models": ["gpt-5.5", "gemini-3.1-pro-preview", "claude-sonnet-4.6"],
      "purpose": "Generate competing candidates before synthesis."
    }
  ]
}
```

Keep generator and judge roles separate. A model can generate one candidate and also serve as a judge in another blind panel, but it should not be the only judge that promotes its own candidate.

## Pairwise judging

When two candidates are close, compare them side by side. Blind labels and flip A/B order when practical to reduce position bias.

## Example scorer mix

```json
{
  "scorers": [
    {
      "id": "metrics",
      "type": "objective_command",
      "command": "python score_candidate.py",
      "primary": true,
      "weight": 2
    },
    {
      "id": "panel",
      "type": "llm_rubric",
      "judge_panel": "design-panel",
      "weight": 1
    }
  ]
}
```
