# Adoption / Rejection Matrix — synthesis-loop-02

- **Loop:** synthesis-loop-02 (synthesis track)
- **Model role / model:** synthesizer / claude-opus-4.8
- **Immediate parent:** synthesis-loop-01 (hill-climb)
- **Ancestor parents (true multi-parent lineage):** single-page-loop-02, resumable-wizard-loop-02, task-cards-loop-01
- **Paradigm:** single-page landmarked one-page checkout (inherited)

synthesis-loop-02 is an immediate hill-climb of synthesis-loop-01. A fresh copy of the Loop 01
functional files (`index.html`, `styles.css`, `app.js`) was authored into `loop-02`, and only the
evidence-backed panel-feedback changes below were applied. Loop 01 was **not** mutated. All prior
three-parent adopt/reject decisions are inherited unchanged.

## Hypothesis

Adopt every synthesis-loop-01 panel-feedback instruction (focus-safe skip destination, lower default
vertical density via persisted default-on compaction after safe restore, user-neutral shipping
default status, a non-sensitive persisted placed flag, and a larger touch-target margin) while
preserving every frozen invariant and keeping all seven objective gates blocking — removing residual
accessibility and human-use frictions without regressing the objective harness or the inherited
multi-parent synthesis.

## Feedback source (input evidence only)

- `judging/synthesis-loop-01/aggregate/synthesis-loop-02-feedback.json`
- `judging/synthesis-loop-01/aggregate/panel-scores.json`
- `judging/synthesis-loop-01/aggregate/dissent.md`
- `judging/synthesis-loop-01/judge-accessibility/manifest-ready.json`
- `judging/synthesis-loop-01/judge-human-use/manifest-ready.json`

The Loop 01 `panel_score` (4.68) and `visual_information_clarity` (4.5) are independent-judge input
evidence cited only as the source of these instructions. **No synthesizer-authored qualitative score
is claimed for synthesis-loop-02;** its independent qualitative judging remains pending.

## Loop 01 panel-feedback adoption

| # | Instruction (source judge) | Decision | Realized in | Gate safety |
|---|----------------------------|----------|-------------|-------------|
| 1 | Make the skip destination programmatically focusable; skip activation moves focus to a named checkout/form start, never BODY. (judge-accessibility) | **Adopt** | `index.html` `form#checkout-form` gains `tabindex="-1"`; `app.js` skip-link handler preventDefaults, focuses the named form (falls back to `contact-name`), scrolls into view, announces move. | Additive; target is a named form start, never BODY. |
| 2 | Reduce initial/resumed vertical density without wizard steps; default compact-completed ON only when safe restore records ≥1 completed section; persist compact preference safely; never leave hidden descendants focusable. (judge-accessibility, judge-human-use) | **Adopt** | `app.js` `restoreSafeState` defaults compaction ON only when contact/delivery is complete on restore; a saved explicit preference wins and is re-persisted; compact checkbox change persists preference. Reveal-safe `.compacted-body` keeps descendants operable for the harness but every compacted descendant gets `tabindex="-1"` and the body is `aria-hidden`. `styles.css` intro padding reduced. No wizard steps. | Compaction disabled while placed and expands on placement; keyboard gate runs fresh with compact OFF; hidden descendants leave the tab order. |
| 3 | Untouched preselected shipping must not claim Complete; show a user-neutral status until focused/changed/acknowledged, then Complete. (judge-human-use) | **Adopt** | `index.html` shipping badge starts as `Default selected: Standard`; `app.js` `stateBadge` keeps that until `shippingAcknowledged`, then `Complete`. Shipping focus/change set and persist a non-sensitive `shippingAcknowledged` flag; an unacknowledged default shipping section is never auto-compacted. `sectionIsComplete('shipping')` unchanged. | No harness assertion checks badge text; placement/progress semantics unchanged. |
| 4 | Persist only a non-sensitive placed flag/confirmation ID so post-confirmation reload keeps Place order disabled and announces `This synthetic order was already placed as SYN-2048.`; never persist payment secrets. (judge-human-use) | **Adopt** | `app.js` `completeOrder` persists only `{ placed:true, confirmationId:'SYN-2048' }` with the existing non-sensitive fields; `restoreSafeState` → `applyPlacedState` disables Place order, reveals confirmation, and shows the new `#placed-banner`. `handleEditAfterPlacement` clears the placed flag when a new synthetic order begins (harness error-recovery clear triggers the same reset). | Payment fields never persisted → resilience secret-absence checks hold; non-editing reloads stay disabled. |
| 5 | Improve target margin above exact 24px where practical; preserve reduced-motion and mobile layout. (panel improvement instruction) | **Adopt** | `styles.css` raises compact-toggle and choice-card / review-check hit areas from 24px to 28px. Reduced-motion media query and responsive layout untouched. | Larger targets only increase the mobile-touch-gate margin. |

