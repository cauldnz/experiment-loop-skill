# Viewer

The Viewer is the standalone, offline handoff and incremental inspection surface
for every Experiment. Open `viewer.html` directly from disk in a normal browser;
it has no runtime network dependency.

> **Do not open the Viewer via `file://` in an in-app WebView (e.g. the GitHub
> Copilot desktop app Browser canvas).** A `file:///…` URL has an empty authority
> and is not a valid `http::Uri`; the app's WebView host (wry/WebView2) panics
> with `InvalidUri(InvalidFormat)` and can terminate the app. Serve the Viewer
> over loopback instead, which renders identically:
>
> ```text
> python scripts/serve_viewer.py --dir <generated-root>
> # then open the printed http://127.0.0.1:<port>/viewer.html URL
> ```

## Incremental viewing

Rebuild the Viewer immediately after every Loop fragment is merged into
`manifest.json`:

```text
python build_viewer.py --data <generated-root> --out <generated-root>/viewer.html
```

Partial Manifests are supported. Until a merged Champion exists, the Viewer shows
an explicit in-progress banner and current iteration count. Empty Champion,
optional story or milestones, incomplete Tracks, and pending judge feedback,
scores, gates, or Artifacts are shown as pending rather than failed or complete.

For local live inspection, leave the dependency-free watcher running:

```text
python build_viewer.py --data <generated-root> --out <generated-root>/viewer.html --watch
```

It builds once, then polls `manifest.json` and recursive
`manifest-fragment.json` files plus JSON sidecars under `human-feedback/`. Rapid
writes are coalesced, its own
`viewer.html` output cannot trigger a rebuild loop, errors are printed, and
Ctrl+C exits cleanly. No network or model calls occur.

## Core experience

The shared Viewer has three fixed views:

1. **Overview** explains the Problem, shows the Champion and featured Artifact,
   tells the authored milestone journey, and links every winning reason or
   caveat to evidence. The exact original Experiment Prompt is directly
   inspectable.
2. **Topology** renders Tracks as horizontal swimlanes and each Track's Loops
   left-to-right, with directed `parent_ids` edges and synthesis convergence.
   Selecting a Loop centers it and opens a collapsible inspector with the primary
   Artifact, metrics, gate state, judge feedback, lesson, and full
   prompt/feedback chain. Pan, pointer-centered zoom, Fit, reset, minimap,
   maximize, and URL-persisted viewport state support large graphs.
3. **Compare** shows Experiment-wide metric progression and compares any two
   Loops, defaulting to the earliest Loop and Champion.

The header's **Human feedback** action is the primary attended review surface.
It captures optional multi-axis criterion ratings and verbatim general, Loop,
and Artifact feedback, validates a canonical intake object, and downloads it for
placement under `generated/human-feedback/intake/`. The Viewer cannot and does
not write local files directly. Human steering appears in a dedicated accented
lane and badge; model judge notes remain a separate neutral lane. Pending,
accepted, deferred, and frozen-invariant-conflict dispositions remain distinct
while the Experiment is in progress.

Raw Manifest and generation fields are advanced evidence. They render as
structured, searchable UI rather than default JSON dumps.

The Overview also shows the explicit human-use applicability/rationale for
physical and digital systems, selected operation/context friction scenarios,
prior-art functional learnings and provenance, and qualitative judging evidence.
Each applicable Loop inspector shows its selected physical and/or digital
findings beside the score and labels it as a qualitative rubric result, not an
objective gate. Legacy Manifests are shown as unclassified rather than silently
inferred.

## Artifact presentation

Manifest v1.1 declares each Artifact's role, presentation mode, primary and
featured state, comparison key, caption, and alternative text. The renderer:

- path-confines files to the Experiment data directory;
- verifies declared SHA-256 hashes before embedding;
- caps each preview at 1 MB and all previews at 8 MB;
- embeds image/SVG, table, JSON, text, code, log, and explicit
  `interactive_html` presentations;
- runs interactive HTML only in a sandboxed iframe without same-origin access;
- falls back to a visible diagnostic and original-file link.

## Interaction contract

Every control is represented by the embedded interaction contract. View state
uses a composite hash such as `#view=topology&loop=loop-003`. The pinned
Playwright judge exercises:

- primary navigation and deep links;
- the graph's single Tab stop, keyboard selection, centered deep links, pan,
  pointer-centered zoom, Fit/reset, minimap, inspector, and maximize controls;
- Loop filters and complete All Loops list;
- Compare selectors;
- theme selection;
- evidence disclosures and Manifest search;
- full-screen Artifact dialogs, focus containment, and focus restoration.

The Viewer respects reduced motion and makes the All Loops list the primary
Topology representation on narrow screens.

## Required generation and gates

Every Experiment ships `build_viewer.py --data DIR --out FILE` and exposes the
same `--watch` mode. The adapter uses `references.viewer_renderer`; a local
`ViewerProfile` may add only curated optional panels.

Run Navigation Evidence, then the blocking Evidence Gate:

```text
node references/navigation_judge/cli.mjs --viewer <run>/viewer.html --out <run>
python <experiment-loop-skill>/scripts/run_evidence_gate.py <run>
```

The Evidence Gate validates Manifest v1.1 schema and semantics, Artifact
integrity and presentation, deterministic Viewer regeneration, static
HTML/JavaScript/accessibility checks, and fresh passing Navigation Evidence.
When canonical feedback exists, it also validates sidecar schemas, hashes,
references, dispositions, exact verbatim text, and the reciprocal consuming Loop
Prompt chain.
Run Navigation Evidence and the Evidence Gate only for the final output.
Incremental Viewers do not relax or satisfy either completion requirement.
