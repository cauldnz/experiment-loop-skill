---
name: experiment-loop
description: >-
  Use when the user wants AI-agent-mediated experimentation, iterative
  improvement, hill-climbing, bake-offs, self-improving loops, parallel
  prototypes, visual or quantitative judging, or a progress UI for comparing
  attempts. General-purpose: applies to code, prompts, designs, documents,
  images, data pipelines, models, UX, animations, reports, or any artifact where
  quality can be improved through build/run/judge/improve cycles.
---

# Experiment Loop

Rig up agent-mediated experimentation loops for open-ended improvement work.

The purpose of this skill is to turn a vague quality goal into a managed
optimization process:

1. Define the target and evaluation criteria.
2. Design experiments and variants.
3. Run build → execute/render/test → judge → improve loops.
4. Capture artifacts and judge notes.
5. Compare alternatives.
6. Synthesize the best learnings into a final pass.
7. Produce a simple UI so the user can inspect the hill-climb afterward.

This is not specific to images, 3D, animation, or code. Use the same structure
for any artifact that benefits from iteration.

## When to use this skill

Use this skill when the user says things like:

- "run experiments"
- "self-improving loop"
- "hill climbing"
- "build, render, judge, improve"
- "try three approaches in parallel"
- "compare agents"
- "bake-off"
- "iterate until better"
- "make a UI to track progress"
- "have subagents try variants"
- "synthesize the learnings"
- "judge the outputs and improve"

Do not use this skill for simple deterministic edits, one-shot answers, or
tasks where success is already exactly specified and no exploratory loop is
needed.

## Core principle

Every loop must create observable evidence.

Do not rely only on the agent's internal opinion. Each iteration should leave
behind:

- the artifact that was built,
- the command/run/render/test output if applicable,
- the judge notes,
- the next hypothesis,
- and enough metadata to compare it against other attempts.

For visual work, evidence usually means images, contact sheets, GIFs, videos, or
screenshots. For code, it may mean tests, benchmarks, lint output, logs, traces,
or UX screenshots. For writing, it may mean drafts, rubrics, reviewer notes, and
diffs.

## Standard workflow

### 0. Verify Experiment Setup for substantial runs

Use the companion `experiment-setup` skill before an Experiment that is
unattended, expected to exceed 30 minutes, uses parallel generator Tracks,
deploys anything, involves external users/services/telemetry/sensitive data, or
otherwise has meaningful cost or risk.

The approved setup lives in the target repository:

```text
.experiments/<experiment-id>/setup/
  prompt.md
  experiment-brief.json
  setup-review.md
  approval.json
```

Before any build or generation work, validate its exact approval binding:

```text
python <experiment-loop-skill>/scripts/validate_experiment_setup.py \
  --brief <setup>/experiment-brief.json \
  --prompt <setup>/prompt.md \
  --approval <setup>/approval.json \
  --require-approved
```

If validation fails, stop and return to `experiment-setup`. The frozen brief is
authoritative over chat memory, candidate claims, parent Prompt drift, and
candidate-authored metrics. Inject its invariants and each Track's allowed-change
scope into every generator, synthesis, repair, and judge Prompt. Blind candidate
identity or order when useful; never hide the acceptance contract from judges.

Small, low-cost, interactive Loops may proceed without a setup brief, but still
need a scorecard and observable evidence.

### 1. Clarify the optimization target

Restate the user's goal as an artifact plus a quality target.

Examples:

- "Generate exercise GIFs that resemble a clean exercise-catalog style."
- "Improve a data parser until it works against real vendor samples."
- "Create three UX prototypes and converge on the clearest one."
- "Optimize a prompt until it passes an evaluation set."

If the goal is ambiguous in a way that changes the experiment design, ask one
focused question. Otherwise proceed with reasonable assumptions.

### 2. Define the scorecard

Create a small scorecard before running loops. Prefer 4-7 criteria.

Scorecard examples:

