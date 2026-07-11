# Judge: loop-02-hardened (Hardened state machine)

Single deep-critic judge. Objective scores come from `test-results.json`; the
error-clarity and maintainability scores are this judge's assessment.

## What changed
- Hardened state machine. Hypothesis: The state machine can absorb the dialect rules and report malformed input cleanly.

## Evidence inspected
- `parser.py` (this loop's snapshot)
- `test-results.json`

## Objective results
- correctness: 15/15 samples (5.0/5); failed: none
- robustness: 3/3 malformed inputs raise ParseError (5.0/5); failed: none
- constraint (no `import csv`): pass (5/5)
- must-pass core samples: all pass

## Judge scores
- error clarity: 4.5/5
- maintainability: 3.5/5
- weighted value: 4.67/5

## Assessment
Now every sample passes and every malformed input raises a ParseError that names the line and column. Correctness and robustness are both at 100%. The trade-off is a busier function: four field-finalisation sites repeat the strip-if-unquoted rule, which is where the next loop can improve maintainability.

## Decision
- **new_best**

## Next hypothesis
- Tidy the field-finalisation logic without regressing correctness or robustness.
