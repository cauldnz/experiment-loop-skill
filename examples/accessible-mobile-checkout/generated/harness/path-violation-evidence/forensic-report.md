# Path violation forensic report

Status: remediated with a permanent procedural caveat.

## Attribution

All 15 root diagnostics are attributed with high confidence to `task-cards-loop-01` (`gemini-3.1-pro-preview`, task call `call_QJI0iLw1cMlBEjyyE86tO0R7`). Their timestamps fall inside the recorded task window and their probes target only task-card Loop 01.

## Recovery

The already-live wizard task deleted the originals after the pause. Each file was reconstructed only from captured full text, except `test-gates.py`, which was restored from the byte-identical frozen harness. Every recovered basename, byte length, and SHA-256 matches the pre-deletion inventory.

## Missing temporary debug copy

`modify.py`, `modify2.py`, and `modify3.py` target `generated/harness/run_checkout_gates_debug.py`. That file is absent. Its former existence or execution is inferred but not proven.

## Dependency and sensitivity

No approved Artifact or report directly references the root files. They likely influenced development diagnosis, so the provenance caveat is permanent. No credentials, environment secrets, external-user data, or external hosts were found; all fixture values are explicitly synthetic.

## Validity

Frozen inputs and every declared completed candidate/report Artifact retain their recorded hashes. Functional evidence remains valid. Procedural validity is remediated but the deviation and omitted command provenance remain visible in the Manifest and Viewer.

Machine-readable details: `provenance.json`, `hash-verification.json`, and `worktree-snapshot.json`.