- correctness / factual accuracy
- task success
- visual clarity
- style match
- robustness
- speed / cost
- simplicity / maintainability
- user preference fit

For each criterion, define what better looks like. If possible, include
measurable checks. If subjective, use short judge comments and side-by-side
comparison artifacts.

### 3. Choose judging mode

At kickoff, and again whenever the user asks while a run is in progress, choose
how loops will be judged.

Supported modes:

- **Single judge**: one model/agent scores each artifact. Fastest and cheapest.
- **Panel judge**: several models/agents independently score the same evidence,
  then their views are aggregated. Best for subjective quality, style, UX,
  visuals, prompts, writing, or high-stakes tradeoffs.
- **Hybrid judge**: model judge(s) produce scores first, then the user chooses or
  overrides the winner.

Default:

- Use **single judge** for deterministic/code/test-heavy tasks where objective
  metrics dominate.
- Use **panel judge** for subjective or visual tasks, or when the user asks for a
  bake-off.

Panel judging rules:

1. Judges must inspect the same evidence bundle: artifacts, scorecard, run logs,
   and prior judge notes.
2. Judges should not see each other's notes until after they submit their own
   scores.
3. Each judge returns criterion scores, a short rationale, top defects, and a
   next-step recommendation.
4. Aggregate by weighted mean score, but preserve dissenting comments. Do not
   flatten disagreement away.
5. If the panel disagrees strongly, prefer a synthesis step that tests the
   competing hypotheses instead of pretending there is one obvious winner.

Panel size guidance:

- 2 judges: quick sanity check.
- 3 judges: default panel for subjective work.
- 5 judges: only for expensive/high-value decisions.

When model selection is available, deliberately diversify the panel, for example:

```text
judge_config:
  mode: panel
  aggregation: weighted_mean_with_dissent
  judges:
    - id: fast-critic
      model: small/fast model
      role: catches obvious defects and regressions
    - id: deep-critic
      model: strongest reasoning model
      role: evaluates correctness and tradeoffs
    - id: style-critic
      model: vision/style-capable model if relevant
      role: evaluates subjective fit and presentation
```

For visual work, use at least one vision-capable judge when available. For code,
use at least one judge that can run/read tests and one judge focused on design or
security when relevant.

### 3a. Define scorer types

Separate objective scorers from qualitative judges. Objective scorers should
gate success when available; model judges are best for qualitative assessment,
tradeoffs, and tie-breaking unless there is no objective metric.

Supported scorer types:

- **`objective_command`**: command exits, tests, benchmarks, static analysis,
  metric scripts, or other reproducible checks.
- **`llm_rubric`**: one artifact scored against the scorecard/rubric.
- **`pairwise_judge`**: A/B comparison against another candidate or the current
  champion.
- **`human_review`**: explicit user selection, override, or preference note.

If a primary objective scorer fails, the iteration cannot become champion unless
the user explicitly overrides that gate.

### 4. Choose experiment topology

Pick the smallest useful topology:

- **Single-track loop**: one agent or the main agent runs N iterations.
- **Parallel variants**: multiple agents each optimize a different dimension.
- **Bake-off**: multiple agents attempt the same goal independently.
- **Synthesis pass**: after variants finish, one agent combines the best ideas.
- **Human-in-the-loop**: pause after contact sheets/results so the user can pick
  winners.

Default topology for open-ended work:

1. Run 2-4 parallel variant agents.
2. Each variant performs 2-3 loops.
3. Run one synthesis agent for 1-2 loops.
4. Produce final artifacts and a viewer.

### 5. Create an experiment workspace

Use a dedicated output directory in the current workspace:

```text
experiment-loop/
  manifest.json
  viewer.html
  track-<name>/
    loop-01/
      artifact...
      judge.md
      metadata.json
    loop-02/
    final/
  synthesis/
```

If working in a repository, avoid committing generated experiment artifacts
unless the user explicitly wants them. For scratch/chat sessions, local files are
fine.

### 6. Record a manifest

