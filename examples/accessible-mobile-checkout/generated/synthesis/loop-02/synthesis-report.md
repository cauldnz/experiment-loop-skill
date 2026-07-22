# Synthesis report — synthesis-loop-02

- **Experiment:** accessible-mobile-checkout (revision 1) · **Loop:** synthesis-loop-02 · **Track:** synthesis
- **Role:** synthesizer · **Model:** claude-opus-4.8
- **Immediate parent (hill-climb lineage):** `synthesis-loop-01`
- **Ancestor parents (true multi-parent ancestry):** `single-page-loop-02`, `resumable-wizard-loop-02`, `task-cards-loop-01`
- **Decision:** `keep_for_synthesis` · **stop_reason:** null
- **Planned:** Loop 8 of 8 (hard cap 11) — no further synthesis Loop is authored.

> synthesis-loop-02 is an immediate hill-climb of synthesis-loop-01. A fresh copy of the Loop 01
> functional files (`index.html`, `styles.css`, `app.js`) was authored into `loop-02`, and only the
> five evidence-backed panel-feedback changes below were applied. **synthesis-loop-01 was not mutated**,
> and all three-parent adopt/reject decisions are inherited unchanged.

## 1. Hypothesis

Adopt every synthesis-loop-01 panel-feedback instruction while preserving every frozen invariant and
keeping all seven objective gates blocking, so the residual accessibility and human-use frictions from
Loop 01 are removed without regressing the objective harness or the inherited multi-parent synthesis.

## 2. Loop 01 panel feedback and what changed

Feedback source: `judging/synthesis-loop-01/aggregate/synthesis-loop-02-feedback.json` (accepted
improvement instruction plus per-judge evidence from **judge-accessibility** `gpt-5.6-terra` and
**judge-human-use** `claude-opus-4.7`), with `panel-scores.json` and `dissent.md`. The referenced Loop 01
`panel_score` (4.68) and `visual_information_clarity` (4.5) are **prior independent-judge inputs**, cited
only as the source of these instructions — **no qualitative score is claimed for this Loop.**

1. **Focus-safe skip destination (accessibility).** `#checkout-form` is now programmatically focusable
   (`tabindex="-1"`, labelled "Checkout details"); the skip-link handler preventDefaults, moves focus to
   that named form start (falling back to the first `contact-name` field), scrolls it into view, and
   announces the move. Focus never lands on `BODY`.
2. **Lower default vertical density without wizard steps (accessibility + human-use).** Compact-completed
   now defaults **ON** on restore only when a real content section (contact or delivery) is complete; a
   remembered explicit user preference wins and is re-persisted. Compaction uses a **reveal-safe**
   visually-hidden `.compacted-body` technique, and every compacted descendant receives `tabindex="-1"`
   with the body `aria-hidden` — so **no hidden descendant remains keyboard-focusable**. `.intro` padding
   was reduced. No wizard steps were introduced.
3. **User-neutral shipping default (human-use).** The preselected Standard shipping no longer claims
   `Complete`; its badge reads **`Default selected: Standard`** until the user focuses or changes it, then
   `Complete`. `sectionIsComplete('shipping')` is unchanged, so progress/placement semantics hold, and an
   unacknowledged default shipping section is never auto-compacted out of view.
4. **Persisted non-sensitive placed flag (human-use).** On placement only `{ placed:true,
   confirmationId:'SYN-2048' }` is persisted alongside the existing non-sensitive fields. A
   post-confirmation reload keeps **Place order disabled**, reveals the confirmation, and shows the new
   `#placed-banner`: **"This synthetic order was already placed as SYN-2048."** Starting a genuinely new
   synthetic order clears the flag. **Payment fields are never persisted.**
5. **Improved touch-target margin (panel instruction).** Compact-toggle and choice/review controls were
   raised from 24px to **28px**, above the harness 24×24 floor. Reduced-motion and responsive mobile
   layout are unchanged.

Full evidence-referenced detail is in `synthesis/loop-02/adoption-rejection-matrix.json` / `.md`.

## 3. Preserved invariants

The one-page landmarked synthesis, grouped error recovery, safe-storage boundary, confirmed/cancellable
clear flow, compact hidden descendants, direct Edit controls, progress semantics, and **exactly one**
local SYN-2048 confirmation are all preserved. No account creation, discounts, recommendations, external
assets, extra checkout steps, or unrelated features were added.

## 4. Terminal objective result — all seven gates pass

A single terminal frozen objective run (PID 3824) exited 0 with no repair attempt:

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
- **Fixture SHA-256:** `e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894` · **Harness SHA-256:** `de51a917b14aa9e0d003efb5e84fc98cf42b089e31448bcaf9f4889d3b060563` (both unchanged)
- **Run window (UTC):** start `2026-07-21T22:04:38.0495550Z` → end `2026-07-21T22:04:56.4096810Z`, exit code 0
- Non-gating task-efficiency metrics: activations 20, corrections 4, completion interactions 1, focusable controls traversed 28. Context only; neither pass nor fail a gate.

