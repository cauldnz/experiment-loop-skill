# Judge: track-state-machine loop 01

## What changed
- Established the baseline hand-rolled parser (`parser.py`) implementing the
  required whole-input character state machine: `_State` enum with
  `FIELD_START`, `IN_UNQUOTED`, `IN_QUOTED`, `QUOTE_PENDING`, `AFTER_QUOTE`,
  `IN_COMMENT`, driven by a single `while pos < n` loop over the input string,
  plus explicit `(line, col)` tracking and an end-of-input finalization step.
- Implemented `ParseError` (carries `.line`/`.col`, message embeds both) and
  `parse(text: str) -> list[list[str]]`.
- Wrote `test_parser.py` (unittest, 30 tests) covering every requirement in
  the prompt: BOM, comments, blanks, quoted commas, embedded LF/CRLF,
  doubled-quote escaping, ragged rows, trimming vs. preservation, comment/
  blank look-alikes retained inside quotes, empty fields/trailing commas,
  CR-only physical lines, and 4 malformed-input cases asserting exact
  line/column. Also asserts the source never imports `csv`.

## Evidence inspected
- `python test_parser.py` -> 30/30 passed (see `test-result.txt` for full
  transcript and counts).
- 15 additional ad-hoc adversarial probes run directly against `parse()`
  (not part of the committed suite) targeting exactly the kind of edge cases
  a hostile reviewer would try: empty quoted fields, quoted field flush at
  EOF without a trailing delimiter, odd-count trailing quotes (must stay
  unterminated), multi-line quoted fields with an error several lines deep
  (verifies line/col tracking survives multiple embedded newlines), bare CR
  inside quotes, comment lines with no trailing newline, BOM appearing mid
  comment / mid unquoted field / as the very last byte, `#` that is not the
  first character of a line, whitespace-only fields made of tabs, mixed
  CRLF/LF row separators in the same file, unicode content (accented letters
  + an emoji), and a still-open field after an odd number of trailing quotes.
  All 15 behaved correctly; details logged in `test-result.txt`.

## Scores
- correctness: 5 — every objective test passes, including all three blocking
  core samples (embedded comma, embedded newline, doubled-quote escaping),
  and adversarial probing found no behavioral defects.
- robustness: 4 — handled every adversarial case thrown at it (BOM
  placement, mixed line endings, odd quote counts, unicode) but this is
  still a single author's first pass; independent judging / more fuzzing in
  loop-02 is warranted before calling it fully proven.
- error_clarity: 4 — every `ParseError` embeds an accurate 1-based line and
  column and a human-readable reason, but messages don't yet say which field
  or row index was affected, which would help on large files.
- maintainability: 2 — this is the real weakness. `parse()` is one ~250-line
  procedural function with the `pos += 1; col += 1` advance pattern
  duplicated roughly 15 times, and mutable list buffers (`row`,
  `field_chars`) captured by inner closures instead of an encapsulated
  cursor/scanner object. It works and is documented, but it is harder to
  unit-test individual states in isolation and harder to extend safely.
- constraint_adherence: 5 — no `csv`, `pandas`, or any third-party parser
  import; architecture is a genuine named-state character state machine
  driven by a single linear scan, not a regex or line-splitting approach.

## Judge mode
- single (self-assessment only; provisional per the track's rules — an
  independent judge decides later and objective tests dominate regardless).

## What improved
- N/A (this is the baseline loop).

## What failed / regressed
- Nothing failed functionally. The identified weakness is architectural
  (maintainability), not a correctness/robustness defect.

## Next hypothesis
- Refactor `parse()` into a small `_Scanner` class that owns `pos`/`line`/
  `col` and exposes `advance()`/`advance_newline()`/`peek()` helpers, and
  split the state dispatch into one method per `_State` so each transition
  is independently readable (and, in principle, independently testable).
  This should raise maintainability without changing any observable
  behavior. Simultaneously expand `test_parser.py` with the 15 adversarial
  probes above (promoted from ad-hoc scripts to committed, repeatable
  tests) plus a few new ones (BOM at absolute EOF, deeply nested doubled
  quotes, comment-only file, tab/space mixed blank lines) to raise
  robustness and error_clarity confidence with real regression coverage.