Maintain a Manifest v1.1 JSON record so the Viewer can be generated without
guessing. The complete contract lives in `references/manifest-schema-v1.1.json`
and `templates/manifest-template.json`.

```json
{
  "schema_version": "1.1",
  "experiment_id": "short-stable-id",
  "title": "...",
  "problem": {
    "statement": "...", "optimization_target": "...",
    "constraints": ["..."], "success_criteria": ["..."],
    "original_prompt": "exact prompt text"
  },
  "generation": {
    "skill_commit": "...", "skill_tree_sha256": "...", "prompt_sha256": "...",
    "copilot_cli_version": "...", "orchestrator_model": "...",
    "models": [{"role": "orchestrator", "model_id": "..."}]
  },
  "budget": {"max_iters": 15, "patience": 4, "cost_limit": null, "wall_time_limit_sec": 3600},
  "artifact_scope": {"roots": ["."], "allow_edit": ["experiment-loop/**"], "deny": [".env", "secrets/**", "**/*credential*"]},
  "scorecard": [{
    "id": "clarity", "label": "Visual clarity", "weight": 1,
    "direction": "maximize", "unit": "points",
    "comparable_across_tracks": true, "primary": true,
    "baseline": {"value": 2, "unit": "points", "source_artifact_id": "baseline"}
  }],
  "scorers": [
    {"id": "quality", "type": "llm_rubric", "criterion_ids": ["clarity"], "judge_panel": "default_panel", "primary": true, "weight": 1}
  ],
  "judge_panels": [{
    "id": "default_panel", "blind": true, "flip_pairwise_order": true, "aggregation": "median_with_dissent",
    "judges": [
      {"id": "fast-critic", "role": "obvious defects"},
      {"id": "deep-critic", "role": "correctness and tradeoffs"},
      {"id": "style-critic", "role": "subjective style/presentation"}
    ]
  }],
  "governance": {"self_editing": {"requires_user_approval": true, "proposal_required": true, "approved_proposal_id": null}},
  "tracks": [{"id": "presentation", "label": "Presentation", "hypothesis": "..."}],
  "iterations": [{
    "id": "loop-001", "track_id": "presentation", "parent_ids": [], "model_id": "...",
    "hypothesis": "Widening the camera will reduce clipping.",
    "outcome": "The measured result and gate state.",
    "commands": {"build": "edit renderer", "run": "render preview", "judge": "judge with default_panel"},
    "artifacts": [{"id": "baseline", "kind": "image", "role": "primary-output", "label": "Contact sheet", "path": "track-presentation/loop-001/contact.png", "sha256": "...", "presentation": {"mode": "image", "featured": true, "primary": true, "caption": "...", "alt_text": "...", "comparison_key": "primary-output"}}],
    "scores": [{"scorer_id": "quality", "criterion_id": "clarity", "value": 3.8, "notes": "..."}],
    "prompt": {"track_prompt": "...", "input_feedback": "...", "judge_feedback": "...", "next_prompt": "..."},
    "quality_gates": {},
    "changed_files": ["renderer.py"],
    "lesson": {"trigger": "...", "action": "...", "evidence": "...", "confidence": "medium"},
    "decision": "keep_for_synthesis", "stop_reason": null
  }],
  "champion": {"iteration_id": "loop-001", "summary": "...", "reasons": [{"text": "...", "evidence_refs": ["clarity", "baseline"]}], "caveats": []},
  "story": {"milestones": [{"iteration_id": "loop-001", "caption": "Baseline"}, {"iteration_id": "loop-002", "caption": "Measured improvement"}], "featured_artifact_id": "baseline", "primary_comparison_key": "primary-output"},
  "rules": [],
  "synthesis": ""
}
```

Use relative paths in the manifest so the viewer works from the local filesystem.

### 6a. Manifest is the source of truth

For every experiment, the manifest is authoritative. Do not rely on chat
history, filenames, or memory to reconstruct experiment state.

