# Accessibility judge — candidate-a

**Judge:** `judge-accessibility` · **Model:** `gpt-5.6-terra` · **Iteration:** `synthesis-loop-01`

## Objective gate
Persisted objective evidence is acknowledged as a terminal pass; it was not rerun. Qualitative findings below do not override that result.

## Scores
| Lens | Score | Finding |
| --- | ---: | --- |
| discoverability | 5 | The synthetic banner, clear H1, five named section links, numbered section headings, progressbar, visible order summary, and direct labels make the checkout’s purpose and available tasks explicit. |
| navigation | 4 | All five anchor links changed hash/position; compact and review Edit controls opened the exact section and focused its first control; Tab/Shift+Tab order was logical. Deduction: Enter on the skip link set #checkout-form but focus landed on BODY because the form target is not programmatically focusable. |
| input_burden | 4 | Field-level synthetic examples, input modes, persistent totals, direct section edits, radio shipping and a single review confirmation reduce hesitation. The full 13-field, five-section form remains long at 390px. |
| error_prevention_recovery | 5 | Empty submit focused an actionable grouped summary (13 items, four sections); its first link focused contact-name. Invalid fields received messages/aria-invalid; a later invalid-payment submit retained valid contact/delivery values. |
| feedback_status | 5 | Progress exposes completed/next section text, saving/restoring/clearing status is announced, a short local busy state appears before confirmation, and successful placement reports SYN-2048. |
| accessibility | 4 | Observed landmark structure, labelled native fields/fieldsets, semantic status/alert/progressbar, visible keyboard focus, native radio arrows, no trap, safe compaction, and reduced-motion behavior are strong. The non-focused skip destination prevents a top score. |
| responsive_touch_ergonomics | 4 | At 390x844 there was no horizontal overflow; cards/buttons/inputs are generally generous and measured minimum interactive dimensions were 24x24px. The exact-minimum native radio/checkbox footprint and long one-page reach keep this below excellent. |
| interruption_resumption | 5 | Explicit save preserved only eight safe fields plus shipping; reload restored them and left all four payment fields blank. Clear uses confirmation, Cancel and Escape, then correctly clears/reloads. |
| latency_perception | 4 | Placement exposes an immediate 'Placing local synthetic order' busy status and resolves to a focused confirmation after the short local delay. Focus temporarily fell to BODY while the disabled action handed off, so feedback is good but not seamless. |
| destructive_actions | 5 | Clear is explicit, describes scope and irreversibility, focuses Cancel, supports Escape and preserves data on cancellation. Confirming clear erased storage. Placement disabled its button and a duplicate native submit kept exactly one confirmation. |
| cognitive_load | 4 | One-page orientation, five-step progress, compact completed sections and concise section status reduce re-orientation. Initial completion still exposes a long multi-section mobile form; the full error panorama can be demanding despite its grouping. |

**Unrounded mean (11 lenses):** 4.454545454545454

**Visual/information clarity:** 4/5 — clear typographic and color hierarchy across captured 390px states; the initial full-form density holds it below excellent.

## Observed evidence
- 36 discoverable controls were exercised; the transcript records 56 actions and 17 keyboard actions.
- Empty keyboard submission focused the error summary; its grouped first link focused `contact-name`; later invalid payment preserved valid safe values.
- Save/reload restored eight safe fields and shipping; four payment fields were empty, and stored data had only `fields` and `shipping`.
- Clear was opened, Escape-dismissed, Cancelled, then confirmed; the compact mode hid completed bodies with zero remaining focusable descendants.
- Local placement announced busy state, focused one `SYN-2048` confirmation, and rejected a duplicate native submit.
- At 390×844: no horizontal overflow; minimum measured target 24×24px; reduced motion matched with 0.01ms transition duration; console errors and external requests were zero.

Evidence: `navigation-transcript-a.json`; `screenshots/01-initial-390x844.png`, `02-error-recovery-390x844.png`, `03-save-clear-confirmation-390x844.png`, `04-compact-edit-390x844.png`, and `05-confirmation-390x844.png`; persisted `../../../synthesis/loop-01/evidence/objective-report.json`.

## Strengths
- Semantically rich, keyboard-operable recovery and progress feedback.
- Excellent safe resumption boundary and cancellable destructive action.
- Safe progressive disclosure and duplicate-safe confirmation.

## Defects and uncertainty
- Skip activation left focus on `BODY` rather than the named form start.
- The full five-section form/error panorama is still vertically dense on mobile; exact-minimum 24px native affordances give little motor margin.
- Chromium/Playwright cannot establish real screen-reader speech or broader AT/browser behavior; local delay is not real payment latency.

## Feedback for Synthesis Loop 02
Make the skip destination focusable and focus it on activation. Then test a progress-anchored compact/resume pattern at 320px and 390px that reduces initial/error-state vertical density without wizard steps or keyboard-focusable hidden descendants. Preserve the grouped recovery, safe storage boundary, Escape cancellation, and one `SYN-2048` confirmation.

## Pairwise
Deferred: only one synthesis candidate is present, so no A/B preference is fabricated.
