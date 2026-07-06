# Prompt used for this worked example

```text
Use the experiment-loop skill.

Goal: Improve a small delivery route optimizer. Produce a route that starts and ends at the depot, visits every stop exactly once, and minimizes total Euclidean distance.

Scorecard:
- route_length: shorter total distance is better
- validity: every stop is visited exactly once and the route returns to the depot
- reproducibility: fixed input data, deterministic algorithms, recorded commands
- explainability: artifacts make it clear why the route improved

Judging mode:
- Use objective_command as the primary scorer.
- Use single judge notes only to explain the objective metrics and next hypothesis.

Topology:
- Run a single quantitative track for baseline, construction heuristic, local search, and synthesis.
- Create an SVG route map, metrics JSON, judge note, manifest, and local viewer for each loop.
```
