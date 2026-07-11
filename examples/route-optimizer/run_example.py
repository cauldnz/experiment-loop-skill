from __future__ import annotations

import hashlib
import html
import json
import math
import random
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import build_viewer  # noqa: E402  (local module, single source of truth for viewer.html)

STOPS = [
    ("Depot", 50, 50),
    ("Museum", 18, 78),
    ("Bakery", 28, 32),
    ("Clinic", 38, 86),
    ("Library", 55, 72),
    ("School", 68, 88),
    ("Market", 82, 58),
    ("Harbor", 90, 24),
    ("Stadium", 64, 18),
    ("Garden", 42, 12),
    ("Station", 15, 15),
    ("Gallery", 75, 42),
]


def distance(a: int, b: int) -> float:
    _, ax, ay = STOPS[a]
    _, bx, by = STOPS[b]
    return math.hypot(ax - bx, ay - by)


def route_length(route: list[int]) -> float:
    return sum(distance(route[i], route[i + 1]) for i in range(len(route) - 1))


def is_valid(route: list[int]) -> bool:
    return route[0] == 0 and route[-1] == 0 and sorted(route[1:-1]) == list(range(1, len(STOPS)))


def nearest_neighbor() -> list[int]:
    route = [0]
    remaining = set(range(1, len(STOPS)))
    while remaining:
        current = route[-1]
        nxt = min(remaining, key=lambda idx: (distance(current, idx), STOPS[idx][0]))
        route.append(nxt)
        remaining.remove(nxt)
    route.append(0)
    return route


def two_opt(route: list[int]) -> tuple[list[int], int]:
    best = route[:]
    improvements = 0
    improved = True
    while improved:
        improved = False
        best_len = route_length(best)
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                if j - i == 1:
                    continue
                candidate = best[:i] + best[i:j][::-1] + best[j:]
                candidate_len = route_length(candidate)
                if candidate_len + 1e-9 < best_len:
                    best = candidate
                    improvements += 1
                    improved = True
                    break
            if improved:
                break
    return best, improvements


def multistart_two_opt() -> tuple[list[int], dict[str, float]]:
    rng = random.Random(42)
    candidates: list[tuple[float, list[int]]] = []
    starts = [nearest_neighbor()]
    for _ in range(35):
        middle = list(range(1, len(STOPS)))
        rng.shuffle(middle)
        starts.append([0] + middle + [0])
    for start in starts:
        improved, _ = two_opt(start)
        candidates.append((route_length(improved), improved))
    candidates.sort(key=lambda item: item[0])
    lengths = [item[0] for item in candidates]
    return candidates[0][1], {
        "starts": len(starts),
        "best_start_length": round(min(route_length(s) for s in starts), 2),
        "median_final_length": round(statistics.median(lengths), 2),
    }


def write_route_svg(route: list[int], path: Path, title: str) -> None:
    width, height = 760, 520
    margin = 52
    scale_x = (width - margin * 2) / 100
    scale_y = (height - margin * 2) / 100

    def xy(idx: int) -> tuple[float, float]:
        _, x, y = STOPS[idx]
        return margin + x * scale_x, height - margin - y * scale_y

    points = " ".join(f"{xy(idx)[0]:.1f},{xy(idx)[1]:.1f}" for idx in route)
    parts = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"760\" height=\"520\" viewBox=\"0 0 760 520\">",
        "<rect width=\"760\" height=\"520\" fill=\"#fbfbf7\"/>",
        f"<text x=\"32\" y=\"34\" font-family=\"Segoe UI, Arial\" font-size=\"22\" font-weight=\"700\" fill=\"#1f2933\">{html.escape(title)}</text>",
        f"<text x=\"32\" y=\"58\" font-family=\"Segoe UI, Arial\" font-size=\"14\" fill=\"#52606d\">Distance: {route_length(route):.2f}; valid: {str(is_valid(route)).lower()}</text>",
        f"<polyline points=\"{points}\" fill=\"none\" stroke=\"#2563eb\" stroke-width=\"4\" stroke-linejoin=\"round\" stroke-linecap=\"round\" opacity=\"0.88\"/>",
    ]
    for order, idx in enumerate(route[:-1]):
        x, y = xy(idx)
        name = STOPS[idx][0]
        color = "#dc2626" if idx == 0 else "#111827"
        radius = 11 if idx == 0 else 8
        parts.append(f"<circle cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"{radius}\" fill=\"{color}\" stroke=\"#ffffff\" stroke-width=\"3\"/>")
        parts.append(f"<text x=\"{x + 12:.1f}\" y=\"{y - 10:.1f}\" font-family=\"Segoe UI, Arial\" font-size=\"12\" fill=\"#1f2933\">{order}. {html.escape(name)}</text>")
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_from_length(length: float, baseline: float) -> float:
    improvement = (baseline - length) / baseline
    return round(min(5.0, 2.0 + improvement * 10.0), 2)


