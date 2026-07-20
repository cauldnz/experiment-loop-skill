# Prompt history: synthesis / loop-01

## Complete Track prompt (as issued to the synthesis Track)

Run the synthesis Track for the messy vendor CSV parser experiment. You must
implement, test, and write all artifacts, not merely advise. Writable subtree:
`generated\synthesis\` only; never modify `prompt.md` or `.github`; actual model
ID `claude-opus-4.8`.

Authoritative facts/rules provided:
- Both candidates objectively pass the shared 64/64 suite and every blocking
  sample; this fact is never overridden.
- The independent `gpt-5.6-terra` judge selected `track-state-machine` as base
  (weighted 4.940 vs 4.745) for named transitions, centralized physical
  coordinates, and line/column/row/field errors.
- Keep the winning character-state-machine architecture; do not hybridize it
  into regex logical-record assembly.
- The judge found no rejected-track helper both necessary and
  architecture-compatible; its offset-map/regex pipeline would duplicate scanner
  responsibilities. A narrowly proven API/test idea from the rejected Track may
  be incorporated only if it improves the winner without changing architecture,
  and evidence must be identified.
- Standard-library `csv` must never be imported. Public API exposes `ParseError`
  and `parse(text: str) -> list[list[str]]`. Preserve all dialect and
  malformed-input requirements.
- Run exactly two synthesis Loops. loop-01: establish a fresh synthesis
  candidate preserving the winning architecture, reconcile the strongest
  compatible test/API evidence from both Tracks, and run the state-machine suite
  plus a synthesis-local copy/adaptation of the shared suite. Multi-parent
  lineage `parent_ids`: [`line-regex-loop-02`, `track-state-machine-loop-02`].

## Input feedback (from the two parent Tracks and the independent judge)

- `track-state-machine-loop-02` (winning base): 53/53 objective tests pass;
  Scanner + per-state handlers; `ParseError` carries line/column/row/field;
  maintainability self-capped at 4/5 because handlers mutate shared instance
  state. No `csv` import.
- `line-regex-loop-02` (rejected): 38/38 tests pass but architecture rejected;
  `ParseError` subclasses `ValueError` with a message-only "at line L, column C"
  format; offers a non-string `TypeError` guard (`test_type_error_for_non_string`)
  and per-character source-offset mapping.
- Cross-evaluation: shared bakeoff 64/64 for both; all blocking samples pass.
- Independent `gpt-5.6-terra` judge: winner = `track-state-machine`
  (4.940 vs 4.745); `proven_helpers_for_synthesis.items = []` because the regex
  offset/record pipeline would duplicate the winner's scanner/state work.

## Judge feedback (this loop's self-assessment)

87/87 objective tests pass (53 winning-suite verbatim + 31 local shared bakeoff
+ 3 non-string guard). All blocking samples pass; forbidden-import scan passes.
Weighted self-score 4.85. Accepted exactly one helper (non-string guard, with
cited evidence); explicitly rejected the regex/offset pipeline and the ValueError
re-base. Union testing found no functional bug but surfaced an under-specified
Unicode-whitespace-only-line edge (deliberate winner behavior, no gate impact).

## Next prompt (handed to loop-02)

Improve only from loop-01's actual evidence. Two measured, behavior-safe
improvements, each with a dedicated regression test, and no parsing-behavior
change: (a) close the coverage/documentation gap surfaced by union testing by
committing regression tests that pin the winner's deliberate ASCII-only
structural-whitespace behavior for Unicode-whitespace-only lines; (b) expose a
`ParseError.reason` attribute so callers can read the bare cause without
substring-parsing the message. Add runnable sample fixtures under
`loop-02/fixtures`. Do not manufacture a failure.
