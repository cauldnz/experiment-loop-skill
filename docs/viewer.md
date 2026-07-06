# Viewer

The viewer is the handoff artifact for an experiment. It should work by opening `viewer.html` directly from disk and should not need external CDN resources.

## Minimum useful viewer

Include:

- goal and scorecard;
- current champion and why it won;
- loop timeline;
- score progression;
- per-loop artifacts;
- judge notes;
- command provenance;
- filters for track and decision;
- regression warnings or rejected loops.

## Artifact paths

Use relative paths in `manifest.json` so the viewer works after the folder is moved or cloned.

For generated HTML, embed manifest data with a safe JSON serialization method. Avoid string replacement approaches that can corrupt Windows backslashes.

## What to inspect

When reviewing a finished experiment, check:

1. the champion artifact;
2. loops marked `reject` or `failed`;
3. the lesson attached to each `new_best`;
4. dissenting judge comments;
5. whether all referenced artifacts exist.

The examples in this repository each include a generated `viewer.html` so users can inspect a completed run without rerunning it.
