# candidate-a — human-use judgement (blind, loop-02)

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

- **scorer_id**: `blind-human-use-panel`
- **actual model**: `claude-opus-4.7`
- **criterion_id**: `human-use-quality`
- **kind**: `qualitative_rubric` (objective_gate = false)
- **primary raw mean (11 lenses)**: **4.91 / 5**
- **visual-information-clarity (separate)**: **5 / 5**

## Lens scores

| Lens | Score | Key finding |
|---|---|---|
| discoverability | 5 | `<nav aria-label='Checkout sections'>` anchor nav, skip link, "One-page checkout" kicker, numbered step badges, persistent order summary, "Compact completed sections" toggle. |
| navigation | 5 | Three landmarks (main + nav + header); clean 25-focusable keyboard tour; Edit-per-section; anchor nav; double-ring focus outline. |
| input_burden | 5 | Inline synthetic-value hints on every field; dedicated "Fictional card to use" hint box; zero Continue clicks; autocomplete tokens throughout. |
| error_prevention_recovery | 5 | "Check 13 items in 4 sections" summary with per-section counts, "Your entries are preserved" reassurance, "Show all 13 corrections" progressive disclosure, per-field friendly copy. Focus lands on `#error-summary`. |
| feedback_status | 5 | `role=status` announces "Synthetic order placed once. Confirmation ID SYN-2048." ("once" conveys atomicity). Full confirmation card. Section state chips update inline. |
| accessibility | 5 | Full landmark set + skip link + role=alert + role=status + aria-describedby + autocomplete + double-ring 4px focus outline. No accessibility gap isolated. |
| responsive_touch_ergonomics | 5 | No overflow at 320 / 360 / 390; large targets; 24×24 gate passes; compact-completed toggle reduces vertical scroll. |
| interruption_resumption | 5 | `northstar-safe-checkout` persists non-sensitive fields + shipping; card fields absent from storage (`4111` substring not present anywhere); explicit "Payment details are cleared on reload and never saved" copy. |
| latency_perception | 4 | Status announces atomicity; duplicate click found no button (DOM-level duplicate-submit block). Small deduction — no directly-observed aria-busy interstitial. |
| destructive_actions | 5 | **Duplicate submit blocked at the DOM level** — Place order button removed after first submit. Review checkbox with explicit rationale. Edit-per-section preserves data. |
| cognitive_load | 5 | Preloaded synthetic hints, compact-completed toggle, section badges, persistent totals, plain-language repeated fictional-context messaging. |

## Strengths

- Only candidate with the full landmark trio (`<main>` + `<nav>` + `<header>`) plus a working skip link.
- Preloaded synthetic values under every field, plus a dedicated "Fictional card to use" box.
- Error summary with per-section counts and preserved-values reassurance is the richest of the three.
- **Place order button is removed from the DOM after successful submit** — the strongest possible duplicate-submit block.
- Optional "Compact completed sections" toggle for progressive disclosure.
- Focus outline is a 4px amber outer + 2px dark inner double-ring that reads on any background.
- Status text 'Synthetic order placed once' explicitly conveys atomicity.
- Zero console/page errors during the operator run.

## Defects

- Removing Place order from the DOM rather than disabling it is a bold pattern that some users expect to see disabled instead of gone. Small deduction on latency_perception only.
- Payment hint box literally shows the fictional card number on-screen; intentional here but a pattern to reframe if ever ported outside a synthetic-demo context.

## Uncertainty

I could not directly observe an aria-busy interstitial because the DOM changed too fast for the operator to capture. This is not a defect; the local simulation completes below the human-perceivable threshold.

## Synthesis recommendation

**Adopt as primary template.** This candidate is the strongest human-use vehicle for the Champion across every lens. Carry over: landmark trio + skip link, one-page anchor nav + Edit-per-section, inline synthetic-value hints, error summary with per-section counts + preserved-values reassurance, DOM-level duplicate-submit blocking, "Compact completed sections" progressive disclosure, atomicity-signalling status copy, and the double-ring focus outline.
