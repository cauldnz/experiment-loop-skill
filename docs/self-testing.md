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

4. **Regression self-test.** Confirm the shipped worked examples still validate
   after your change:

   ```
   python scripts/skill_selftest.py
   ```

   Validate each run's manifest against schema v0.2 with the bundled validator,
   too. It prefers a real JSON Schema check against
   `references/manifest-schema-v0.2.json` when `jsonschema` is importable and
   falls back to stdlib structural checks otherwise:

   ```
   python references/validate_manifest.py <run>/manifest.json
   ```

5. **Gate the proposal on evidence.** Attach the benchmark comparison and the
   self-test result to the proposal. A change that does not beat the current skill
   on the benchmark should not be proposed as an improvement.

## Why external + pinned matters

This mirrors the skill's rule that a generator must not be the sole judge of its
own output. A skill revision must not be the sole author of the test that decides
whether it is better. Keep the harness and rubric out of the candidate and under
version control.
