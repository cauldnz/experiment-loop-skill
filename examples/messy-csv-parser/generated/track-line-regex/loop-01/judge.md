# Judge: line-regex loop 01

## What changed
- Established a line-oriented parser with regex physical-line splitting, regex
  ignorable-line recognition, explicit quote-balance assembly, and regex field
  tokenization.
- Added 18 objective tests spanning all three blocking samples and the requested
  valid/malformed categories.

## Evidence inspected
- `python test_parser.py` output in `test-result.txt`: 18 run, 17 passed, 1 failed.
- Source inspection test for forbidden `csv` imports passed.

## Scores
- correctness: 4.2/5 — all valid-input tests and rejection tests pass, but one
  required error location is imprecise.
- robustness: 3.4/5 — broad baseline boundaries are covered; malformed-token
  diagnosis remains generic.
- error_clarity: 2.8/5 — messages are actionable and carry line/column, but junk
  after a closing quote reports column 1 instead of column 4.
- maintainability: 4.0/5 — focused helpers and compact regexes make the
  architecture understandable.
- constraint_adherence: 4.5/5 — no CSV library is imported and tokenization is
  genuinely line/regex oriented.

Weighted provisional score: 3.83/5.

## Judge mode
- single provisional self-judge; objective tests are authoritative.

## What improved
- Blocking core samples all pass: embedded comma, embedded newline, and doubled
  quote escaping.
- BOM/comments/blanks, ragged rows, trimming, interior physical lines, trailing
  empties, and CR-only record separators pass.

## What failed / regressed
- `test_junk_after_closing_quote_has_precise_location` failed: the field regex
  correctly rejects `"x"x`, but fallback diagnostics point to the token start.
- The objective gate therefore fails and this loop is rejected despite all core
  gates passing.

## Next hypothesis
- Keep regex tokenization, but add a small line-oriented diagnostic scanner that
  classifies the first illegal character and maps record offsets precisely.
  Expand malformed cases to guard closing-quote junk, tabs, multiline offsets,
  stray quotes, newline spellings, and BOM positions.
