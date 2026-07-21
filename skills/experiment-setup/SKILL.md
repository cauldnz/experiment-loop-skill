---
name: experiment-setup
description: >-
  Use before substantial, unattended, high-cost, multi-track, deployed, or
  high-risk Experiment Loops. Discovers repository facts, interviews the user
  one decision at a time, freezes invariants and optimization variables,
  proposes topology/models/judging/evidence, runs an independent setup critique,
  and produces an explicitly approved Experiment Prompt and machine-readable
  brief for experiment-loop.
---

# Experiment Setup

Create a reviewable, frozen contract before an expensive Experiment begins.
This skill plans the Experiment; it does not run Loops.

## Non-negotiable interaction contract

1. Inspect the target repository before asking questions. Discover facts such as
   toolchains, existing commands, baselines, constraints, prior Artifacts, and
   likely edit scope yourself.
2. Ask only decisions the user must make.
3. Ask exactly one question at a time and wait for the answer.
4. Give a recommended answer with every question.
5. Adapt the interview: deepen ambiguous or risky branches, accept verified
   defaults for low-risk details, and do not run a fixed exhaustive script.
6. Do not run the Experiment or edit product code during setup.
7. Stop for explicit approval after presenting the complete Prompt, frozen
   brief, critic findings, and autonomy envelope.
8. Every setup must explicitly classify `human_use.applicability` as `applicable`
   or `not_applicable` and record a rationale. Never infer and omit the branch.

## Default output location

Write setup source into the target repository, never into the reusable skill
repository:

```text
.experiments/<experiment-id>/setup/
  prompt.md
  experiment-brief.json
  setup-review.md
  approval.json
```

The Experiment writes runtime output to:

```text
.experiments/<experiment-id>/generated/
  human-feedback/
    intake/
    dispositions/
  harness/
    scratch/
```

If the target project already has an Experiment convention, use it instead and
record the repository-relative paths in the brief.

For unattended Windows runs, `target.scratch_root` must be inside
`target.generated_root`; default to
`.experiments/<experiment-id>/generated/harness/scratch`. Prepare it before
handoff with:

```text
python <experiment-setup-skill>/scripts/prepare_scratch.py \
  --generated-root .experiments/<experiment-id>/generated
```

Never direct unattended agents to `%TEMP%` or a Claude/Copilot session
scratchpad. Windows session paths can contain 8.3 components such as
`CHRISA~1`, causing manual suspicious-path prompts. If a session scratch
directory is unavoidable, run the helper with `--session-scratch <path>`, record
and distribute only the printed long-form path, and make failure to expand a
pause condition.

## Phase 1 — Repository discovery

Read project context and ADRs. Determine without asking:

- artifact type and current implementation;
- existing tests, benchmarks, renders, linters, and build commands;
- current baseline Artifacts and likely comparison keys;
- file ownership and safe edit scope;
- available models/tools and environment limitations;
- deployment, telemetry, external-service, user-data, privacy, or credential
  signals;
- prior related attempts in repository or session history.
- owner-provided prior-art references, including local files, cited pages, and
  images that must be reviewed for functional reasoning.

Run only safe, existing, non-destructive preflight commands within a small
budget. Record commands and observed results. Do not install dependencies unless
an existing preflight fails specifically because dependencies are missing.

## Phase 2 — Adaptive interview

Resolve these branches in dependency order:

1. **Problem and audience** — Artifact, user, pain, and credible success.
2. **Human use** — explicitly decide applicable or not applicable and record why.
   Human-operated includes physical tools, web/mobile/desktop UI, interactive
   artifacts, and workflows. When applicable, select the relevant operation and
   context categories. Physical categories include grips, forces/loads,
   insertion/removal, inversion/retention, repetitive use, hand/contact edges,
   and assembly/disassembly. Digital/interaction categories include
   discoverability, navigation, input burden, error prevention/recovery,
   feedback/status, responsive/touch ergonomics, interruption/resumption,
   latency perception, destructive actions, and cognitive load. Also consider
   foreseeable misuse and relevant accessibility/safety interactions. Do not
   force irrelevant physical geometry categories onto digital systems. Every
   material friction becomes either a qualitative scorecard criterion or an
   explicitly justified design invariant.
   Ergonomics remains qualitative: do not invent mandatory edge-radius, force,
   torque, or similar numeric gates.
3. **Prior art** — review every owner-provided reference for source, observed
   functional choice, inferred rationale, adopt/adapt/reject decision and reason,
   originality implications, and evidence. Do not copy geometry or style.
   Independent search is optional and may occur only when `risks.network_access`
   records explicit approval, purpose, and allowed hosts; preserve query/source/
   retrieval provenance and never silently browse.
