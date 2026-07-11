# Judge: loop-01-scanner (Character state machine)

Single deep-critic judge. Objective scores come from `test-results.json`; the
error-clarity and maintainability scores are this judge's assessment.

## What changed
- Character state machine. Hypothesis: Scanning character by character with a quote state can cross line boundaries safely.

## Evidence inspected
- `parser.py` (this loop's snapshot)
- `test-results.json`

## Objective results
- correctness: 11/15 samples (3.67/5); failed: blank_lines, bom, comment_line, ws_unquoted_trim
- robustness: 0/3 malformed inputs raise ParseError (0.0/5); failed: bare_quote_in_unquoted, text_after_close_quote, unterminated_quote
- constraint (no `import csv`): pass (5/5)
- must-pass core samples: all pass

## Judge scores
- error clarity: 2.5/5
- maintainability: 4.0/5
- weighted value: 3.14/5

## Assessment
Switching architecture pays off immediately: the state machine passes every must-pass core sample, including the embedded newline that killed the regex track. It is a clean, readable loop. It does not yet strip the BOM, skip comments or blank lines, or trim unquoted whitespace, and it is lenient rather than raising on malformed input — but the hard part is done and the approach is sound.

## Decision
- **new_best**

## Next hypothesis
- Add the vendor-dialect niceties (BOM, comments, blank lines, trimming) and clean errors.
