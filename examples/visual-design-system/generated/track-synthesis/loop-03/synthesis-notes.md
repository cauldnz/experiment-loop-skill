# Synthesis 03 — context-preserving repair

## Trigger

Human review found that synthesis-02 changed the primary headline from
**Designing with Feedback Loops** to stress-test copy.

## Root cause

The synthesis-01 next prompt asked for a three-line stress-test display event
without declaring primary copy immutable or requiring stress content to remain
in a secondary fixture. Synthesis-02 therefore used the stress case as the
primary Artifact, and no content-fidelity gate blocked promotion.

## Repair

- Restore **Designing with Feedback Loops** in the primary card.
- Preserve synthesis-02's width-aware metadata, contrast, protected routing
  module, and badge rules.
- Keep the long-title scenario in `variants.svg` as explicitly secondary stress
  evidence.
- Add machine-readable `context-fidelity.json`.

## Prevention

Future visual Experiments must define canonical content once, carry immutable
brief fields into every Loop prompt, and score content fidelity objectively.
Stress fixtures may test resilience but cannot silently replace the primary
candidate.
