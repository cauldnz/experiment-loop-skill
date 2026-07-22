# Judge-human-use — final panel — candidate-b

**Model:** claude-opus-4.7  •  **Scope:** final  •  **Revision:** 1  •  **Viewport:** 390x844 (also captured 320x568, 360x800)  •  **Reduced motion:** reduce

## Objective-report acceptance (as persisted; not rerun)

| Gate | Result |
| --- | --- |
| content-fidelity | PASS |
| semantic-accessibility-gate | PASS |
| keyboard-completion-gate | PASS |
| error-recovery-gate | PASS |
| mobile-touch-gate | PASS |
| resilience-gate | PASS |
| offline-safety-gate | PASS |
| Failed gate IDs | (none) |
| Blocking failure | no |
| Harness rerun | false |

## Observed operation summary

- 31 recorded steps, 0 console messages, 0 external network requests (0/18 total)
- 58 focus stops from top Tab*60; 0 hidden-ancestor focus leaks in both normal and compact modes
- 47 interactive controls measured; 0 truly interactive controls below 24×24 CSS px (one `p.field-help` paragraph was picked up by the audit selector but is non-interactive)
- SYN-2048 confirmation present; duplicate submit is a no-op (confirmation node count stays 3→3)
- Post-reload state after successful placement: safe fields restored, payment fields empty, confirmation **dismissed** and Place order **re-enabled**
- Full destructive-safety triad on Clear-progress: Confirm, Cancel and Escape all handled; explicit Save-progress present; progressbar landmark present

## Scorecard (11 required + visual clarity)

| Sub-score | Score | Evidence |
| --- | :-: | --- |
| discoverability | 5 | Section nav, skip link, 10 headings, error-summary, explicit Save/Clear, progressbar landmark |
| navigation | 5 | Anchor jumps for 5 sections; 58 focusable stops, zero hidden-ancestor leaks; summary link moves focus into field |
| input_burden | 4 | Standard grouped form; explicit save is one optional tap that improves confidence |
| error_prevention_recovery | 5 | Blank submit → grouped summary + focus; invalid postcode inline error clears on correction; review error scoped |
| feedback_status | 5 | Status region + progressbar + aria-busy during submit; duplicate-block status text |
| accessibility | 5 | Landmarks, heading outline, progressbar, skip link, zero hidden focus leaks, keyboard-completable |
| responsive_touch_ergonomics | 5 | 47 controls, no interactive control below 24px; clean at 320/360/390 widths |
| interruption_resumption | 4 | Explicit save; safe reload restores; but post-confirmation reload re-editable with Place order re-enabled — duplicate-safety across a reload weaker than the strongest candidate |
| latency_perception | 5 | Purely local, zero external requests, no perceptible submit latency, reduced-motion honoured |
| destructive_actions | 5 | Clear-progress: Cancel default-focused, Escape dismisses, Confirm required; duplicate submit no-op |
| cognitive_load | 4 | Well-organised but slightly more chrome than the leanest candidate |
| visual_information_clarity | 5 | Progressbar surfaces where you are, totals block readable, confirmation ID explicit |

**Unrounded mean of 12 sub-scores: 4.750**

## Primary strengths

- Full Confirm + Cancel + Escape destructive-safety on Clear-progress dialog.
- Explicit Save-progress with live status announcement.
- Progressbar landmark improves feedback and orientation.
- Zero focus leaks in compact mode.

## Primary frictions

- Post-confirmation reload returns the form to editable state with Place order re-enabled; duplicate-safety across a reload boundary is weaker than the strongest candidate.
- Slightly more chrome than the leanest candidate keeps cognitive load at 4 rather than 5.
