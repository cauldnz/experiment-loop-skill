# Blind human-use judge — synthesis-loop-01 candidate-a

- **Judge:** judge-human-use · **Model:** claude-opus-4.7 (no fallback used)
- **Candidate:** candidate-a · **Iteration:** synthesis-loop-01
- **Viewport exercised:** 390×844, `prefers-reduced-motion: reduce`, mobile touch context
- **Objective terminal pass accepted:** yes — `synthesis/loop-01/evidence/objective-report.json`, all seven gates PASS, `failed_gate_ids: []`, 0 external requests. Harness was not rerun.
- **Generator identity / paradigm labels:** intentionally ignored during scoring.
- **Not read while judging:** the sibling `judge-accessibility/` directory.

Judging was performed by driving the candidate live in local Playwright/Chromium at 390×844 with a full realistic cross-disability journey (see `navigation-transcript-a.json` and `screenshots/`).

## 1. Scores (integer 1–5)

| Lens | Score |
| --- | --- |
| discoverability | 5 |
| navigation | 5 |
| input_burden | 5 |
| error_prevention_recovery | 5 |
| feedback_status | 5 |
| accessibility | 5 |
| responsive_touch_ergonomics | 5 |
| interruption_resumption | 5 |
| latency_perception | 5 |
| destructive_actions | 5 |
| cognitive_load | 4 |
| **Unrounded arithmetic mean of the 11 lenses** | **4.909090909090909** |
| visual_information_clarity | 5 |

## 2. Lens findings

### 2.1 Discoverability — 5
`<header>`, `<main data-hook=checkout-root>`, `<aside>`, `<nav aria-label="Checkout sections">`, and `<footer>` provide five DOM landmarks; a `role="note"` synthetic banner adds a labelled prelude; `role="progressbar"` with `aria-valuemin/max/now` and a descriptive `aria-valuetext` (e.g. `"0 of 5 sections complete: start with Contact."`) provides orientation; a `.skip-link` targets `#checkout-form`; the section-nav offers five in-page anchors; H1 introduces the flow and H2s label each task section. Evidence: `logs/landmarks.json`, `screenshots/01-initial-390x844.png`, `navigation-transcript-a.json#steps[initial_load]`.

### 2.2 Navigation — 5
Section-nav anchors scroll to `#contact / #delivery / #shipping / #payment / #review` without page transitions. Every review-section Edit button and every compact-summary Edit button opens the target section, expands its body if compacted, and focuses the first input. No focus trap observed across 40 Tab presses in either expanded or compact modes. No "Continue" click is required to advance. Evidence: `logs/tab-order.json`, `logs/tab-order-compact.json`, `navigation-transcript-a.json#steps[nav_click_#contact..#review, edit_contact_from_compact]`.

### 2.3 Input burden — 5
Every field carries an inline `Synthetic value: …` hint via `aria-describedby`, removing guessing about demonstration values; native autocomplete tokens (`name`, `email`, `tel`, `shipping address-line1/level2/level1/postal-code/country-name`, `cc-number/exp/csc/name`) are set, so switch and voice users benefit from native completion; Standard shipping is preselected so zero clicks are required for the default; the one-page structure eliminates multi-screen Continue navigation.

### 2.4 Error prevention and recovery — 5
Empty submit produced the exact string:

> Check 13 items in 4 sections … Your entries are preserved. Start with one link per affected section, or expand the full list. Contact: 3 items need attention · Delivery address: 5 items need attention · Synthetic payment: 4 items need attention · Review …

Focus moved to `#error-summary` (`role="alert"`, `aria-live="assertive"`, `tabindex="-1"`); clicking the first grouped link moved focus to `#contact-name`. On blur with `"abcd"` in `#address-postcode`, an inline field error appeared, `aria-invalid="true"` was set, and `aria-describedby` chained to the error id; restoring `"2000"` cleared the error. Values were preserved through submit-time validation. Evidence: `screenshots/02-empty-submit-error-summary.png`, `screenshots/03-error-recovery-invalid-postcode.png`, transcript steps 9–10 and 13–14.

