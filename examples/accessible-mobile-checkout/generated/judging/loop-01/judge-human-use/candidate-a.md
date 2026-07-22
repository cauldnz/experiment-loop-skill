# candidate-a — human-use judgement

- Judge: `judge-human-use`
- Judge model: `claude-opus-4.7`
- Loop: `loop-01`
- Judged at: 2026-07-21T17:38:00+10:00
- `human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
- Objective gate note: All seven objective gates pass per `generated/judging/blind-loop-01/candidate-a/evidence/objective-report.json`. Qualitative human-use scores are not objective gates and are not used to override them.

## Operation evidence

- Navigation transcript: `generated/judging/loop-01/judge-human-use/navigation-transcript-a.json`
- Screenshots: `generated/judging/loop-01/judge-human-use/screenshots/candidate-a/`
- Runtime page errors observed: 0
- Console messages observed: 0

## Lens scores (raw, 1–5)

| Lens | Score |
|---|---|
| discoverability | 3 |
| navigation | 3 |
| input_burden | 3 |
| error_prevention_recovery | 3 |
| feedback_status | 3 |
| accessibility | 3 |
| responsive_touch_ergonomics | 3 |
| interruption_resumption | 2 |
| latency_perception | 2 |
| destructive_actions | 2 |
| cognitive_load | 3 |
| **human-use-quality (mean of 11)** | **2.73** |
| visual-information-clarity | 3 |

## Lens findings

- **discoverability** — H1 "Checkout", synthetic-scope banner, and 4 numbered task cards each with a live `Incomplete/Complete` badge in the top-right corner (visible on initial screenshot). Users can see at a glance which section is done. However there is no progress indicator, no section-nav, and no persistent visible order summary — the summary + Place order live only at the bottom of the page after all four task cards, so a user must know to scroll to complete the flow.
- **navigation** — One long continuous form; no skip-link; Edit contact/address/shipping/payment buttons live in the bottom summary and focus the first input of the target section. First Tab focus lands on the contact-name input. Keyboard users must Tab through every focusable to reach Place order.
- **input_burden** — Autocomplete tokens present, which helps AT autofill. Validation is permissive ("Please enter a value" for empty fields; email checks only for `@`). Section-level `Incomplete/Complete` badges give per-section progress. Down-side: `card-name` (payment info) is persisted to localStorage between reloads — the code excludes `card-number/expiry/security` but not `card-name` — so users returning after interruption see a partial payment leftover.
- **error_prevention_recovery** — Error summary at top with h2 "There is a problem" and per-field links that focus the field on click. `aria-invalid` + `aria-describedby` wired on invalid inputs. Messages are generic ("Please enter a value", "Please enter a valid email address") rather than field-specific — less actionable than candidates B or C. On invalid submit the error summary receives focus and the assertive status region announces "There are errors in the form. Please correct them to proceed."
- **feedback_status** — Status region is visually-hidden with `aria-live='assertive'`. Using assertive for routine transitions ("Processing your order...", "Order successfully placed.") is stronger than necessary and interrupts screen-reader users; polite would be the appropriate level. No aria-live coupling on the `Incomplete/Complete` badges so screen-reader users get no announcement when a section becomes complete.
- **accessibility** — Native semantics: fieldset/legend, labels-for, `aria-invalid`, error summary with `role='alert'` and `tabindex=-1` that receives focus. H1 + numbered H2s. No landmark `<aside>`/`<nav>`, no skip-link. `aria-live='assertive'` on status region is misused for routine updates. Card-name persistence on reload is a soft privacy concern.
- **responsive_touch_ergonomics** — At 320×568 no horizontal scroll; buttons and inputs meet the mobile-touch objective gate. The `Edit-{Contact/Address/Shipping/Payment}` buttons in the review section are small and closely spaced 2×2, tighter than corresponding controls in B and C.
- **interruption_resumption** — Auto-persists on every input; restores on reload — but `card-name` is restored too (payment-field leak). No user-visible Save or Clear controls, no aria-live announcement on restore, and no explicit statement to the user about what will or will not persist.
- **latency_perception** — Placement `setTimeout` is 500 ms (hard-coded) except under `prefers-reduced-motion` where it is 0. `aria-busy` is set and status announces "Processing your order...", but 500 ms is arbitrarily long for a purely local synthetic operation. Confirmation was not visible when I sampled 500 ms after click; it did appear before the duplicate-safety sample.
- **destructive_actions** — Duplicate-submit safety is weak: Place order button is disabled only inside the 500 ms `setTimeout` callback — during that window additional clicks/Enters schedule additional setTimeouts. A single `SYN-2048` did render, but there is no explicit `placementStarted` flag guarding submit, unlike candidate B. No user-facing destructive control (no Clear progress) — safer for accidental data loss but leaves the persisted card-name until submit clears storage.
- **cognitive_load** — Four task cards + bottom summary is a reasonable IA and the per-section badges help sighted users. But no persistent visible order summary or progress indicator, plus merging of "Order Summary and Review" into one bottom block (Edit buttons + confirmation checkbox + Place order), forces users to hold more state in working memory.

## Strengths

- Per-section `Incomplete/Complete` badge is a clear sighted-user progress cue.
- Reduced-motion path completes without delay (`setTimeout` 0 under `prefers-reduced-motion`).
- Section semantics + fieldset/legend + labels + error summary meet the accessibility gate baseline.
- Edit-{section} buttons in the review block focus the first input of the correct task card.

## Defects

- (significant) interruption_resumption — Payment field `card-name` is persisted to localStorage across reloads.
- (significant) destructive_actions — No `placementStarted` guard; Place order disabled only after the 500 ms setTimeout resolves.
- (moderate) accessibility — Status region is `aria-live='assertive'` for routine transitions (should be polite); `Complete/Incomplete` badges are not in a live region.
- (moderate) latency_perception — Hard-coded 500 ms placement delay for a purely local synthetic confirmation with no meaningful interim feedback.
- (moderate) error_prevention_recovery — Field error messages default to generic "Please enter a value" rather than field-specific guidance.
- (minor) discoverability — No skip-link, no section-nav, no progress indicator, and no persistent order summary.

## Uncertainty

- Blinded evidence; Track paradigm inferred from artifact behaviour (task cards with completion badges).
- Confirmation visibility at 500 ms was not visible when sampled by Playwright but did render before the duplicate-safety sample.

## Loop 02 recommendation

- Priority: high.
- Change: Exclude `card-name` from the persistence allowlist and add a `placementStarted` flag that disables the submit path immediately on the first click of Place order (not inside the `setTimeout` callback); also reduce the non-reduced-motion setTimeout from 500 ms to ≈150 ms and change the status region `aria-live` from `assertive` to `polite` for routine flow transitions.
- Evidence: `generated/judging/blind-loop-01/candidate-a/app.js` lines 17 and 42 (persist filter), lines 179–260 (submit + timeout), and `generated/judging/loop-01/judge-human-use/navigation-transcript-a.json` entry `reload persistence check`.
