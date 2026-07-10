# Prompt used for this worked example

```text
Use the experiment-loop skill.

Goal: Hand-roll a parser for a messy vendor CSV dialect. It must handle quoted commas, embedded newlines, doubled-quote escaping, a BOM, comment lines, blank lines, ragged rows, and whitespace rules — without importing the standard-library csv module. Settle the design with objective sample tests.

Scorecard:
- correctness: reproduces the expected rows for every committed sample (weight 2, objective)
- robustness: raises ParseError on every malformed input (objective)
- error_clarity: error messages are actionable and name the line/column (judge)
- maintainability: the code stays simple, readable, and extensible (judge)
- constraint_adherence: hand-rolled; never imports csv (objective)

Judging mode:
- Use the objective correctness suite as the primary scorer.
- Treat the core samples (embedded commas, embedded newlines, doubled-quote escaping) as a hard gate: a variant that fails one cannot become champion, and if an architecture can never pass one, reject that track.
- Break ties on the weighted scorecard, not on raw correctness alone.
- Use a single deep-critic judge only to score error clarity and maintainability; it never overrides the objective result.

Topology:
- Run two competing architecture tracks in parallel: a line-based regex track and a character state-machine track.
- Add a synthesis track that merges the winning architecture with the best helper from the rejected track.
- For each loop, emit a parser snapshot, a test-results JSON, and a judge note; then a manifest and a local viewer with the experiment graph, score timeline, decision gate, per-loop provenance, artifact inventory, raw iteration JSON, and raw manifest JSON.
```
