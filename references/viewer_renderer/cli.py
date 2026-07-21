from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import DEFAULT_PROFILE, ViewerProfile, render_viewer


WATCH_FRAGMENT_NAME = "manifest-fragment.json"


@dataclass(frozen=True)
class WatchSnapshot:
    files: tuple[tuple[str, int, int], ...]


@dataclass
class WatchDebouncer:
    debounce_seconds: float
    pending_since: float | None = None

    def observe(self, changed: bool, now: float) -> bool:
        if changed:
            self.pending_since = now
            return False
        if (
            self.pending_since is not None
            and now - self.pending_since >= self.debounce_seconds
        ):
            self.pending_since = None
            return True
        return False


def load_manifest(data_dir: Path) -> tuple[dict, str]:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        return {}, f"manifest.json not found in {data_dir}"
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"manifest.json could not be read: {exc}"
    if not text.strip():
        return {}, "manifest.json is empty"
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, f"manifest.json did not parse: {exc}"
    if not isinstance(loaded, dict):
        return {}, "manifest.json is not a JSON object"
    return loaded, ""


def build_viewer(
    data_dir: Path,
    out_path: Path,
    *,
    profile: ViewerProfile = DEFAULT_PROFILE,
) -> int:
    manifest, diagnostic = load_manifest(data_dir)
    if diagnostic:
        print(diagnostic, file=sys.stderr)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_viewer(
        manifest,
        profile=profile,
        diagnostic=diagnostic,
        data_dir=data_dir,
    )
    temporary = out_path.with_name(f".{out_path.name}.tmp")
    try:
        temporary.write_text(rendered, encoding="utf-8", newline="\n")
        os.replace(temporary, out_path)
    finally:
        temporary.unlink(missing_ok=True)
    return 0


def snapshot_watch_inputs(data_dir: Path) -> WatchSnapshot:
    """Capture one deterministic polling snapshot of Manifest inputs."""
    candidates = {data_dir / "manifest.json"}
    if data_dir.is_dir():
        candidates.update(data_dir.rglob(WATCH_FRAGMENT_NAME))
    files: list[tuple[str, int, int]] = []
    for path in sorted(candidates):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        files.append(
            (
                path.relative_to(data_dir).as_posix(),
                stat.st_mtime_ns,
                stat.st_size,
            )
        )
    return WatchSnapshot(tuple(files))


def poll_watch_inputs(
    data_dir: Path,
    previous: WatchSnapshot,
) -> tuple[WatchSnapshot, tuple[str, ...]]:
    """Poll once and return the new snapshot plus created, changed, or removed inputs."""
    current = snapshot_watch_inputs(data_dir)
    before = {path: (mtime, size) for path, mtime, size in previous.files}
    after = {path: (mtime, size) for path, mtime, size in current.files}
    changed = tuple(
        sorted(
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        )
    )
    return current, changed


def watch_viewer(
    data_dir: Path,
    out_path: Path,
    *,
    profile: ViewerProfile = DEFAULT_PROFILE,
    poll_interval: float = 0.25,
    debounce: float = 0.2,
) -> int:
    """Build once, then rebuild after coalesced Manifest input changes."""
    if poll_interval <= 0:
        raise ValueError("poll_interval must be greater than zero")
    if debounce < 0:
        raise ValueError("debounce must be zero or greater")

    snapshot = snapshot_watch_inputs(data_dir)
    try:
        build_viewer(data_dir, out_path, profile=profile)
    except OSError as exc:
        print(f"Initial Viewer build failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Watching {data_dir / 'manifest.json'} and {WATCH_FRAGMENT_NAME} files. "
        "Press Ctrl+C to stop.",
        file=sys.stderr,
    )
    debouncer = WatchDebouncer(debounce)
    while True:
        time.sleep(poll_interval)
        snapshot, changed = poll_watch_inputs(data_dir, snapshot)
        if changed:
            print(f"Manifest input changed: {', '.join(changed)}", file=sys.stderr)
        if not debouncer.observe(bool(changed), time.monotonic()):
            continue
        try:
            build_viewer(data_dir, out_path, profile=profile)
        except OSError as exc:
            print(f"Viewer rebuild failed: {exc}", file=sys.stderr)
            continue
        print(f"Rebuilt {out_path}", file=sys.stderr)


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def main(
    argv: list[str] | None = None,
    *,
    profile: ViewerProfile = DEFAULT_PROFILE,
) -> int:
    parser = argparse.ArgumentParser(description="Render an experiment Viewer.")
    parser.add_argument("--data", required=True, help="directory containing manifest.json")
    parser.add_argument("--out", required=True, help="output viewer.html path")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="rebuild after manifest.json or manifest-fragment.json changes",
    )
    parser.add_argument(
        "--poll-interval",
        type=_positive_float,
        default=0.25,
        metavar="SECONDS",
        help="watch polling interval (default: 0.25)",
    )
    parser.add_argument(
        "--debounce",
        type=_non_negative_float,
        default=0.2,
        metavar="SECONDS",
        help="quiet period used to coalesce watch rebuilds (default: 0.2)",
    )
    args = parser.parse_args(argv)
    data_dir = Path(args.data)
    out_path = Path(args.out)
    try:
        if args.watch:
            return watch_viewer(
                data_dir,
                out_path,
                profile=profile,
                poll_interval=args.poll_interval,
                debounce=args.debounce,
            )
        return build_viewer(data_dir, out_path, profile=profile)
    except KeyboardInterrupt:
        print("Watch stopped.", file=sys.stderr)
        return 0
    except OSError as exc:
        print(f"Viewer build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
