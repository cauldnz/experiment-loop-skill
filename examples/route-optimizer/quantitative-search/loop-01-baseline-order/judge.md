# Judge: quantitative route loop loop-01-baseline-order

## What changed
- Baseline input-order route

## Evidence inspected
- `route.svg`
- `metrics.json`

## Scores
- route_length: 423.88 total units.
- validity: pass.
- reproducibility: deterministic script and fixed stop list.
- explainability: route SVG and metrics show the change.

## Judge mode
- single with primary objective command.

## What improved
- Improvement versus baseline: 0.0%.

## What failed / regressed
- No regression; objective distance improved.

## Next hypothesis
- Try a greedy construction heuristic that chooses the nearest unvisited stop.
