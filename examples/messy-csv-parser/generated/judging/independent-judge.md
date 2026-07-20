# Independent qualitative judge

**Judge model:** `gpt-5.6-terra`  
**Decision:** select `track-state-machine` as the synthesis base.

## Scope and objective gate

This is an independent qualitative tie-break, not a replacement for objective
testing. I inspected the two final parsers and final test files, both loop-02
test transcripts and provisional judge notes, and the complete cross-evaluation
bundle (`test_bakeoff.py`, `test-result.txt`, and `summary.json`).

The shared bakeoff is the primary gate: it reports **64/64 passed** for the two
candidates together, no failures, and all blocking samples passed for each.
I also reran `python test_bakeoff.py`: 64/64 passed. The local final suites also
passed when rerun (38/38 and 53/53 respectively). Therefore correctness is
recorded as **5.0/5 for both candidates**. Track-local test counts are not
compared or used to select a winner.

## Blind first pass

Identities were withheld while assigning the following labels and scores.
Qualitative scores only break the objective parity.

| Criterion (weight) | Candidate A | Candidate B |
|---|---:|---:|
| Correctness (.40) | 5.0 | 5.0 |
| Robustness (.20) | 4.6 | 4.8 |
| Error clarity (.15) | 4.5 | 5.0 |
| Maintainability (.15) | 4.2 | 4.8 |
| Constraint adherence (.10) | 5.0 | 5.0 |
| **Weighted total** | **4.745** | **4.940** |

### Candidate A

Candidate A has a compact, understandable decomposition: line segmentation
(`_physical_lines`, lines 43-52), logical-record assembly (lines 55-127), then
field tokenization (lines 130-156). It explicitly tests both structural
recognition and regex tokenization. Its direct categories, such as
`"quote in unquoted field"` (line 107) and
`"non-whitespace after closing quote before delimiter"` (lines 97-101), are
actionable; `_location` returns 1-based physical positions (lines 29-40).

Its maintainability cost is that one grammar is represented twice: quote-state
logic in `_logical_records` (especially lines 74-112) and a second, dense
regular expression in `_FIELD` (lines 16-26). Correct mapping through logical
multiline records also requires per-character `source_offsets` bookkeeping
(lines 71, 117, 130-142). Those parts are valid and passed the common tests,
but make grammar changes and error-path review less localized. Error messages
also omit row and field context.

### Candidate B

Candidate B makes the parser grammar explicit in `_State` (lines 65-105), and
centralizes cursor ownership and all physical line/column movement in
`_Scanner` (lines 115-153). The state handlers are short, named units with
clear branch-local behavior: unquoted parsing at lines 226-246, quoted parsing
at lines 248-260, quote disambiguation at lines 262-272, and post-quote
validation at lines 274-296. The dispatch table (lines 308-315) exposes the
complete transition surface.

`ParseError` carries and reports 1-based line, column, row, and field values
(lines 45-62); errors are raised at the current scanner position (lines
174-176), while an unterminated field deliberately points to its opening quote
(lines 339-346). This is precise and more useful to a caller than position-only
text. One residual trade-off prevents a perfect maintainability score: handler
methods coordinate through mutable machine buffers (`row`, `field_chars`, and
state initialized at lines 164-172), so state invariants still need disciplined
review.

## Unblinding and recommendation

- Candidate A = `line-regex`
- Candidate B = `track-state-machine`

Choose **`track-state-machine`**. Its margin comes from legible named
transitions, one authoritative physical-position mechanism, and richer,
actionable `ParseError` context. Both satisfy the no-`csv` constraint verified
by the shared bakeoff (test source lines 99-103) and both remain objectively
correct.

## Dissent and uncertainty

The line/regex design is shorter and its structural pre-scan is a reasonable
solution; it is not rejected for a test failure. Its local tests include useful
non-string input coverage, but that is not a shared requirement and did not
change the correctness score. Conversely, the state-machine’s mutable
object-wide buffers and larger implementation mean the preference is
qualitative, not absolute. No helper is recommended for transplant from the
rejected architecture: its offset-map and regex pipeline would duplicate the
winner’s scanner/state responsibilities.

## Explicit gate statement

Objective tests were **not overridden**: both finalists pass all 64 shared
tests and all blocking samples. This recommendation only selects a base
architecture for synthesis after that objective parity.
