# Synthesis champion -- messy vendor CSV parser

This is the promoted champion of the **synthesis** Track (`claude-opus-4.8`),
snapshot of `synthesis-loop-02`. The synthesis Track kept the winning
**character-state-machine** architecture selected by the independent
`gpt-5.6-terra` judge (weighted 4.940 vs 4.745 over the rejected line-oriented/
regex Track) and selectively incorporated one narrowly-proven, architecture-
neutral helper from the rejected Track.

## Public API

```python
from parser import ParseError, parse

rows = parse(text)   # text: str  ->  list[list[str]]  (rows of string fields)
```

- `parse(text: str) -> list[list[str]]` parses an already-decoded string into
  rows of string fields, preserving ragged row widths.
- `parse(...)` raises `TypeError("text must be str")` if `text` is not a `str`
  (a boundary precondition incorporated from the rejected Track).
- Malformed input raises `ParseError`, whose message includes a 1-based
  **line**, **column**, **row**, and **field**, and which exposes those as
  attributes plus `.reason` (the bare cause):

  ```python
  try:
      parse('a,b"c\n')
  except ParseError as e:
      e.reason        # "Unexpected quote character inside an unquoted field"
      e.line, e.col   # 1, 4
      e.row_number, e.field_number  # 1, 2
      str(e)          # "...inside an unquoted field (line 1, column 4, row 1, field 2)"
  ```

No standard-library `csv`, `pandas`, or any third-party parsing library is
imported.

## Dialect rules

- **UTF-8 BOM** accepted only at absolute offset zero (consumed silently, does
  not occupy a column); a BOM anywhere else is a `ParseError`.
- **Comment lines** whose first non-whitespace character is `#` are ignored when
  not inside a quoted field.
- **Blank / whitespace-only physical lines** are ignored when not inside a
  quoted field. *Only ASCII space (0x20) and tab (0x09) count as structural
  whitespace* -- a line of only Unicode whitespace (e.g. U+00A0) is data, not a
  blank line (see `test_parser.py::TestUnicodeWhitespacePinned`).
- **Quoted fields** may contain commas, embedded newlines (CRLF/CR/LF are
  normalized to `\n`), and doubled quotes (`""` -> `"`). Interior whitespace is
  preserved; spaces/tabs are allowed around the quoted token and are trimmed.
- **Unquoted fields** have surrounding spaces/tabs trimmed.
- **Ragged rows** (differing field counts) are preserved as-is.
- **Malformed inputs** raising `ParseError`: a quote inside an unquoted field,
  non-whitespace after a closing quote before a comma/newline, an unterminated
  quoted field (reported at its opening quote), and a BOM away from offset zero.

## Run

```
python test_parser.py
```

Runs 97 tests (the winning state-machine suite verbatim + a local copy of the
architecture-neutral shared bakeoff suite + the non-string-guard, `.reason`,
Unicode-whitespace-pinning, and fixture-loading tests). No external
dependencies; runnable directly from this directory.

## Files

- `parser.py` -- the parser (`ParseError`, `parse`).
- `test_parser.py` -- 97 objective tests.
- `fixtures/sample.csv` -- a valid, deliberately messy example (comment + blank
  lines, quoted embedded comma, embedded newline, doubled-quote escape, unquoted
  padding trimmed, ragged row).
- `fixtures/malformed_unterminated_quote.csv`,
  `fixtures/malformed_quote_in_unquoted.csv` -- malformed examples demonstrating
  actionable `ParseError` messages.
- `test-result.txt` -- champion verification transcript and counts.

## Provenance

Lineage: `synthesis-loop-02` <- `synthesis-loop-01` <-
[`line-regex-loop-02` (rejected), `track-state-machine-loop-02` (winning base)].
See `../loop-01/` and `../loop-02/` for per-loop artifacts,
`../synthesis-report.md` for the full contribution/rejection analysis, and
`../manifest-fragment.json` for the manifest-ready records.
