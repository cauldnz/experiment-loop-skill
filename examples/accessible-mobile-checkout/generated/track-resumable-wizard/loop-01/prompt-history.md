# Prompt history — `resumable-wizard-loop-01`

## 1. Complete Track instruction acted on (verbatim)

`human_use.applicability = applicable`. Rationale: The Artifact is a
human-operated mobile checkout. Its success depends on discoverability,
navigation, input burden, error recovery, feedback, accessibility, touch
ergonomics, interruption recovery, perceived latency, destructive-action
safety, and cognitive load across cross-disability use.

Qualitative use-friction is not an objective ergonomics gate. Objective
browser assertions below cover only frozen technical correctness and
compatibility requirements. Required qualitative lenses for any later judge:
`discoverability`, `navigation`, `input_burden`, `error_prevention_recovery`,
`feedback_status`, `accessibility`, `responsive_touch_ergonomics`,
`interruption_resumption`, `latency_perception`, `destructive_actions`,
`cognitive_load`. These lenses must not be turned into objective ergonomics
claims by this Loop.

---

Execute exactly ONE candidate Loop as model role `generator-resumable-wizard`
under the approved accessibility-first mobile checkout Experiment. Do the
work, run the frozen objective harness, and write complete artifacts. Do not
judge yourself as new_best and do not touch any other Track.

Repository root:
`<skill-repository>`

Approved contract (read, never edit):
- `.experiments\accessible-mobile-checkout\setup\experiment-brief.json`
  revision 1, SHA-256
  ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13
- `.experiments\accessible-mobile-checkout\setup\prompt.md` SHA-256
  86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928

