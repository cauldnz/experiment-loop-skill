# Judge-human-use — final panel — candidate-c

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

- 29 recorded steps, 0 console messages, 0 external network requests (0/12 total)
- 58 focus stops from top Tab*60; 0 hidden-ancestor focus leaks in both normal and compact modes
- 42 interactive controls measured; 0 controls below 24×24 CSS px
- SYN-2048 confirmation present; duplicate submit is a no-op (confirmation node count stays 3→3); status announces `Synthetic order placed once. Confirmation ID SYN-2048.`
- Post-reload state after successful placement: safe fields restored, payment fields empty, confirmation dismissed and Place order re-enabled
- **No user-initiated Clear-saved-progress affordance** — no Confirm/Cancel/Escape destructive-safety pattern present
- **No explicit Save-progress button** — autosave-on-input/change instead
- **No progressbar landmark**

## Scorecard (11 required + visual clarity)

| Sub-score | Score | Evidence |
| --- | :-: | --- |
| discoverability | 4 | Section nav, skip link, 10 headings, error-summary present; no progressbar and no explicit Save/Clear controls, so persistence/progress state less discoverable |
| navigation | 5 | Anchor jumps for 5 sections; 58 focusable stops, zero hidden-ancestor leaks; summary link moves focus into field |
| input_burden | 4 | Same underlying fields; autosaves silently — no explicit save tap required, though user cannot deliberately verify save |
| error_prevention_recovery | 5 | Blank submit → grouped summary + focus; invalid postcode inline error clears on correction; review error scoped |
| feedback_status | 4 | Live status region announces autosave and post-confirmation duplicate-block; no progressbar reduces status coverage |
| accessibility | 5 | Landmarks, heading outline, skip link, zero hidden focus leaks, keyboard-completable end-to-end |
| responsive_touch_ergonomics | 5 | 42 controls, no interactive control below 24px; clean at 320/360/390 widths |
| interruption_resumption | 3 | Safe reload restores; but no explicit save (silent autosave), and post-confirmation reload re-editable with Place order re-enabled — weaker duplicate-safety across a reload boundary |
| latency_perception | 5 | Purely local, zero external requests, no perceptible submit latency, reduced-motion honoured |
| destructive_actions | 3 | Duplicate submit is a no-op with status message, but no user-initiated Clear-progress affordance exists; no Confirm/Cancel/Escape destructive-safety pattern to evaluate |
| cognitive_load | 5 | Leanest UI of the three; fewest optional controls to reason about |
| visual_information_clarity | 4 | Totals and confirmation explicit; no progressbar reduces at-a-glance sense of "where am I in the flow" |

**Unrounded mean of 12 sub-scores: 4.333**

## Primary strengths

- Leanest UI: fewest optional controls to reason about (lowest cognitive load).
- Autosave on input/change removes the need for an explicit Save tap.
- Same clean error/inline recovery pattern as the other candidates.

## Primary frictions

- No user-initiated Clear saved progress affordance — no Confirm/Cancel/Escape destructive-safety pattern present.
- No explicit Save progress button; user must trust silent autosave.
- No progressbar landmark; progress state is not surfaced explicitly.
- Post-confirmation reload re-editable with Place order re-enabled — weaker duplicate-safety across a reload boundary than the strongest candidate.
