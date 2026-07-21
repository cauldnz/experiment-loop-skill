# Proposal 010: Build and watch incremental Viewers

## Trigger

GitHub issue #8 reports that long-running Experiments expose checkpointed
Manifest data but no current human-readable Viewer. The owner explicitly
selected the full scope, including watch mode, and authorized implementation on
2026-07-21 as the next sequential issue fix.

## Proposed change

- Rebuild `viewer.html` after every Loop fragment is merged into `manifest.json`.
- Render incomplete Manifests as explicitly in progress, with pending evidence
  distinguished from failed or final evidence.
- Add a dependency-free `--watch` mode to the standard Viewer CLI and adapter.
- Keep Navigation Evidence and the Evidence Gate as final-output requirements.

## Files to change

- `SKILL.md`
- `skills/experiment-setup/SKILL.md`
- `references/viewer_renderer/`
- `references/experiment-brief-schema-v1.0.json`
- `templates/experiment-brief-template.json`
- `templates/build-viewer-adapter.py`
- `README.md`
- `docs/quickstart.md`
- `docs/viewer.md`
- `PACKAGE_MANIFEST.json`
- `tests/`

## Exact intended diff or snippet

Experiments rebuild after each merge:

```text
python build_viewer.py --data <generated-root> --out <generated-root>/viewer.html
```

For a persistent local rebuild loop:

```text
python build_viewer.py --data <generated-root> --out <generated-root>/viewer.html --watch
```

Watch mode polls only `manifest.json` and recursive `manifest-fragment.json`
inputs, coalesces bursts, and exits cleanly on Ctrl+C.

## Expected benefit

Humans can inspect current Loops during long unattended runs without reading raw
JSON, while the final standalone Viewer remains deterministic and offline.

## Risks / regressions

Partial data could be mistaken for final evidence. The Viewer therefore labels
itself in progress whenever no merged Champion exists and never treats missing
scores or gates as passing. Watch mode is optional and performs no network or
model calls.

## Rollback

Remove watch arguments and polling helpers, restore final-only Viewer guidance,
and remove the in-progress presentation fields and UI.

## Approval status

approved - GitHub issue #8 and the owner's explicit 2026-07-21 selection of the
full scope including watch mode
