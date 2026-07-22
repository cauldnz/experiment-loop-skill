# Self-observation — `resumable-wizard-loop-01`

This document reports **objective evidence only** — the frozen harness's
gate results, assertions, and non-gating metrics from the actual runs
against this candidate. It makes **no promotion, `new_best`, ranking, or
qualitative-lens score claim**. Those require an independent blind judge
(`judge-accessibility`, `judge-human-use`), which this Loop is explicitly
not permitted to invoke or substitute for.

## Command and exit code (final, required run)

```
python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-01 --out .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-01\evidence
```

Exit code: `0`

## Objective gate results (from `evidence/objective-report.txt` and `.json`)

| Gate | Result |
|---|---|
| content-fidelity | PASS |
| semantic-accessibility-gate | PASS |
| keyboard-completion-gate | PASS |
| error-recovery-gate | PASS |
| mobile-touch-gate | PASS |
| resilience-gate | PASS |
| offline-safety-gate | PASS |

`Failed gate IDs: none`. `Blocking failure: no`.

Fixture SHA-256 recorded in the report: matches the frozen
`canonical-fixture.json` hash
`e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894`.

`human_use.applicability = applicable` is recorded verbatim in the objective
report with the exact required rationale.

## Non-gating task-efficiency metrics (objective, from the harness)

```json
{
  "activations": 24,
  "completion_interactions": 1,
  "corrections": 4,
  "focusable_controls_traversed": 29
}
```

These are raw interaction counts recorded by the harness during a scripted
run. They are not gate thresholds and are not, by themselves, a judgment of
usability quality.

## History of objective attempts (all preserved, none rewritten)

1. **`evidence-attempt-1/`** — exit code `1`. Failing gates:
   `semantic-accessibility-gate` (missing `<h1>`, missing visible "Guest"
   text, shipping-label hooks unreadable by `inner_text()`, no visible focus
   indicator, non-text-control-contrast, focus-contrast), `error-recovery-gate`
   (`preserve-valid-safe-value`), `resilience-gate`
   (`reduced-motion-completes-once`), `offline-safety-gate`
   (`invalid-or-unreviewed-placement-blocked`), and `content-fidelity`. Root
   cause: a strict single-step-visible wizard cannot satisfy gates that need
   to re-fill or re-check an earlier step's fields once the wizard has moved
   past it, because the harness's `reveal()` helper is strictly forward-only.
2. **`evidence-attempt-2/`** — exit code `1`. Failing gates:
   `semantic-accessibility-gate` (`focus-contrast=1.2468590984757486`, below
   the required 3:1 threshold) and `offline-safety-gate`
   (`invalid-or-unreviewed-placement-blocked` reported `1`, expected `0`).
   All other gates passed after rearchitecting to a progressive-disclosure
   wizard (completed steps stay reachable; exactly one frontier Continue
   control is visible at a time) and fixing the heading, guest-checkout text,
   shipping-label hooks, and button-contrast defects found in attempt 1.
3. **`evidence-attempt-3/`** — exit code `0`. All 7 gates passed after two
   further fixes: (a) `.btn-primary:focus` now uses a light outline color
   with sufficient contrast against the dark-green button background
   instead of the site-wide dark-navy focus-ring color; (b) the confirmation
   number (`SYN-2048`) is populated by JavaScript only at the moment of a
   real, successful order placement, rather than being present as static
   text in the initial HTML underneath a `hidden` confirmation region
   (`inner_text()` in this Playwright build still returns a hidden ancestor's
   descendant text, so a statically-present confirmation string was always
   counted by `confirmation_count()`, incorrectly indicating a premature
   placement).
4. **`evidence/`** — exit code `0`, identical gate results to attempt 3, run
   with the exact `--out` path required by this Loop's task. This is the
   authoritative evidence directory.

## Files produced under this Loop's write scope

`index.html`, `styles.css`, `app.js`, `status.json`, `metadata.json`,
`prompt-history.md`, `self-observation.md` (this file), `evidence/`,
`evidence-attempt-1/`, `evidence-attempt-2/`, `evidence-attempt-3/`, and the
Track-level `..\manifest-fragment.json`.

## Explicitly out of scope for this Loop (not performed)

- No independent blind judge (`judge-accessibility`, `judge-human-use`) was
  run.
- No `new_best` or promotion decision was made; `metadata.json` and
  `manifest-fragment.json` both record `decision: needs_human_review`.
- No Loop 02 was created.
- No Manifest merge or Viewer build was performed.
- No other Track's files were read, written, or otherwise touched.
