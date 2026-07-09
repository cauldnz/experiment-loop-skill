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

## Navigation-based judging for interactive artifacts

When the artifact is *interactive* — a viewer, dashboard, SPA, prototype, or any UI with tabs, filters, keyboard controls, or deep-links — a static screenshot is not sufficient evidence. Judges must **operate** the artifact and score from observed behaviour, not appearance.

Each judge, or a shared navigation harness that every judge runs, should:

- exercise every discoverable control (click each tab, select each filter option, toggle each checkbox);
- record, per interaction, whether the view actually changed;
- keyboard-operate the primary control group (focus, Arrow keys, Enter/Space);
- round-trip any URL-hash / deep-link view state;
- capture a screenshot per interaction state plus a transcript of actions to outcomes and any console errors.

Score interactivity, hierarchy, and robustness from that transcript, citing the concrete interaction observed. A control that is visibly present but does nothing — a nav link that only scrolls, a dead filter, a non-operable tablist — is a defect, not something to credit from a screenshot. Prefer a shared, reproducible harness so every judge exercises the same states and the evidence is auditable.

`scripts/navigate.mjs` is a reference harness: `node scripts/navigate.mjs --viewer viewer.html --out nav/`. It drives the locally installed Edge via `playwright-core`, discovers and exercises controls, tests keyboard operability and hash deep-links, and writes `transcript.json`, per-state screenshots, and `report.md` for the judges to inspect.

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
      "command": "python run_example.py",
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
