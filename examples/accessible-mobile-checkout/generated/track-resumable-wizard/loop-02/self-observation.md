# Self-observation — `resumable-wizard-loop-02`

This document reports **objective evidence only** — the frozen harness's
gate results, assertions, and non-gating metrics from the actual runs
against this candidate, plus directly-verified interaction facts gathered
via ad-hoc Playwright probes run from the designated scratch root. It makes
**no promotion, `new_best`, ranking, or qualitative-lens score claim**. Those
require an independent blind judge (`judge-accessibility`,
`judge-human-use`), which this Loop is explicitly not permitted to invoke or
substitute for.

## Command and exit code (final, required run)

```
python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-02 --out .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-02\evidence
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

`Failed gate IDs: []`. `Blocking failure: false`. All 287 individual
assertions across the 7 gates report `status: pass` (0 failures).

Fixture SHA-256 recorded in the report matches the frozen
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

These numbers are **identical** to Loop 01's. This is not treated as
evidence that the required fixes had no effect (see "Why the metrics are
unchanged" below) — the qualitative evidence that motivated the three
changes is not overridden by an unchanged interaction count, per this Loop's
explicit instruction.

## The three evidence-backed changes and how each was verified

1. **Skip-link activation moves programmatic focus to the checkout steps.**
   `index.html`/`app.js`: the skip-link now has `data-hook="skip-link"`; its
   `click` handler calls `preventDefault()` and moves focus to the current
   active step's `<h2>` (falling back to `#wizard-form`, which now carries
   `tabindex="-1"`). Verified directly with a Playwright probe
   (`generated/harness/scratch/debug_probe6.py`): focusing the skip-link and
   pressing Enter leaves `document.activeElement` on the step heading
   (`H2`), not `BODY`.
2. **The active step is validated and useful focus is retained before
   advancing; empty-step progression is blocked.** `app.js`:
   `handleContinue(stepNum)` now computes the current step's errors first;
   if any exist, it renders the step-scoped error summary, sets a status
   message, focuses the first invalid field, persists state, and returns
   without calling `goToStep`. Verified directly with a Playwright probe
   (`generated/harness/scratch/debug_probe.py`/`debug_probe2.py`): pressing
   Continue on a blank Step 1 keeps the wizard on Step 1 (progress stays at
   1), shows a 3-problem step-scoped summary (`contact-name`,
   `contact-email`, `contact-phone`), and moves focus to `contact-name` — not
   the 13-problem whole-order summary that only `handlePlaceOrder` produces.
3. **Clear saved progress requires explicit confirmation before discarding
   state.** `index.html`/`app.js`/`styles.css`: a new `#clear-confirm` panel
   (Cancel / "Yes, clear saved progress") appears on the first Clear
   activation; focus moves to Cancel by default; Escape also cancels;
   `localStorage` is left untouched until the explicit confirm button is
   pressed. Verified directly with a Playwright probe
   (`generated/harness/scratch/debug_probe5.py`): saved state survives the
   first Clear click and a Cancel click, and is only removed after the
   explicit "Yes, clear saved progress" click.

## Why the objective metrics are unchanged from Loop 01

Investigated because identical activation/correction/traversal counts after
adding a real validation-blocking change was unexpected. Root cause,
confirmed with direct Playwright probes: the frozen harness's `reveal()` /
`fill_all()` helpers check `is_visible()` on each field hook directly, and a
pre-existing CSS interaction — unmodified, inherited unchanged from Loop 01
— means later/not-yet-reached steps' controls still report as "visible" to
Playwright even while correctly `hidden` + `aria-hidden="true"` +
`tabindex="-1"`. Specifically: `.pending-control` sets `max-height: 0`, but
`.btn` and text `input` elements also set `min-height: 44px`; per the CSS
box-sizing algorithm, when a used min-height exceeds a used max-height the
min-height wins, so the "collapsed" control keeps its real rendered
height. Additionally, `.pending-control`'s own `display: block` (an
author-origin rule) overrides the native `[hidden] { display: none }`
user-agent rule for the same element, since author-origin CSS always wins
over user-agent-origin CSS regardless of selector specificity. The net
effect: `self.visible(hook)` in the harness returns `True` for fields inside
not-yet-reached steps immediately, without ever needing a Continue press, so
the harness's own traversal never actually exercises the new per-step
Continue-blocking logic — it fills/reads fields directly via automation
before there is any chance of a blocked Continue press mattering to the
gate outcome.

This does not affect real users: the same not-yet-reached controls are
removed from the tab order (`tabindex="-1"`) and hidden from assistive
technology (`aria-hidden="true"` on the ancestor `.step-pending` section), so
keyboard and screen-reader users cannot reach them early; and visually they
render inside a zero-height, `overflow: hidden` ancestor, so a mouse user has
no on-screen target to click. A direct manual Playwright reproduction of a
real user pressing Continue on a genuinely blank Step 1 (not the harness's
own `fill()`-based traversal) confirms the fix blocks progression as
intended (see item 2 above). This CSS characteristic was present unmodified
in Loop 01 and is not something this Loop introduced; it is recorded as a
durable lesson for a future Loop rather than corrected here, since altering
the shared `.pending-control`/`.btn` sizing rules is outside the three
required evidence-backed changes and risks unintended regressions elsewhere
in the frozen-gate-passing candidate.

## History of objective attempts

1. **`evidence-attempt-1/`** — exit code `0`. All 7 gates passed on the
   first attempt after implementing the three changes; metrics matched Loop
   01 exactly (see investigation above). Preserved unchanged as the first
   verification run; not deleted or overwritten.
2. **`evidence/`** — exit code `0`. Identical gate results and metrics to
   attempt 1, run with the exact `--out` path required by this Loop's task.
   This is the authoritative evidence directory. No code changes were needed
   between attempt 1 and this final run — both runs reflect the same
   implementation; the second run was the required, exactly-specified
   invocation.

## Files produced under this Loop's write scope

`index.html`, `styles.css`, `app.js`, `status.json`, `metadata.json`,
`prompt-history.md`, `self-observation.md` (this file), `evidence/`,
`evidence-attempt-1/`, and the updated Track-level
`..\manifest-fragment.json`.

Ad-hoc diagnostic scripts (`debug_probe.py` through `debug_probe6.py`) were
written to the exact designated scratch root
(`generated/harness/scratch/`) to verify the three fixes and diagnose the
metrics question; these are scratch artifacts, not part of this Loop's
candidate deliverable set.

## Explicitly out of scope for this Loop (not performed)

- No independent blind judge (`judge-accessibility`, `judge-human-use`) was
  run.
- No `new_best` or promotion decision was made; `metadata.json` and
  `manifest-fragment.json` both record `decision: needs_human_review`.
- No Loop 03 was created.
- No Manifest merge, Navigation Judge, Evidence Gate, or Viewer build was
  performed.
- No other Track's files were read, written, or otherwise touched.
- Loop 01 and its evidence were never modified.