4. **Frozen invariants** — facts, content, behavior, safety, compatibility, and
   correctness that candidates may not change.
5. **Optimization variables** — what Loops are allowed to change.
6. **Scorecard** — one primary criterion, supporting criteria, direction,
   measurement, and blocking gates.
7. **Evidence** — baseline, commands, Artifacts, comparisons, Viewer, Navigation
   Evidence, and Evidence Gate.
8. **Topology** — smallest useful set of Tracks and synthesis relationships.
9. **Models and judges** — exact model IDs, explicit fallback IDs, role
   separation, independent critics, and dissent handling.
10. **Budget and stopping** — iteration/time limits, convergence, failure, and
   escalation conditions.
11. **Autonomy** — attended/unattended mode, allowed/denied paths and actions,
   pause conditions, prohibited actions, commit/PR policy, and the
   unattended-to-attended checkpoint protocol.
12. **Risk branch** — activate when deployment, external users, telemetry,
    external services, or sensitive data is detected. Resolve consent, privacy,
    retention, credentials, rollback, and human approval boundaries.

Do not treat a candidate-authored value as ground truth for an invariant. Every
blocking invariant must identify an external canonical source and verification
procedure. Stress, localization, adversarial, and capacity fixtures remain
secondary and visibly labelled.

## Phase 3 — Proposed configuration

Propose rather than interrogate the user about every implementation detail:

- topology and hypotheses;
- generator, synthesizer, and judge roles;
- exact primary models and permitted fallbacks;
- objective and qualitative scorers;
- the applicable human-use friction rubric with relevant selected lenses:
  physical contact/comfort/retention/strength and degraded geometry operations
  when physical interaction applies; discoverability, navigation, input burden,
  errors/recovery, status, accessibility, responsive/touch use, interruption,
  latency, destructive actions, and cognitive load when digital interaction
  applies;
- prior-art functional learnings and any approved-search provenance;
- iteration and wall-time budgets;
- evidence and Artifact contract.

Explain material tradeoffs and ask for one decision at a time only where the
proposal changes scope, cost, risk, or behavior.

## Phase 4 — Persist a draft

Use:

- `references/experiment-brief-schema-v1.0.json` (supports legacy v1.0 and
  explicit-human-use v1.1 briefs)
- `templates/experiment-brief-template.json`
- `scripts/validate_experiment_setup.py`

Write `experiment-brief.json` with status `draft`. Write `prompt.md` as the
complete instruction that a fresh agent can execute without chat history. It
must:

- instruct the agent to invoke `experiment-loop`;
- name the brief path and revision as authoritative;
- restate the frozen invariants and allowed-change scope;
- inject the exact frozen `human_use` declaration, friction analysis, prior-art
  decisions/provenance, and qualitative judging contract into every generator,
  synthesis, repair, and judge Prompt;
- repeat even a `not_applicable` classification and rationale in each handoff
  Prompt so downstream agents never infer the branch from artifact type;
- pin topology, models/fallbacks, scorers, evidence, budgets, and autonomy;
- name the exact experiment-local scratch root in every unattended agent Prompt;
- require Manifest v1.1, exact Prompt/feedback history, Viewer, Navigation
  Evidence, and Evidence Gate when declared in the brief;
- require `viewer.html` to be rebuilt immediately after every Loop fragment merge
  when the Viewer is required, with optional local `--watch` mode for live
  inspection;
- state that interim Viewers are explicitly in progress and that Navigation
  Evidence and the Evidence Gate remain final-output requirements;
- name `generated/human-feedback/` as the canonical immutable intake/disposition
  root, require Viewer-native local-download intake, and require exact verbatim
  Manifest and `prompt.input_feedback_refs` linkage for accepted entries;
- define the attended checkpoint: finish the current atomic operation, merge and
  rebuild the Viewer, checkpoint intake, pause before the next Loop Prompt,
  disposition feedback, then resume;
- state which actions require explicit approval and which in-scope validation,
  disposition, and Loop work may proceed;
- prohibit silent mutation of the brief.

Validate the draft before critique:

```text
python <experiment-loop-skill>/scripts/validate_experiment_setup.py \
  --brief .experiments/<id>/setup/experiment-brief.json
```

Any missing measurable success signal, objective blocking gate, runnable
evidence path, model assignment, or unattended autonomy boundary is a blocking
setup defect.
For applicable human-use work, missing category assessments, unmapped material
frictions, a numeric ergonomics gate, missing prior-art dispositions, or missing
qualitative judge evidence plans are also blocking setup defects.

Before critique, run this approval-blocking human-use checklist against the
actual brief and generated handoff Prompts:

1. The brief literally records `applicable` or `not_applicable` plus rationale.
2. Every generator, synthesis, repair, and judge Prompt repeats that exact
   classification and rationale. A not-applicable Prompt says so; it does not
   silently omit the branch.
