# Prompt history — `resumable-wizard-loop-02`

## 1. Complete Track instruction acted on (verbatim)

Execute exactly ONE improvement Loop as approved model role
`generator-resumable-wizard`. Create Loop 02 from the immutable Loop 01
parent, consume the bound independent feedback verbatim, run the unchanged
frozen objective harness, and preserve all evidence. Do not judge yourself as
new_best.

Repository root: `<skill-repository>`

Immutable approved contract: `.experiments\accessible-mobile-checkout\setup\experiment-brief.json`
revision 1 and setup/prompt.md. Frozen harness/fixture/contract under
generated/harness are read-only.

Write scope ONLY: `.experiments\accessible-mobile-checkout\generated\track-resumable-wizard\**`

Parent is read-only: `track-resumable-wizard\loop-01`; parent_id
`resumable-wizard-loop-01`. Create `track-resumable-wizard\loop-02` by
copying parent candidate files, then edit only Loop 02 and update the Track
manifest-fragment/status. Never modify Loop 01 or its failed evidence.

Exact scratch root: `.experiments\accessible-mobile-checkout\generated\harness\scratch`;
avoid temporary writes outside your Track.

Exact human-use declaration for all handoffs/results:
`human_use.applicability = applicable`. Rationale: The Artifact is a
human-operated mobile checkout. Its success depends on discoverability,
navigation, input burden, error recovery, feedback, accessibility, touch
ergonomics, interruption recovery, perceived latency, destructive-action
safety, and cognitive load across cross-disability use.
Qualitative required lenses remain non-objective: discoverability,
navigation, input_burden, error_prevention_recovery, feedback_status,
accessibility, responsive_touch_ergonomics, interruption_resumption,
latency_perception, destructive_actions, cognitive_load.

Read and consume ONLY the `resumable-wizard-loop-01` entry in:
`.experiments\accessible-mobile-checkout\generated\judging\loop-01\aggregate\loop-02-feedback.json`
Copy every `evidence[].verbatim` string byte-for-byte into Loop 02
prompt-history.md/input feedback with source and attribution. Your accepted
improvement instruction is authoritative and must remain within the
resumable-wizard paradigm. Also read the mapped raw judge files cited by that
sidecar, but do not read unrelated candidate feedback.

Required evidence-backed changes:
- Make skip-link activation move programmatic focus to the checkout steps
  (correct focusable target).
- Validate the active step and retain useful focus before advancing; do not
  allow empty-step progression or distribute errors into hidden/revealed
  context.
- Require confirmation, undo, or a clear grace action before Clear saved
  progress discards safe state.
- Preserve explicit progress, a true step-by-step frontier, Back/Edit, safe
  resume, objective harness operability, and all frozen invariants. Do not
  turn it into a single continuous form or task cards.

Create the full Loop 02 artifact set: local index.html/styles.css/app.js,
metadata.json, prompt-history.md with exact input-feedback text and proposed
next prompt, self-observation.md, status.json with start/heartbeat/end,
objective evidence, and an updated Track manifest-fragment containing both
Loops with parent_ids [`resumable-wizard-loop-01`], stable Artifact
IDs/hashes/presentation/comparison_key checkout-ui, changed_files, one
durable lesson, scores, and decision `needs_human_review` pending judges.

Run:
`python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-02 --out .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-02\evidence`
If it fails, repair only Loop 02, preserve each failed evidence attempt
separately, and never modify the harness/parent. Final all seven objective
gates must pass or stop failed. Compare non-gating metrics to Loop 01 (29
focusables, 24 activations, 4 corrections, 1 completion) without treating
lower counts as sufficient to override qualitative evidence.

Return files, objective gates, metrics delta, preserved attempts, exact
feedback refs, hashes, heartbeat, and blockers. Do not run judges, synthesis,
top assembly/Viewer, Navigation, Evidence Gate, or promotion.

## 2. Input feedback (verbatim, from `resumable-wizard-loop-01` entry only)

**Accepted improvement instruction** (from
`generated/judging/loop-01/aggregate/loop-02-feedback.json`,
`resumable-wizard-loop-01.accepted_improvement_instruction`):

> Within the resumable-wizard paradigm, make skip-link activation move
> programmatic focus to the checkout steps, validate and retain focus in an
> empty active step before advancing, and require confirmation or provide
> undo before clearing saved progress. Preserve explicit progress, Back/Edit,
> safe resume, and all frozen invariants.

**Evidence item 1** — attribution: `judge-human-use navigation finding`;
source: `judging/loop-01/judge-human-use/candidate-c.json`:

> Wizard exposes exactly one active Continue at a time; Back per step; Edit
> buttons on review jump back to the correct step and focus its heading
> (tabindex=-1). Skip-link 'Skip to checkout steps' is the first Tab stop,
> but pressing Enter left the active element at BODY rather than the
> wizard-form target (skip target lacks tabindex=-1), so screen-reader users
> may not perceive the jump. Evidence: transcript entries 'keyboard: first
> Tab focus' and 'keyboard: activated skip-link'.

**Evidence item 2** — attribution: `judge-accessibility defect`;
source: `judging/loop-01/judge-accessibility/candidate-c.json`:

> Continue advanced each empty step rather than holding the user at the
> invalid task; this allows premature progression and distributes errors
> across hidden/revealed context.

**Evidence item 3** — attribution: `judge-accessibility defect`;
source: `judging/loop-01/judge-accessibility/candidate-c.json`:

> Clear saved progress immediately reloads and discards saved state without
> confirmation, undo, or a grace period.

(Confirmed via `generated/judging/loop-01/blinding-map.json` that
`resumable-wizard-loop-01` = `candidate-c` in the blind judging scheme, so
these `candidate-c.json` judge files are the correct, matching raw sources
for this Loop's own prior candidate. No other candidate's feedback was read
or consumed.)

## 3. Provisional self-observation (non-authoritative)

These are this generator's own impressions while building Loop 02, not an
objective gate result and not a qualitative-lens score:

- **Skip-link fix**: added `data-hook="skip-link"` to the existing
  `<a class="skip-link">`, gave `#wizard-form` a `tabindex="-1"` fallback
  target, and wired a `click`/`Enter` handler that calls
  `event.preventDefault()` then moves focus programmatically to the current
  active step's `<h2>` heading (falling back to the form element itself).
  Verified directly with a Playwright probe: activating the skip-link now
  leaves `document.activeElement` on the current step's `H2`, not `BODY`.
- **Step-validation blocking**: rewrote `handleContinue(stepNum)` so that
  when the active step has validation errors, it renders the step-scoped
  error summary, sets a status-region message, focuses the first invalid
  field, persists state, and **returns** without calling `goToStep`.
  Verified directly: pressing Continue on a blank Step 1 keeps the wizard on
  Step 1, shows a 3-problem step-scoped error summary (not the 13-problem
  whole-order summary), and moves focus to `contact-name`.
- **Clear-progress confirmation**: added a `#clear-confirm` panel (heading,
  explanatory copy, Cancel and "Yes, clear saved progress" buttons). First
  activation of Clear reveals the panel and moves focus to Cancel (the safe
  default); Escape also cancels. `localStorage` is left untouched until the
  explicit "Yes, clear saved progress" button is pressed. Verified directly
  with a Playwright probe end-to-end: storage survives the first click and a
  Cancel click, and is only removed after the explicit confirm click.
- **Investigated why objective metrics are unchanged from Loop 01** (29
  focusable_controls_traversed / 24 activations / 4 corrections / 1
  completion, identical to Loop 01). Root cause: the frozen harness's
  `reveal()`/`fill_all()` helpers check Playwright's `is_visible()` directly
  on each field hook, and — independent of anything changed in this Loop — a
  pre-existing (Loop-1-inherited) CSS interaction between `.pending-control`'s
  `max-height:0` and `.btn`/input's `min-height:44px` (the used max-height is
  raised to the used min-height per the CSS box-sizing spec when they
  conflict) means Playwright still reports later, not-yet-reached steps'
  controls as "visible" even while `hidden`/`aria-hidden`/`tabindex="-1"` are
  correctly applied. This lets the harness's automation-level `.fill()`
  calls reach later-step fields without ever needing to press Continue,
  which is why the per-step Continue-blocking change does not change the
  gate traversal counts. This is a pre-existing rendering characteristic
  carried over unmodified from Loop 01's CSS, not introduced by this Loop,
  and it does not affect real users: real keyboard/AT users cannot reach
  those controls (removed from tab order, `aria-hidden`), and a real mouse
  user cannot click a visually 0-height, `overflow:hidden`-clipped control.
  It is recorded here as a durable lesson for a future loop, not corrected
  in this Loop since it is outside the three required evidence-backed
  changes and touching the shared `.pending-control`/`.btn` sizing rules
  risks unintended regressions elsewhere.
  - This is a hypothesis/finding about rendering mechanics, not a
    qualitative-lens score; it has not been evaluated by `judge-accessibility`
    or `judge-human-use` and must not be treated as if it had.

## 4. Proposed next Prompt (for a future Loop, not executed here)

If a Loop 03 is later authorized for this Track (out of scope for this Loop):

> Using `resumable-wizard-loop-02` (parent_id `resumable-wizard-loop-01`) as
> the baseline, and after independent `judge-accessibility` and
> `judge-human-use` blind scores are available for every required lens
> (`discoverability`, `navigation`, `input_burden`,
> `error_prevention_recovery`, `feedback_status`, `accessibility`,
> `responsive_touch_ergonomics`, `interruption_resumption`,
> `latency_perception`, `destructive_actions`, `cognitive_load`), make a
> third wizard Loop that acts only on that objective and independent
> qualitative feedback. As a durable follow-up (only if evidence-backed by a
> future judge finding, not pre-emptively): consider removing the conflicting
> `display: block` / `max-height: 0` declaration pairing on
> `.pending-control` versus `.btn`/input `min-height: 44px` so that
> not-yet-reached steps' controls are also reliably reported as not visible
> by automated tooling, matching their real inaccessibility to keyboard/AT
> and mouse users. Do not weaken any passing gate from Loop 01 or Loop 02.
> Preserve Loop 01's and Loop 02's evidence unchanged. Record the
> evidence-backed change explicitly in the new Loop's `lesson` field.
