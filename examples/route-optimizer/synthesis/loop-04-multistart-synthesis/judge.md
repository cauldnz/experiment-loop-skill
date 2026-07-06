# Judge: quantitative route loop loop-04-multistart-synthesis

## What changed
- Deterministic multi-start 2-opt synthesis

## Evidence inspected
- `route.svg`
- `metrics.json`

## Scores
- route_length: 307.18 total units.
- validity: pass.
- reproducibility: deterministic script and fixed stop list.
- explainability: route SVG and metrics show the change.

## Judge mode
- single with primary objective command.

## What improved
- Improvement versus baseline: 27.53%.

## What failed / regressed
- No regression; objective distance improved.

## Next hypothesis
- Stop: deterministic restarts did not find a shorter valid route than the current champion.