def write_judge_note(path: Path, loop_id: str, title: str, metrics: dict[str, object], next_hypothesis: str) -> None:
    path.write_text(
        f"""# Judge: quantitative route loop {loop_id}

## What changed
- {title}

## Evidence inspected
- `route.svg`
- `metrics.json`

## Scores
- route_length: {metrics["distance"]} total units.
- validity: {"pass" if metrics["valid"] else "fail"}.
- reproducibility: deterministic script and fixed stop list.
- explainability: route SVG and metrics show the change.

## Judge mode
- single with primary objective command.

## What improved
- Improvement versus baseline: {metrics["improvement_pct"]}%.

## What failed / regressed
- {metrics["regression_note"]}

## Next hypothesis
- {next_hypothesis}
""",
        encoding="utf-8",
    )


def main() -> None:
    loops = [
        {
            "id": "loop-01-baseline-order",
            "track": "quantitative-search",
            "title": "Baseline input-order route",
            "route": list(range(len(STOPS))) + [0],
            "hypothesis": "A baseline route establishes the objective distance to beat.",
            "next": "Try a greedy construction heuristic that chooses the nearest unvisited stop.",
        },
        {
            "id": "loop-02-nearest-neighbor",
            "track": "quantitative-search",
            "title": "Nearest-neighbor construction",
            "route": nearest_neighbor(),
            "hypothesis": "Choosing the nearest unvisited stop should cut obvious cross-town jumps.",
            "next": "Apply local edge swaps to remove route crossings left by the greedy heuristic.",
        },
    ]
    opt_route, improvements = two_opt(nearest_neighbor())
    loops.append(
        {
            "id": "loop-03-two-opt",
            "track": "quantitative-search",
            "title": f"2-opt local search ({improvements} edge improvements)",
            "route": opt_route,
            "hypothesis": "2-opt should shorten the route by reversing crossed or inefficient segments.",
            "next": "Use deterministic restarts to check whether the local optimum is robust.",
        }
    )
    synthesis_route, synthesis_meta = multistart_two_opt()
    loops.append(
        {
            "id": "loop-04-multistart-synthesis",
            "track": "synthesis",
            "title": "Deterministic multi-start 2-opt synthesis",
            "route": synthesis_route,
            "hypothesis": "Multiple deterministic starts should avoid over-trusting one local optimum.",
            "next": "Stop: deterministic restarts did not find a shorter valid route than the current champion.",
            "extra": synthesis_meta,
        }
    )

    baseline_length = route_length(loops[0]["route"])
    best_length = float("inf")
    best_id = None
    iterations = []

    for loop in loops:
        loop_dir = ROOT / loop["track"] / loop["id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        route = loop["route"]
        length = route_length(route)
        valid = is_valid(route)
        if valid and length < best_length - 1e-9:
            decision = "new_best"
            best_length = length
            best_id = loop["id"]
            regression_note = "No regression; objective distance improved."
        elif valid:
            decision = "keep_for_synthesis"
            regression_note = "Valid but did not improve the current champion."
        else:
            decision = "reject"
            regression_note = "Rejected because the route failed the validity gate."
        metrics = {
            "distance": round(length, 2),
            "valid": valid,
            "improvement_pct": round((baseline_length - length) / baseline_length * 100, 2),
            "route": route,
            "route_names": [STOPS[idx][0] for idx in route],
            "regression_note": regression_note,
        }
        metrics.update(loop.get("extra", {}))
        metrics_path = loop_dir / "metrics.json"
        route_path = loop_dir / "route.svg"
        judge_path = loop_dir / "judge.md"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        write_route_svg(route, route_path, loop["title"])
        write_judge_note(judge_path, loop["id"], loop["title"], metrics, loop["next"])
        iterations.append(
            {
                "id": loop["id"],
                "track_id": loop["track"],
                "parent_id": None if len(iterations) == 0 else iterations[-1]["id"],
                "hypothesis": loop["hypothesis"],
                "commands": {
                    "build": "Select deterministic route-construction or route-improvement variant.",
                    "run": "python run_example.py",
                    "judge": "Read metrics.json; enforce validity gate; compare route_length to champion.",
                },
                "artifacts": [
                    {
                        "kind": "image",
                        "label": "Route SVG",
                        "path": f"{loop['track']}/{loop['id']}/route.svg",
                        "sha256": sha256(route_path),
                    },
                    {
                        "kind": "data",
                        "label": "Metrics JSON",
                        "path": f"{loop['track']}/{loop['id']}/metrics.json",
                        "sha256": sha256(metrics_path),
                    },
                    {
                        "kind": "markdown",
                        "label": "Judge note",
                        "path": f"{loop['track']}/{loop['id']}/judge.md",
                        "sha256": sha256(judge_path),
                    },
                ],
                "scores": [
                    {
                        "scorer_id": "route-metrics",
                        "type": "objective_command",
                        "value": score_from_length(length, baseline_length) if valid else 0,
                        "per_criterion": {
                            "route_length": round(length, 2),
                            "validity": 5 if valid else 0,
                            "reproducibility": 5,
                            "explainability": 4.5,
                        },
                        "notes": regression_note,
                        "raw": metrics,
                    }
                ],
                "changed_files": ["run_example.py"],
                "lesson": {
                    "trigger": loop["hypothesis"],
                    "action": loop["next"],
                    "evidence": f"{loop['track']}/{loop['id']}/route.svg and metrics.json",
                    "confidence": "high" if valid else "low",
                },
                "decision": decision,
                "stop_reason": None if loop["id"] != "loop-04-multistart-synthesis" else "Patience exhausted: no deterministic restart beat 2-opt champion.",
            }
        )

    manifest = {
        "schema_version": "0.2",
        "experiment_id": "route-optimizer-worked-example",
        "title": "Route Optimizer Worked Example",
        "goal": "Minimize a deterministic delivery route while preserving validity and reproducibility.",
        "created_at": "2026-07-03T00:00:00Z",
        "budget": {"max_iters": 4, "patience": 1, "cost_limit": None, "wall_time_limit_sec": 60},
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": ["quantitative-search/**", "synthesis/**", "manifest.json", "viewer.html"],
            "deny": [".env", "secrets/**", "**/*credential*"],
        },
        "scorecard": [
            {"id": "route_length", "label": "Route length", "weight": 3},
            {"id": "validity", "label": "Visits every stop exactly once", "weight": 3},
            {"id": "reproducibility", "label": "Deterministic and rerunnable", "weight": 1},
            {"id": "explainability", "label": "Artifacts explain the improvement", "weight": 1},
        ],
        "scorers": [
            {
                "id": "route-metrics",
                "type": "objective_command",
                "command": "python run_example.py",
                "primary": True,
                "weight": 3,
            }
        ],
        "judge_panels": [],
        "governance": {
            "self_editing": {
                "requires_user_approval": True,
                "proposal_required": True,
                "approved_proposal_id": None,
            }
        },
        "tracks": [
            {
                "id": "quantitative-search",
                "label": "Quantitative route search",
                "hypothesis": "Simple deterministic heuristics can rapidly improve a route when objective distance is measurable.",
            },
            {
                "id": "synthesis",
                "label": "Synthesis and robustness check",
                "hypothesis": "Deterministic restarts test whether the local-search champion is robust.",
            },
        ],
        "iterations": iterations,
        "best": {
            "iteration_id": best_id,
            "score": round(score_from_length(best_length, baseline_length), 2),
            "why": f"Shortest valid route at {best_length:.2f} units.",
        },
        "rules": [
            {
                "trigger": "A primary objective metric exists.",
                "action": "Use it as a gate before qualitative explanation.",
                "confidence": "high",
            }
        ],
        "synthesis": "Nearest-neighbor removed obvious waste, 2-opt made the largest objective improvement, and deterministic restarts confirmed the champion rather than replacing it.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "viewer.html").write_text(
        build_viewer.render_viewer(manifest), encoding="utf-8", newline="\n"
    )
    print(f"Best route: {best_id} at {best_length:.2f} units")


if __name__ == "__main__":
    main()
