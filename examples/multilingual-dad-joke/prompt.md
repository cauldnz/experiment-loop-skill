Use the experiment-loop skill.

Create the best wholesome dad joke that works naturally in English, French,
Spanish, and Japanese. Prefer a universal comic mechanism that survives
translation over English-only wordplay.

Score cross-language equivalence, dad-joke groan, brevity, cultural portability,
and translation naturalness. A blocking objective completeness scorer requires
all four languages in native script.

Run three independent generator Tracks: `gpt-5.5`,
`gemini-3.1-pro-preview`, and `claude-sonnet-5`. Each Track must produce and
improve a candidate rather than stopping after one attempt. Judge candidates
with a blind panel of `claude-opus-4.8`, `gpt-5.6-terra`, and
`gemini-3.1-pro-preview`, preserving dissent. Use `gpt-5.6-sol` for a synthesis
Track that explicitly accepts or rejects lessons from all three parents.

Produce multilingual drafts, structured candidate Artifacts, judge notes,
complete prompt/feedback history, and a Manifest v1.1. Record the actual model
ID for every generator, judge, synthesis role, and Loop.
