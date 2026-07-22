# Accessibility judge — Candidate B

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

Objective reports are accepted as passing. These qualitative results do not override them.

**Model:** gpt-5.6-terra  
**Human-use-quality:** 4.18/5  
**Visual-information-clarity:** 5/5

**Evidence refs:** `judging/loop-01/judge-accessibility/navigation-transcript-b.json`, `judging/loop-01/judge-accessibility/screenshots/candidate-b/initial-390.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-b/error.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-b/review.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-b/confirmation.png`

## Lens scores and observed evidence
- **discoverability — 5/5:** The opening title, section links, numbered headings, persistent summary, synthetic-value help, and explicit final review make requirements immediately findable. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **navigation — 4/5:** Every section link changed the hash in keyboard use and review edit controls focused the intended section; the long one-page return trip remains a cost. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **input_burden — 3/5:** Exact required fields and helpful formats avoid ambiguity, but all contact, address, payment, and review work are exposed in one extended pass. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **error_prevention_recovery — 5/5:** Empty submission focused the summary and rendered 13 linked, field-associated corrections while preserving all entries. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **feedback_status — 4/5:** Safe-progress restoration, error count, placing status, and single confirmation were explicit; the brief busy state is still sparse visually. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **accessibility — 4/5:** Space selected shipping, Enter placed the order, focus recovery worked, reduced-motion ran, and no runtime errors occurred; custom radio styling warrants caution. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **responsive_touch_ergonomics — 4/5:** All tested widths had no horizontal overflow and controls remained legible, although five compact section links and the full-page length constrain comfort. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **interruption_resumption — 5/5:** Reload restored every safe value and cleared every tested payment secret with an explicit restoration message. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **latency_perception — 4/5:** The busy state was observed on keyboard placement and repeat activation was safely prevented before a deterministic local confirmation. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **destructive_actions — 5/5:** Edit controls preserved data and repeated Place order yielded exactly one SYN-2048 confirmation. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).
- **cognitive_load — 3/5:** Strong hierarchy and help reduce ambiguity, but the full 13-item error panorama and long single page retain substantial working-memory demand. (`judging/loop-01/judge-accessibility/navigation-transcript-b.json`; screenshots: initial, error, review, confirmation).

## Strengths
- The structured one-page sequence gives strong orientation through numbered headings, working section links, contextual synthetic-value help, order summary, and explicit review.
- The error state is exceptionally actionable: a focused summary, 13 linked corrections, field messages, preserved values, and a clear status.
- Shipping selection, edit controls, safe resume, reduced motion, keyboard placement, and duplicate protection all operated without runtime errors.

## Defects
- At 390px, the complete one-page form and 13-item error state are cognitively and physically long; the user must manage many fields before review.
- The custom keyboard shipping treatment worked for Space/Enter in the run, but its bespoke label-as-radio presentation is less immediately conventional than native radios.

## Uncertainty
The run exercised Tab/Shift+Tab/Enter/Space but not every possible screen-reader command or radio-arrow interaction.

## Evidence-backed Loop 02 recommendation
Keep the clear single-page landmarks and recovery pattern, but reduce the initial traversal burden with optional progressive disclosure or a compact completed-section summary.

No other judge notes were read.
