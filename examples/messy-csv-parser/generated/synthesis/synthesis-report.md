# Synthesis report -- messy vendor CSV parser

**Synthesis role model:** `claude-opus-4.8`
**Champion:** `synthesis-loop-02` (promoted to `generated/synthesis/final/`)
**Result:** 97/97 objective tests pass; all blocking core samples pass; no
forbidden `csv` import; zero regression across loops.

---

## 1. Starting point (authoritative, never overridden)

Both finalist architectures objectively pass the shared **64/64** architecture-
neutral bakeoff and every blocking core sample (embedded comma, embedded
newline, doubled-quote escaping). The independent `gpt-5.6-terra` judge did
**not** override objective tests; it broke the correctness tie qualitatively and
selected the **character-state-machine** Track as the synthesis base:

| Criterion (weight) | line-regex (rejected) | track-state-machine (winner) |
|---|---:|---:|
| correctness (.40) | 5.0 | 5.0 |
| robustness (.20) | 4.6 | 4.8 |
| error_clarity (.15) | 4.5 | 5.0 |
| maintainability (.15) | 4.2 | 4.8 |
| constraint_adherence (.10) | 5.0 | 5.0 |
| **weighted total** | **4.745** | **4.940** |

The winner's margin: legible named `_State` transitions, one authoritative
physical-position mechanism (`_Scanner`), and richer, actionable `ParseError`
context (1-based line/column **plus** row/field).

## 2. What each Track contributed

### track-state-machine (winning base) -- kept verbatim
- The entire architecture: `_State` enum, `_Scanner` (sole owner of
  pos/line/col), per-state `_Machine` handlers, dict dispatch, and a
  row/field-aware `ParseError`. Preserved byte-for-byte in synthesis loop-01;
  **not** hybridized with any regex logical-record assembly.
- Its full 53-case objective suite, reproduced verbatim in the synthesis suite.

### line-regex (rejected) -- one narrowly-proven helper incorporated
- **Accepted:** the **non-string input guard**. `parse()` now raises
  `TypeError("text must be str")` at the public boundary.
  - *Evidence:* `track-line-regex/final/parser.py` lines 161-162 and its
    committed, passing test `test_type_error_for_non_string`.
  - *Why it improves the winner:* the winner previously leaked an opaque
    `TypeError: 'NoneType' object is not subscriptable` from an internal string
    slice on misuse; the guard makes misuse actionable.
  - *Why it is architecture-compatible:* it is a boundary precondition, not a
    parsing mechanism, so the state machine is untouched.

## 3. What was rejected, and why

- **The regex/offset pipeline** (`_physical_lines`, `_logical_records`,
  `_FIELD`, per-character `source_offsets`). The independent judge recorded
  `proven_helpers_for_synthesis = []`: importing this would duplicate the
  winner's scanner and state-transition responsibilities. Confirmed
  independently -- the winner already yields precise physical line/column *and*
  richer row/field context without any offset map. This is an explicit,
  evidence-based rejection of the incompatible helpers.
