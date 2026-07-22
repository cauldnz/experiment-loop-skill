# Self-observation — single-page-loop-01

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

## Scope

This is objective evidence recorded by the generator, not an independent judgement. It makes no promotion or `new_best` claim. The qualitative lenses remain pending independent review and are not treated as objective ergonomics results.

## Actual objective evidence

- Frozen command: `python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\track-single-page\loop-01 --out .experiments\accessible-mobile-checkout\generated\track-single-page\loop-01\evidence`
- Final exit code: `0`.
- Final report SHA-256: `805d112c0f00ffde9e017ec246f6ff9770171203f259f6544bf02f68aeb5d564`.
- Frozen fixture SHA-256 recorded by the report: `e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894`.
- All seven objective gates report `pass`: content fidelity, semantic accessibility, keyboard completion, error recovery, mobile touch, resilience, and offline safety.
- The final report has no failed gate IDs and `blocking_failure: false`.
- Non-gating metrics: 25 focusable controls traversed, 13 activations, 4 corrections, and 1 completion interaction.
- The harness produced initial, keyboard-completion, final, and 320x568, 360x800, and 390x844 viewport screenshots.
- Failed attempts remain unchanged in `evidence-attempt-01-failed` and `evidence-attempt-02-failed`.

## Repair evidence

Attempt 1 exited `1` with five failed gate IDs. Attempt 2 exited `1` with two failed gate IDs. Repairs were limited to clear candidate implementation defects in this Loop. Attempt 3 used the same frozen command and exited `0`.

## Pending evidence

No independent qualitative judge ran. No scores exist for discoverability, navigation, input burden, error prevention and recovery, feedback and status, accessibility, responsive touch ergonomics, interruption and resumption, latency perception, destructive actions, or cognitive load.
