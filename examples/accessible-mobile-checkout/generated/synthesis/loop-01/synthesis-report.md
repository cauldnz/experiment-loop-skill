# Synthesis report — synthesis-loop-01

- **Experiment:** accessible-mobile-checkout (revision 1) · **Loop:** synthesis-loop-01 · **Track:** synthesis
- **Role:** synthesizer · **Model:** claude-opus-4.8
- **Parents (true multi-parent lineage, in order):** `single-page-loop-02`, `resumable-wizard-loop-02`, `task-cards-loop-01`
- **Decision:** `keep_for_synthesis` · **stop_reason:** null

> This report is reconstructed from persisted evidence only, during a single owner-authorized post-reboot continuation. No objective, harness, Playwright/browser, generator, or judge command was rerun. All fourteen immutable functional outputs were hash-verified against `synthesis/recovery/recovery-inventory.json` before and after these records were written.

## 1. Hypothesis

Use single-page **A** (`single-page-loop-02`) as the structural template while adopting resumable-wizard **B**'s (`resumable-wizard-loop-02`) progress and destructive-action safety patterns and task-cards **C**'s (`task-cards-loop-01`) independently understandable per-section completion state — so the Loop 02 panel's A-vs-B split is resolved by synthesis rather than averaged away. A fresh synthesis candidate was authored; no parent Artifact was mutated.

## 2. Preserved panel dissent

The Loop 02 blind panel split on candidate A versus candidate B, and the split is preserved rather than blended:

- **Accessibility judge → candidate-b** (medium-high confidence): "B offers stronger recoverability: it has explicit save/restore, step-local validation, and a tested clear-progress confirmation; A remains more direct and has safe compact keyboard behavior."
- **Human-use judge → candidate-a** (high confidence): A is stronger on discoverability (three landmarks vs one, section anchor nav, numbered step badges), input burden (inline synthetic-value hints), error prevention/recovery (a section-grouped "Check N items in M sections" summary with preserved-values reassurance vs an unobserved `role=alert` div in B), destructive actions (Place-order button removed from the DOM after submit vs a still-visible button in B), and cognitive load. The judge explicitly noted that B's two-step Clear-saved-progress dialog and `role=progressbar` `aria-valuetext` step announcement "should be carried into the Champion."
- **Resolution:** A is the structural template; B's save/progress/clear-safety and C's completion-state are selectively adopted where compatible with one page. A-vs-C and B-vs-C were consensus (both preferred over C).

Evidence: `judging/loop-02/aggregate/dissent.md`, `judging/loop-02/aggregate/panel-scores.json`, `judging/loop-02/aggregate/pairwise-aggregate.json`. Overall panel aggregate order: candidate-a, candidate-b, candidate-c.

## 3. Parent adoption / rejection (summary)

Full evidence-referenced detail is in `synthesis/loop-01/adoption-rejection-matrix.json` and `.md`. In brief:

### `single-page-loop-02` — primary structural template
- **Adopt:** landmark trio + skip link; one-page anchor nav + direct Edit controls (no Continue clicks); section-grouped error summary with preserved-values reassurance; compact-completed progressive disclosure with hidden descendants removed from focus; fictional-value hints and atomic single-placement.
- **Reject:** no discoverable confirmed clear-progress control → **remedied by adopting B**; literal card-number hints "outside a synthetic demonstration" → **retained only** because this *is* the canonical synthetic demonstration, clearly labelled.

