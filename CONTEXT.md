# Experiment Loop

This context describes repeatable improvement experiments and the evidence they produce.

## Language

**Example Prompt**:
The durable problem definition used to initiate an example experiment.
_Avoid_: Example Definition, worked example

**Generated Example**:
The disposable result of running an Example Prompt, including its experiment evidence and outputs.
_Avoid_: Example Run, generated run

**Evidence Gate**:
The blocking determination that a Generated Example contains valid, reproducible evidence and may be treated as complete.
_Avoid_: Manifest gate, Viewer gate

**Viewer**:
The reviewable record of an experiment's metadata, evidence, Loops, and Champion.
_Avoid_: Progress UI, report

**Navigation Evidence**:
The recorded outcomes of operating a Viewer through its controls, keyboard interactions, and deep links.
_Avoid_: Navigation transcript, UI smoke test

**Manifest**:
The durable record of an experiment's topology, Loops, evidence, decisions, Champion, and generation provenance.
_Avoid_: Run log, metadata file

**Human-use Analysis**:
The explicit applicable/not-applicable declaration for physical or digital
human-operated systems, rationale, selected first-principles friction scenarios,
prior-art functional learnings, and qualitative use evidence frozen by setup and
carried through judging.
_Avoid_: inferred ergonomics, numeric comfort gate

**Human Feedback Intake**:
The immutable, Viewer-exported canonical JSON that preserves the owner's exact
words, structured criterion review, targets, provenance, and binding.
_Avoid_: Feedback Markdown, chat note

**Human Feedback Disposition**:
The immutable orchestrator-authored JSON that interprets one intake entry,
records accepted/conflicting/deferred status, and names any consuming Loops.
_Avoid_: Edited intake, silent override
