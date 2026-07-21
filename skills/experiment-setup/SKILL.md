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

Run only safe, existing, non-destructive preflight commands within a small
budget. Record commands and observed results. Do not install dependencies unless
an existing preflight fails specifically because dependencies are missing.

## Phase 2 — Adaptive interview

Resolve these branches in dependency order:

1. **Problem and audience** — Artifact, user, pain, and credible success.
2. **Frozen invariants** — facts, content, behavior, safety, compatibility, and
   correctness that candidates may not change.
3. **Optimization variables** — what Loops are allowed to change.
4. **Scorecard** — one primary criterion, supporting criteria, direction,
   measurement, and blocking gates.
5. **Evidence** — baseline, commands, Artifacts, comparisons, Viewer, Navigation
   Evidence, and Evidence Gate.
6. **Topology** — smallest useful set of Tracks and synthesis relationships.
7. **Models and judges** — exact model IDs, explicit fallback IDs, role
   separation, independent critics, and dissent handling.
8. **Budget and stopping** — iteration/time limits, convergence, failure, and
   escalation conditions.
9. **Autonomy** — allowed/denied paths and actions, pause conditions, prohibited
   actions, and commit/PR policy.
10. **Risk branch** — activate when deployment, external users, telemetry,
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
- iteration and wall-time budgets;
- evidence and Artifact contract.

Explain material tradeoffs and ask for one decision at a time only where the
proposal changes scope, cost, risk, or behavior.

## Phase 4 — Persist a draft

Use:

- `references/experiment-brief-schema-v1.0.json`
- `templates/experiment-brief-template.json`
- `scripts/validate_experiment_setup.py`

Write `experiment-brief.json` with status `draft`. Write `prompt.md` as the
complete instruction that a fresh agent can execute without chat history. It
must:

- instruct the agent to invoke `experiment-loop`;
- name the brief path and revision as authoritative;
- restate the frozen invariants and allowed-change scope;
- pin topology, models/fallbacks, scorers, evidence, budgets, and autonomy;
- name the exact experiment-local scratch root in every unattended agent Prompt;
- require Manifest v1.1, exact Prompt/feedback history, Viewer, Navigation
  Evidence, and Evidence Gate when declared in the brief;
- require `viewer.html` to be rebuilt immediately after every Loop fragment merge
  when the Viewer is required, with optional local `--watch` mode for live
  inspection;
- state that interim Viewers are explicitly in progress and that Navigation
  Evidence and the Evidence Gate remain final-output requirements;
- prohibit silent mutation of the brief.

Validate the draft before critique:

```text
python <experiment-loop-skill>/scripts/validate_experiment_setup.py \
  --brief .experiments/<id>/setup/experiment-brief.json
```

Any missing measurable success signal, objective blocking gate, runnable
evidence path, model assignment, or unattended autonomy boundary is a blocking
setup defect.

## Phase 5 — Independent setup critic

Use an independent model that did not author the draft. Give it the repository
facts, Prompt, brief, and preflight evidence. Ask it to find:

- ambiguous or self-referential invariants;
- optimization variables that can silently change the Problem;
- subjective criteria pretending to be objective;
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
3. scorecard and blocking gates;
4. topology, models, judges, and fallbacks;
5. evidence and baseline;
6. autonomy/risk envelope;
7. complete generated Prompt;
8. critic findings and resolutions.

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
