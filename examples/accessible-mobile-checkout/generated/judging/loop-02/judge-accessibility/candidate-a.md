# Accessibility judge — candidate-a

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

## Raw scores

- human-use-quality raw mean: **4.18/5**
- visual-information-clarity: **4/5**

## Lens findings

- **discoverability — 4/5:** The labelled sections and persistent review make required work apparent, although the full single-page length delays the lower sections. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-a/initial.png`.
- **navigation — 4/5:** Skip navigation, section edit controls, and reverse traversal worked; the compacted sections remained recoverable. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **input_burden — 4/5:** All inputs are reachable in one flow with autocomplete-oriented field types, but address and payment remain a long sequential form. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-a/review.png`.
- **error_prevention_recovery — 4/5:** An empty explicit submission reached the error state and the completed correction path retained values. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-a/error.png`.
- **feedback_status — 4/5:** Completion, restored-progress, and single-confirmation messages were observed, but status is less directive before the user reaches review. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **accessibility — 5/5:** First Tab exposed a skip link; compacted-body traversal found no hidden focus target; no console/runtime errors were recorded. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **responsive_touch_ergonomics — 4/5:** All three operated widths had scrollWidth equal to clientWidth; controls retain visible spacing, though the long page increases scrolling. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **interruption_resumption — 4/5:** Reload restored Alex Morgan while payment fields were empty. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **latency_perception — 4/5:** Reduced motion reported no duration over 10 ms; repeated activation gave exactly one confirmation, with a clear local completion status. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **destructive_actions — 4/5:** Review edit and duplicate-submit behavior were safe, but no clear-progress confirmation affordance was discoverable to test. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`.
- **cognitive_load — 5/5:** Optional compact summaries, section completion state, and persistent review reduce memory load without concealing completed details. Evidence: `judging/loop-02/judge-accessibility/screenshots/candidate-a/review.png`.

## Strengths
- Optional compact summaries reduce revisiting completed work without removing it from keyboard traversal.
- Reload restored contact and withheld payment; a repeated Place order produced one confirmation.

## Defects
- No discoverable clear-progress confirmation control was available during the operated flow.
- The compacted review remains long on a narrow screen.

## Uncertainty
The accepted objective report establishes the technical gates; this qualitative run did not infer any identity or rerun them.

## Synthesis recommendation
Adopt the optional compact-completed pattern only: it preserved keyboard exclusion from hidden bodies (supplemental hidden-focus count 0). Reject copying the absence of a discoverable clear-progress confirmation affordance.

Objective reports were accepted as passing and not rerun or overridden.
