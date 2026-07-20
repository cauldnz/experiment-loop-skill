# Prompt history: synthesis / loop-02

## Complete Track prompt (synthesis Track, loop-02 portion)

loop-02: improve only from actual loop-01 evidence (e.g. a real gap found by
union testing/review, error/API clarity, or maintainability); if no functional
bug exists, make a measured, behavior-safe improvement with a dedicated
regression test. `parent_ids`: [`synthesis-loop-01`]. Do not manufacture
failures. Keep the winning character-state-machine architecture; never import
the standard-library `csv`; preserve the public API (`ParseError`,
`parse(text: str) -> list[list[str]]`) and all dialect/malformed-input
requirements. Include runnable sample fixture(s) under `loop-02/fixtures`.
Per-loop files required: parser.py, test_parser.py, test-result.txt (commands +
complete outputs/counts), judge.md, metadata.json, prompt-history.md. A Loop
failing any objective hard gate cannot be champion; embedded comma/newline/
doubled quote are blocking.

## Input feedback (from synthesis-loop-01)

- loop-01 candidate = winning state machine (verbatim) + one incorporated helper
  (non-string `TypeError` guard). 87/87 objective tests pass (53 winning-suite +
  31 local shared bakeoff + 3 guard); forbidden-import scan passes; all blocking
  samples pass.
- loop-01 union-testing/review evidence:
  1. Error-API review: the winner exposes structured `line/col/row/field` but
     not the bare cause; callers must substring-parse the message to get it.
  2. Union testing: Unicode-whitespace-only lines are treated as data by the
     winner (ASCII-only structural whitespace) vs. ignorable by the rejected
     Track. This is a deliberate, self-consistent winner choice (aligned with
     the shared `unicode_not_padding` case) -- NOT a functional bug -- but it was
     implicit and untested.
- Explicit instruction: no functional bug exists, so make measured,
  behavior-safe improvements with dedicated regression tests; do not manufacture
  a failure.

## Judge feedback (this loop's self-assessment)

97/97 objective tests pass. Two behavior-safe improvements landed, each with
dedicated regression tests: (1) `ParseError.reason` attribute (message text and
all other attributes unchanged); (2) committed tests pinning the winner's
deliberate ASCII-only structural-whitespace behavior. Zero-regression proven:
loop-01's unmodified 87-test suite passes against loop-02's parser. All hard
gates green; weighted self-score 4.85. Recommended as synthesis champion.

## Next prompt (would be handed to a hypothetical loop-03)

The synthesis Track's plan called for exactly two Loops, so there is no loop-03.
If maintainability were the deciding factor in a future loop, the next
hypothesis -- inherited from the winning Track's own backlog -- would be to
reshape each `_step_*` handler into a standalone pure function of
`(machine_state, ch) -> (new_state, actions)` rather than a bound method
mutating `self`, pushing maintainability toward 5 at the cost of extra ceremony.
This should be pursued only if an evaluator flags maintainability as decisive,
since loop-02 found no functional defect requiring it. The other high-value
follow-up is acquiring real vendor fixtures to resolve the under-specified
Unicode-whitespace question against ground truth rather than pinning the current
deliberate choice.
