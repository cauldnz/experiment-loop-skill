# candidate-b — human-use judgement (blind, loop-02)

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

- **scorer_id**: `blind-human-use-panel`
- **actual model**: `claude-opus-4.7`
- **criterion_id**: `human-use-quality`
- **kind**: `qualitative_rubric` (objective_gate = false)
- **primary raw mean (11 lenses)**: **4.09 / 5**
- **visual-information-clarity (separate)**: **4 / 5**

## Lens scores

| Lens | Score | Key finding |
|---|---|---|
| discoverability | 4 | `role=progressbar` with `aria-valuetext='Step 1 of 4: Contact details'`, visible four-chip step list, skip link, prominent synthetic-demo banner, persistent order summary. |
| navigation | 4 | Skip link → wizard form works; Continue-to-delivery/payment/review advance cleanly; keyboard-only tour of step 1 is clean. Only `<main>` landmark. |
| input_burden | 4 | Friendly per-field help, autocomplete tokens, small chunks. No preloaded fictional card values. |
| error_prevention_recovery | 3 | Per-step validation catches errors early. Whole-form error-summary text was not directly captured in this run; DOM has a `role=alert` div. |
| feedback_status | 5 | Multiple correctly-scoped live regions; explicit "Order placed. Confirmation SYN-2048." + named confirmation ("Thank you, Alex Morgan."). Strongest programmatic status of the three. |
| accessibility | 4 | Skip link, `role=progressbar`, `role=status`, `role=alert`, fieldset/legend, aria-describedby, visible 3px focus outline. Only `<main>` landmark; shipping radios inside `<aside>`. |
| responsive_touch_ergonomics | 4 | No overflow at 320 / 360 / 390; large dark-green primary buttons; wide radio-row targets; 24×24 gate passes. |
| interruption_resumption | 4 | `northstar-wizard-checkout-v1` persists non-sensitive state + currentStep; card fields absent from storage. Explicit "Payment details are never saved" copy. |
| latency_perception | 4 | Immediate status announcement on Place order; one SYN-2048 rendered despite duplicate click. Local simulation was too fast to observe aria-busy interstitial. |
| destructive_actions | 5 | **Explicit Clear-saved-progress with two-step confirm dialog** and separate Save-progress. Place order hidden until step 4. Review checkbox required. Strongest of the three. |
| cognitive_load | 4 | Wizard chunking + plain-language repeated reassurance ("synthetic", "no real order"). Weakness: shipping fieldset lives inside `<aside>`. |

## Strengths

- Explicit `role=progressbar` with descriptive `aria-valuetext` → authoritative "Step X of 4" for screen readers.
- Two-step Clear-saved-progress confirmation dialog with plain-language explanation.
- Full SYN-2048 confirmation with a named greeting: "Thank you, Alex Morgan."
- Wizard chunking structurally blocks premature Place order.
- Payment privacy honoured; storage keys never contain a `4111` substring after reload.
- Zero console/page errors during the operator run.

## Defects

- Only `<main>` landmark — no `<nav>` or `<header>`.
- Shipping radio fieldset lives inside the order-summary `<aside>`, mixing cart chrome with a required input decision.
- No preloaded synthetic card / expiry / CVV — testers must invent values.
- Skip link jumps to `#wizard-form` (the form itself) rather than the first step heading; users need one extra Tab.

## Uncertainty

Because Place order is hidden until step 4, my whole-form empty-submit probe accidentally opened the Clear-saved-progress dialog on step 1. The per-step validation surfaced through Continue was observed to work; the DOM-level `role=alert` error summary was not directly triggered in this run.

## Synthesis recommendation

**Adopt selectively.** Bring the skip-link + `role=progressbar` announcement pattern, the Save / Clear-saved-progress + two-step confirm dialog, and the synthetic-context copy into the Champion. Do not carry over the shipping-in-aside layout; add landmark diversity and inline synthetic-card hints when merging.
