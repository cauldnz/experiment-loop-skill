# Accessibility judge — Candidate C

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

Objective reports are accepted as passing. These qualitative results do not override them.

**Model:** gpt-5.6-terra  
**Human-use-quality:** 4.27/5  
**Visual-information-clarity:** 4/5

**Evidence refs:** `judging/loop-01/judge-accessibility/navigation-transcript-c.json`, `judging/loop-01/judge-accessibility/screenshots/candidate-c/initial-390.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-c/error.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-c/review.png`, `judging/loop-01/judge-accessibility/screenshots/candidate-c/confirmation.png`

## Lens scores and observed evidence
- **discoverability — 5/5:** Step 1 of 4 progress, clear Continue labels, persistent summary, save/resume controls, and review edits clearly expose the journey. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **navigation — 5/5:** Skip link, Back, Continue, and all four review Edit controls operated by keyboard and directed focus to the intended target. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **input_burden — 3/5:** Progressive disclosure limits simultaneous choices but does not reduce the required contact, address, payment, and review inputs. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **error_prevention_recovery — 4/5:** Invalid placement exposed a summary and focused Contact, but empty Continue actions advanced through three steps rather than preventing the premature move. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **feedback_status — 5/5:** Progress text, step-complete feedback, save and resume messages, busy status, and confirmation provide clear, timely state changes. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **accessibility — 4/5:** Keyboard actions, focus movement, skip link, reduced-motion operation, and accepted objective pass evidence were strong; hidden-step complexity remains a qualitative caveat. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **responsive_touch_ergonomics — 4/5:** No horizontal overflow at all tested viewports; full-width Continue controls and readable cards support touch, while small utility links are less forgiving. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **interruption_resumption — 5/5:** Save, clear, reload, and resumed-progress messages were actually operated; safe values restored and payment secrets cleared. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **latency_perception — 4/5:** Busy feedback appeared during local placement and repeat activation still produced only one confirmation. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **destructive_actions — 3/5:** Order placement is explicit and duplicate-safe, but Clear saved progress immediately reloads without undo or confirmation. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).
- **cognitive_load — 5/5:** One active task, explicit progress, and a concise review lower memory demand more effectively than the fully exposed alternatives. (`judging/loop-01/judge-accessibility/navigation-transcript-c.json`; screenshots: initial, error, review, confirmation).

## Strengths
- Explicit step progress, a single visible next action, Save/Clear controls, resumable state messaging, summary, and editable review make the path highly legible.
- The valid canonical journey, review edits, reduced-motion run, safe resume, payment-secret clearing, keyboard order placement, and one confirmation all worked with no console/runtime errors.
- The focused first field after invalid placement and the error-summary recovery controls support correction across concealed/revealed steps.

## Defects
- Continue advanced each empty step rather than holding the user at the invalid task; this allows premature progression and distributes errors across hidden/revealed context.
- Clear saved progress immediately reloads and discards saved state without confirmation, undo, or a grace period.

## Uncertainty
No assistive-technology speech output was available; qualitative judgement is based on browser operation, rendered states, and accepted objective evidence.

## Evidence-backed Loop 02 recommendation
Validate and retain focus in the active step before revealing the next one, and add an undo/confirmation affordance to Clear saved progress without weakening resumability.

No other judge notes were read.
