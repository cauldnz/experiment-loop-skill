# candidate-c — human-use judgement

- Judge: `judge-human-use`
- Judge model: `claude-opus-4.7`
- Loop: `loop-01`
- Judged at: 2026-07-21T17:36:00+10:00
- `human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
- Objective gate note: All seven objective gates pass per `generated/judging/blind-loop-01/candidate-c/evidence/objective-report.json`. Qualitative human-use scores are not objective gates and are not used to override them.

## Operation evidence

- Navigation transcript: `generated/judging/loop-01/judge-human-use/navigation-transcript-c.json`
- Screenshots: `generated/judging/loop-01/judge-human-use/screenshots/candidate-c/`
- Runtime page errors observed: 0
- Console messages observed: 0

## Lens scores (raw, 1–5)

| Lens | Score |
|---|---|
| discoverability | 4 |
| navigation | 4 |
| input_burden | 4 |
| error_prevention_recovery | 4 |
| feedback_status | 5 |
| accessibility | 4 |
| responsive_touch_ergonomics | 4 |
| interruption_resumption | 5 |
| latency_perception | 4 |
| destructive_actions | 4 |
| cognitive_load | 5 |
| **human-use-quality (mean of 11)** | **4.27** |
| visual-information-clarity | 4 |

## Lens findings

- **discoverability** — Progress stepper (with narrated `aria-valuetext`), persistent Order summary showing shipping method and totals, banner declaring synthetic scope, and a clear "Continue to delivery address" CTA. Minor friction: shipping selection lives in the aside not the wizard body, so users who ignore the summary card may not know when it was set.
- **navigation** — Wizard exposes exactly one active Continue at a time; Back per step; Edit buttons on the review jump to the correct step and focus its heading (`tabindex=-1`). Skip-link "Skip to checkout steps" is the first Tab stop, but pressing Enter left `document.activeElement` at `BODY` rather than the wizard-form target (target lacks `tabindex=-1`), so screen-reader users may not perceive the jump.
- **input_burden** — Autocomplete tokens present; validation is tolerant (any 4-digit postcode, any 12–19 digit card number, generic phone); explicit Save/Clear progress buttons; the wizard keeps at most 3–5 fields visible at once.
- **error_prevention_recovery** — Per-field `aria-invalid` + `aria-describedby` chained to help+error; error summary lists each problem as a button that navigates back to the offending step and focuses the field; a nuanced status message ("N item(s) still need attention — you can continue now and fix them before placing your order") means partial errors never block flow.
- **feedback_status** — Polite `aria-live` status region receives running updates ("Step X complete", "Placing your order…", "Order placed. Confirmation SYN-2048.", "Resumed your saved progress…"). `aria-busy` on Place order during placement. Progress bar `aria-valuetext` narrates the current step.
- **accessibility** — Native semantics (fieldset/legend, labels-for, form submit), pending steps are `aria-hidden=true` with their controls set `tabindex=-1`, single `<main>` + `<aside>` landmarks, `role='progressbar'` narrated. Minor issue: skip-link Enter left focus at BODY; `.radio-row` labels carry unusual `tabindex='-1'` but harmless.
- **responsive_touch_ergonomics** — At 390×844 and 320×568 no horizontal scroll; Continue/Back are large, radio rows are full width, primary CTA has generous padding. Mobile-touch objective gate passes independently.
- **interruption_resumption** — Explicit Save + auto-persist on input; hydrate restores field values, step position, and shipping method; polite announcement about payment non-persistence. On reload, all four payment fields returned empty (transcript `reload persistence check`).
- **latency_perception** — 120 ms placement `setTimeout`; `aria-busy` set; status announces "Placing your order…". Reduced-motion path still succeeds.
- **destructive_actions** — Clear-saved-progress button reloads without confirm dialog but its label is unambiguous and payment was never stored to lose. Repeated Place order produced exactly one `SYN-2048` (transcript `duplicate-safety report`: `placeOrderAriaDisabled: 'true'`).
- **cognitive_load** — One task per view with a persistent summary and progress. The review reprints every entered value verbatim (contact, address, shipping label, and card ending in last-4 with expiry), so verification does not require scroll-hunting.

## Strengths

- Wizard grouping keeps working memory low and gives explicit control (Continue, Back, Edit, Save progress).
- Review step reprints every field verbatim, including a card-masked last-4 that confirms entry without exposing the PAN.
- Strongest interruption-resumption of the three: explicit save/clear, restored step position, polite status about payment non-persistence.
- Progress bar with `aria-valuetext` narration is the clearest orientation cue for screen-reader users.

## Defects

- (minor) navigation — Skip-link target `#wizard-form` lacks `tabindex=-1`; activation left `document.activeElement` at BODY.
- (minor) discoverability — Shipping method lives inside the Order summary aside rather than a wizard step; users focused on the wizard body may not realise when it was chosen.
- (cosmetic) accessibility — `radio-row` labels carry `tabindex='-1'`, an unusual but harmless pattern.

## Uncertainty

- Blinded evidence; Track paradigm inferred from artifact behaviour only (wizard with progressive reveal).
- Screen-reader announcement fidelity was not measured with an actual AT; findings rely on ARIA attributes, live regions, and focus movement observed via Playwright.

## Loop 02 recommendation

- Priority: medium.
- Change: Add `tabindex='-1'` to `#wizard-form` (or move the skip target to the first step heading) so activating the skip-link moves programmatic focus and screen-reader position, and consider narrating shipping-method changes in the polite status region so wizard-focused users know when Standard/Express is selected.
- Evidence: `generated/judging/loop-01/judge-human-use/navigation-transcript-c.json` entries `keyboard: first Tab focus` and `keyboard: activated skip-link`.
