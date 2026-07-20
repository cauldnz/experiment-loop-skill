#!/usr/bin/env python3
"""Independent Held-Karp exact oracle for the fixed route instance."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    depot = data["depot"]
    stops = sorted(data["stops"], key=lambda stop: stop["name"])
    points = [depot, *stops]

    def distance(i: int, j: int) -> float:
        return math.hypot(
            float(points[i]["x"]) - float(points[j]["x"]),
            float(points[i]["y"]) - float(points[j]["y"]),
        )

    count = len(stops)
    dp: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
    for j in range(count):
        dp[(1 << j, j)] = (distance(0, j + 1), (j,))
    for mask in range(1, 1 << count):
        for end in range(count):
            if not mask & (1 << end) or (mask, end) not in dp:
                continue
            cost, path = dp[(mask, end)]
            for nxt in range(count):
                if mask & (1 << nxt):
                    continue
                key = (mask | (1 << nxt), nxt)
                proposal = (cost + distance(end + 1, nxt + 1), (*path, nxt))
                current = dp.get(key)
                if current is None or proposal < current:
                    dp[key] = proposal
    full = (1 << count) - 1
    optimum_cost, optimum_indices = min(
        (
            cost + distance(end + 1, 0),
            path,
        )
        for end in range(count)
        for cost, path in [dp[(full, end)]]
    )
    optimum_route = [
        depot["name"],
        *(stops[index]["name"] for index in optimum_indices),
        depot["name"],
    ]
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    candidate_cost = float(candidate["route_length_km"])
    result = {
        "solver": "Held-Karp dynamic programming",
        "proof_scope": "Exhaustive dynamic programming over all stop subsets and endpoints",
        "state_count": len(dp),
        "optimal_route": optimum_route,
        "optimal_length_km": round(optimum_cost, 9),
        "candidate_length_km": round(candidate_cost, 9),
        "optimality_gap_km": round(candidate_cost - optimum_cost, 9),
        "candidate_is_globally_optimal": abs(candidate_cost - optimum_cost) <= 1e-8,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["candidate_is_globally_optimal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
