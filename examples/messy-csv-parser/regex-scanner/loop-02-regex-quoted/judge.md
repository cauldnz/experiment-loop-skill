# Judge: loop-02-regex-quoted (Per-line regex tokeniser)

Single deep-critic judge. Objective scores come from `test-results.json`; the
error-clarity and maintainability scores are this judge's assessment.

## What changed
- Per-line regex tokeniser. Hypothesis: A per-line regex that understands quotes can handle embedded commas and doubled quotes.

## Evidence inspected
- `parser.py` (this loop's snapshot)
- `test-results.json`

## Objective results
- correctness: 13/15 samples (4.33/5); failed: quoted_newline, vendor_multiline
- robustness: 0/3 malformed inputs raise ParseError (0.0/5); failed: bare_quote_in_unquoted, text_after_close_quote, unterminated_quote
- constraint (no `import csv`): pass (5/5)
- must-pass core samples: FAIL

## Judge scores
- error clarity: 2.0/5
- maintainability: 2.5/5
- weighted value: 3.03/5

## Assessment
This is so close — 13 of 15 samples pass, including quoted commas, doubled quotes, the BOM and the dialect niceties. But it splits the input into lines before parsing, so a quoted field containing a newline is torn in half. The quoted_newline and vendor_multiline core samples fail, and no amount of regex tuning fixes it: the architecture is line-based. The objective test settles the debate — reject the track.

## Decision
- **reject**

## Next hypothesis
- Abandon the line-based approach: it cannot represent a field that spans two lines.