3. Applicable setups name selected operation/context categories, map every
   material friction, and explicitly say the use-friction score is qualitative,
   not an objective gate.
   - For a physical tool, explicitly disposition grip, force/load,
     insertion/removal, inversion/retention, repetitive use, hand/contact edges,
     assembly/disassembly, foreseeable misuse, and accessibility/safety as
     selected with scenarios or not selected with rationale.
   - For a digital system, do the same for discoverability, navigation, input
     burden, error prevention/recovery, feedback/status, accessibility,
     responsive/touch use, interruption/resumption, latency perception,
     destructive actions, and cognitive load.
4. Every owner-provided reference has all required functional-review fields:
   source, observed functional choice, inferred rationale, adopt/adapt/reject
   decision and reason, originality implications, and evidence.
5. Independent search is explicitly not performed unless approved network policy
   and provenance exist.
6. Every selected lens appears verbatim in the judge Prompt, and degraded
   physical or digital operations are identified as scored defects.
7. Qualitative use-friction does not become a blocking objective gate merely
   because it is severe. Only separately justified correctness or safety
   invariants with canonical verification may block objectively; touch precision,
   comfort, cognitive load, and similar experience judgements stay qualitative.

## Phase 5 — Independent setup critic

Use an independent model that did not author the draft. Give it the repository
facts, Prompt, brief, and preflight evidence. Ask it to find:

- ambiguous or self-referential invariants;
- optimization variables that can silently change the Problem;
- subjective criteria pretending to be objective;
- omitted or inferred human-use applicability; unexamined physical, digital, or
  workflow operations;
- ergonomics represented as an objective geometry/load gate rather than the
  approved qualitative rubric;
- owner references copied stylistically or not dispositioned for function and
  originality;
- independent prior-art search without explicit network approval and provenance;
- missing correctness, safety, content-fidelity, or compatibility gates;
- correlated judges sharing the same incomplete contract;
- unmeasurable evidence or commands that do not exercise the real outcome;
- unsafe unattended permissions or missing pause conditions;
- unattended scratch paths outside the Experiment or containing Windows 8.3
  components;
- risk signals without complete controls;
- budget/topology/model choices that cannot answer the hypothesis.

Write `setup-review.md`. Resolve every blocking finding. Record the critic model
and final status in `experiment-brief.json`. A passing review has no unresolved
findings.

## Phase 6 — Approval and freezing

Show the user:

1. concise Problem and success definition;
2. invariants versus optimization variables;
3. human-use applicability/rationale, friction mapping, and prior-art decisions;
4. scorecard and blocking gates, clearly separating qualitative ergonomics;
5. topology, models, judges, and fallbacks;
6. evidence and baseline;
7. autonomy/risk envelope, including network approval or denial;
8. attended-mode pause, checkpoint, approval, and proceed-without-approval rules;
9. complete generated Prompt;
10. critic findings and resolutions.

Ask one final approval question. Do not launch Loops in the same turn.

After explicit approval:

1. set brief status to `approved`;
2. hash the exact brief and Prompt bytes with SHA-256;
3. write `approval.json` using
   `references/experiment-approval-schema-v1.0.json`;
4. validate the frozen binding:

```text
python <experiment-loop-skill>/scripts/validate_experiment_setup.py \
  --brief .experiments/<id>/setup/experiment-brief.json \
  --prompt .experiments/<id>/setup/prompt.md \
  --approval .experiments/<id>/setup/approval.json \
  --require-approved
```

The downstream Experiment may start only after this command passes.

## Revisions

Never silently edit an approved brief. Create revision `N+1`, set
`supersedes_revision`, show a semantic diff, rerun the independent critique,
and require new approval. Preserve prior revisions and approvals.

## Handoff to experiment-loop

Provide the approved Prompt and setup directory. `experiment-loop` must verify
the approval binding before unattended or high-cost work and treat the brief as
authoritative over chat memory, candidate claims, or intermediate Prompts.
When `evidence.viewer_required` is true, the handoff must also carry
`viewer_update_policy: after_each_loop_merge` and the approved
`viewer_watch_mode`; default watch mode to `on_request`.
The handoff must carry `autonomy.attended_protocol`. Human arrival during an
unattended run switches execution to attended only after the current atomic
operation and Viewer checkpoint. The approved brief remains authoritative;
feedback that conflicts with it is answered and recorded, not obeyed.
The handoff must carry the exact `human_use` object into Manifest setup and every
generator, synthesis, repair, and judge Prompt. Applicable runs must preserve the
qualitative ergonomics criterion and evidence contract; not-applicable runs must
preserve the explicit rationale without manufacturing friction evidence.
