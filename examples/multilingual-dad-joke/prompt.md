# Prompt used for this worked example

```text
Use the experiment-loop skill.

Goal: Create the perfect wholesome dad joke that works equally well in English, French, Spanish, and Japanese. Prefer a universal comic mechanism that survives translation over English-only wordplay.

Scorecard:
- cross_language_equivalence: the same joke mechanic survives in all four languages
- dad_joke_groan: it has the harmless groan/reversal quality of a dad joke
- brevity: the joke is short enough to tell aloud
- cultural_portability: it does not depend on one culture's idioms or local references
- translation_naturalness: each language reads naturally, not like a forced translation

Judging mode:
- Use an objective text-completeness gate for all four languages.
- Use a multi-model judge panel for qualitative scoring.
- Preserve dissent rather than flattening it away.

Topology:
- Run A: GPT-style generator candidate.
- Run B: Gemini-style generator candidate.
- Run C: Claude-style generator candidate.
- Run D: synthesis loop that uses the candidates and judge dissent as parents.
- Produce multilingual joke drafts, candidate JSON, judge notes, a manifest, and a local viewer with graph lineage, metadata/provenance drawers, raw iteration JSON, and raw manifest JSON.
```