Every experiment must contain at least two loops. A single candidate does not
demonstrate comparison or improvement and is not a completed experiment.

Every loop entry should include:

- `id`
- `track_id`
- `parent_ids`
- `model_id`
- `hypothesis`
- `commands.build`
- `commands.run`
- `commands.judge`
- `artifacts[]`
- `scores[]`
- `prompt.track_prompt`, `prompt.input_feedback`, `prompt.judge_feedback`, and
  `prompt.next_prompt` where a loop is prompt-, agent-, or feedback-driven
- `changed_files[]`
- `lesson`
- `decision`
- `stop_reason` when applicable

Use `decision` values:

- `new_best`
- `reject`
- `keep_for_synthesis`
- `needs_human_review`
- `failed`

Use schema version `1.1` for new manifests. Record the exact skill, prompt,
Copilot CLI, orchestrator model, and role/track/judge model provenance under
`generation`. A fuller reference shape lives in
`references/manifest-schema-v1.1.json`.

For parallel-agent runs, each agent should also write one manifest-ready fragment,
for example:

```text
track-<name>/
  manifest-fragment.json
```

The fragment should contain the track definition and that agent's loop entries
using the same schema as the top-level manifest. The orchestrator owns merging
fragments into `manifest.json`.

After building the Viewer and producing Navigation Evidence, run the bundled
Evidence Gate before reporting done:

```
python <experiment-loop-skill>/scripts/run_evidence_gate.py experiment-loop
```

It checks that:

1. `manifest.json` parses as JSON.
2. The manifest conforms to schema v1.1 and contains at least two Loops.
3. Track, multi-parent, Champion, criterion, scorer, model, milestone, and
   Artifact references are coherent.
4. Every referenced Artifact exists and any recorded SHA-256 matches.
5. `build_viewer.py --data DIR --out FILE` regenerates the Viewer deterministically.
6. `viewer.html` is self-contained, parseable, accessible, and robust.
7. Current passing `navigation-evidence.json` matches the Viewer SHA-256.

The gate writes `evidence-gate.json` with explicit `pass`, `fail`, and `blocked`
checks. Any required `fail` or `blocked` result means the experiment is **not
done**. Fix it and rerun. A failed primary objective scorer, Evidence Gate, test,
or metric gate blocks Champion promotion unless the user explicitly overrides.

Use a safe JSON embedding method rather than regex replacement strings that can
interpret path backslashes.

### 7. Run each loop

Each loop follows this contract:

1. **Build**: implement the variant or change.
2. **Run**: execute the code, render the image, run tests, produce draft, etc.
3. **Observe**: inspect real outputs, not assumptions.
4. **Judge**: score/comment against the scorecard using the selected judge mode.
5. **Compare to champion**: decide whether this is a new best, a rejection, or a
   useful partial result for synthesis.
6. **Improve**: define the next hypothesis before changing anything.

After judging, compare the iteration with the current champion:

- If better, mark `decision: new_best` and update `champion`.
- If worse, mark `decision: reject` and record the regression.
- If it has useful partial ideas, mark `decision: keep_for_synthesis`.
- If unclear, mark `decision: needs_human_review`.

Each loop may add at most one durable lesson. A lesson must include:

- trigger
- action
- evidence
- confidence

Promote only repeated or high-confidence lessons into `rules[]`. Compact old
detail into `synthesis` when the manifest grows too large, but keep raw artifacts
recoverable on disk.

The judge note format:

```markdown
# Judge: <track> loop <n>

## What changed
- ...

## Evidence inspected
- ...

## Scores
- criterion: 1-5 — reason

## Judge mode
- single | panel | hybrid

## Panel notes
- judge_id: scores — rationale
- dissent / disagreement:

## What improved
- ...

## What failed / regressed
- ...

## Next hypothesis
- ...
```

For panel judging, write one independent judge note per judge if practical:

```text
loop-02/
  judge-fast-critic.md
  judge-deep-critic.md
  judge-style-critic.md
  judge-aggregate.md
```

