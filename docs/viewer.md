# Viewer

The viewer is the handoff artifact for an experiment. It should work by opening `viewer.html` directly from disk and should not need external CDN resources.

## Minimum useful viewer

Include:

- goal and scorecard;
- current champion and why it won;
- experiment graph or lineage view based on `parent_id`;
- loop timeline;
- score progression;
- per-loop artifacts;
- judge notes;
- prompt and feedback chain for each iteration: generator prompt, parent or human feedback, judge feedback, and next prompt;
- command provenance;
- per-loop metadata/provenance drawers;
- visual-quality gate output for visual/UX/design artifacts, including overlap, clipping, readability, or broken-layout failures;
- raw manifest JSON for audit and reuse;
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
5. the prompt/feedback chain that caused each loop to change;
6. visual-quality gate failures for rejected visual artifacts;
7. whether all referenced artifacts exist.

The examples in this repository each include a generated `viewer.html` so users can inspect a completed run without rerunning it.
