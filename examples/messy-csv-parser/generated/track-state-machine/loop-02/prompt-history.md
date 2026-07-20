# Prompt history: track-state-machine / loop-02

## Track prompt (as issued to this Track)
Hand-roll a robust Python parser for a messy vendor CSV dialect without
importing the standard-library csv module. Public API should expose
ParseError and parse(text: str) -> list[list[str]]. Requirements: UTF-8 BOM
accepted only at start; comment lines whose first non-whitespace character
is # are ignored when not inside a quoted field; blank/whitespace-only
physical lines ignored when not inside quoted field; quoted commas; embedded
CRLF/LF newlines normalized to \n within quoted fields; doubled quotes decode
to one quote; ragged rows preserved; unquoted fields trim surrounding
spaces/tabs; quoted fields preserve interior whitespace while allowing
spaces/tabs around the quoted token; any malformed input raises actionable
ParseError containing 1-based line and column. Reject quote in an unquoted
field, non-whitespace after a closing quote before comma/newline,
unterminated quote, and BOM away from offset zero. Do not import csv,
pandas, or third-party parser libraries.

Architecture constraint: implement an explicit whole-input character state
machine with named states/invariants and precise source positions. Keep it
simple and testable.

This is Loop 2 of 2 for this Track: improve loop-01 based on its actual
failures/weaknesses; expand adversarial malformed cases and error location
checks.

## Input feedback
loop-01's parser.py and test_parser.py (30 tests, all passing) plus 15
ad-hoc adversarial probes run against it directly (documented in
loop-01/test-result.txt). No functional defects were found by those
probes; the only real weakness surfaced was architectural.

## Judge feedback
From loop-01/judge.md: correctness 5/5, robustness 4/5, error_clarity 4/5,
maintainability 2/5, constraint_adherence 5/5. Explicit next hypothesis:
"Refactor parse() into a small _Scanner class that owns pos/line/col and
exposes advance()/advance_newline()/peek() helpers, and split the state
dispatch into one method per _State ... Simultaneously expand
test_parser.py with the 15 adversarial probes above (promoted from ad-hoc
scripts to committed, repeatable tests) plus a few new ones ... to raise
robustness and error_clarity confidence with real regression coverage."

## Next prompt (would be handed to a hypothetical loop-03)
This Track's plan called for exactly two Loops, so there is no loop-03.
If the independent judge (gpt-5.6-terra, per the parent experiment prompt)
or the synthesis Track flags maintainability as still needing work, the
next hypothesis to try would be reshaping each `_step_*` handler into a
standalone pure function of (state, char, cursor) -> (new_state, actions)
rather than a method that mutates `self`, to remove the last bit of
implicit shared-state coupling noted in loop-02/judge.md. Otherwise,
loop-02 is the Track's final candidate for synthesis.
