# Judge: quantitative route loop loop-03-two-opt

## What changed
- 2-opt local search (0 edge improvements)

## Evidence inspected
- `route.svg`
- `metrics.json`

## Scores
- route_length: 339.73 total units.
- validity: pass.
- reproducibility: deterministic script and fixed stop list.
- explainability: route SVG and metrics show the change.

## Judge mode
- single with primary objective command.

## What improved
- Improvement versus baseline: 19.85%.

## What failed / regressed
- Valid but did not improve the current champion.

## Next hypothesis
- Use deterministic restarts to check whether the local optimum is robust.
