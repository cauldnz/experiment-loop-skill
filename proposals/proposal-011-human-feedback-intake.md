# Proposal 011: Formalize human-feedback intake and disposition

## Trigger

GitHub issue #10 identifies that Experiments can declare `human_review` scorers
but have no durable intake, disposition, consumption, or Viewer workflow. The
owner requested sequential implementation of all open issues and delegated the
review-surface product decision. The creator selected Viewer-native intake and
approved implementation on 2026-07-21.

## Proposed change

- Export schema-validated, immutable human intake sidecars from the Viewer under
  `generated/human-feedback/intake/`.
- Record one immutable orchestrator disposition per feedback entry under
  `generated/human-feedback/dispositions/`.
- Preserve human-authored fields separately from orchestrator interpretation,
  rationale, disposition, and consuming Loop references.
- Support `accepted`, `answered_conflicts_with_frozen_invariant`, and `deferred`.
  The frozen brief wins; conflicting feedback is answered and recorded.
- Add optional backward-compatible Manifest v1.1 links and
  `prompt.input_feedback_refs` so owner words can be traced to consuming Loops.
- Render human steering separately from model judge notes and support intake
  while the Viewer is in progress.
- Define the unattended-to-attended checkpoint and approval protocol.

## Files to change

- `SKILL.md` and `skills/experiment-setup/SKILL.md`
- `references/human-feedback-*-schema-v1.0.json`
- `references/human_feedback.py`
- `references/manifest-schema-v1.1.json`
- `references/viewer_renderer/`
- `templates/`
- `scripts/`
- `docs/`, `README.md`, and `PACKAGE_MANIFEST.json`
- `tests/`

## Expected benefit

Human steering becomes a first-class, recoverable, queryable part of Experiment
evidence without allowing chat memory or mutable Markdown to override the frozen
brief.

## Risks / regressions

Manifest links duplicate selected sidecar fields for standalone viewing. Semantic
validation therefore requires exact verbatim text, intake hashes, disposition
fields, and two-way consuming Loop references to agree. Existing Manifest v1.1
files remain valid because all additions are optional.

## Rollback

Remove the optional Manifest fields, sidecar schemas/validator, Viewer intake and
lane, and attended-mode guidance. Existing Manifests and the legacy human-judge
schema remain unchanged.

## Approval status

approved - GitHub issue #10, the owner's sequential-fix delegation, and the
creator's Viewer-native design selection on 2026-07-21
