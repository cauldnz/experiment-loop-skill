# Adoption / rejection matrix — synthesis-loop-01

- **Loop:** synthesis-loop-01 · **Track:** synthesis · **Role:** synthesizer · **Model:** claude-opus-4.8
- **Dominant paradigm:** single-page landmarked one-page checkout (parent `single-page-loop-02`).
- **Hypothesis:** Test single-page **A** as the structure while adopting resumable-wizard **B**'s progress and destructive-action safety patterns and task-cards **C**'s independently understandable completion state, resolving the panel A-vs-B split by synthesis rather than averaging it away.

`human_use.applicability = applicable`. Rationale: the Artifact is a human-operated mobile checkout whose success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use. Qualitative use-friction is **not** an objective ergonomics gate; the objective browser assertions cover only frozen technical correctness and compatibility. Independent qualitative judging of this synthesis Loop is **pending**.

## Preserved panel dissent

- **Accessibility judge** preferred **candidate-b** (resumable wizard) for explicit save/restore, step-local validation, and a confirmed clear-progress control.
- **Human-use judge** preferred **candidate-a** (single-page) for stronger landmarks, lower input burden, section-grouped recovery, and direct one-page editing.
- **Resolution:** A is the structural template; B's save/progress/clear-safety and C's completion-state are selectively adopted where compatible with one page. Dissent is preserved, not averaged.
- Evidence: `judging/loop-02/aggregate/dissent.md`, `judging/loop-02/aggregate/panel-scores.json`, `judging/loop-02/aggregate/pairwise-aggregate.json`.

## single-page-loop-02 — primary structural template

| Disposition | Item | Realized in | Evidence |
| --- | --- | --- | --- |
| Adopt | Landmark trio + skip link | `header`/`.synthetic-banner[role=note]`/`main[data-hook=checkout-root]`/`footer`, `a.skip-link` | `dissent.md`, `synthesis-input.json`, `track-single-page/loop-02/index.html` |
| Adopt | One-page anchor nav + direct Edit controls (no Continue clicks) | `nav.section-nav`, `data-edit-*` → `openSection` | `synthesis-input.json`, `dissent.md`, `track-single-page/loop-02/app.js` |
| Adopt | Section-grouped error summary with preserved-values reassurance | `showErrorSummary` grouped links + collapsible full list | `dissent.md`, `track-single-page/loop-02/app.js` |
| Adopt | Compact-completed disclosure with hidden descendants removed from focus | `setSectionCompacted` uses `[hidden]` on `data-section-body` | `synthesis-input.json`, `track-single-page/loop-02/app.js` |
| Adopt | Fictional-value hints + atomic single-placement | per-field `.help` hints; `completeOrder` inserts confirmation-id once, disables place-order | `dissent.md`, `track-single-page/loop-02/app.js` |
| Reject → remedied | No discoverable confirmed clear-progress control | added B's confirmed Clear saved progress | `synthesis-input.json` |
| Reject → scoped | Literal card-number hints *outside* a synthetic demo | retained only because this **is** the canonical synthetic demonstration; clearly labelled | `synthesis-input.json`, `dissent.md`, `harness/canonical-fixture.json` |

## resumable-wizard-loop-02 — selective safety and progress contributor

| Disposition | Item | Realized in | Evidence |
| --- | --- | --- | --- |
| Adopt | `role=progressbar` with descriptive `aria-valuetext` | `div[data-hook=progress]`; `updateProgress` → "N of 5 sections complete" | `dissent.md`, `synthesis-input.json`, `track-resumable-wizard/loop-02/app.js` |
| Adopt | Step-local, focused validation (one-page compatible) | per-field `blur` validation that leaves other fields and the grouped summary untouched | `dissent.md`, `synthesis-input.json`, `track-resumable-wizard/loop-02/app.js` |
| Adopt | Explicit Save progress | `button[data-action=save-now]` → `persistSafeState(true)` | `synthesis-input.json`, `track-resumable-wizard/loop-02/index.html` |
| Adopt | Confirmed Clear saved progress + Cancel (Escape-dismissable) | `#clear-confirm` dialog + handlers | `dissent.md`, `synthesis-input.json`, `track-resumable-wizard/loop-02/app.js` |
| Adopt | Named synthetic confirmation SYN-2048 | `completeOrder`; announced in `aria-valuetext` | `synthesis-input.json`, `harness/canonical-fixture.json` |
| Reject | Shipping choices nested in the order-summary aside | shipping kept as its own `#shipping` task section | `synthesis-input.json`, `track-resumable-wizard/loop-02/index.html` |
| Reject | Extra step transitions that don't reduce cognitive load | one-page layout removes multi-step Continue navigation | `synthesis-input.json` |

## task-cards-loop-01 — independent task-status contributor

| Disposition | Item | Realized in | Evidence |
| --- | --- | --- | --- |
| Adopt | Independently understandable per-section completion state | `data-section-state` badges; `stateBadge` → Not started / In progress / Complete | `synthesis-input.json`, `track-task-cards/loop-01/index.html` |
| Adopt | Direct per-section editability | per-section + review Edit controls → `openSection` | `synthesis-input.json`, `track-task-cards/loop-01/index.html` |
| Reject | Loop 02 hidden-focus collapse (focusable while collapsed) | `[hidden]` removes compacted fields from focus | `synthesis-input.json` |
| Reject | Silent review-checkbox reset | review checkbox is never silently cleared | `synthesis-input.json` |
| Reject | Flat generic error dump | A's section-grouped, value-preserving summary used | `synthesis-input.json` |
| Reject | Weak landmarks + fragile completion state | strong A landmarks; rule-based completion detection | `synthesis-input.json` |
| Reject | Loop 01 all-open mobile density | optional compact-completed disclosure offered | `synthesis-input.json` |

## No-regression check

The synthesis passes **all seven** blocking gates using the same canonical fixture SHA-256 (`e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894`) as every parent finalist. Each parent's `evidence/objective-report.json` records `failed_gate_ids: []`, and the synthesis records `failed_gate_ids: []` — no pass-to-fail regression against any parent.

## Permanent path-remediation procedural caveat

A permanent procedural provenance caveat applies to this lineage. During `task-cards-loop-01`, fifteen diagnostic scripts were written at the repository root outside the task write scope; `resumable-wizard-loop-02` later deleted them before quarantine and omitted scratch provenance. This was remediated with a permanent caveat. Forensics found no environment/credential reads, no external data, no generated secrets, and no network hosts, and the recovered `test-gates.py` was byte-identical to the frozen harness. Functional and hash validity of the affected candidate is **preserved**; the caveat is **procedural only** and does **not** imply functional invalidity of any parent or of this synthesis. Evidence: `harness/path-violation-evidence/provenance.json`.
