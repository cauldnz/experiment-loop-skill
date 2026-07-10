# Judge: loop-01-naive-split (Naive comma split)

Single deep-critic judge. Objective scores come from `test-results.json`; the
error-clarity and maintainability scores are this judge's assessment.

## What changed
- Naive comma split. Hypothesis: Splitting each line on commas is the simplest thing that could possibly work.

## Evidence inspected
- `parser.py` (this loop's snapshot)
- `test-results.json`

## Objective results
- correctness: 8/15 samples (2.67/5); failed: bom, doubled_quote, quoted_comma, quoted_empty, quoted_newline, vendor_multiline, ws_quoted_preserve
- robustness: 0/3 malformed inputs raise ParseError (0.0/5); failed: bare_quote_in_unquoted, text_after_close_quote, unterminated_quote
- constraint (no `import csv`): pass (5/5)
- must-pass core samples: FAIL

## Judge scores
- error clarity: 1.0/5
- maintainability: 3.0/5
- weighted value: 2.39/5

## Assessment
The baseline establishes the bar. It is tiny and readable, but it treats every comma as a delimiter and every quote as literal text, so it fails all four must-pass core samples. It never raises on malformed input because it does not understand quoting at all.

## Decision
- **new_best**

## Next hypothesis
- Handle quotes so commas and quotes inside a field stop breaking rows.
