# Judge: synthesis loop-01

**Role:** synthesis generator self-assessment (`claude-opus-4.8`). Provisional
only; the independent `gpt-5.6-terra` judge already selected the base
architecture and objective tests dominate.

**Parents:** `line-regex-loop-02` (rejected), `track-state-machine-loop-02`
(winning base).

## What this loop did

1. **Kept the winning architecture verbatim.** The character state machine
   (`_State`, `_Scanner`, per-state `_Machine` handlers, row/field-aware
   `ParseError`) is preserved byte-for-byte from `track-state-machine`
   loop-02. It was *not* hybridized with the rejected Track's logical-record /
   regex assembly.

2. **Reconciled the strongest compatible cross-Track evidence.** The union of
   both Tracks' objective evidence is now committed as one runnable suite:
   the full 53-case winning suite (verbatim) plus a local re-run of the 31
   architecture-neutral shared bakeoff cases (`TestSharedBakeoffSuite`,
   copied from `generated/cross-evaluation/test_bakeoff.py`) executed against
   this parser with no external imports.

3. **Incorporated exactly one narrowly-proven helper from the rejected
   Track:** a non-`str` input guard at the `parse()` boundary
   (`raise TypeError("text must be str")`). Evidence:
   `track-line-regex/final/parser.py` lines 161-162 and its committed test
   `test_type_error_for_non_string`. This is a boundary precondition, not a
   parsing mechanism, so it changes nothing about the state machine and turns
   an opaque internal `TypeError` (from slicing `None`) into an actionable one.

## What was rejected and why

- The rejected Track's `_physical_lines` / `_logical_records` / `_FIELD` regex
  pipeline and per-character `source_offsets` map. The independent judge found
  no such helper both necessary and architecture-compatible; importing it
  would duplicate the winner's scanner/state responsibilities. Confirmed:
  the winner already produces precise physical line/column (and richer
  row/field context) without an offset map.
- Re-basing `ParseError` onto `ValueError` (as the rejected Track does). Not
  adopted: the winner's `Exception` base plus structured `line/col/row/field`
  attributes is a deliberate, stable contract; no objective test requires the
  change, and altering the exception hierarchy could subtly shift caller
  `except` semantics for zero proven benefit.

## Evidence inspected

- `python test_parser.py` -> **Ran 87 tests, OK** (see `test-result.txt` for
  the full transcript and counts: 53 + 31 + 3).
- `forbidden_import_scan` -> PASS (no `import csv` / `from csv`).
- All three blocking core samples pass (embedded comma, embedded newline,
  doubled-quote escaping).
- Union-testing probe (both Tracks' adversarial inputs vs. this parser): found
  **no functional bug**, but surfaced one under-specified edge -- Unicode-
  whitespace-only lines are content in the winner vs. ignorable in the rejected
  Track. This is a deliberate, self-consistent winner choice aligned with the
  shared suite's own `unicode_not_padding` expectation; it affects no hard gate.

## Scores (0-5)

| Criterion (weight) | Score | Basis |
|---|---:|---|
| correctness (.40) | 5 | 87/87 objective tests pass, incl. all 3 blocking samples and the full local shared suite. |
| robustness (.20) | 5 | Winner's adversarial coverage plus the shared bakeoff plus non-string boundary now all committed and green. |
| error_clarity (.15) | 5 | `ParseError` reports line/column/row/field; misuse now yields an actionable `TypeError`. |
| maintainability (.15) | 4 | Scanner + per-state handlers (no duplicated advance logic); not 5 because handlers still mutate shared `_Machine` state. |
| constraint_adherence (.10) | 5 | No `csv`/`pandas`/third-party import; genuine named-state character state machine preserved. |

**Weighted total:** 0.40·5 + 0.20·5 + 0.15·5 + 0.15·4 + 0.10·5 = **4.85**.

## Quality gates

- core_samples: **pass**
- objective_tests: **pass**
- forbidden_import_scan: **pass**

## Next hypothesis (handed to loop-02)

Improve only from this loop's real evidence: (a) close the coverage/
documentation gap surfaced by union testing by committing explicit regression
tests that pin the winner's deliberate ASCII-only-whitespace behavior, and
(b) make a measured, behavior-safe error-API clarity improvement by exposing a
`ParseError.reason` attribute (the bare cause, currently only recoverable by
substring-parsing the message), each with dedicated regression tests. Do not
change parsing behavior; do not manufacture a failure.