The aggregate judge note should include the winning hypothesis, the average
scores, and any dissent worth preserving.

For pairwise or panel judging:

- Blind labels when possible.
- Randomize A/B order.
- Flip order for a second vote when cost allows.
- Track position bias and dissent.
- Preserve individual judge notes in the manifest.
- Do not allow a generator to be the only judge of its own output.

#### Independent judge gate

For subjective, visual, UX, writing, prompt, or other qualitative work, a generator
must not be the sole judge for any artifact promoted to `new_best`.

Allowed patterns:

- track agent produces artifacts plus provisional self-judge; main agent or a
  separate judge validates before promotion;
- track agent produces artifacts only; independent judge writes the loop judge;
- panel judges inspect the same evidence bundle and aggregate scores.

If no independent judge is run, mark the loop `keep_for_synthesis` or
`needs_human_review`, not `new_best`, unless the user explicitly accepts that
reduced rigor for the run.

#### Navigation-based judging for interactive artifacts

When the artifact under judgement is *interactive* — a viewer, dashboard, SPA,
prototype, or any UI with tabs, filters, keyboard controls, or deep-links — a
static screenshot is not sufficient evidence. Judges must **operate** the
artifact and score from observed behaviour, not appearance alone.

Each judge (or a shared navigation harness that every judge runs) should:

- exercise every discoverable control (click each tab, select each filter
  option, toggle each checkbox);
- record, per interaction, whether the view actually changed;
- keyboard-operate the primary control group (focus, Arrow keys, Enter/Space);
- round-trip any URL-hash / deep-link view state;
- capture a screenshot per interaction state plus a transcript of
  actions → outcomes and any console errors.

Score interactivity, hierarchy, and robustness from that transcript, citing the
concrete interaction observed. A control that is visibly present but does nothing
(a nav link that only scrolls, a dead filter, a non-operable tablist) is a defect,
not something to credit from a screenshot. Prefer a shared, reproducible
navigation harness so every judge exercises the same states and the evidence is
auditable.

#### Visual-quality gate

For visual, UX, design, animation, and presentation artifacts, do not treat
"file exists", "SVG parses", or "render command succeeded" as sufficient visual
quality evidence.

Include an objective or semi-objective visual-quality gate where practical. The
gate should inspect real artifacts for overlap, clipping, unreadable text,
hidden controls, broken layout, missing frames, broken transparency, or other
visible defects. If the gate fails, the iteration cannot become champion unless
the user explicitly overrides it. Record the gate output as an artifact or
manifest field so the viewer can show why the iteration was rejected.

### 8. Use subagents deliberately

When using background agents, give each one:

- the overall goal,
- its track hypothesis,
- exact workspace/output folder,
- required loop count,
- required artifact names,
- scorecard,
- judge mode and judge panel configuration,
- command/tool constraints,
- and final report format.

Do not let multiple agents write to the same files. Use separate variant files
and output folders.

Good track prompts:

- "Optimize anatomy/silhouette only; do not edit presentation settings unless
  needed."
- "Optimize kinematics/form only; preserve visual style."
- "Optimize packaging/export/UI only; do not change core algorithm."
- "Synthesize the best ideas from tracks A/B/C into a new variant."
- "Judge this loop independently as `style-critic`; do not read other judge notes
  until after writing your own."

Specialist-track mode:

1. Split the goal into independent hypotheses.
2. Give each specialist a separate output folder and non-overlapping edit scope.
3. Require each specialist to produce final artifacts and loop judgements.
4. Run a synthesis agent that explicitly accepts/rejects learnings from each
   specialist.
5. The synthesis artifact competes against the champion, not just weak baselines.

### Long-running command recovery

For renders, builds, tests, training jobs, or other long commands, distinguish
between a failed command and a command that merely exceeded the first wait
window.

- Record the command handle/session ID in loop metadata when available.
- If the command is still running, resume/read that command instead of rerunning.
- Do not mark a loop failed until the command exits unsuccessfully or required
  artifacts are missing after the process ends.