Frozen harness (read-only):
`.experiments\accessible-mobile-checkout\generated\harness\`; required hashes
are in frozen-hashes.json. Read canonical-fixture.json and
candidate-contract.json before coding.

Exact scratch root supplied by contract:
`.experiments\accessible-mobile-checkout\generated\harness\scratch`; do not
write there unless unavoidable. Keep all authored work in your Track.

Write scope ONLY:
`.experiments\accessible-mobile-checkout\generated\track-resumable-wizard\**`
No setup, harness, build_viewer.py, other Track, examples, repository source,
dependency, node_modules, lockfile, network, browser install, git, commit, or
PR changes.

Exact human-use declaration for every handoff/evidence file:
`human_use.applicability = applicable`. Rationale: The Artifact is a
human-operated mobile checkout. Its success depends on discoverability,
navigation, input burden, error recovery, feedback, accessibility, touch
ergonomics, interruption recovery, perceived latency, destructive-action
safety, and cognitive load across cross-disability use. Qualitative required
lenses: discoverability, navigation, input_burden,
error_prevention_recovery, feedback_status, accessibility,
responsive_touch_ergonomics, interruption_resumption, latency_perception,
destructive_actions, cognitive_load. Do not turn these qualitative lenses
into objective ergonomics claims.

Track hypothesis: A step-by-step wizard with explicit progress, back/edit
controls, per-step validation, and safe save/resume reduces cognitive load
without hiding status or trapping keyboard and screen-reader users.

Loop ID: `resumable-wizard-loop-01`; parent_ids: []; interaction paradigm
must remain a true step-by-step wizard with one primary task step visible at
a time, explicit named progress, keyboard-safe continue/back/edit, and
resumable state. The frozen harness may require all hook elements to exist
in the DOM; inactive steps may be hidden accessibly but must become operable
through the wizard journey.

Create under `track-resumable-wizard\loop-01\`:
- standalone local `index.html`, local `styles.css`, and local `app.js`; no
  external resource or server;
- complete exact synthetic fixture, explicit fictional/synthetic labelling,
  all required candidate data hooks, native semantics first, accessible
  labels/descriptions/errors/status, keyboard-visible focus, 24x24 minimum
  targets, pinned contrast, reduced-motion <=10ms, safe non-sensitive resume,
  no payment persistence, explicit review, duplicate-safe local SYN-2048
  confirmation;
- `metadata.json` with loop/model/hypothesis/parent_ids/commands/changed_files/
  lesson/decision (`needs_human_review` pending independent judges)/stop_reason,
  frozen hashes, and human-use declaration;
- `prompt-history.md` containing the complete Track instruction you acted on,
  input feedback (none), provisional self-observation clearly marked
  non-authoritative, and proposed next Prompt;
- `self-observation.md` describing actual objective evidence only, no
  promotion claim;
- `status.json` written at start and updated at least once with UTC
  heartbeat, then terminal status;
- Track-level `track-resumable-wizard\manifest-fragment.json` containing the
  Track definition and this one Manifest-ready iteration with stable artifact
  IDs, SHA-256 values, `interactive_html` presentation, comparison_key
  `checkout-ui`, prompt chain, scores only for objective evidence available,
  and `decision: needs_human_review`.

Run the frozen command from repository root:
`python .experiments\accessible-mobile-checkout\generated\harness\run_checkout_gates.py --candidate .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-01 --out .experiments\accessible-mobile-checkout\generated\track-resumable-wizard\loop-01\evidence`
Record exact command/exit. If it fails, inspect the objective report and
repair only clear implementation defects within this same Loop; preserve
each failed evidence attempt in a separately named evidence directory before
rerunning and never rewrite failure evidence. Final evidence must remain
under loop-01/evidence. If a frozen requirement is impossible, stop failed
and preserve output rather than weakening the harness.

Return exact files, objective gate states, metrics, hashes, heartbeat/status,
and blockers. Do not run an independent judge, create Loop 02, merge the top
Manifest, or build the Viewer.

## 2. Input feedback

None. This is Loop 01, the measured paradigm baseline for Track B, with
`parent_ids: []`. No prior objective report, judge finding, or human feedback
existed for this Track before this Loop began.

## 3. Provisional self-observation (non-authoritative)

The notes below are this generator's own impressions while building the
candidate. They are **not** an objective gate result and **not** a
qualitative-lens score — both require the frozen harness and an independent
blind judge respectively, neither of which this Loop is permitted to
substitute for itself:

- The forward-only design constraint (the harness's `reveal()` helper never
  presses `back`) pushed the implementation toward a "progressive disclosure"
  wizard rather than a strict single-step-visible wizard. Subjectively, this
  still reads as a genuine step-by-step wizard: only one step is the *active*
  task with a visible Continue control at a time, but once a step is reached
  its fields stay visible and editable rather than disappearing, which may
  incidentally also serve real users needing to see or fix earlier answers
  without losing later progress.
  - This is a hypothesis about human-use quality, not a measured finding. It
    has not been evaluated by `judge-accessibility` or `judge-human-use` and
    must not be treated as if it had.
- Two failure modes were only found empirically, not from reading the harness
  source alone: (a) `.inner_text()` in this Playwright build returns a
  descendant's static text even when an ancestor is `hidden`, so a
  confirmation ID must never be present in the initial HTML; (b) a single
  global `:focus` outline color can have very different measured contrast
  depending on the background of the specific focused control, so a
  dark-background button needed its own focus-outline color.

## 4. Proposed next Prompt (for a future Loop, not executed here)

If a Loop 02 is later authorized for this Track (out of scope for this Loop):

> Using `resumable-wizard-loop-01` (parent_id `resumable-wizard-loop-01`) as
> the baseline, and after independent `judge-accessibility` and
> `judge-human-use` blind scores are available for every required lens
> (`discoverability`, `navigation`, `input_burden`,
> `error_prevention_recovery`, `feedback_status`, `accessibility`,
> `responsive_touch_ergonomics`, `interruption_resumption`,
> `latency_perception`, `destructive_actions`, `cognitive_load`), make a
> second wizard Loop that acts only on that objective and independent
> qualitative feedback. Do not weaken any passing gate from Loop 01. Preserve
> Loop 01's evidence unchanged. Record the evidence-backed change explicitly
> in the new Loop's `lesson` field.
