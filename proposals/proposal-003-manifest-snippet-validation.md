# Proposal 003: Manifest snippet / fragment validation before a run is reported done

> **Backfilled record.** This proposal was approved and applied before the
> `proposals/` audit trail existed in this repository; it is reconstructed here so
> the history travels with the skill. It was later hardened and **superseded by
> Proposal 005** (see [below](#superseded-by)).

## Trigger

Multi-track and parallel-agent runs have each agent write part of the manifest,
which the orchestrator then merges into a single `manifest.json`. Two failure
modes showed up in practice:

1. Without an explicit post-merge validation step, a merged manifest could parse
   as JSON yet be structurally incomplete (missing keys, dangling artifact paths,
   or an embedded viewer manifest that does not parse). "It's valid JSON" was
   being treated as "it's a valid manifest."
2. Embedding the manifest into `viewer.html` with regex string replacement
   mangled Windows paths, because backslashes in artifact paths were interpreted
   as escape sequences.

## Proposed change

1. **Fragment authoring.** Each specialist track writes a manifest-ready snippet
   per loop, or a single `manifest-fragment.json`, using the same schema as the
   top-level manifest. The orchestrator owns merging fragments into
   `manifest.json`.
2. **Validate before reporting done.** After merging, the orchestrator validates
   the result before a run may be called done:
   - `manifest.json` parses as JSON;
   - the viewer's embedded manifest, if any, parses;
   - newly added artifact paths (including GIF `contact_path` values) exist;
   - viewer JavaScript syntax parses when a local JS runtime is available.
3. **Safe embedding.** Embed the manifest into the viewer with a safe JSON
   embedding method (e.g. a JSON serializer writing into a `type="application/json"`
   script block), never regex replacement strings that reinterpret path
   backslashes.

## Files to change

- `SKILL.md` (§6a "Manifest is the source of truth" — fragment guidance, the
  post-merge validation checklist, and the safe-embedding note)
- `docs/viewer.md` (safe-embedding / self-contained viewer guidance)

## Exact intended diff or snippet

Add fragment guidance and, in `SKILL.md` §6a, a post-merge checklist:

```text
After merging, validate before reporting done:

1. `manifest.json` parses as JSON.
2. The viewer's embedded manifest, if any, parses as JSON or valid JavaScript.
3. Newly added artifact paths and GIF `contact_path` values exist.
4. Viewer JavaScript syntax parses when a local JS runtime is available.

Use a safe JSON embedding method rather than regex replacement strings that can
interpret path backslashes.
```

## Expected benefit

Turns "the manifest is the source of truth" from an aspiration into something the
orchestrator checks, and stops the class of parallel-run failures where a merged
manifest looks done but references missing artifacts or embeds an unparseable
viewer payload. The safe-embedding rule removes a Windows-specific corruption bug.

## Risks / regressions

- The checklist was advisory: it depended on each agent actually running it, with
  no shipped tool to enforce it. (This gap is what Proposal 005 closed.)
- Parse-ability was still doing double duty for "conformance" in step 1 — a
  manifest could pass the checklist while omitting a required schema key.

## Rollback

Remove the fragment guidance, the post-merge checklist, and the safe-embedding
note from `SKILL.md` §6a / `docs/viewer.md`. No manifest data-format change, so
existing manifests remain valid either way.

## Approval status

approved

Approved in chat on 2026-07-03 alongside proposals 002 (independent-judging-gate)
and 004 (long-running-recovery-heartbeats).

## Superseded by

**Proposal 005 — "Ship a manifest validator and mandate it as a blocking evidence
gate."** Proposal 003 told agents to "validate before reporting done" but shipped
no validator, so validation depended on discretion and step 1 conflated
parse-ability with schema conformance. Proposal 005:

- ships `references/validate_manifest.py` (stdlib-only, exits 0/1, `--json`);
- rewrites `SKILL.md` §6a to **mandate** it as a blocking evidence gate — a run is
  "not done" until the validator exits zero;
- enforces schema v0.2 conformance (required top-level keys, `schema_version`,
  every iteration's required fields, and the `decision` enum), explicitly noting
  that "parse-ability is not schema conformance."

The fragment-authoring guidance and the safe-embedding rule introduced by
Proposal 003 remain in force; only its discretionary checklist was replaced.

## Applied result

Applied to:

- `SKILL.md` (§6a — fragment authoring, post-merge validation checklist, and the
  safe-embedding note)
- `docs/viewer.md` (self-contained viewer + safe-embedding guidance)

Subsequently hardened by Proposal 005 (mandated `references/validate_manifest.py`
gate). A later follow-up made `references/manifest-schema-v0.2.json` **load-bearing**
in that validator: it now prefers a real JSON Schema check against the schema file
when the `jsonschema` package is importable and falls back to the stdlib structural
checks otherwise, so schema conformance is enforced against the published schema
rather than a hand-maintained key list.
