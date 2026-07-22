# Accessibility judge — candidate-c

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

## Raw scores

- human-use-quality raw mean: **3.18/5**
- visual-information-clarity: **3/5**

## Lens findings

- **discoverability — 3/5:** Numbered accordion headers show a broad task outline, but the relationship between collapsed cards and the review action is less immediate. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-c/initial.png`.
- **navigation — 2/5:** The Tab sequence entered address, shipping, and payment descendants while their headers reported aria-expanded=false, creating invisible navigation stops. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **input_burden — 3/5:** Task grouping is useful, but keyboard traversal through collapsed sections adds avoidable effort. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **error_prevention_recovery — 4/5:** The empty submit produced an error state and the operated correction path completed successfully. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-c/error.png`.
- **feedback_status — 4/5:** Section completion and confirmation feedback are present, though collapsed status does not match keyboard exposure. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-c/review.png`.
- **accessibility — 1/5:** Direct supplemental evidence shows focus on address-line1, shipping controls, and card-expiry inside `.hidden` ancestors after their headers were collapsed. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-c/collapsed-focus-defect.png`.
- **responsive_touch_ergonomics — 4/5:** The three viewport checks reported no horizontal overflow and the controls were visually spaced. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **interruption_resumption — 4/5:** Reload restored contact while payment remained empty. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **latency_perception — 4/5:** Reduced motion had no duration above 10 ms and duplicate Place order produced one confirmation. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **destructive_actions — 3/5:** Review edit and duplicate-submit are safe, but no discoverable clear-progress confirmation control was available. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
- **cognitive_load — 3/5:** The card headings help chunk work, but mismatch between collapsed presentation and tab order makes the interaction mentally unstable. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-c/collapsed-focus-defect.png`.

## Strengths
- The visible accordion headers, section completion labels, error state, reload restoration, and one-confirmation behavior provide some helpful structure.
- No horizontal overflow, runtime error, or reduced-motion duration over 10 ms was observed.

## Defects
- Severe: Address, shipping, and payment headers began aria-expanded=false, yet Tab reached their visually collapsed controls (including card expiry).
- No skip link or discoverable clear-progress confirmation control was available in the operated candidate; collapsed-card behavior raises both navigation and cognitive-load friction.

## Uncertainty
The objective report remains accepted as passing; this score records observed qualitative use friction, especially the independent collapsed-focus check.

## Synthesis recommendation
Reject this accordion implementation for synthesis until collapsed panels remove descendants from keyboard and screen-reader exposure and a safe clear-progress path is provided. A labelled section-status pattern may be adopted only after that repair.

Objective reports were accepted as passing and not rerun or overridden.
