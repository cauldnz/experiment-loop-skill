Use the experiment-loop skill.

Hand-roll a parser for a messy vendor CSV dialect without importing the Python
standard-library `csv` module. It must handle quoted commas, embedded newlines,
doubled-quote escaping, a BOM, comment lines, blank lines, ragged rows, and
whitespace rules.

Score correctness, robustness, error clarity, maintainability, and constraint
adherence. Objective sample tests are primary. Embedded commas, embedded
newlines, and doubled-quote escaping are blocking core samples; a Track that
cannot pass one must be rejected. Malformed inputs must raise an actionable
`ParseError` with line and column information.

Run two competing architecture Tracks in parallel. Use `gpt-5.6-sol` for a
line-oriented/regular-expression approach and `claude-sonnet-5` for a
character-state-machine approach, with at least two Loops per Track. Use
`gpt-5.6-terra` as an independent maintainability and error-clarity judge; it
cannot override objective tests. Use `claude-opus-4.8` for a synthesis Track
that keeps the winning architecture and selectively incorporates any proven
helper from the rejected Track.

Produce runnable parser snapshots, committed sample fixtures, test-result
Artifacts, judge notes, complete prompt/feedback history, and a Manifest v1.1.
Record the actual model ID for every generator, judge, synthesis role, and Loop.
