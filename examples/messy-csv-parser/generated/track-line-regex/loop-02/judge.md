# Judge: line-regex loop 02

## What changed
- Replaced generic quote toggling with a per-physical-line structural scan that
  validates quote placement while retaining regex field tokenization.
- Added source-offset maps for logical records so normalized multiline fields do
  not corrupt later error coordinates.
- Expanded from 18 to 38 tests, including a reusable multiline fixture and
  adversarial classification/location checks.

## Evidence inspected
- `python test_parser.py` output in `test-result.txt`: 38 run, 38 passed.
- Three blocking core tests passed.
- The in-suite source scan found no forbidden `csv` import.

## Scores
- correctness: 5.0/5 — every requested behavior and the expanded objective suite
  passes.
- robustness: 4.8/5 — multiline CRLF offsets, balanced/unbalanced stray quotes,
  BOM placements, mixed newlines, Unicode whitespace, and first-offender cases
  are covered.
- error_clarity: 4.8/5 — malformed categories identify the offending construct
  at precise 1-based physical coordinates.
- maintainability: 4.6/5 — quote validation adds state, but it remains isolated
  to line assembly; regexes still own line recognition and field tokenization.
- constraint_adherence: 4.8/5 — the implementation is explicitly line-oriented,
  regex-tokenized, dependency-free, and does not import `csv`.

Weighted provisional score: 4.85/5.

## Judge mode
- single provisional self-judge; objective tests are authoritative.

## What improved
- The loop-01 failure now reports `"x"x` at line 2, column 4, with a specific
  non-whitespace-after-closing-quote message.
- CRLF normalization no longer shifts the physical source location of later
  errors.
- Quote-in-unquoted-field errors are distinguished from unterminated quoted
  tokens where possible.

## What failed / regressed
- No objective regression observed. This remains a hand-rolled dialect parser,
  not an implementation of every optional CSV convention.

## Next hypothesis
- Stop after the mandated second loop. Promote loop 02 as the strongest snapshot;
  future work should be driven by new vendor fixtures rather than speculative
  complexity.
