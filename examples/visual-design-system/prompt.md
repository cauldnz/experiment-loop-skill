Use the experiment-loop skill.

Create a polished, reusable SVG event-card design system for a fictional
"Loop Lab" workshop. The cards must communicate event title, date, time, venue,
and call to action at a glance while remaining reusable across event variants.
Use the same canonical event brief in every primary candidate: the headline is
exactly **“Designing with Feedback Loops.”** Track and Loop comparisons may
change visual treatment but must not change canonical event copy. Long-content,
localization, or stress-test copy belongs in separately labelled test variants,
never in the primary candidate.

Score visual hierarchy, brand distinctiveness, information clarity, system
coherence, production polish, SVG validity, and layout quality. Subjective
criteria use a 1–5 point scale and maximize. SVG validity and layout quality use
pass/fail objective gates: overlap, clipping, unreadable text, inaccessible
contrast, missing required content, or invalid SVG prevents Champion promotion.
Visual hierarchy is the primary criterion.
Add a blocking objective content-fidelity check against the canonical brief.

Run three Tracks. Use `claude-sonnet-5` for an editorial-typography Track with
at least two Loops. Use `gemini-3.1-pro-preview` for an independent generative
visual-language Track with at least two Loops. Use `gpt-5.6-sol` for a synthesis
Track with at least two Loops that combines the strongest evidence from both
parents through true multi-parent lineage and repairs at least one objectively
detected visual defect.

Use an independent judge panel containing `gpt-5.6-terra`,
`claude-opus-4.8`, and `gemini-3.1-pro-preview`; include a layout-critic role
and preserve dissent. Add a `human_review` scorer assigned only to visual
hierarchy, brand distinctiveness, information clarity, system coherence, and
production polish so the conditional Human Judge UI is available. Its export
must contain no reviewer identity and must support verdict, notes, optional
criterion scores, selected Loop and Artifact notes, preferred Loop, and
keep/reject/needs-improvement recommendation.

Produce directly viewable SVG card Artifacts, design-token JSON, objective
layout metric sets, judge notes, and complete prompt/feedback chains. Produce a
Manifest v1.1 with authored milestones, evidence-linked Champion reasons and
caveats, featured Artifact captions and alternative text, and actual model IDs
for every generator, judge, synthesis role, and Loop. Generate and gate the
shared Viewer.