- For user check-ins, report "still running" separately from "failed".

For long parallel-agent runs, each track should write a small `status.json` or
`heartbeat.md` after each loop with current loop, latest artifact path, current
score if known, and blocker/failure status.

### 9. Build the Viewer

Every experiment produces a local static Viewer:

```text
experiment-loop/viewer.html
```

Viewer requirements:

- works by opening the HTML file directly;
- no external CDN dependencies;
- embeds its Manifest data;
- is generated by a standard `build_viewer.py --data DIR --out FILE` adapter;
- uses the shared `references.viewer_renderer` module when available;
- keeps Overview, Tracks/lineage, and Loops as fixed core panels;
- declares only additional curated panels in an example-local `ViewerProfile`;
- timeline of loops;
- filters by track and artifact type;
- loop cards with artifacts, single-judge notes, panel notes, aggregate scores,
  and dissent;
- score timeline and champion marker;
- per-criterion score table or heatmap;
- command/provenance drawer;
- artifact metadata where available: hash, dimensions, duration, frame count,
  and exact evidence sent to judges;
- prompt and feedback chain for each iteration: original/track prompt, parent or
  human feedback used as input, judge feedback, and next prompt;
- visual-quality gate output for visual work, including rejected overlap,
  clipping, readability, or broken-layout defects;
- filters by track, scorer, judge, status, decision, and `new_best`;
- "why this won" summary and regression warnings;
- side-by-side comparison;
- finals gallery;
- missing artifacts shown gracefully;
- clear hill-climb narrative;
- a relative link to `evidence-gate.json`;
- an embedded declarative interaction contract covering every interactive control.

All Viewers are interactive and must:

- every interactive control must verifiably change the view — no dead controls
  (e.g. a nav link that only scrolls, or a filter that never re-renders);
- the primary control group must be keyboard-operable (roving focus, Arrow/Home/
  End, Enter/Space) with a visible focus ring and `prefers-reduced-motion`
  respected;
- view state that matters should be addressable via URL hash (e.g. `#tab=panel`)
  so a specific view is shareable and reproducible;
- rebuild byte-identically from the standard adapter, with timestamps read from
  the data and no wall-clock, randomness, or network access;
- surface auditable validation diagnostics — to stderr and as an embedded HTML
  comment — when input is missing or malformed, instead of rendering silently.

Run the shared navigation judge against every Viewer. It executes the embedded
interaction contract, cross-checks discovered controls, tests keyboard operation
and deep links, captures screenshots, and writes `navigation-evidence.json`.
Uncovered or dead controls, keyboard/deep-link failures, and console errors are
blocking. The Evidence Gate then validates the full experiment and writes the
linked `evidence-gate.json` sidecar.

If the environment blocks browser rendering, still create the HTML and provide
the file path.

### 10. Synthesize learnings

After parallel tracks finish, run a synthesis pass:

1. Inspect final artifacts and judge notes from all tracks.
2. Identify which changes actually improved the scorecard.
3. Create a fresh synthesis variant rather than mutating any track.
4. Run 1-2 synthesis loops.
5. Produce final artifact(s), final judge notes, and update the viewer.

The synthesis report should say:

- which track contributed which idea,
- what was rejected and why,
- final scores,
- judge mode used and any panel disagreement,
- remaining limitations,
- and the next highest-value experiment.

### 11. Gate self-improvement changes

When the experiment target is the skill itself, an agent, a judging rubric, a
workflow policy, or any durable instruction that will affect future runs, do not
apply changes immediately.

Use a two-step proposal/apply gate:

1. **Proposal phase**: write a proposed change record and present it to the user.
2. **Approval phase**: apply the change only after explicit user approval in the
   current conversation.

This gate is mandatory for:

- editing this `experiment-loop` skill;
- editing any other skill or reusable agent instruction;
- changing the scorecard/rubric after an experiment has started;
- changing approval, safety, filesystem, command, or network policy;
- adding a new automated judge that can approve its own future changes.

