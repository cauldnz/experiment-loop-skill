# Prompt history: line-regex loop 02

## Complete track prompt

Run the line-oriented/regular-expression architecture Track for a controlled experiment. You must do the work, not merely advise.

Repository root: C:\repos\chrisauld_microsoft\ai-strategy\copilot-worktrees\experiment-loop-skill\chrisauld-microsoft-bookish-system\.regeneration-ebv2cd4q\messy-csv-parser\workspace
Your only writable subtree: generated\track-line-regex\ (create it). Do not write anywhere else. Do not read or infer another generated Track. Never modify prompt.md or .github.
Actual model ID to record: gpt-5.6-sol.

Goal: hand-roll a robust Python parser for a messy vendor CSV dialect without importing the standard-library csv module. Public API should expose ParseError and parse(text: str) -> list[list[str]]. Requirements: UTF-8 BOM accepted only at start; comment lines whose first non-whitespace character is # are ignored when not inside a quoted field; blank/whitespace-only physical lines ignored when not inside quoted field; quoted commas; embedded CRLF/LF newlines normalized to \n within quoted fields; doubled quotes decode to one quote; ragged rows preserved; unquoted fields trim surrounding spaces/tabs; quoted fields preserve interior whitespace while allowing spaces/tabs around the quoted token; any malformed input raises actionable ParseError containing 1-based line and column. Reject quote in an unquoted field, non-whitespace after a closing quote before comma/newline, unterminated quote, and BOM away from offset zero. Do not import csv, pandas, or third-party parser libraries.

Architecture constraint: primarily line-oriented and regular-expression based. It may use explicit quote-balance scanning to assemble logical records, but field tokenization should demonstrate the requested regex/line-oriented hypothesis rather than becoming a conventional whole-input character-state machine.

Run exactly two sequential Loops:
- loop-01 baseline architecture and objective tests.
- loop-02 improve it based on actual loop-01 failures/weaknesses; expand adversarial malformed cases and error location checks.
Each loop must retain a runnable parser snapshot (parser.py), executable tests (test_parser.py using unittest), test-result.txt with command/output and counts, judge.md self-assessment, metadata.json, and prompt-history.md with complete track prompt/input feedback/judge feedback/next prompt. Copy the strongest snapshot to final/parser.py and tests/fixtures to final as useful. Produce manifest-fragment.json containing the Track definition and two manifest-ready iteration objects with parent_ids lineage, exact model_id, hypotheses, outcomes, commands, artifacts without hashes if you cannot calculate them, scores for correctness/robustness/error_clarity/maintainability/constraint_adherence on 0-5, gates core_samples and objective_tests, changed_files, durable lesson, decision, stop_reason. Also write status.json.

Blocking core samples: embedded comma, embedded newline, and doubled-quote escaping. A loop failing any must be rejected. Objective tests dominate self-assessment. Test at least: BOM + comments + blanks; quoted comma; embedded LF and CRLF; doubled quote; ragged rows; trimming of unquoted vs preservation in quoted; comments and blank-looking lines inside quoted fields retained; empty fields/trailing commas; CR-only physical lines if supportable; and malformed cases asserting line and column in message. Verify source has no `import csv` or `from csv`.

Scorecard definitions, all 0-5: correctness (objective required behavior, weight .40, primary hard gate); robustness (adversarial valid/malformed boundaries, .20); error_clarity (actionable message plus precise 1-based line/column, .15); maintainability (clear architecture, API, focused helpers/tests, .15); constraint_adherence (no csv and genuinely line/regex oriented, .10). Self-judging is provisional only; an independent judge will decide later.

Keep all artifacts plain text/JSON/code and ensure tests can be run from each loop directory with `python test_parser.py`. Final response should summarize paths, exact test counts, known caveats, and loop progression.

## Input feedback

Loop 01 ran 18 objective tests: 17 passed and 1 failed. All blocking core samples
passed. The failure showed that non-whitespace after a closing quote was rejected
correctly but reported at the field start instead of the offending character.
The next prompt also requested broader malformed and physical-location checks.

## Judge feedback

All 38 expanded tests pass. The original location failure is fixed; malformed
messages now distinguish quote-in-unquoted, post-closing-quote junk,
unterminated quote, and misplaced BOM. Source-offset mapping preserves physical
coordinates after CRLF normalization. Core and objective gates pass.

## Next prompt

Stop after exactly two loops and promote loop 02. Retain its parser, tests, and
fixture in `final`; record lineage, evidence, scores, gates, durable lesson, and
the stop reason in the manifest fragment and status.
