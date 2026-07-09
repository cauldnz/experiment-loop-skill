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

## Interactive viewers

If the viewer is interactive (tabs, filters, deep-links), it must also:

- make every interactive control verifiably change the view — no dead controls (e.g. a nav link that only scrolls, or a filter that never re-renders);
- keep the primary control group keyboard-operable (roving focus, Arrow/Home/End, Enter/Space) with a visible focus ring and `prefers-reduced-motion` respected;
- address view state that matters via URL hash (e.g. `#tab=panel`) so a specific view is shareable and reproducible;
- ship a deterministic generator (`<build> --data DIR --out FILE`, timestamps read from the data, no wall-clock, no network) plus a companion smoke test, so the viewer rebuilds byte-identically and degrades gracefully on malformed input;
- surface auditable validation diagnostics — to stderr and as an embedded HTML comment — when input is missing or malformed, instead of rendering silently.

Judges then operate the interactive viewer per `docs/judging.md` (navigation-based judging) rather than scoring it from screenshots.

## Objective viewer gate

Gate the viewer with a small objective check before judging. `scripts/check_viewer.py` is a reference gate:

```text
python scripts/check_viewer.py --viewer viewer.html [--json]
python scripts/check_viewer.py --viewer viewer.html \
    --build "node build.mjs" --data data/ --degraded fixtures/ --json
```

Static checks (always): `self_contained` (no CDN/network refs), `embedded_json` (data blocks parse), `js_parse` (every inline script passes `node --check`), `link_integrity` (local links resolve), and `a11y_static` (`<html lang>`, non-empty `<title>`, a landmark/role, and a reduced-motion guard when animation is used). When `--build` is supplied it also checks `determinism` (building twice is byte-identical) and `robustness` (building against a degraded fixture exits cleanly and still parses). Record the gate output as an artifact so the viewer can show why a candidate passed or failed. The gate needs `node` for the JavaScript parse check; otherwise it is Python standard library only.

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
