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

## Panel judging

Use a small panel when the output is subjective or high-value. A practical default is three judges:

- fast critic for obvious defects;
- deep critic for tradeoffs and correctness;
- style or domain critic for audience fit.

Preserve dissent. If judges disagree strongly, run a synthesis loop that tests the competing hypotheses instead of hiding the disagreement in an average.

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
