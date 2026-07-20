#!/usr/bin/env python3
"""Deterministic candidate optimizer for the fixed delivery-route experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Callable

Point = dict[str, object]
Route = list[str]


def load_data(path: Path) -> tuple[Point, list[Point]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    depot = data["depot"]
    stops = data["stops"]
    names = [str(stop["name"]) for stop in stops]
    if len(names) < 12 or len(names) != len(set(names)):
        raise ValueError("input requires at least 12 uniquely named stops")
    if str(depot["name"]) in names:
        raise ValueError("depot name must differ from every stop")
    return depot, stops


def distance(a: Point, b: Point) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def route_length(route: Route, points: dict[str, Point]) -> float:
    return sum(distance(points[a], points[b]) for a, b in zip(route, route[1:]))


def baseline(depot: Point, stops: list[Point]) -> Route:
    ordered = sorted(str(stop["name"]) for stop in stops)
    return [str(depot["name"]), *ordered, str(depot["name"])]


def nearest_neighbor(
    depot: Point, stops: list[Point], forced_first: str | None = None
) -> Route:
    points = {str(point["name"]): point for point in [depot, *stops]}
    depot_name = str(depot["name"])
    remaining = {str(stop["name"]) for stop in stops}
    route = [depot_name]
    if forced_first is not None:
        route.append(forced_first)
        remaining.remove(forced_first)
    while remaining:
        current = route[-1]
        next_name = min(
            remaining, key=lambda name: (distance(points[current], points[name]), name)
        )
        route.append(next_name)
        remaining.remove(next_name)
    return [*route, depot_name]


def two_opt(route: Route, points: dict[str, Point]) -> Route:
    best = route[:]
    best_length = route_length(best, points)
    while True:
        candidate_route: Route | None = None
        candidate_length = best_length
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                candidate = best[:i] + list(reversed(best[i : j + 1])) + best[j + 1 :]
                length = route_length(candidate, points)
                if length < candidate_length - 1e-12:
                    candidate_route = candidate
                    candidate_length = length
        if candidate_route is None:
            return best
        best, best_length = candidate_route, candidate_length


def local_search(depot: Point, stops: list[Point]) -> Route:
    points = {str(point["name"]): point for point in [depot, *stops]}
    return two_opt(nearest_neighbor(depot, stops), points)


def multi_start(depot: Point, stops: list[Point]) -> Route:
    points = {str(point["name"]): point for point in [depot, *stops]}
    candidates = [
        two_opt(nearest_neighbor(depot, stops, str(stop["name"])), points)
        for stop in sorted(stops, key=lambda stop: str(stop["name"]))
    ]
    return min(candidates, key=lambda route: (route_length(route, points), route))


STRATEGIES: dict[str, Callable[[Point, list[Point]], Route]] = {
    "baseline": baseline,
    "nearest": nearest_neighbor,
    "two_opt": local_search,
    "multi_start": multi_start,
}


def validate(route: Route, depot: Point, stops: list[Point]) -> tuple[bool, list[str]]:
    depot_name = str(depot["name"])
    expected = sorted(str(stop["name"]) for stop in stops)
    visited = route[1:-1]
    errors: list[str] = []
    if not route or route[0] != depot_name:
        errors.append("route does not start at the depot")
    if not route or route[-1] != depot_name:
        errors.append("route does not return to the depot")
    if sorted(visited) != expected:
        errors.append("route does not visit every stop exactly once")
    return not errors, errors


def render_svg(
    route: Route, points: dict[str, Point], title: str, length: float
) -> str:
    width, height, margin = 760, 560, 58
    xs = [float(point["x"]) for point in points.values()]
    ys = [float(point["y"]) for point in points.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    def project(name: str) -> tuple[float, float]:
        point = points[name]
        x = margin + (float(point["x"]) - x_min) / (x_max - x_min) * (width - 2 * margin)
        y = height - margin - (float(point["y"]) - y_min) / (y_max - y_min) * (height - 2 * margin)
        return x, y

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(project, route))
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="560" viewBox="0 0 760 560" role="img">',
        f"<title>{title}: {length:.6f} km</title>",
        '<rect width="760" height="560" fill="#f8fafc"/>',
        f'<text x="30" y="32" font-family="system-ui" font-size="19" font-weight="700" fill="#172554">{title}</text>',
        f'<text x="730" y="32" text-anchor="end" font-family="system-ui" font-size="14" fill="#334155">{length:.6f} km</text>',
        f'<polyline points="{polyline}" fill="none" stroke="#2563eb" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>',
    ]
    for order, name in enumerate(route[:-1]):
        x, y = project(name)
        is_depot = order == 0
        fill = "#dc2626" if is_depot else "#f59e0b"
        radius = 9 if is_depot else 7
        label = "DEPOT" if is_depot else f"{order}. {name}"
        elements.extend(
            [
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="#fff" stroke-width="2"/>',
                f'<text x="{x + 10:.1f}" y="{y - 9:.1f}" font-family="system-ui" font-size="11" fill="#0f172a">{label}</text>',
            ]
        )
    elements.append("</svg>")
    return "\n".join(elements)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    depot, stops = load_data(args.data)
    points = {str(point["name"]): point for point in [depot, *stops]}
    runs = [STRATEGIES[args.strategy](depot, stops) for _ in range(3)]
    route = runs[0]
    valid, errors = validate(route, depot, stops)
    reproducible = all(candidate == route for candidate in runs[1:])
    length = route_length(route, points)
    input_sha = hashlib.sha256(args.data.read_bytes()).hexdigest()
    args.out.mkdir(parents=True, exist_ok=True)

    route_record = {
        "strategy": args.strategy,
        "route": route,
        "route_length_km": round(length, 9),
    }
    metrics = {
        "strategy": args.strategy,
        "route_length_km": round(length, 9),
        "validity": 1 if valid else 0,
        "reproducibility": 1 if reproducible else 0,
        "repeat_runs": 3,
        "identical_routes": reproducible,
        "stop_count": len(stops),
        "starts_at_depot": route[0] == str(depot["name"]),
        "ends_at_depot": route[-1] == str(depot["name"]),
        "unique_stops_visited": len(set(route[1:-1])),
        "validation_errors": errors,
        "input_sha256": input_sha,
    }
    (args.out / "route.json").write_text(
        json.dumps(route_record, indent=2) + "\n", encoding="utf-8"
    )
    (args.out / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    (args.out / "route-map.svg").write_text(
        render_svg(route, points, args.strategy.replace("_", " ").title(), length),
        encoding="utf-8",
    )
    print(json.dumps(metrics, sort_keys=True))
    return 0 if valid and reproducible else 2


if __name__ == "__main__":
    raise SystemExit(main())
