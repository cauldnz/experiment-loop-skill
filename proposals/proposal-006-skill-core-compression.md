# Proposal 006: Compress the SKILL.md core, push detail to docs

## Trigger

`SKILL.md` had grown to 826 lines. In the meta-experiment, a candidate that
compressed the core by ~16% (collapsing an oversized inline manifest example and
tightening list-heavy sections) was run end-to-end across the full benchmark by a
fresh agent on a fixed model. It produced **zero regressions** on any objective
gate and the blind panel scored it comparably to baseline on outcome while noting
the leaner core is easier to follow faithfully. Two of three judges marked it
keep-for-synthesis; one marked promote.

## Proposed change

Compress the `SKILL.md` core while preserving every heading, rule, and durable
requirement. Specifically: collapse the ~127-line fully-inlined manifest JSON
example down to a compact illustrative shape that points to the canonical
`references/manifest-schema-v0.2.json` for the exhaustive version, and tighten the
most list-heavy prose (practical-patterns-by-artifact-type and similar) without
dropping any item. No guidance is removed; detail moves to the reference/docs
that already exist.

## Files to change

- `SKILL.md`

## Exact intended diff or snippet

Two representative compressions (full reviewed result is the candidate file
`meta-experiment/candidates/track-A-clarity/skill/SKILL.md`):

1. The inline manifest example in §6 shrinks from a ~127-line exhaustive object to
   a compact shape showing the required structure, followed by:

   ```text
   The full, field-by-field example lives in
   `references/manifest-schema-v0.2.json`.
   ```

2. The "Practical patterns by artifact type" bullets are tightened from multi-line
   entries to single-line entries, preserving every criterion.

Net effect: 826 -> 695 lines (-16%); all 43 headings preserved; no rule or
`decision`/scorer/governance requirement removed.

## Expected benefit

A shorter core is cheaper to load into every agent's context and easier to follow
without skimming past requirements — the meta-experiment's premise is that a skill
is only as good as an agent's faithful adherence to it. Detail that belongs in a
reference is kept in the reference, not the hot path.

## Risks / regressions

- Over-compression could drop a nuance. Mitigation: the change is additive-safe
  (all headings/rules preserved) and was validated by a full benchmark run with no
  regressions and an independent panel.
- The compressed manifest section relies on `references/manifest-schema-v0.2.json`
  being present. It **is** present in this repo, so the cross-reference resolves;
  do not remove that file without updating the pointer. (An early snapshot that
  omitted the file produced a false "dead reference" flag in review — a snapshot
  artifact, not a defect in the change.)

## Rollback

Restore the previous `SKILL.md`. Purely a text change; no schema, tooling, or
data-format impact.

## Evidence from the meta-experiment

- Objective: 4/4 benchmark gates passed, no regression vs baseline on any metric.
- Panel: keep-for-synthesis (2/3), promote (1/3); highest outcome/cost-efficiency
  scores of the three candidates.
- Folded into the synthesis candidate (`meta-experiment/candidates/synthesis`),
  which then passed 4/4 gates.

## Approval status

approved

Approved in chat on 2026-07-08 after the meta-experiment presented the proposal with benchmark + blind-panel evidence.

## Applied result

Applied to:

- `SKILL.md` (core compressed 826 -> 729 lines as part of the integrated synthesis; all 43 baseline headings preserved, §12 added by proposal 007)

Post-apply validation: all SKILL.md cross-references resolve (including the compressed manifest section's pointer to `references/manifest-schema-v0.2.json`); no rule or scorer/governance requirement removed.
