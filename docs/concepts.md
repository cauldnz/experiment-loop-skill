# Concepts

The skill turns open-ended improvement work into a small, auditable optimization process.

## Artifact

The thing being improved: code, an image, a CAD model, a prompt, a document, a route, a UI flow, or any other output.

## Scorecard

A short list of criteria that defines "better" before loops start. Use 4-7 criteria for real work. Objective criteria should include measurable gates; subjective criteria should include plain-language descriptions of what better means.

## Track

A track is a focused line of attack with one hypothesis. Examples:

- optimize correctness while preserving style;
- optimize presentation while keeping the algorithm unchanged;
- try a simpler geometry;
- try a more expressive prompt.

Tracks should write to separate folders so agents do not overwrite each other.

## Loop

One build -> run -> observe -> judge -> improve cycle. Each loop should produce artifacts, metrics or logs, judge notes, and a manifest entry.

## Champion

The best iteration so far according to the scorecard. A new champion needs evidence. For subjective work, it also needs independent judging unless the user explicitly accepts a lower-rigor run.

## Synthesis

A later pass that combines the best lessons from earlier tracks. Synthesis should create a fresh candidate rather than mutating one track until the lineage is unclear.

## Manifest

`manifest.json` is the durable record. It tracks scorecard, scorers, tracks, iterations, artifacts, decisions, lessons, and the current best result. The viewer should be generated from the manifest or embed the same manifest data.

## Viewer

The viewer is a local static HTML file for reviewing the experiment after the chat context is gone. It should make the hill-climb understandable to someone who did not watch the run happen.
