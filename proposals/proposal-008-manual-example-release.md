# Proposal 008: Make Example release work manual

## Trigger

The owner stopped an expensive four-Example regeneration and requested that
Example regeneration and its freshness/browser/Evidence Gate release checks run
only when deliberately triggered after a batch of skill changes.

## Proposed change

- Keep Example regeneration as the explicit local command
  `python scripts/regenerate_examples.py`.
- Run Example freshness, browser navigation, Evidence Gate validation, and Pages
  publication only from a manually dispatched GitHub workflow.
- Add lightweight Python unit tests on pull requests and pushes.
- Document that stale committed Examples are allowed during ordinary development
  and are refreshed together at an intentional release checkpoint.

## Files to change

- `.github/workflows/examples.yml`
- `.github/workflows/tests.yml`
- `README.md`
- `docs/self-testing.md`
- `docs/worked-examples.md`

## Exact intended diff or snippet

Replace the automatic `pull_request`/`push` triggers on `examples.yml` with
`workflow_dispatch`, optionally publishing Pages after validation. Add a separate
automatic unit-test workflow that does not regenerate or validate Examples.

## Expected benefit

Multiple related fixes can land without repeatedly spending model tokens to
refresh all generated snapshots. Example generation cost is paid once at the
chosen release checkpoint.

## Risks / regressions

Committed Examples may be stale between manual release runs. Unit tests continue
to catch source regressions, while the manual workflow remains the release gate
for refreshed Example snapshots.

## Rollback

Restore the pull-request and main-push triggers on `examples.yml`, remove
`tests.yml`, and restore the previous documentation.

## Approval status

approved — explicitly selected by the owner on 2026-07-21
