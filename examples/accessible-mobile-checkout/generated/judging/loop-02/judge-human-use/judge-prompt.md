# Judge prompt (verbatim, `judge-human-use`, loop-02)

This file preserves the exact instruction issued to this judge. This judge did not read any other judge notes, the orchestrator-only blinding map, or the `.experiments/accessible-mobile-checkout/generated/judging/loop-02/orchestrator` directory. Setup files were opened read-only for the acceptance contract and were not used to infer candidate identity.

---

You are the approved independent blind `judge-human-use` for Loop 02 of the frozen accessibility-first mobile checkout Experiment. Operate and judge three blinded candidates. Do not edit candidates, read Track/model identities, read the orchestrator-only blinding map, read other judge output, or create a new candidate.

Repository root: <skill-repository>
Approved immutable setup (read for acceptance contract, never edit and never use to infer candidate identity):
- `.experiments\accessible-mobile-checkout\setup\experiment-brief.json`, revision 1, SHA-256 ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13
- `.experiments\accessible-mobile-checkout\setup\prompt.md`, SHA-256 86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928
Frozen objective harness and fixture are read-only. The remediation provenance does not change candidate scoring; all three final objective reports pass and their hashes were reverified.

Blinded evidence bundles, evaluate in this flipped exact order:
1. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-02\candidate-c`
2. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-02\candidate-b`
3. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-02\candidate-a`
Each bundle contains only a local candidate, final objective report/screenshots, and an identity-free bundle manifest. Do not search outside these bundle directories for candidate identity, source Track, parent, metadata, model, prior score, prior judge notes, or `.experiments\accessible-mobile-checkout\generated\judging\loop-02\orchestrator`.

Write scope ONLY:
`.experiments\accessible-mobile-checkout\generated\judging\loop-02\judge-human-use\**`
No setup, harness, blind bundle, candidate, other judge, orchestrator map, Manifest/Viewer, dependency, network, git, commit, PR, promotion, or Example changes.

Exact human-use declaration to repeat in every handoff/result:
`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
Qualitative scores are not objective gates. All objective reports pass; do not override, weaken, or rerun them.

Required lenses, each independently scored 1-5 with concrete evidence references and findings:
- discoverability
- navigation
- input_burden
- error_prevention_recovery
- feedback_status
- accessibility
- responsive_touch_ergonomics
- interruption_resumption
- latency_perception
- destructive_actions
- cognitive_load
Also score `visual-information-clarity` 1-5. Primary raw `human-use-quality` is the arithmetic mean of the 11 lens scores for your record only; later orchestration aggregates per-lens medians and preserves dissent.

You must operate each local UI with cached Python Playwright in a separate fresh context, not judge screenshots alone. Use identical synthetic tasks/data for every candidate. Exercise every discoverable control and canonical checkout path; validation/error recovery; edit/review; reload/resume and payment non-persistence; reduced-motion; 320x568, 360x800, and 390x844 behavior; keyboard Tab/Shift+Tab/Enter/Space; repeated Place order; confirmation; and console/runtime errors. Explicitly test whether keyboard focus can enter visually collapsed, clipped, inactive, or aria-hidden content; whether accordion/wizard expanded state matches actual keyboard and screen-reader exposure; skip-link focus; empty-step progression; clear-progress confirmation; routine live-region politeness; and duplicate-submit behavior. Score from observed behavior, not implementation claims. Capture an action-to-outcome transcript and screenshots for initial, error, review, confirmation, and each material defect.

Write:
- `status.json` at start, timestamped heartbeat after each candidate, and terminal;
- `candidate-a.json/.md`, `candidate-b.json/.md`, `candidate-c.json/.md` with actual model `claude-opus-4.7`, exact scores, evidence refs relative to generated root, all 11 lens findings, visual-information-clarity, strengths, defects, uncertainty, and one evidence-backed synthesis adoption/rejection recommendation;
- `navigation-transcript-a.json`, `navigation-transcript-b.json`, `navigation-transcript-c.json` with actions, outcomes, console errors, viewport/motion/keyboard states, and screenshot refs;
- screenshots under `screenshots/<candidate>/`;
- `pairwise.json/.md` comparing C/B, B/A, C/A in that flipped order, preference, rationale, confidence, and evidence refs, without guessing identity;
- `manifest-ready.json` containing one raw Manifest-ready qualitative record per blinded candidate: criterion_id `human-use-quality`, scorer_id `blind-human-use-panel`, kind `qualitative_rubric`, objective_gate false, score, evidence_refs, and exactly all 11 lens_findings; plus the raw `visual-information-clarity` score and synthesis feedback;
- `judge-prompt.md` preserving this exact instruction and stating no other judge notes or identity map were read.

Do not aggregate, reveal identities, select Track finalists, choose a Champion, modify Loop decisions, launch synthesis, build Viewer/Navigation/Evidence Gate, or perform promotion. If an artifact cannot be operated, record the concrete failure and score it; never invent evidence. Return paths, raw scores, pairwise preferences, major defects, heartbeat, and blockers.
