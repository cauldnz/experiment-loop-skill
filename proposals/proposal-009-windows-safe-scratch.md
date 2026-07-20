# Proposal 009: Require Windows-safe unattended scratch paths

## Trigger

GitHub issue #7 reports unattended Windows Experiments stalling when session
scratchpad writes use 8.3 path components such as `CHRISA~1`, which trigger a
manual suspicious-path permission prompt. The owner instructed implementation
on 2026-07-21 as the next sequential issue fix.

## Proposed change

- Default unattended scratch work to
  `<generated-root>/harness/scratch/`.
- Require unattended setup briefs to declare an experiment-local `scratch_root`.
- Provide a helper that creates the local scratch directory and expands an
  unavoidable existing Windows session path to long form.
- Carry the policy through both skills, setup templates, documentation, and
  installers.

## Files to change

- `SKILL.md`
- `skills/experiment-setup/SKILL.md`
- `references/experiment-brief-schema-v1.0.json`
- `templates/experiment-brief-template.json`
- `scripts/prepare_scratch.py`
- `scripts/validate_experiment_setup.py`
- `scripts/install.ps1`
- `scripts/install.sh`
- `README.md`
- `INSTALL.md`
- `docs/quickstart.md`
- `PACKAGE_MANIFEST.json`
- `tests/test_experiment_setup.py`
- `tests/test_prepare_scratch.py`

## Exact intended diff or snippet

Unattended briefs use:

```json
"scratch_root": ".experiments/<id>/generated/harness/scratch"
```

Agents prepare it with:

```text
python <skill>/scripts/prepare_scratch.py --generated-root <generated-root>
```

The fallback `--session-scratch` mode must expand all 8.3 components before the
path is distributed to agents.

## Expected benefit

Unattended Windows runs no longer block on manual permission prompts caused by
short-form session scratch paths, while temporary state remains beside
checkpointed Experiment output.

## Risks / regressions

Existing interactive v1.0 briefs may omit `scratch_root` for compatibility.
Unattended briefs without it now fail setup validation and must be revised.

## Rollback

Remove the scratch helper and guidance, remove `scratch_root` from the template
and schema, and remove the unattended validator checks.

## Approval status

approved - GitHub issue #7 and the owner's explicit 2026-07-21 implementation
instruction
