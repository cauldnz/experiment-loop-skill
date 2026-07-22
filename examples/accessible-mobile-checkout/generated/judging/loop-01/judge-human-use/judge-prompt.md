# judge-prompt (verbatim instruction preserved)

This file preserves the exact instruction under which the `judge-human-use` blind panel record for Loop 01 was produced. No other-judge output was read before or during this judgement.

---

You are the approved independent blind `judge-human-use` for Loop 01 of an accessibility-first mobile checkout Experiment. Operate and judge three blinded candidates. Do not edit candidates, read Track/model identities, read other judge output, or create a new candidate.

Repository root: <skill-repository>
Approved immutable setup (read for acceptance contract, not candidate identity):
- `.experiments\accessible-mobile-checkout\setup\experiment-brief.json`, revision 1
- `.experiments\accessible-mobile-checkout\setup\prompt.md`
Frozen objective harness and fixture are read-only.

Blinded evidence bundles, evaluate in this flipped exact order:
1. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-01\candidate-c`
2. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-01\candidate-b`
3. `.experiments\accessible-mobile-checkout\generated\judging\blind-loop-01\candidate-a`
Each has local index.html/styles.css/app.js and a passing frozen objective report/screenshots. Do not search outside these bundle directories for candidate identity, source Track, metadata, or model.

Write scope ONLY:
`.experiments\accessible-mobile-checkout\generated\judging\loop-01\judge-human-use\**`
No setup, harness, blind bundle, candidate, other judge, top Manifest/Viewer, dependency, network, git, commit, PR, or promotion changes.

Exact human-use declaration to repeat in every handoff/result:
`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.
Qualitative human-use scores are not objective gates. All three objective reports pass; you cannot override them.

Required lenses, each independently scored 1-5 with concrete evidence refs and findings:
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
Also score `visual-information-clarity` 1-5. Primary overall `human-use-quality` is the arithmetic mean of the 11 lens scores for your raw judge record only; later aggregation uses the panel median and preserves dissent.

You must operate each local UI with cached Python Playwright in a separate fresh context, not judge screenshots alone. Use identical tasks/data for each candidate. Exercise every discoverable control and the required canonical path; validation/error recovery; edit/review; reload/resume and payment non-persistence; reduced-motion mode; mobile viewports; keyboard operation (Tab/Shift+Tab/Enter/Space); repeated Place order; confirmation; and inspect console/runtime errors. Capture your own action→outcome transcript and screenshots for initial, error, review, confirmation, and any defect. Do not alter objective harness evidence.

Write:
- `status.json` at start, heartbeat, and terminal;
- `candidate-a.json/.md`, `candidate-b.json/.md`, `candidate-c.json/.md` with actual model `claude-opus-4.7`, exact scores, evidence refs relative to generated root, lens findings, strengths, defects, uncertainty, and one evidence-backed Loop 02 recommendation;
- `navigation-transcript-a.json`, `-b.json`, `-c.json` with actions/outcomes/console errors and screenshot refs;
- screenshots under `screenshots/<candidate>/`;
- `pairwise.json/.md` comparing C/B, B/A, C/A in that flipped order, preferences and confidence, without guessing identity;
- `manifest-ready.json` containing one raw manifest-ready qualitative judging record per blinded candidate: criterion_id human-use-quality, scorer_id blind-human-use-panel, kind qualitative_rubric, objective_gate false, score, evidence_refs, and all 11 lens_findings; plus visual-information-clarity raw score and next-loop feedback;
- `judge-prompt.md` preserving this exact instruction and noting no other judge notes were read.

Do not aggregate with another judge, choose a final Champion, reveal identities, modify Loop decisions, run Loop 02, or build the Viewer. If an artifact cannot be operated, record the concrete failure and score it; never invent evidence. Return paths, raw scores, pairwise preferences, major defects, heartbeat, and blockers.

---

## Provenance note

- Judge model actually used: `claude-opus-4.7` (primary role for `judge-human-use`; no fallback).
- No other judge's output (for example any `judge-accessibility` files under `.experiments\accessible-mobile-checkout\generated\judging\loop-01\`) was opened at any point before or during this judgement. Only the setup contract, the frozen objective reports inside each blinded bundle, and the bundles' own `index.html` / `styles.css` / `app.js` were read.
- No aggregation with another judge was performed; no Champion was selected.
