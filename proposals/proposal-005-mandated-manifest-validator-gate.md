# Proposal 005: Ship a manifest validator and mandate it as a blocking evidence gate

## Trigger

A meta-experiment used the experiment-loop skill to improve the experiment-loop
skill itself: three candidate revisions of `SKILL.md` were each run end-to-end
across a fixed, external benchmark (quantitative, visual, writing, governance) by
fresh agents on a fixed model, then scored by an independent blind panel of three
diverse models (opus-4.8, gpt-5.5, gemini-3.1-pro).

Two findings converged on this proposal:

1. Proposal 003 told agents to "validate before reporting done" but shipped **no
   validator**, so validation depended on each agent's discretion. In the
   benchmark, the candidate that did *not* mandate a validator produced a writing
   run whose `manifest.json` parsed as JSON but **omitted the required top-level
   `tracks` key** — a schema violation an agent's own eyeball check missed.
2. The candidate that shipped a real `validate_manifest.py` and mandated it as a
   blocking gate passed every objective gate on every task, and the synthesis
   that folded it in **fixed the exact writing-run failure above** (that run then
   passed the evidence gate). The blind panel ranked this change **first and
   recommended promote unanimously** ("strongest single change; it would have
   caught the other candidate's failure").

## Proposed change

Ship an executable, dependency-free `references/validate_manifest.py` and update
`SKILL.md` §6a so that, after merging fragments, agents must run it and treat a
non-zero exit as a **blocking evidence gate** (the run is "not done" until it
passes). This turns "parse-ability" into enforced schema conformance and closes
the gap proposal 003 left open.

## Files to change

- `references/validate_manifest.py` (new — the shipped validator)
- `SKILL.md` (§6a "Manifest is the source of truth")

## Exact intended diff or snippet

In `SKILL.md` §6a, replace the current soft checklist:

```text
After merging, validate before reporting done:

1. `manifest.json` parses as JSON.
2. The viewer's embedded manifest, if any, parses as JSON or valid JavaScript.
3. Newly added artifact paths and GIF `contact_path` values exist.
4. Viewer JavaScript syntax parses when a local JS runtime is available.
```

with a mandated blocking gate:

```text
After merging, validate before reporting done. Run the bundled validator; treat
it as a **blocking evidence gate**:

    python references/validate_manifest.py experiment-loop/manifest.json

It checks that:

1. `manifest.json` parses as JSON.
2. The manifest conforms to schema v0.2: required top-level keys are present,
   `schema_version` is `0.2`, and every iteration carries its required fields
   with a `decision` from the allowed enum. (Parse-ability is not schema
   conformance.)
3. Referenced artifact paths, including GIF `contact_path` values, exist on disk.
4. The viewer's embedded manifest, if any, parses.
5. A sibling `viewer.html` is present for visual or multi-loop runs.

If the validator exits non-zero the run is **not done**: fix the manifest and
re-run until it passes. A failed primary objective scorer (this validator, tests,
or a metric gate) blocks champion promotion unless the user explicitly overrides.
```

The shipped `references/validate_manifest.py` is stdlib-only (runs anywhere),
exits 0/1, supports `--json`, and enforces the full v0.2 required-loop-field set
(`id`, `track_id`, `parent_id`, `hypothesis`, `commands`, `artifacts`, `scores`,
`changed_files`, `lesson`, `decision`) plus artifact existence and the
viewer-presence check. The reviewed copy lives at
`meta-experiment/candidates/synthesis/skill/references/validate_manifest.py`.

## Expected benefit

Prevents the class of failure observed in the benchmark: a run that "looks done"
but ships a schema-incomplete manifest the viewer/tools cannot rely on. Makes the
"manifest is the source of truth" claim enforceable instead of aspirational, and
gives every run a reproducible, model-independent evidence gate. The
viewer-presence check additionally catches the panel-flagged pattern of visual /
multi-loop runs that passed deterministic gates but shipped no viewer.

## Risks / regressions

- Adds a required tool invocation to every multi-loop run (small, stdlib-only,
  sub-second). Environments without Python can fall back to the manual checklist,
  which should be noted.
- A stricter gate will (correctly) fail some runs that previously slipped through;
  that is the intent, but it means slightly more iteration on manifests.
- The validator must stay in sync with the schema; schema changes require a
  matching validator change.

## Rollback

Delete `references/validate_manifest.py` and restore the previous soft 4-item
checklist in `SKILL.md` §6a. No manifest data format changes, so existing
manifests remain valid either way.

## Evidence from the meta-experiment

- Panel: ranked #1 of 3 candidates; **promote** from all three judges (mean
  criterion scores ~4.7 outcome / 4.7 evidence / 5.0 governance).
- Objective: the candidate passed 4/4 benchmark gates; the synthesis that folded
  it in passed 4/4 including the writing task that a non-validator candidate
  hard-failed (missing `tracks`).
- Viewer: `meta-experiment/experiment-loop/viewer.html` (score matrix + judge
  meta-scorecard + topology graph).

## Approval status

approved

Approved in chat on 2026-07-08 after the meta-experiment presented the proposal with benchmark + blind-panel evidence.

## Applied result

Applied to:

- `references/validate_manifest.py` (new — stdlib-only, exits 0/1, `--json`)
- `SKILL.md` (§6a — mandated blocking validation gate)

Post-apply validation: `scripts/skill_selftest.py` validated all 3 shipped examples (0 errors); `references/validate_manifest.py` PASSed each example manifest; the §6a cross-reference to the validator resolves.
