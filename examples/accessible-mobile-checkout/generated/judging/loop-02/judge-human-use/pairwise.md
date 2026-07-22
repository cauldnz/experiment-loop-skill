# Pairwise — loop-02 blind human-use panel

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

Evaluation was performed in the flipped order **C → B → A**. Identity map, orchestrator directory, and other judge notes were not read.

## Pair C vs B — preferred **candidate-b** (high confidence)

Candidate-b outperforms candidate-c on 10 of the 11 required lenses. B has:

- A real skip link (`Skip to checkout steps`).
- `role=progressbar` with `aria-valuetext="Step 1 of 4: Contact details"`.
- Save-progress and Clear-saved-progress with a two-step confirmation dialog.
- A full SYN-2048 confirmation with a named greeting ("Thank you, Alex Morgan.").

Candidate-c has no skip link, no landmark diversity, and a silent review-checkbox reset on every non-checkbox input change. In my run the form stayed in an "errors in the form" state despite every accordion section reporting Complete. C's very strong 4px black focus outline is worth adopting individually, but does not offset the structural gaps.

Evidence: `navigation-transcript-c.json#steps[confirmation_state]`, `navigation-transcript-b.json#steps[confirmation_state]`.

## Pair B vs A — preferred **candidate-a** (high confidence)

Both candidates complete SYN-2048 cleanly with correct payment privacy and both have skip links. Candidate-a is stronger on:

- **Discoverability** — three landmarks (`main` + `nav` + `header`) vs one; section anchor nav; numbered step badges.
- **Input burden** — inline synthetic-value hints on every field; explicit "Fictional card to use — 4111 1111 1111 1111 · expiry 12/34 · security code 123 · Alex Morgan" hint box.
- **Error prevention & recovery** — "Check 13 items in 4 sections" summary with per-section counts and preserved-values reassurance vs an unobserved `role=alert` div in B.
- **Destructive actions** — Place order button *removed from the DOM* after successful submit vs a still-visible button with an internal placement flag.
- **Cognitive load** — one-page layout removes Continue clicks; "Compact completed sections" toggle offers progressive disclosure.

Candidate-b's most valuable edges — the explicit two-step Clear-saved-progress dialog and the `role=progressbar` `aria-valuetext` step announcement — should be adopted into the Champion. But overall A is materially stronger.

Evidence: `navigation-transcript-a.json#steps[empty_submit_state]`, `navigation-transcript-a.json#steps[duplicate_submit_attempted]`, `navigation-transcript-b.json#steps[empty_submit_state]`.

## Pair C vs A — preferred **candidate-a** (high confidence)

Candidate-a is superior to candidate-c on every one of the 11 lenses. A completes SYN-2048; C did not in my run even though the frozen objective report passes, which itself indicates a fragile submission state machine (silent review-checkbox reset). A has the landmark trio + skip link (vs `<main>`-only), preloaded synthetic-value hints (vs blank card fields), a section-grouped error summary with preserved-values copy (vs a flat 12-row generic list), DOM-level duplicate-submit blocking (vs a `placementStarted` flag), and compact-completed progressive disclosure (vs accordion-only). C's only unique strength is its 4px black focus outline; adopt it as a fallback but do not use C's submission pattern.

## Overall ranking

1. **candidate-a** — adopt as primary template.
2. **candidate-b** — adopt selectively (progressbar + save/clear-progress + confirm dialog).
3. **candidate-c** — reject submission-gating pattern; borrow only the high-contrast focus outline.

Confidence: high across all three pairs.
