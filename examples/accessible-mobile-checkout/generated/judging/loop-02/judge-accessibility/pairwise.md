# Pairwise accessibility comparison

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

## candidate-a vs candidate-b

Preference: **candidate-b** (medium-high). B offers stronger recoverability: it has explicit save/restore, step-local validation, and a tested clear-progress confirmation; A remains more direct and has safe compact keyboard behavior. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`, `judging/loop-02/judge-accessibility/navigation-transcript-b.json`.

## candidate-b vs candidate-c

Preference: **candidate-b** (very-high). B kept unrevealed steps out of the operated tab sequence and supplies clear-progress confirmation; C allowed focus into headers-marked collapsed content. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-b.json`, `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.

## candidate-a vs candidate-c

Preference: **candidate-a** (high). A's compacted bodies did not receive keyboard focus, while C's collapsed address, shipping, and payment controls did. Evidence: `judging/loop-02/judge-accessibility/navigation-transcript-a.json`, `judging/loop-02/judge-accessibility/navigation-transcript-c.json`.