### 2.5 Feedback / status — 5
Polite `role="status"` region announces state changes (save, restore, shipping change, cancel-clear, submit); `role="alert"` summary is used for the batched error announcement; `aria-valuetext` on the progressbar transitions through `"N of 5 sections complete: next: <label>."` and finalises to `"Order placed. Confirmation SYN-2048."`; `aria-busy="true"` is set on Place order while the local placement resolves, then `"false"` on completion; section-state badges give a non-live per-section status ("Not started" / "In progress" / "Complete").

### 2.6 Accessibility — 5
Native semantics used first: real labels for/id, fieldsets with legends, real inputs with types, real radios, native `<details><summary>` for the order-summary and the error-summary "Show all corrections" list. `hidden` (not `display:none` and not `aria-hidden` tricks) is used to collapse completed section bodies, so compacted content **leaves** the tab order — verified by capturing 40 Tab presses in compact mode: `hidden-ancestor focus leaks: 0`. `prefers-reduced-motion: reduce` was applied and the page loaded and completed with no perceptible animation. ARIA is limited to `role="progressbar"`, `role="note"`, `role="status"`, `role="alert"`, `aria-invalid`, `aria-describedby`, `aria-expanded`, `aria-labelledby` — every case is justified.

### 2.7 Responsive touch ergonomics — 5
Of 47 audited controls at 390×844 with `has_touch=true, is_mobile=true`, only one was below 24×24: a non-interactive `<p class="help">` field help paragraph (a false positive of the audit selector). Every real interactive control — `<a>`, `<button>`, `<input>`, and `<label class="choice-card">` — measured ≥ 24×24 CSS pixels. No horizontal overflow was observed at 390×844. Choice-card labels present the whole card as a tap target rather than the radio dot. Evidence: `logs/touch-targets.json`, `screenshots/01-initial-390x844.png`.

### 2.8 Interruption / resumption — 5
`Save progress` button is present in addition to autosave on input/change; `localStorage["northstar-synthesis-checkout"]` contained only the eight safe-field keys and `shipping` — no `card-number`, `card-security`, or `card-expiry` (regex tested and key list explicit). After `page.reload()`, all eight safe fields restored, all four payment fields were empty, and the status live-region announced `"Safe progress restored. Re-enter synthetic payment details; they were not saved."` Evidence: `navigation-transcript-a.json#steps[payment_secret_check, reload_restore]`, `screenshots/09-post-reload-restored.png`.

### 2.9 Latency perception — 5
Every interaction other than placement responded within one frame. Placement uses a 180 ms `setTimeout` with `aria-busy="true"` and a polite `"Placing local synthetic order. Please wait."` message, so any perceived wait is explained. Zero external requests were fired during the entire realistic journey plus a reload (`external_requests: 0`), so no unbounded-wait risk exists.

### 2.10 Destructive actions — 5
Clear saved progress is a labelled two-step group:
1. Clicking the trigger reveals the `#clear-confirm` region and moves focus to Cancel (the safer button by default).
2. Escape acts as Cancel; Cancel restores focus to the trigger and leaves the storage unchanged.
3. Only the explicit `"Yes, clear saved progress"` button removes the storage key and reloads.

Place order is disabled after the confirmation node is inserted. I attempted a duplicate click and a synthetic `form.dispatchEvent(new Event('submit', …))` after confirmation; both left the `[data-hook="confirmation-id"]` count at 1 (transcript step 27: `before=1, after=1`). Evidence: `screenshots/06-clear-confirm-dialog.png`, `screenshots/08-confirmation-SYN-2048.png`, `navigation-transcript-a.json#steps[clear_progress_prompt,clear_progress_cancel,clear_progress_escape,clear_confirm_action,duplicate_submit_attempted,duplicate_dispatch_submit]`.

