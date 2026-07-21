# Human feedback

The Viewer is the canonical review and intake surface. It supports criterion
scores/ratings and freeform general, Loop, and Artifact feedback, then validates
and downloads a JSON sidecar. Browsers cannot safely write local files, so place
the downloaded file unchanged under the Experiment:

```text
generated/
  human-feedback/
    intake/
      <review-id>.json
    dispositions/
      <disposition-id>.json
```

Intake files conform to
`references/human-feedback-intake-schema-v1.0.json`. They contain stable review
and entry IDs, exact owner words, optional criterion/target structure, provenance,
and Manifest/Viewer binding. They contain no orchestrator interpretation and no
reviewer identity.

The orchestrator writes one immutable disposition sidecar per entry using
`references/human-feedback-disposition-schema-v1.0.json`. It records
interpretation, rationale, the disposition, and consuming Loop refs:

| Disposition | Meaning | Consuming Loops |
| --- | --- | --- |
| `accepted` | Inside frozen optimization variables | One or more |
| `answered_conflicts_with_frozen_invariant` | Conflicts with approved setup; owner is answered | None |
| `deferred` | Valid but outside current scope or budget | None |

The frozen brief wins. Changing an invariant requires a new setup revision and
approval; it is never an implicit effect of feedback.

## Manifest chain

Optional Manifest v1.1 `human_feedback[]` entries link the intake and disposition
paths/hashes, verbatim text, disposition, and consuming Loops. Each consuming Loop repeats the
entry ID in `prompt.input_feedback_refs` and preserves the exact verbatim text in
`prompt.input_feedback`. This makes `owner said X -> Loop N did Y` queryable in
either JSON or the Viewer.

Validate the complete chain:

```text
python <experiment-loop-skill>/scripts/validate_human_feedback.py \
  --data <generated-root>
```

## Attended-mode checkpoint

When a human joins an unattended run:

1. Finish the current atomic build, write, or Manifest merge.
2. Rebuild the in-progress Viewer.
3. Move the downloaded intake JSON into `human-feedback/intake/` unchanged.
4. Pause before issuing the next Loop Prompt.
5. Validate and disposition every entry.
6. Link accepted entries into the next Prompt and Manifest, then resume.

In-scope validation, disposition, and already-approved Loop work may proceed.
Setup revision, invariant/risk changes, deployment, credential access, budget
expansion, and actions named by an approval boundary require explicit approval.
Pending intake stays visible and is not treated as accepted.
