# Prompt history: track-state-machine / loop-01

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

This is Loop 1 of 2 for this Track: baseline architecture and objective
tests.

## Input feedback
None yet — this is the first loop of the Track. No prior artifact to react
to.

## Judge feedback
Self-assessment only (see judge.md). Summary: correctness 5/5, robustness
4/5, error_clarity 4/5, maintainability 2/5, constraint_adherence 5/5. All
30 objective tests pass, all 3 blocking core samples pass. Adversarial
probing beyond the committed suite found no functional defects. The
material weakness is architectural: `parse()` is a single ~250-line
procedural function with the `pos += 1; col += 1` advance pattern
duplicated roughly 15 times across branches, and mutable list buffers
captured by inline logic rather than an encapsulated cursor/scanner
abstraction. This is a genuine maintainability liability even though it
does not currently cause incorrect output.

## Next prompt (handed to loop-02)
Refactor the loop-01 parser to fix the identified maintainability weakness
without changing observable behavior: introduce a small internal scanner
abstraction that owns position/line/column and exposes reusable
advance/advance-newline helpers, and give each state its own clearly named
handler so the dispatch is no longer one long duplicated if/elif chain.
Then expand test_parser.py with the adversarial cases that were only
probed ad-hoc in loop-01 (empty quoted pair, quoted field flush at EOF with
no trailing delimiter, odd-count trailing quotes remaining unterminated,
a multi-line quoted field whose error is several embedded newlines deep —
verifying line/col tracking survives that, bare CR inside quotes, comment
line with no trailing newline, BOM appearing mid-comment / mid-unquoted-
field / as the last character of the file, a `#` that is not the first
character of a line, whitespace-only fields made of tabs, mixed CRLF/LF
row separators in one file, unicode content, and a still-open quoted field
after an odd number of trailing quote characters), plus any further
malformed/error-location cases that seem worthwhile. All existing behavior
and all 30 loop-01 tests must continue to pass unchanged.
