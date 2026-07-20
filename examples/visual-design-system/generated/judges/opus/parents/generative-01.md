# Deep-Design Critique — generative-01 (track-generative / loop-01)

- **Model:** claude-opus-4.8
- **Role:** deep-design-critic (independent, blind to other judges)
- **Evidence inspected:** card.svg, tokens.json, layout-metrics.json, prompt-chain.json, self-review.md
- **Independent verification:** re-parsed the SVG; recomputed contrast pairs from raw hex — and found a misreported CTA value (see below).

## What I actually see
A dark slate (`#0f172a`) card with three phase-shifted cubic signal paths sweeping across the *entire* canvas at 0.6 opacity, over which the left-aligned content sits: a cyan "LOOP LAB WORKSHOP" eyebrow, a 72px white two-line title ("Synthesis & / Routing Systems"), a metadata cluster with empty rounded-square icon chips, and a blue pill CTA. The comment in the source is candid — it literally labels the text/path collision a "Defect." This is a deliberately-unfinished baseline.

## Scores (1–5)
- **visual_hierarchy (PRIMARY): 2** — The type ramp itself (eyebrow → 72px title → metadata → CTA) is fine in isolation, but the signal paths cut straight through the metadata band, so the secondary tier fights a decorative layer for the same pixels. Hierarchy that is destroyed by your own background is not working hierarchy.
- **brand_distinctiveness: 4** — The phase-shifted paths are the most on-brief interpretation of "modular loops / signal paths" and give the card a genuine synth/routing character. Distinctiveness is this candidate's one real strength.
- **information_clarity: 2** — Fields are all present but the metadata legibility is compromised by the overlap (self-admitted), and the icon chips are empty — decorative squares with no glyph, so they signify nothing.
- **system_coherence: 2** — tokens.json is thin: colors and a font trio only. No type scale, no spacing, no component geometry, no variant mechanism. It is a palette, not a system, and cannot support reuse.
- **production_polish: 1** — It intentionally ships a known layout defect and empty placeholders. That is an honest baseline, but as a standalone artifact it is not production-viable.

## Objective gates
- **svg_validity: PASS** — independently re-parsed; well-formed, title/desc present.
- **layout_quality: FAIL** — two problems: (1) the self-admitted metadata × signal-path overlap trips the overlap/unreadable gate; (2) the CTA contrast is **misreported**. layout-metrics claims `cta_text_bg: 4.5`, but white on `#3b82f6` is actually **3.68:1** by my calculation — below the 4.5 normal-text AA threshold (it clears only the 3:1 large-text exception). The reported number is not reproducible.

## Top defects
1. **Decorative layer over live text (blocking):** signal paths sweep through metadata, reducing legibility.
2. **Fabricated/incorrect CTA contrast:** claimed 4.5:1, actually 3.68:1 — a real accuracy failure, not rounding.
3. **Hollow system + empty icon chips:** tokens carry no scale/spacing/components; the metadata icons are content-free squares.

## Next step
Zone the composition (text vs. graphic) to kill the overlap, and — more importantly for the brief — grow tokens.json into an actual system with a type scale, spacing, and a variant mechanism. loop-02 does the former but neglects the latter.

## Honest note
Credit for labelling its own defect in the source rather than hiding it. But the misreported CTA contrast means this track's self-metrics cannot be taken at face value, which colors my read of its successor.
