# Quickstart

Use `experiment-loop` when the answer is not obvious up front and you want agents to improve an artifact through evidence-backed iterations.

## 1. Install the skill

From this repository root:

```powershell
.\scripts\install.ps1
```

On macOS or Linux:

```bash
bash scripts/install.sh
```

Restart Copilot or reload skills after installation.

## 2. Start with a compact prompt

```text
Use the experiment-loop skill.

Goal: Improve <artifact> until it satisfies <quality target>.

Scorecard:
- correctness: what a correct result must do
- quality: what a better result looks like
- reproducibility: evidence and commands exist for every loop

Topology:
- Run 2 or 3 tracks.
- Each track runs 2 or 3 loops.
- Keep a manifest, judge notes, artifacts, and a local viewer.
```

If you already know the exact implementation, do not use the skill. Use normal engineering work instead.

## 3. Require observable evidence

Every loop should leave behind:

- the artifact that was produced;
- objective command output, metrics, renders, screenshots, or drafts;
- judge notes tied to the scorecard;
- the next hypothesis;
- a manifest entry.

The manifest is the source of truth. Chat history is not.

## 4. Pick the judging mode

Use objective commands when correctness can be measured, for example tests, route length, benchmarks, or schema validation.

Use independent qualitative judges when the target is visual quality, UX, writing, prompt quality, or design taste. The generator should not be the only judge of its own work if a result is promoted as the champion.

## 5. Inspect the result

Open the generated `viewer.html` directly in a browser. It should show the loop history, score progression, artifacts, judge notes, current champion, and why the champion won.

For complete examples, see:

- `examples\route-optimizer` for quantitative judging;
- `examples\cadquery-design` for qualitative design judging with CAD artifacts.