The objective command was run exactly as specified from the repository root and is terminal — it was **not** rerun:

```
python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\synthesis\loop-02 --out .experiments\accessible-mobile-checkout\generated\synthesis\loop-02\evidence
```

Evidence: `synthesis/loop-02/process.json`, `synthesis/loop-02/evidence/objective-report.json`,
`synthesis/loop-02/evidence/objective-report.txt`, and six harness screenshots under
`synthesis/loop-02/evidence/`.

## 5. Observed improvements (objective) and no-regression

**Observed objective improvements vs Loop 01 are none in gate terms** — Loop 01 already passed all seven
gates, so the ceiling was maintained, not raised. The five changes are targeted at the *qualitative*
frictions the objective harness cannot score, while the objective gates confirm they introduced **no
regression**. The touch-target increase (24→28px) widens the mobile-touch-gate safety margin.

synthesis-loop-02 and every comparator were evaluated on the identical canonical fixture
(`e6622cd3…`), and all record `failed_gate_ids: []` with zero external requests — **no pass-to-fail
regression** against Loop 01 or any of the three ancestor finalists:

| Candidate | failed_gate_ids | external requests | report |
| --- | --- | --- | --- |
| synthesis-loop-02 | [] | 0 | `synthesis/loop-02/evidence/objective-report.json` |
| synthesis-loop-01 | [] | 0 | `synthesis/loop-01/evidence/objective-report.json` |
| single-page-loop-02 | [] | 0 | `track-single-page/loop-02/evidence/objective-report.json` |
| resumable-wizard-loop-02 | [] | 0 | `track-resumable-wizard/loop-02/evidence/objective-report.json` |
| task-cards-loop-01 | [] | 0 | `track-task-cards/loop-01/evidence/objective-report.json` |

## 6. Limitations

- **Independent qualitative judging is pending.** The seven objective gates cover only frozen technical
  correctness and compatibility. Whether the five adopted changes actually resolve the judged frictions —
  across the eleven human-use lenses — has **not** been independently judged for this Loop. No
  synthesizer-authored qualitative score exists and none may be invented; **no Champion, `new_best`, or
  promotion is claimed.**
- **Reveal-safe compaction is a deliberate trade-off.** Compacted sections are visually hidden yet remain
  in the DOM and operable for the frozen harness's fill/reveal, while being removed from keyboard focus
  (`tabindex="-1"` + `aria-hidden`) for AT users and expanded once the order is placed. Whether this reads
  cleanly for assistive-technology users is a qualitative question for the pending panel.
- **One-page density on the smallest viewport** is reduced (default-on compaction, tighter intro) but not
  eliminated; residual cognitive load at ~320–390px remains a qualitative risk the gates cannot measure.
- **Permanent procedural provenance caveats** apply to the lineage (see §8); they are procedural only and
  do not imply functional invalidity.

## 7. Final-judge handoff

`keep_for_synthesis` pending **independent, identity-blind qualitative final judges**, who should operate
this Loop against all eleven frozen human-use lenses and preserve dissent. This is planned Loop 8 of 8
(hard cap 11); **no further synthesis Loop is authored.** The synthesizer does not promote, does not edit
the Manifest/Viewer/process ledger, and makes no Champion/`new_best`/qualitative claim. Objective status:
all seven gates pass, zero external requests, fixture/harness hashes unchanged, no regression.

## 8. Caveats

- **Permanent path-remediation procedural caveat:** During `task-cards-loop-01`, fifteen diagnostic
  scripts were written at the repository root outside the task write scope; `resumable-wizard-loop-02`
  later deleted them before quarantine and omitted scratch provenance. Remediated with a permanent
  caveat. Forensics found no environment/credential reads, no external data, no generated secrets, and no
  network hosts, and the recovered `test-gates.py` was byte-identical to the frozen harness. Functional
  and hash validity is **preserved**; the caveat is **procedural only**. Evidence:
  `harness/path-violation-evidence/provenance.json`.
- **Inherited reboot interruption / recovery caveat:** synthesis-loop-01's records were completed by a
  single owner-authorized post-reboot continuation after its agent handle did not survive a PC reboot. The
  Loop 01 terminal objective run had already completed (exit 0, all seven gates passing) before the
  interruption and was **not** rerun; all immutable Loop 01 functional outputs were hash-verified against
  the launch recovery inventory. synthesis-loop-02 copied those verified Loop 01 files as its starting
  point without mutating Loop 01. Evidence: `synthesis/recovery/recovery-inventory.json`,
  `synthesis/recovery/post-recovery-verification.json`.
