# Self-testing the skill

When the thing you are optimizing is **this skill itself** — its guidance, a
rubric, judge policy, or any reusable instruction — an opinion that "the new
wording is clearer" is not evidence. Measure the change the same way the skill
tells you to measure anything else: by the quality of the runs it produces.

## The method

1. **Keep an external, version-pinned benchmark.** A small suite of representative
   tasks with at least one of each kind:
   - a quantitative/code task with an objective metric,
   - a visual task with an objective layout/quality gate,
   - a writing/prompt task with a structural gate plus judged quality,
   - a governance-trap task that pressures the agent to self-edit the skill.

   The benchmark, its objective checkers, and the judge rubric must live **outside
   the skill** and be version-pinned. If a candidate skill could edit its own test,
   the test is worthless.

2. **Run current vs proposed.** Have a fresh agent run each benchmark task twice:
   once following the current skill, once following the proposed skill. Score both
   with the objective gates and an independent judge panel.

3. **Compare induced run quality**, not the diff prose: outcome metric, evidence
   completeness, judging rigor, and governance adherence.
   When a change introduces conditional applicability, include both applicable
   and not-applicable cases. Human-use changes must include at least one
   human-operated digital system as well as any relevant physical case so the
   benchmark does not equate ergonomics with geometry.

4. **Regenerate the examples at a deliberate release checkpoint.** An Example
   Prompt is maintained source; its `generated/` directory is a disposable
   snapshot. Batch related skill changes, then manually regenerate every Example
   once through Copilot CLI:

   ```
   python scripts/regenerate_examples.py
   ```

   Regeneration stages every run in isolation, records exact skill/prompt/model
   provenance, runs Navigation Evidence and the Evidence Gate, and promotes the
   batch only when every example passes. Ordinary pull-request CI intentionally
   does not regenerate Examples or fail because snapshots are stale. At the
   release checkpoint, check committed snapshots with:

   ```
   python scripts/check_example_freshness.py
   python scripts/ci_validate_examples.py
   ```

   The manually dispatched `Validate and publish examples (manual)` workflow
   runs the same release checks and can optionally publish GitHub Pages.

5. **Gate the proposal on evidence.** Attach the benchmark comparison and the
   self-test result to the proposal. A change that does not beat the current skill
   on the benchmark should not be proposed as an improvement.

## Why external + pinned matters

This mirrors the skill's rule that a generator must not be the sole judge of its
own output. A skill revision must not be the sole author of the test that decides
whether it is better. Keep the harness and rubric out of the candidate and under
version control.
