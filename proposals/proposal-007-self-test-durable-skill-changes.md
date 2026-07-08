# Proposal 007: Self-test durable skill changes against an external benchmark

## Trigger

When the experiment target is this skill (or a rubric, judge policy, or other
reusable instruction), §11 requires a proposal + human approval — but the skill
gave no method for *generating evidence* that a proposed change is actually an
improvement. The meta-experiment demonstrated the missing method: run the current
and proposed skill over a fixed external benchmark and compare the quality of the
runs each induces, rather than arguing about the diff.

A candidate that added this "self-test" guidance scored well conceptually with the
panel, but its own standalone run **hard-failed** the evidence gate (its writing
run omitted the required `tracks` key) — so it is proposed as a **method + tooling
addition, not as a standalone promote**. The self-test method is what let the
whole meta-experiment measure itself; Proposal 005 is what would have caught this
candidate's own failure. They are complementary.

## Proposed change

Add a short, non-mandatory §12 "Self-test durable skill changes" that points to a
new `docs/self-testing.md` describing the method, and ship a small
`scripts/skill_selftest.py` regression check so shipped examples keep validating.
Framed as **recommended proposal evidence**, not a heavy prerequisite for every
change.

## Files to change

- `SKILL.md` (new §12, lean — a pointer, not a restatement of the doc)
- `docs/self-testing.md` (new — the full method)
- `scripts/skill_selftest.py` (new — regression self-test over shipped examples)

## Exact intended diff or snippet

Lean §12 in `SKILL.md` (full text in
`meta-experiment/candidates/synthesis/skill/SKILL.md`):

```text
### 12. Self-test durable skill changes

When the experiment target is this skill, a rubric, judge policy, or another
reusable instruction, do not trust that a change is an improvement — measure it.
Before writing the proposal above, run the current skill and the proposed skill
over a small **external, version-pinned** benchmark (at least one each of:
code/quantitative, visual, writing, and a governance check) plus objective
validators, and compare the quality of the runs they produce — not opinions about
the diff. The benchmark and its rubric must live outside the skill so a change
cannot weaken its own test. Confirm shipped examples still validate:

    python scripts/skill_selftest.py

Attach the benchmark comparison and self-test result to the proposal as evidence;
a change that does not beat the current skill should not be proposed as an
improvement. See `docs/self-testing.md` for the full method.
```

`docs/self-testing.md` expands the method (external + version-pinned benchmark;
current-vs-proposed runs; compare induced run quality; regression self-test; gate
the proposal on evidence) and explains why the harness/rubric must live outside
the candidate (a skill revision must not be the sole author of the test that
judges it — the same principle as "no self-approving judge"). The §12 pointer and
the doc are deliberately de-duplicated: the rule lives in `SKILL.md`, the method
lives in the doc.

## Expected benefit

Gives future self-improvement proposals a concrete, reproducible way to produce
outcome evidence, and hard-wires the anti-self-approval principle into skill
self-testing. Turns §11's governance gate from "propose and hope" into "propose
with benchmark evidence."

## Risks / regressions

- Could imply heavy overhead for tiny changes. Mitigation: framed as recommended,
  proportionate evidence — a one-line wording fix does not need a full benchmark.
- Adds a maintained benchmark/harness surface. Mitigation: the benchmark is
  external and version-pinned, so it is not shipped inside the skill and cannot be
  weakened by a candidate.

## Rollback

Remove §12, `docs/self-testing.md`, and `scripts/skill_selftest.py`. No schema or
data-format impact.

## Evidence from the meta-experiment

- Concept validated: this method is exactly how all three candidates in this
  experiment were measured (external benchmark + blind panel + objective gates).
- Caveat recorded: the standalone candidate that shipped this idea hard-failed its
  own writing run (missing `tracks`) — which is precisely why it is paired with
  Proposal 005's mandated validator in the synthesis rather than promoted alone.
- Panel: keep-for-synthesis / reject as a standalone; the *method* is retained,
  the weak standalone execution is not.

## Approval status

approved

Approved in chat on 2026-07-08 after the meta-experiment presented the proposal with benchmark + blind-panel evidence.

## Applied result

Applied to:

- `SKILL.md` (new lean §12 pointer)
- `docs/self-testing.md` (new — the full method)
- `scripts/skill_selftest.py` (new — regression self-test; skips gracefully when no examples)

Post-apply validation: `scripts/skill_selftest.py` validated all 3 shipped examples (0 errors, exit 0); §12's pointer to `docs/self-testing.md` resolves.
