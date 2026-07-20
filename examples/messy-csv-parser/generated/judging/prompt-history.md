# Independent judge prompt and feedback chain

## Judge prompt

Act as the independent qualitative judge for the two-track parser experiment.
Inspect the specified final parser/test files, loop-02 test results and
provisional notes, plus the shared cross-evaluation files. Treat the fact that
both finalists pass all 64 shared tests and all blocking samples as
non-overridable. Blind the first scoring pass as Candidate A/B. Score
maintainability and error clarity on a 0-5 scale; record correctness as 5.0 for
both and optionally score robustness and constraint adherence. Use weights:
correctness .40, robustness .20, error clarity .15, maintainability .15, and
constraint adherence .10. Qualitative scores only break objective parity.
Write the independent judgment, structured scores, this prompt chain, and
status under `generated\judging\`; choose a base architecture for synthesis.
Do not modify the tracks, prompt, cross-evaluation, or `.github`.

## Input evidence inspected identically

1. `generated\track-line-regex\final\parser.py`
2. `generated\track-line-regex\final\test_parser.py`
3. `generated\track-line-regex\loop-02\test-result.txt`
4. `generated\track-line-regex\loop-02\judge.md` (provisional only)
5. `generated\track-state-machine\final\parser.py`
6. `generated\track-state-machine\final\test_parser.py`
7. `generated\track-state-machine\loop-02\test-result.txt`
8. `generated\track-state-machine\loop-02\judge.md` (provisional only)
9. `generated\cross-evaluation\test_bakeoff.py`
10. `generated\cross-evaluation\test-result.txt`
11. `generated\cross-evaluation\summary.json`

Independent verification commands and results:

```text
python generated\cross-evaluation\test_bakeoff.py        -> 64 passed
python generated\track-line-regex\final\test_parser.py   -> 38 passed
python generated\track-state-machine\final\test_parser.py -> 53 passed
```

The differing local-suite counts are evidence of each track's own regression
coverage only; they were not used as a cross-track score.

## Provisional judge feedback received, not adopted as final

- Line/regex self-judge: 38/38 local tests; provisional weighted score 4.85.
  It credited source-offset maps, quote classification, and location checks.
- State-machine self-judge: 53/53 local tests; provisional scores included
  maintainability 4 and error clarity 5. It credited `_Scanner`, named
  handlers, and row/field error context.

Both sources explicitly described themselves as provisional self-assessments.
The independent judge reread the implementation and common test harness rather
than treating either provisional total as authoritative.

## Independent judge feedback

Blind scores: Candidate A 4.745, Candidate B 4.940. Both have correctness 5.0
because the shared gate passes. Candidate B has the stronger qualitative case:
one cursor owner for 1-based physical positions, named grammar states, and
`ParseError` row/field context. Candidate A remains a valid, objectively
passing implementation; its regex grammar plus structural pre-scan and
per-character offset mapping are less localized for evolution.

After scoring, identities were revealed: Candidate A is `line-regex`; Candidate
B is `track-state-machine`.

## Next prompt to synthesis

```text
Use generated\track-state-machine\final\parser.py as the base architecture.
Preserve its shared-bakeoff behavior and its Scanner/State/ParseError
invariants. Do not import the rejected line-regex record/offset pipeline:
the independent judge found no rejected-track helper that is both necessary
and architecture-compatible. Any change must retain the 64 shared-test pass
gate and report errors with accurate 1-based physical line/column.
```