## Out-of-scope features confirmed absent

No account creation, discounts/coupons, recommendations/upsell, external assets, extra checkout
steps, or unrelated features were added. The content-fidelity gate confirms forbidden scopes
(account, sign in, coupon, recommendation, upsell, stock) remain absent.

## Inherited three-parent decisions (unchanged)

All prior three-parent adopt/reject decisions from synthesis-loop-01 remain inherited. No parent-level
adoption or rejection was revised; only Loop 01 panel feedback was layered on top. See
`synthesis/loop-01/adoption-rejection-matrix.json` / `.md`.

- **single-page-loop-02 — primary structural template (inherited):** still adopts landmark trio + skip
  link (skip link now focus-safe, #1), one-page anchor nav + direct Edit controls, section-grouped
  error summary, compact-completed disclosure with focus-excluded descendants (now default-on after
  safe restore, #2), fictional hints + atomic single placement (now with persisted placed flag, #4).
  Still rejects: missing confirmed clear control (remedied by B); literal card hints outside a
  synthetic demonstration (retained only here).
- **resumable-wizard-loop-02 — safety/progress contributor (inherited):** still adopts `role=progressbar`
  with `aria-valuetext`, step-local validation, explicit Save progress, confirmed cancellable Clear
  saved progress, and the single named SYN-2048 confirmation. Still rejects: shipping-in-aside, and
  extra step transitions.
- **task-cards-loop-01 — independent task-status contributor (inherited):** still adopts independently
  understandable per-section completion state (shipping default now user-neutral, #3) and direct
  per-section editability. Still rejects: collapsed-but-focusable content, silent review reset, flat
  error dump, weak landmarks, and Loop 01 all-open density.

## No-regression check

synthesis-loop-02 passes **all seven** blocking gates on the same canonical fixture
(`e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894`) as synthesis-loop-01 and all three
ancestor finalists — no objective pass-to-fail regression. Candidate `failed_gate_ids: []`, external
requests `0`.

| Comparator | failed_gate_ids | external_request_count | report |
|-----------|-----------------|------------------------|--------|
| synthesis-loop-01 | [] | 0 | `synthesis/loop-01/evidence/objective-report.json` |
| single-page-loop-02 | [] | 0 | `track-single-page/loop-02/evidence/objective-report.json` |
| resumable-wizard-loop-02 | [] | 0 | `track-resumable-wizard/loop-02/evidence/objective-report.json` |
| task-cards-loop-01 | [] | 0 | `track-task-cards/loop-01/evidence/objective-report.json` |

## Permanent caveats (preserved)

- **Path-remediation procedural caveat (permanent):** During task-cards-loop-01, fifteen diagnostic
  scripts were written at the repository root outside the task write scope, and resumable-wizard-loop-02
  later deleted them before quarantine and omitted scratch provenance. Remediated with a permanent
  caveat. Forensic analysis found no environment/credential reads, no external data, no generated
  secrets, and no network hosts; the recovered `test-gates.py` was byte-identical to the frozen
  harness. The caveat is procedural only and implies no functional invalidity. Evidence:
  `harness/path-violation-evidence/provenance.json`.
- **Reboot-interruption recovery caveat (permanent, inherited):** synthesis-loop-01's records were
  completed by an owner-authorized post-reboot continuation after the original agent handle did not
  survive a PC reboot. Its terminal objective run had already completed (exit 0, all seven gates
  passing) before the interruption and was not rerun; all immutable Loop 01 functional outputs were
  hash-verified against `synthesis/recovery/recovery-inventory.json`. synthesis-loop-02 copied those
  verified files as its starting point without mutating Loop 01. Evidence:
  `synthesis/recovery/recovery-inventory.json`, `synthesis/recovery/post-recovery-verification.json`.
