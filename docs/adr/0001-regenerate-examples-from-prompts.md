# Regenerate examples from prompts

An Example Prompt is the only maintained source for an example; its Generated Example is a disposable committed snapshot produced in isolation by the current experiment-loop skill. We rejected backward-compatible generated layouts and deterministic handwritten example runners because they test maintained fixtures rather than the real skill and encourage refactoring derived output. Consequently, a skill or Example Prompt change must regenerate and gate every example before merge to `main`, while working branches may remain temporarily stale.
