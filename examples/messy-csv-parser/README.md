# Messy Vendor CSV Parser Architecture Bake-off

## Goal and result

This experiment compared two hand-rolled Python architectures for a messy vendor CSV dialect. The champion is **`synthesis-loop-02`**: a character-state-machine parser with a centralized scanner, named transitions, actionable `ParseError` context, a non-string boundary guard, and a pinned whitespace contract. It passes **97/97** final objective tests and an **87/87** zero-regression rerun.

## Topology and judging

The run used **2 parallel architecture Tracks x 2 Loops**: line-oriented/regular-expression (`gpt-5.6-sol`) and character-state-machine (`claude-sonnet-5`). A blind-first-pass independent judge (`gpt-5.6-terra`) selected the objectively tied state-machine finalist as the synthesis base. A 2-Loop synthesis Track (`claude-opus-4.8`) kept that architecture and accepted only a proven architecture-neutral helper.

Judging is objective-first. Shared tests and blocking core gates for embedded commas, embedded newlines, and doubled-quote escaping are authoritative. Qualitative judgement cannot override a failed objective gate; this is why `line-regex-loop-01` remains rejected despite passing the core samples.

## Inspect and reproduce

- Open `generated\viewer.html` after the orchestrator builds it. Use Overview for the problem, original prompt, champion, milestones, and linked evidence; Topology for Tracks, parent lineage, Loops, gates, and prompt-feedback chains; Compare for score progression and parser snapshots.
- Inspect `generated\manifest.json` for authoritative provenance, scores, decisions, hashes, and artifact paths. Artifacts are below `generated\track-*`, `generated\cross-evaluation`, `generated\judging`, and `generated\synthesis`.
- Run the champion tests: `python generated\synthesis\final\test_parser.py`.
- Run the shared cross-evaluation: `python generated\cross-evaluation\test_bakeoff.py`.
- Rebuild the Viewer: `python generated\build_viewer.py --data generated --out generated\viewer.html`.

The orchestrator will later produce `generated\navigation-evidence.json` and `generated\evidence-gate.json`. Those blocking artifacts demonstrate navigation/keyboard/deep-link behavior and validate schema, references, hashes, deterministic Viewer regeneration, and evidence freshness.

## Feature surface demonstrated

**Viewer capabilities:** Overview problem/original prompt/champion evidence; Topology `parent_ids` and multi-parent synthesis; Compare score progression; prompt-feedback chains; authored milestones; evidence-linked reasons/caveats; objective gate and judge dissent.

**Manifest capabilities:** artifact presentation and SHA-256 hashes; exact model provenance; three Tracks and six Loops; scorer and blind judge-panel metadata; quality gates, lineage, lessons, decisions, stop reasons, and the authoritative objective-first synthesis narrative.
