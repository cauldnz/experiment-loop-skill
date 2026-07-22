# Pairwise preferences (raw judge record)

- Judge: `judge-human-use`
- Judge model: `claude-opus-4.7`
- Loop: `loop-01`
- Order (flipped, exact): candidate-c → candidate-b → candidate-a
- `human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
- All three objective reports pass; qualitative preferences here do not override any objective gate. Pairwise preferences are advisory raw judge input; final aggregation is by panel median with dissent preserved.
- No Champion is selected in this record.

## candidate-c vs candidate-b — prefer **candidate-c** (confidence: high)

Candidate C wins on:
- **input_burden** — tolerant, shape-only validation vs candidate B's exact-fixture rules (state must equal `NSW`, country `australia`, card `4111111111111111`, name `alex morgan`, CSC `123`, expiry `12/34`).
- **cognitive_load** — one wizard step visible at a time (3–5 fields) vs B's ~20 required fields on one long scroll.
- **interruption_resumption** — explicit `Save progress` / `Clear saved progress` controls and restored step position, plus a polite `Resumed your saved progress. Payment details are never saved and must be re-entered.` message vs B's auto-only save.
- **feedback_status** — `role='progressbar'` with narrated `aria-valuetext` alternates plus a polite status region vs B's polite status but assertive-only error live region.

Candidate B is slightly stronger on **error_prevention_recovery** (its per-field error messages are extremely specific), but suffers from a double-radio ARIA anti-pattern on shipping (`role='radio'` on `<label>` wrapping `aria-hidden` real radios) and `autocomplete='off'` on every input, both of which penalise motor- and cognitively-impaired users.

Neutral: discoverability, navigation, responsive_touch_ergonomics, latency_perception, destructive_actions.

Evidence: `screenshots/candidate-c/01-initial-390x844.png`, `screenshots/candidate-b/01-initial-390x844.png`, and each candidate's `navigation-transcript-*.json` `post-invalid-submit report` and `reload persistence check` entries.

## candidate-b vs candidate-a — prefer **candidate-b** (confidence: high)

Candidate B wins on:
- **error_prevention_recovery** — highly specific messages vs candidate A's generic `Please enter a value`.
- **feedback_status** — polite `aria-live` status with running narration + focused assertive error summary vs A's misused assertive routine updates.
- **latency_perception** — 180 ms placement vs A's hard-coded 500 ms.
- **destructive_actions** — `placementStarted` flag + immediate `placeOrder.disabled=true` vs A's disable-only-inside-`setTimeout`-callback.
- **interruption_resumption** — no payment-field leak vs A restoring `card-name` on reload.
- **navigation / discoverability** — visible section-nav pills, landmark nav+aside, visible order summary vs A's no-skip-link / no-nav / bottom-only summary.
- **responsive_touch_ergonomics** — larger choice-card shipping targets vs A's tighter 2×2 Edit buttons.

Candidate A retains marginal advantages in cognitive_load-per-view (fewer visible fields at once), but the accumulated missing skip-link, missing landmark aside, `aria-live='assertive'` misuse, and payment-field leakage outweigh that.

Neutral: input_burden, cognitive_load, accessibility.

Evidence: `screenshots/candidate-b/02-error-summary.png`, `screenshots/candidate-a/02-error-summary.png`, and each candidate's `navigation-transcript-*.json` `reload persistence check` entries.

## candidate-c vs candidate-a — prefer **candidate-c** (confidence: high)

Candidate C dominates almost every lens: narrated progress bar (feedback_status), explicit Save/Clear controls with restored step position (interruption_resumption), 120 ms placement with `aria-busy` narration (latency_perception), `aria-disabled` Place order + `orderPlaced` flag (destructive_actions), field-specific error messages routed to the correct step (error_prevention_recovery), single-active-continue wizard grouping (cognitive_load), skip-link present (discoverability/navigation), and no payment-field persistence.

Candidate A has no skip-link, no landmark aside, misuses assertive `aria-live`, restores `card-name` on reload, and imposes a 500 ms placement delay.

Neutral: responsive_touch_ergonomics.

Evidence: `screenshots/candidate-c/01-initial-390x844.png`, `screenshots/candidate-a/01-initial-390x844.png`, and each candidate's `navigation-transcript-*.json`.

## Identity note

No attempt was made to infer or reveal Track or model identity from bundle contents. Comparisons are strictly artifact-behaviour based.