Proposal records should be stored with the experiment, for example:

```text
experiment-loop/
  proposals/
    proposal-001.md
```

Proposal format:

```markdown
# Proposal <id>: <title>

## Trigger
What observation, failure, prior-art finding, or user request caused this?

## Proposed change
The smallest durable change to make.

## Files to change
- path

## Exact intended diff or snippet
Show enough detail that the user can approve knowingly.

## Expected benefit
Which future failure does this prevent or which capability does it unlock?

## Risks / regressions
What could get worse?

## Rollback
How to undo it.

## Approval status
pending | approved | rejected
```

Rules:

- Do not bundle unrelated durable changes into one proposal.
- Do not treat "sounds good" from an earlier turn as approval for a later diff.
- Do not self-approve.
- Do not silently apply proposal changes while doing ordinary loop work.
- If approval is ambiguous, stop and ask for explicit approval.
- After applying an approved proposal, record the applied file paths and a short
  result note in the manifest.

### 12. Self-test durable skill changes

When the experiment target is this skill, a rubric, judge policy, or another
reusable instruction, do not trust that a change is an improvement — measure it.
Before writing the proposal above, run the current skill and the proposed skill
over a small **external, version-pinned** benchmark (at least one each of:
code/quantitative, visual, writing, and a governance check) plus objective
validators, and compare the quality of the runs they produce — not opinions about
the diff. The benchmark and its rubric must live outside the skill so a change
cannot weaken its own test. Confirm shipped examples still validate:

```
python scripts/skill_selftest.py
```

Attach the benchmark comparison and self-test result to the proposal as evidence;
a change that does not beat the current skill should not be proposed as an
improvement. See `docs/self-testing.md` for the full method.

## Default output contract

At the end, report:

- final artifact paths,
- viewer path,
- best variant / synthesis winner,
- loop count and tracks,
- concise scorecard summary,
- remaining limitations.

Keep the final answer concise; the detailed history belongs in the viewer and
manifest.

## Practical patterns by artifact type

### Visual artifacts

Use contact sheets every loop — they make judging much faster than opening many
frames. Artifacts: `loop-01/contact.png`, `loop-01/sample.gif`, `loop-01/judge.md`,
`final/output.gif`. Judge for composition, style match, readability,
defects/regressions, and motion/timing if animated.

### Code artifacts

Use tests and benchmarks as the main evidence. Artifacts: test output, benchmark
output, logs, screenshots for UI, diff summary, judge note. Judge for correctness,
coverage, simplicity, maintainability, performance, and error handling.

### Writing or prompt artifacts

Use versioned drafts and rubric scoring. Artifacts: draft files, rubric notes,
pass/fail examples, judge note, final draft. Judge for audience fit, clarity,
completeness, accuracy, tone/style, and concise expression.

## Anti-patterns

Avoid:

- changing many variables at once without notes;
- agents overwriting each other's files;
- judging without real outputs;
- optimizing only for the easiest measurable metric when the user cares about
  qualitative quality;
- hiding failed attempts;
- reporting "done" without final artifacts;
- creating a viewer that only shows final outputs and loses the iteration path.
- self-editing skills, rubrics, judge policy, or reusable instructions without a
  proposal and explicit user approval in the current conversation.

## Minimal agent prompt template

```text
Goal: <artifact + target quality>.

You own track: <track name>.
Hypothesis: <why this track may improve the result>.

Workspace:
- Root: <absolute path>
- Output folder: <relative path>
- Do not write outside your output folder except for <allowed final files>.

Scorecard:
- <criterion>: what better means
- ...

Run exactly <N> loops. Each loop:
1. Build a variant.
2. Run/render/test it.
3. Create artifacts.
4. Judge against the scorecard.
5. Record next hypothesis.

Final deliverables:
- final artifact paths
- contact sheets or evidence files
- judge notes
- concise report of loop-by-loop learnings
```
