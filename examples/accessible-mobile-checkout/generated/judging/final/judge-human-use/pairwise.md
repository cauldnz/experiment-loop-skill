# Judge-human-use — final panel — pairwise

**Model:** claude-opus-4.7  •  **Scope:** final  •  **Revision:** 1
**Objective gates:** all seven gates PASS for all three candidates (as persisted). Harness not rerun.

Comparison order (fixed): **c vs b**, then **c vs a** (required final strongest-parent-versus-candidate; flipped from the sibling judge's A-then-C order), then **b vs a**.

## candidate-c vs candidate-b — preferred: **candidate-b** (confidence: medium-high)

- **Regression assessment:** No regressions on any of the seven objective gates in either direction.
- **Observed rationale:**
  - candidate-b exposes a progressbar landmark (valuenow/valuetext) that surfaces where the user is in the flow; candidate-c has no progressbar landmark.
  - candidate-b provides an explicit Save-progress button with a live status announcement; candidate-c autosaves silently on input/change (user cannot deliberately verify state was saved).
  - candidate-b offers a full Confirm + Cancel + Escape destructive-safety flow on Clear-saved-progress; candidate-c offers no user-initiated Clear-progress affordance at all.
  - candidate-c has fewer controls (42 vs 47) — a small cognitive-load win, not enough to offset the missing feedback and destructive-safety affordances.
- **Uncertainty:** The cognitive-load advantage of candidate-c is real; users who dislike optional chrome could prefer it.

## candidate-c vs candidate-a — preferred: **candidate-a** (confidence: high) *(required final strongest-parent-versus-candidate)*

- **Regression assessment:** No regressions on any of the seven objective gates in either direction.
- **Observed rationale:**
  - candidate-a preserves duplicate-safety across a browser reload: after successful placement, `page.reload()` still shows the confirmation region and Place order remains disabled. candidate-c returns the form to editable state with Place order re-enabled after reload.
  - candidate-a provides explicit Save-progress with live status announcement; candidate-c does not.
  - candidate-a provides a full Confirm + Cancel + Escape destructive-safety flow on Clear-saved-progress; candidate-c offers no user-initiated Clear-progress affordance at all.
  - candidate-a exposes a progressbar landmark; candidate-c has no progressbar landmark.
  - candidate-c's leaner UI is a real cognitive-load win but is materially outweighed by the additional interruption-safety, feedback and destructive-safety affordances in candidate-a.
- **Observed pair ordering by this judge:** candidate-c then candidate-a (flipped from the sibling judge who observed A then C). The flip is procedural; it does not alter the preferred candidate.
- **Uncertainty:** None material — the four observed friction gaps for candidate-c all touch on affordances the task brief actively probes.

## candidate-b vs candidate-a — preferred: **candidate-a** (confidence: medium)

- **Regression assessment:** No regressions on any of the seven objective gates in either direction.
- **Observed rationale:**
  - candidate-a: after `page.reload()` following successful placement, `reload_state.confirmation_visible=true` and `reload_state.place_order_disabled=true`.
  - candidate-b: same reload, `reload_state.confirmation_visible=false` and `reload_state.place_order_disabled=false`.
  - Both share explicit Save-progress with live status, full Confirm + Cancel + Escape Clear-progress destructive-safety, progressbar landmark, and identical navigation and error-recovery patterns.
  - The differentiator is a stronger cross-reload duplicate-safety guarantee in candidate-a.
- **Uncertainty:** A design case could be argued that users who deliberately reload after placing an order might expect a fresh session (candidate-b), but from a friction/harm-avoidance standpoint the preserved confirmation is safer.

## Dissent

None to preserve at this step. If a downstream reviewer weighs cognitive-load parsimony above interruption/destructive-safety affordances, the c-vs-b and c-vs-a comparisons could shift toward candidate-c; the b-vs-a comparison would still stand on the cross-reload duplicate-safety evidence.