### `resumable-wizard-loop-02` — selective safety and progress contributor
- **Adopt:** `role=progressbar` with descriptive `aria-valuetext`; step-local focused validation (re-expressed for one page, coexisting with A's grouped submit-time summary); explicit Save progress; confirmed, cancellable Clear saved progress (Escape-dismissable); named synthetic confirmation SYN-2048.
- **Reject:** shipping nested inside the order-summary aside; extra step transitions that don't reduce cognitive load.

### `task-cards-loop-01` — independent task-status contributor (retained after its Loop 02 regression)
- **Adopt:** independently understandable per-section completion state; direct per-section editability.
- **Reject:** Loop 02 collapsed-but-keyboard-focusable content; silent review-checkbox reset; flat generic error dump; weak landmarks + fragile completion state; Loop 01 all-open mobile density.

## 4. Terminal objective result — all seven gates pass

A single terminal frozen objective run (PID 53728) exited 0 with no repair attempt:

| Gate | Result |
| --- | --- |
| content-fidelity | PASS |
| semantic-accessibility-gate | PASS |
| keyboard-completion-gate | PASS |
| error-recovery-gate | PASS |
| mobile-touch-gate | PASS |
| resilience-gate | PASS |
| offline-safety-gate | PASS |

- **Failed gate IDs:** none · **Blocking failure:** no · **Repair attempts:** 0
- **External requests:** 0 (offline-safe)
- **Fixture SHA-256:** `e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894` · **Harness SHA-256:** `de51a917b14aa9e0d003efb5e84fc98cf42b089e31448bcaf9f4889d3b060563`
- **Run window (UTC):** start `2026-07-21T09:07:03.705Z` → end `2026-07-21T09:07:12.389Z`, exit code 0
- Non-gating task-efficiency metrics: activations 20, corrections 4, completion interactions 1, focusable controls traversed 28. These are context only and neither pass nor fail a gate.

The objective command is terminal and was **not** rerun:

```
python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\synthesis\loop-01 --out .experiments\accessible-mobile-checkout\generated\synthesis\loop-01\evidence
```

Evidence: `synthesis/loop-01/process.json`, `synthesis/loop-01/evidence/objective-report.json`, `synthesis/loop-01/evidence/objective-report.txt`, and six harness screenshots under `synthesis/loop-01/evidence/`.

## 5. Objective no-regression against the three parent reports

The synthesis and all three parent finalists were evaluated on the identical canonical fixture (`e6622cd3…`), and all four record `failed_gate_ids: []` with zero external requests — so there is **no pass-to-fail regression** against any parent.

| Candidate | failed_gate_ids | external requests | focusable | activations | corrections | completion | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthesis-loop-01 | [] | 0 | 28 | 20 | 4 | 1 | `synthesis/loop-01/evidence/objective-report.json` |
| single-page-loop-02 | [] | 0 | 25 | 20 | 4 | 1 | `track-single-page/loop-02/evidence/objective-report.json` |
| resumable-wizard-loop-02 | [] | 0 | 29 | 24 | 4 | 1 | `track-resumable-wizard/loop-02/evidence/objective-report.json` |
| task-cards-loop-01 | [] | 0 | 20 | 22 | 4 | 1 | `track-task-cards/loop-01/evidence/objective-report.json` |

The metric deltas are non-gating context only. The synthesis' focusable-control count (28) sits within the parents' range (20–29), consistent with grafting B's progress/save/clear controls and C's per-section state onto A's one-page structure without introducing wizard steps.

## 6. Remaining limitations

- **Independent qualitative synthesis judging is pending.** The seven objective gates cover only frozen technical correctness and compatibility. Qualitative use-friction across the eleven human-use lenses (discoverability, navigation, input burden, error prevention/recovery, feedback/status, accessibility, responsive touch ergonomics, interruption/resumption, latency perception, destructive actions, cognitive load) has **not** been independently judged for this synthesis. No synthesizer-authored qualitative score exists and none may be invented; no Champion, `new_best`, or promotion is claimed.
- **One-page density on the smallest viewport.** The human-use judge's residual concern about a long one-page form and error panorama at ~320–390px remains a qualitative risk the objective gates cannot measure; the compact-completed disclosure mitigates but does not eliminate it.
- **Selective-adoption fidelity is unaudited qualitatively.** Whether B's step-local validation truly coexists with A's grouped submit-time summary without confusion, and whether C's per-section completion badges read cleanly for AT users, requires the pending independent panel.
- **Permanent procedural provenance caveat** applies to the lineage (see §8); it is procedural only and does not imply functional invalidity.

## 7. Evidence-backed next hypothesis

Authorize `synthesis-loop-02` **only after** independent identity-blind judges operate this synthesis Loop against all eleven frozen lenses and preserve dissent. If judged, apply exactly one evidence-backed refinement: reduce the residual cognitive load of the full one-page form on the smallest (320px) viewport by strengthening the compact-completed disclosure default and progress-anchored resume — **without** introducing wizard steps or making collapsed content keyboard-focusable, and while keeping all seven gates blocking and the harness unchanged. This is grounded in the human-use judge's one-page density finding and the accessibility judge's endorsement of B's recoverability, both preserved above.

## 8. Caveats

- **Permanent path-remediation procedural caveat:** During `task-cards-loop-01`, fifteen diagnostic scripts were written at the repository root outside the task write scope; `resumable-wizard-loop-02` later deleted them before quarantine and omitted scratch provenance. This was remediated with a permanent caveat. Forensics found no environment/credential reads, no external data, no generated secrets, and no network hosts, and the recovered `test-gates.py` was byte-identical to the frozen harness. Functional and hash validity of the affected candidate is **preserved**; the caveat is **procedural only** and does **not** imply functional invalidity of any parent or of this synthesis. Evidence: `harness/path-violation-evidence/provenance.json`.
- **Reboot interruption / recovery caveat:** The original `synthesis-loop-01` agent did not survive a PC reboot; its handle was not registered afterward, no background agents or shell sessions survived, and objective PID 53728 was not alive. The terminal objective run had already completed before the reboot and both adoption/rejection matrices were written; the interruption occurred while authoring the remaining records. The persisted `status.json` was stale (`state=running`, heartbeat `2026-07-21T09:02:38.916Z`, `objective_status=not_started`). This report and the sibling records were completed under one explicit owner authorization; the objective command was **not** rerun, and all fourteen immutable outputs were hash-verified against the launch recovery inventory before and after writing. Evidence: `synthesis/recovery/recovery-inventory.json`, `synthesis/recovery/reconciliation-ledger-event.json`, `synthesis/recovery/post-recovery-verification.json`.
