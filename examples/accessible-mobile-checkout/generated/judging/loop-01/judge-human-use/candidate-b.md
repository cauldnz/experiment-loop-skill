# candidate-b — human-use judgement

- Judge: `judge-human-use`
- Judge model: `claude-opus-4.7`
- Loop: `loop-01`
- Judged at: 2026-07-21T17:37:00+10:00
- `human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
- Objective gate note: All seven objective gates pass per `generated/judging/blind-loop-01/candidate-b/evidence/objective-report.json`. Qualitative human-use scores are not objective gates and are not used to override them.

## Operation evidence

- Navigation transcript: `generated/judging/loop-01/judge-human-use/navigation-transcript-b.json`
- Screenshots: `generated/judging/loop-01/judge-human-use/screenshots/candidate-b/`
- Runtime page errors observed: 0
- Console messages observed: 0

## Lens scores (raw, 1–5)

| Lens | Score |
|---|---|
| discoverability | 4 |
| navigation | 4 |
| input_burden | 2 |
| error_prevention_recovery | 4 |
| feedback_status | 4 |
| accessibility | 3 |
| responsive_touch_ergonomics | 4 |
| interruption_resumption | 4 |
| latency_perception | 4 |
| destructive_actions | 4 |
| cognitive_load | 3 |
| **human-use-quality (mean of 11)** | **3.64** |
| visual-information-clarity | 4 |

## Lens findings

- **discoverability** — Site header, synthetic-scope banner, and in-page "Checkout sections" nav (Contact / Delivery / Shipping / Payment / Review) as anchor pills. Numbered section circles reinforce the 5-step arc. Order summary at the top with running total. Payment section carries a "Fictional card to use" fixture panel that reveals the exact demo values.
- **navigation** — Anchor pills jump between sections; `Edit contact` / `Edit shipping` buttons call `scrollIntoView` + focus the first field of the target section and narrate the move. First Tab focus lands on the section-nav "Contact" anchor. No true skip-link, but the section-nav row serves a similar purpose for sighted keyboard users and screen-reader users get a labelled nav landmark.
- **input_burden** — Validation is strict-fixture: state must equal `NSW` (case-sensitive), country must equal `australia`, card number must equal `4111111111111111`, expiry must equal `12/34`, CSC must equal `123`, cardholder must equal `alex morgan`. Any real-world variation is rejected. All inputs also have `autocomplete='off'`, which disables browser autofill / password-manager assistance — a documented accessibility anti-pattern for motor-constrained and cognitively-impaired users. The `Synthetic value:` helper text and the fixture card mitigate for sighted users who read them, but the underlying interaction burden is high.
- **error_prevention_recovery** — Empty submit produced 13 highly specific error messages routed through a single error summary that focuses itself and lists each item as a link ("Enter the synthetic phone number with at least 8 digits.", "Select NSW for this demonstration.", "Enter the 4-digit synthetic postcode."). `aria-invalid` + `aria-describedby` chained to the correct help+error IDs; on correction each field's error is cleared on input/change.
- **feedback_status** — Polite `aria-live` status region with `aria-atomic='true'` updates through the flow ("Safe contact, delivery and shipping progress saved…", "Placing local synthetic order. Please wait.", "Synthetic order placed once. Confirmation ID SYN-2048."). Assertive live on the error summary. Focus moves to the confirmation section on completion.
- **accessibility** — Solid landmark tree (header/nav/main/aside/footer), fieldset+legend per section, `aria-describedby` chained, error summary `role='alert'` with `tabindex=-1` that receives focus after invalid submit. Concerns: (a) Shipping uses a double-radio anti-pattern — `<label class='choice-card' role='radio' aria-checked>` wrapping a real `<input type='radio' aria-hidden='true'>` — SR users may hear the group twice or miss state updates; (b) `autocomplete='off'` on every field is an anti-pattern for AT-assisted form filling; (c) no visible skip-link even though the section-nav helps sighted keyboard users.
- **responsive_touch_ergonomics** — At 320×568 no horizontal scroll. Shipping choice-cards and Place-order button are large tap targets; section anchors are pill-sized. Mobile-touch objective gate passes independently.
- **interruption_resumption** — Safe fields auto-persisted on input; on reload restored and status announces "Safe progress restored. Re-enter synthetic payment details; they were not saved." Payment fields returned empty on reload (transcript `reload persistence check`). No manual save or clear controls.
- **latency_perception** — 180 ms placement `setTimeout`, `placeOrder.disabled=true` immediately, `aria-busy='true'` during processing, then narrated confirmation.
- **destructive_actions** — Duplicate submit is guarded twice (`placementStarted` flag + disabled button + re-narrated status "This synthetic order is already confirmed as SYN-2048. No duplicate was created."). One `SYN-2048` produced on repeated activation.
- **cognitive_load** — All five sections plus ~20 required fields on one continuously-scrolled page. Nav pills help orientation, but the sheer field count on a small viewport is heavy. Exact-match validation adds hidden rules a real user must reason through. The review block reprints only aggregate values rather than every field verbatim.

## Strengths

- Error messages are among the most specific and actionable observed — they name the exact field and expected format.
- `aria-live` status region combined with focused error summary gives strong feedback loops.
- Section-nav anchor pills give sighted keyboard users a fast way to jump around the long single-page flow.
- Duplicate submit guarded twice (flag + disabled button + status re-announce).

## Defects

- (significant) input_burden — Exact-fixture validation makes the checkout a memory test of the fictional values; cross-disability users, especially with cognitive impairment, will hit rejection loops.
- (significant) accessibility — `autocomplete='off'` on every input disables browser and AT autofill; a documented anti-pattern that penalises motor-constrained and cognitively-impaired users.
- (moderate) accessibility — Custom `role='radio'` on `<label>` wrapping `aria-hidden` real radios creates screen-reader ambiguity.
- (minor) cognitive_load — All five sections and ~20 required fields load in one continuous scroll; review block does not reprint every field.

## Uncertainty

- Blinded evidence; Track paradigm inferred from artifact behaviour (single-page landmarked checkout).
- Screen-reader announcement fidelity of the double-radio pattern is inferred from ARIA and DOM, not measured with an actual AT.

## Loop 02 recommendation

- Priority: high.
- Change: Replace the double-radio shipping choice-card pattern with a plain `<fieldset><legend>` + real `<input type='radio'>` pairs styled as cards, remove `autocomplete='off'` from every input, and relax the input validation to shape-only checks (email regex, 4-digit postcode, 16-digit numeric card ignoring spaces, `MM/YY`, 3-digit CSC) — keep the `Synthetic value:` hints for guidance but accept legitimate variations.
- Evidence: `generated/judging/blind-loop-01/candidate-b/app.js` lines 25–38 (fieldRules), `generated/judging/blind-loop-01/candidate-b/index.html` lines 171–184 (shipping choice-cards).
