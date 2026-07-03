# Minimal experiment-loop prompt

```text
Goal: Improve <artifact> until it better satisfies <quality target>.

Use the experiment-loop skill.

Scorecard:
- correctness: what better means
- clarity: what better means
- user preference fit: what better means
- automation: artifacts can be reproduced

Topology:
- Run 3 parallel tracks.
- Each track runs 3 loops.
- Produce artifacts, judge notes, metadata, and a manifest entry per loop.
- Run one synthesis pass after the tracks complete.
- Build or update a local viewer.

Governance:
- If you propose changes to the skill, rubric, judge policy, or reusable workflow instructions, write a proposal and wait for explicit human approval before applying it.
```