### 2.11 Cognitive load — 4
Held back by three observed frictions:
1. `compact-completed` is a strong disclosure control but is **off by default**, so cognitive-load-sensitive users see the full one-page form on first render — a substantial vertical panorama on 390×844.
2. The Shipping section badge reads **"Complete" from initial load** because Standard is preselected. The state is technically true, but it can be misread as the system claiming credit for work the user did not perform.
3. After a successful submit, `page.reload()` re-enables Place order (`place_order_disabled=false`) because the placed-flag is not persisted in the safe-restore ledger. A user reloading to review the confirmation could re-arm placement.

Positives: numbered step badges, per-section state badges, persistent order summary, and the compact disclosure remove considerable load once discovered.

### 2.12 Visual / information clarity — 5
Persistent order summary with subtotal / shipping / tax / total; the Review section restates the due amount adjacent to Place order; three distinct badge classes (`state-empty`, `state-progress`, `state-complete`); numbered progress list mirroring section order; confirmation card presents `SYN-2048` in an emphasised span. No overlapping controls or clipped text observed at 390×844.

## 3. Strengths (evidence-backed)

- Landmark trio + skip link + section-nav + progressbar cover discoverability more than once, without duplication.
- Section-grouped error summary with per-group counts, preserved-values reassurance, and a details/summary full list — the strongest observed error-recovery ergonomics.
- `hidden` on collapsed content — zero hidden-ancestor focus leaks across 40 Tab presses in compact mode.
- Two-step Clear saved progress with Cancel-focused-by-default, Escape dismissal, and unmodified storage on cancel.
- Payment secrets provably absent from localStorage; safe-only restoration on reload with a status announcement.
- Duplicate placement blocked both by the disabled button and by an idempotency guard on submit; `dispatchEvent(submit)` after confirmation did not double-fire.
- Zero external network requests across the entire realistic journey.

## 4. Defects (minor)

- **Compact-completed default:** off by default; dense first view on 390×844.
- **Shipping "Complete" pre-badge:** reads "Complete" before any user action on shipping.
- **Placed-flag not persisted:** after a successful submit, a reload re-arms Place order.

None of the above are objective-gate failures.

## 5. Uncertainty

- Screen-reader speech ordering was not captured; conclusions about `aria-valuetext` / `role="alert"` double-announcement are inferred from DOM state, not observed against JAWS/NVDA/VoiceOver.
- Visible-focus contrast against every background swatch was not measured pixel-by-pixel; the objective harness's contrast check is accepted for that dimension.
- Compact-completed disclosure was toggled once per section state; long-form user cognitive load under repeated switching was not stress-tested.

## 6. Residual friction

- Dense first-view on 390×844 without compact-on default.
- Non-user-actioned Shipping "Complete" label can mislead.
- Placed-flag does not survive reload.

## 7. Improvement instruction for Synthesis Loop 02

Reduce residual cognitive load at 390×844 **without** introducing wizard steps or making collapsed content keyboard-focusable. Specifically:

1. Default `compact-completed` to **ON** when the safe-restore ledger already records any completed section, and persist the user's compact preference in the ledger so revisits keep it.
2. Change the initial Shipping badge from `"Complete"` to a user-neutral `"Default selected: Standard"` (or `"Ready to review"`) until the user has focused or changed the choice; keep `"Complete"` once the user has acknowledged shipping.
3. Persist a placed-flag in the safe-restore ledger so that after a successful `SYN-2048` submit and a reload, Place order remains disabled and a status banner reads `"This synthetic order was already placed as SYN-2048."`

These changes must not weaken any harness gate and must not persist any payment secret.

## 8. Pairwise

Deferred until Synthesis Loop 02 / final Champion-vs-parent comparison. Only one synthesis candidate is present in Synthesis Loop 01, so an A/B preference from this judge would be fabricated. See `pairwise.json` and `pairwise.md`.
