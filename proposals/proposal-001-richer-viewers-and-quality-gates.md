# Proposal 001: Richer viewers and visual-quality gates

## Trigger

Human review of the SVG visual design-system worked example found that a syntactically valid SVG was promoted even though visual elements overlapped. The viewer also did not show enough of the iteration prompt, parent feedback, judge feedback, and next prompt that drove each loop.

## Proposed change

Update the durable experiment-loop skill guidance so future viewers and manifests must expose the prompt/feedback chain for each loop, and visual/UX experiments must include an explicit visual-quality gate that can block champion promotion when artifacts have layout defects such as overlap, clipping, illegibility, or hidden controls.

## Files to change

- `SKILL.md`
- `docs\viewer.md`
- `docs\worked-examples.md`
- `templates\manifest-template.json`
- `references\manifest-schema-v0.2.json`
- `examples\visual-design-system\**`

## Exact intended diff or snippet

Add prompt/feedback fields to the manifest iteration guidance:

```json
"prompt": {
  "track_prompt": "Prompt or instruction sent to the generator for this loop.",
  "input_feedback": "Feedback, prior judge notes, parent evidence, or human notes used as input.",
  "judge_feedback": "Condensed feedback returned by judges for this loop.",
  "next_prompt": "Next hypothesis/prompt that should drive the following loop."
}
```

Add a visual-quality gate requirement for visual/UX/design work:

```text
For visual, UX, and design artifacts, include an objective or semi-objective
visual-quality gate where practical. The gate should inspect real artifacts for
overlap, clipping, unreadable text, hidden controls, broken layout, missing
frames, or other visible defects. If the gate fails, the iteration cannot become
champion unless the user explicitly overrides it.
```

Extend viewer requirements:

```text
Viewers must show the prompt/feedback chain for each iteration: original/track
prompt, parent or human feedback used as input, judge feedback, and next prompt.
For visual work, viewers must also show visual-quality gate output and make
rejected visual defects easy to inspect.
```

## Expected benefit

Future experiment viewers will be more auditable: users can see not just the final artifact, but what the agent was asked to do, what feedback it received, how judges responded, and why the next iteration changed. Visual examples will no longer confuse "artifact exists" or "SVG parses" with actual visual quality.

## Risks / regressions

- Manifests and viewers become more verbose.
- Some experiments may not have a meaningful automated visual-quality gate; the guidance should allow a qualitative/manual gate when objective inspection is impractical.
- Existing manifests remain valid because the fields are additive.

## Rollback

Remove the added prompt/feedback viewer requirement, visual-quality gate requirement, and optional schema/template fields from the listed files.

## Approval status

approved

Approved in chat on 2026-07-06 after the proposal was presented.

## Applied result

Applied to:

- `SKILL.md`
- `docs\viewer.md`
- `docs\worked-examples.md`
- `templates\manifest-template.json`
- `references\manifest-schema-v0.2.json`
- `examples\visual-design-system\**`

The SVG visual design-system worked example was also regenerated to include prompt/feedback chains, layout-quality metrics, a rejected collision loop, and a repaired champion loop.
