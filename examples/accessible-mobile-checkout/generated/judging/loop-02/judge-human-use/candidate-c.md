# candidate-c — human-use judgement (blind, loop-02)

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

- **scorer_id**: `blind-human-use-panel`
- **actual model**: `claude-opus-4.7`
- **criterion_id**: `human-use-quality`
- **kind**: `qualitative_rubric` (objective_gate = false)
- **primary raw mean (11 lenses)**: **3.0 / 5**
- **visual-information-clarity (separate)**: **3 / 5**

## Lens scores

| Lens | Score | Key finding |
|---|---|---|
| discoverability | 3 | Numbered accordion headers and Incomplete/Complete pill are helpful. No skip link, no `<nav>`, no progress indicator, no synthetic-value preload for card. |
| navigation | 3 | 25-focusable keyboard tour is logically ordered. No skip link and no `<nav>` landmark, so screen-reader users Tab through everything to reach primary actions. |
| input_burden | 3 | Fields well-labelled with per-field help. Per-card Continue advances flow. No preload for the fictional card credentials. |
| error_prevention_recovery | 3 | Empty submit surfaces `role=alert` summary and focuses it. Weakness: 12-row flat list with generic "Please enter a value" copy and no section grouping. |
| feedback_status | 2 | `aria-live=polite` status and card-status badges work, but the review checkbox silently unchecks on any other input change with no announcement — hidden failure mode. |
| accessibility | 3 | Correct label / describedby / aria-expanded / aria-controls; role=alert error summary; **very strong 4px black focus outline**. Missing skip link and landmark diversity. |
| responsive_touch_ergonomics | 4 | No overflow at 320 / 360 / 390; large tap targets; objective 24×24 gate passes. |
| interruption_resumption | 4 | localStorage restores non-sensitive fields; card fields explicitly excluded and absent from storage after reload. |
| latency_perception | 3 | Correct `aria-busy` and status announcement pattern; but in my run the form rejected Place order with a vague "errors in the form" while every section badge read Complete. |
| destructive_actions | 3 | `placementStarted` flag + disabled button + explicit review checkbox. No "Clear saved progress" affordance. Silent review-reset is destructive-safe but confusing. |
| cognitive_load | 2 | Accordion-only pattern with no persistent progress. 12-row generic error dump. No synthetic-value hints for payment. Hidden review-reset state. |

## Strengths

- Very strong `outline: solid 4px black` focus indicator on every focusable element.
- Correct accordion semantics: `aria-expanded` matches actual `.hidden` state.
- Complete list of missing fields in the empty-submit error summary, with focus moved onto the alert.
- Payment privacy honoured: `4111` substring appears in no storage key after mid-flow reload.
- No page errors and no console errors during the operator run.

## Defects

- **No skip link and no `<nav>` / `<header>` landmarks.** Materially harder navigation for cross-disability mobile use.
- **Silent review-checkbox reset on every non-checkbox input change** (see `app.js` `input.addEventListener('change'…)` and the equivalent loadProgress branch). No live-region announcement, no visible signal.
- Empty-submit error summary is a flat 12-row list with no section grouping, jump-to-field links, or "your entries are preserved" reassurance.
- No preloaded synthetic card / expiry / CVV values; testers must invent them, and a real user has no on-screen hint of the fictional expectation.
- Place order can silently reject after every accordion badge reads Complete, without identifying the failing field.

## Uncertainty

Rapid programmatic fills likely interact with the "reset review checkbox on any input change" pattern in ways a slow human typist would not encounter. The frozen objective report passes, so completion is achievable, but the underlying reset pattern remains a real defect.

## Synthesis recommendation

**Reject** this candidate's submission-gating pattern. Keep only its high-contrast focus outline and its clean accordion `aria-expanded`/`aria-controls` implementation. Do not adopt the "silently reset review checkbox on every input change" pattern into the Champion.