- **Re-basing `ParseError` on `ValueError`** (the rejected Track's hierarchy).
  Not adopted: no objective test requires it, and the winner's `Exception` base
  plus structured `line/col/row/field` attributes is a deliberate, stable
  contract; changing the base could subtly shift caller `except` semantics for
  zero proven benefit.

## 4. Loop progression

### synthesis-loop-01 -- establish the candidate (parents: line-regex-loop-02, track-state-machine-loop-02)
- Winning state machine verbatim + the accepted non-string guard.
- Committed one runnable **union** suite: 53 winning-suite cases (verbatim) +
  31 local shared-bakeoff cases (24 valid + 7 error, copied from
  `generated/cross-evaluation/test_bakeoff.py` and run against the local parser)
  + 3 non-string guard tests = **87/87 pass**.
- **Union-testing finding (no functional bug):** the rejected Track treats
  Unicode-whitespace-only lines (e.g. U+00A0, U+2003) as ignorable blank/comment
  lines; the winner treats only ASCII space/tab as structural whitespace, so
  such a line is data. This is a *deliberate, self-consistent* winner choice --
  it agrees with the shared suite's own `unicode_not_padding` case -- and
  affects **no** hard gate. It was, however, implicit and untested.

### synthesis-loop-02 -- improve only from loop-01 evidence (parent: synthesis-loop-01)
Because loop-01 found **no functional bug**, two *measured, behavior-safe*
improvements were made, each with a dedicated regression test and zero
behavior change:
1. **Error-API clarity:** `ParseError` now exposes a `.reason` attribute (the
   bare cause). The formatted message and every existing attribute are
   unchanged. (`TestParseErrorReasonAttribute`, 4 tests.)
2. **Coverage/documentation gap:** committed regression tests that **pin** the
   winner's deliberate ASCII-only structural-whitespace behavior, converting an
   implicit behavior into an explicit contract. (`TestUnicodeWhitespacePinned`,
   3 tests, incl. a contrast test that ASCII space/tab-only lines are still
   blanks.)
3. **Runnable fixtures** under `fixtures/` loaded by `TestFixtures` (3 tests).

Total **97/97 pass**. **Zero-regression** proven: loop-01's unmodified 87-test
suite passes against loop-02's `parser.py`.

## 5. Final scores (0-5) and gate

Objective correctness is the primary hard gate and dominates; qualitative scores
are provisional self-assessment.

| Criterion (weight) | Champion score | Notes |
|---|---:|---|
| correctness (.40) | 5 | 97/97 objective tests, all blocking samples, zero regression. |
| robustness (.20) | 5 | Winning adversarial coverage + shared bakeoff + non-string boundary + pinned Unicode edge + fixtures. |
| error_clarity (.15) | 5 | `ParseError` reports line/column/row/field and exposes `.reason`; misuse raises an actionable `TypeError`. |
| maintainability (.15) | 4 | Clean `_Scanner` + per-state handlers; not 5 because handlers mutate shared instance state. |
| constraint_adherence (.10) | 5 | No `csv`/`pandas`/third-party import; state-machine architecture preserved. |

**Weighted total: 4.85.** Quality gates: `core_samples` PASS, `objective_tests`
PASS, `forbidden_import_scan` PASS. As a synthesis Loop passing every objective
hard gate, loop-02 is eligible as champion and is promoted.

## 6. Independent judge result (recap)

`gpt-5.6-terra` selected `track-state-machine` as base (4.940 vs 4.745), with
objective tests **not** overridden (64/64 for both finalists), and recorded no
architecture-compatible transplantable helper. The synthesis honored both: kept
the architecture, and incorporated only a boundary-level API idea the judge's
"no proven helper" note was specifically about the *regex/offset pipeline*, not
about a precondition guard.

## 7. Remaining limitations

- **Self-judged synthesis loops.** Objective tests are authoritative and green;
  qualitative scores are provisional.
- **Maintainability 4/5.** Per-state handlers still coordinate through mutable
  `_Machine` buffers. A functional-core refactor (pure
  `(state, char) -> (new_state, actions)` handlers) is deferred; it adds real
  ceremony and no functional defect requires it.
- **Under-specified Unicode whitespace.** The champion *pins* the deliberate
  ASCII-only interpretation, but the prompt does not define the whitespace set;
  a byte-oriented or Unicode-aware consumer might expect different blank-line
  handling.
- **Position units.** Line/column are per Python `str` code point (parse accepts
  an already-decoded `str`), not per UTF-16 unit or UTF-8 byte.

## 8. Next highest-value experiment

**Acquire real vendor CSV fixtures** (ground truth) to resolve the one genuine
open question -- whether Unicode-whitespace-only lines should be ignored -- and,
if maintainability becomes the deciding factor for a downstream consumer,
**refactor each `_step_*` handler into a standalone pure function** of
`(machine_state, ch) -> (new_state, actions)` to push maintainability toward 5
without changing behavior. The fixture-driven question is higher value: it could
convert a currently-pinned *assumption* into a *verified requirement*.

---

### Artifact index

- `loop-01/` and `loop-02/` -- per-loop `parser.py`, `test_parser.py`,
  `test-result.txt`, `judge.md`, `metadata.json`, `prompt-history.md`
  (loop-02 also has `fixtures/`).
- `final/` -- champion `parser.py`, `test_parser.py`, `test-result.txt`,
  `README.md`, `fixtures/`.
- `manifest-fragment.json` -- Track definition + two manifest-ready iterations
  with SHA-256 artifact hashes, full prompt chain, parent lineage, scores,
  quality gates, changed files, lessons, decisions, stop reasons.
- `status.json` -- machine-readable Track status.
