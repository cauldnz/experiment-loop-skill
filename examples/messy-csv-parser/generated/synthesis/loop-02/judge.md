# Judge: synthesis loop-02

**Role:** synthesis generator self-assessment (`claude-opus-4.8`). Provisional;
objective tests dominate.

**Parent:** `synthesis-loop-01`.

## What this loop did (only from loop-01 evidence; no manufactured failure)

loop-01 found **no functional bug** but produced two pieces of real evidence:
(1) a review of the two Tracks' error APIs showed the winner exposes structured
`line/col/row/field` attributes but *not* the bare cause, forcing callers to
substring-parse the message; and (2) union testing surfaced an under-specified
edge -- Unicode-whitespace-only lines are data in the winner (ASCII-only
structural whitespace) but ignorable in the rejected Track, and this behavior
was implicit/untested in the winner. loop-02 acts on both with measured,
behavior-safe changes:

1. **Error-API clarity (behavior-safe):** `ParseError` now sets
   `self.reason = reason`. The formatted message string and all existing
   attributes are unchanged. Callers can read `err.reason` directly instead of
   parsing text. Covered by `TestParseErrorReasonAttribute` (4 tests), including
   an assertion that the message still starts with the reason and still carries
   the coordinate suffix, and that `line/col/row/field` are unchanged.

2. **Coverage/documentation gap (no behavior change):** committed
   `TestUnicodeWhitespacePinned` (3 tests) that pin the winner's deliberate
   ASCII-only structural-whitespace behavior for Unicode-whitespace-only lines,
   with a contrasting test proving ASCII space/tab-only lines are still blanks.
   This converts an implicit, untested behavior into an explicit contract.

3. **Runnable fixtures:** `fixtures/sample.csv` (valid, messy: comment + blank
   lines, quoted comma, embedded newline, doubled-quote escape, unquoted
   padding trimmed, ragged row) and two malformed fixtures, loaded by
   `TestFixtures` (3 tests) relative to the test file so `python test_parser.py`
   runs standalone.

## Evidence inspected

- `python test_parser.py` -> **Ran 97 tests, OK** (see `test-result.txt`).
- **Zero-regression check:** loop-01's unmodified 87-test suite re-run against
  loop-02's `parser.py` -> 87/87 OK. The `reason` addition is purely additive.
- `forbidden_import_scan` -> PASS. Blocking core samples -> PASS.

## Scores (0-5)

| Criterion (weight) | Score | Basis |
|---|---:|---|
| correctness (.40) | 5 | 97/97 pass incl. all blocking samples; zero regression vs loop-01. |
| robustness (.20) | 5 | Under-specified Unicode-whitespace edge now pinned; fixtures exercised. |
| error_clarity (.15) | 5 | `ParseError.reason` adds programmatic access to the cause on top of line/column/row/field. |
| maintainability (.15) | 4 | Same clean Scanner + per-state design; handlers still mutate shared state (documented future work). |
| constraint_adherence (.10) | 5 | No `csv`/`pandas`/third-party import; architecture unchanged. |

**Weighted total:** 0.40·5 + 0.20·5 + 0.15·5 + 0.15·4 + 0.10·5 = **4.85**.

## Quality gates

- core_samples: **pass**
- objective_tests: **pass**
- forbidden_import_scan: **pass**

## What did not change / remaining limitation

- No parsing behavior changed. The only runtime-visible addition is the new
  `ParseError.reason` attribute (message text identical).
- Maintainability remains 4/5: the per-state handlers still coordinate through
  mutable `_Machine` instance buffers. A functional-core refactor (pure
  `(state, char) -> (new_state, actions)` handlers) is the documented
  highest-value next experiment but adds real ceremony and was not pursued
  because loop-02 found no functional defect requiring it.

## Champion recommendation

loop-02 is the synthesis champion: it strictly dominates loop-01 (superset of
tests, added programmatic error access, pinned an under-specified edge) with
zero behavioral regression and all hard gates green.
