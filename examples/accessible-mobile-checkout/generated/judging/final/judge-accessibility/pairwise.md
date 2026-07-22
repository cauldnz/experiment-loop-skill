# Accessibility final pairwise judgment

Judge/model: `judge-accessibility` / `gpt-5.6-terra`

All persisted objective reports pass all seven gates with zero external requests; the harness was not rerun.

## candidate-a-vs-candidate-b
Observed order: candidate-a → candidate-b
Preferred: **candidate-a** (moderate)
Both completed all exercised controls and passed all objective gates. A uniquely moved skip-link focus to checkout-form and retained the local SYN-2048 confirmation after reload; B had strong visible progress/status treatment but its skip activation had no identified target and its confirmation disappeared after reload.

Regression assessment: B is not objectively regressed. The preference is qualitative: focused skip behavior and post-confirmation resumption are stronger in A; B may be preferred by users who value its progress strip.

## candidate-a-vs-candidate-c
Observed order: candidate-a → candidate-c
Preferred: **candidate-a** (high)
Both passed the terminal objective reports and completed SYN-2048 without external requests. A provided explicit safe save, confirmed clear with Escape and Cancel paths, focused the skip destination, and preserved confirmation after reload. C safely auto-restored fields but offered no discoverable clear/reversal control and its confirmation did not persist.

Regression assessment: C's automatic safe restoration is a useful low-effort feature, not an objective failure; the absence of user-visible clear/cancel/Escape makes it qualitatively weaker for reversibility and predictable resumption.

## candidate-b-vs-candidate-c
Observed order: candidate-b → candidate-c
Preferred: **candidate-b** (moderate)
Both had grouped error recovery, safe payment-secret clearing, large targets, and terminal objective passes. B adds explicit safe save plus clear confirmation/Escape/Cancel controls and stronger visible state feedback; C reduces a step through automatic restoration but omits a discoverable reversal route.

Regression assessment: C has no objective failure and automatic restore may suit users who dislike save actions. B is preferred for explicit agency and safe destructive-action recovery.

Uncertainty/dissent: This is one independent accessibility-focused qualitative vote. A different panelist could reasonably value B's more prominent progress treatment or C's automatic restoration more strongly; neither preference changes the acknowledged objective passes.
