# Accessibility judge — Candidate A

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

Objective reports are accepted as passing. These qualitative results do not override them.

**Model:** gpt-5.6-terra  
**Human-use-quality:** 3.55/5  
**Visual-information-clarity:** 3/5

**Evidence refs:** `judging/loop-01/judge-accessibility/navigation-transcript-a.json`, `judging/loop-01/judge-accessibility/screenshots/candidate-a/initial-390.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-a/error.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-a/review.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-a/confirmation.png`

## Lens scores and observed evidence
- **discoverability — 4/5:** Numbered card headings, Complete/Incomplete states, and always-present review identify the work, though four open cards dilute the first task. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **navigation — 4/5:** Keyboard-operated edit buttons moved focus to Contact, Address, Shipping, and Payment; all sections remained directly reachable. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **input_burden — 3/5:** The required data are not duplicated, but all inputs are exposed in one long mobile traversal. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **error_prevention_recovery — 4/5:** Empty submission produced a focused visible summary and retained filled values; linked correction path was operable. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **feedback_status — 3/5:** Visual card completion state is useful, but feedback is less prominent between task changes than in the wizard. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **accessibility — 4/5:** Keyboard shipping and review edits worked; accepted objective report passes, with visible focus and errors evident in screenshots. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **responsive_touch_ergonomics — 3/5:** No horizontal overflow at 320/360/390, but dense cards, compact radio rows, and very long scroll reduce mobile comfort. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **interruption_resumption — 4/5:** All safe values restored and card number/expiry/security code cleared after reload. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **latency_perception — 3/5:** Processing feedback completes safely, but the visual busy treatment is modest. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **destructive_actions — 4/5:** Review confirmation and duplicate-safe order placement reduce accidental finalisation; repeated activation yielded one confirmation. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).
- **cognitive_load — 3/5:** Clear card grouping helps, but simultaneous exposure of every task and heavy outlines create scanning load. (`judging/loop-01/judge-accessibility/navigation-transcript-a.json`; screenshots: initial, error, review, confirmation).

## Strengths
- All task cards, review edits, keyboard shipping selection, safe reload, reduced motion, and confirmation were operable with no console or runtime errors.
- Focused error summary and persistent Complete/Incomplete card states make recovery and work status visible.

## Defects
- All four task cards are open at once on mobile, creating a long, visually repetitive form before review.
- The high-contrast, heavy double-outline treatment makes cards and primary action visually noisy rather than prioritising content.

## Uncertainty
Screen-reader speech output and real switch-scanning dwell burden were not available; semantic objective results are accepted as passing.

## Evidence-backed Loop 02 recommendation
Preserve independently editable cards, but collapse completed card details or add a concise review/status rail so mobile users do not repeatedly traverse the full form.

No other judge notes were read.
