from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import DEFAULT_PROFILE, ViewerProfile, render_viewer


def load_manifest(data_dir: Path) -> tuple[dict, str]:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        return {}, f"manifest.json not found in {data_dir}"
    text = manifest_path.read_text(encoding="utf-8")
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
    out_path.write_text(
        render_viewer(
            manifest,
            profile=profile,
            diagnostic=diagnostic,
            data_dir=data_dir,
        ),
        encoding="utf-8",
        newline="\n",
    )
    return 0


def main(
    argv: list[str] | None = None,
    *,
    profile: ViewerProfile = DEFAULT_PROFILE,
) -> int:
    parser = argparse.ArgumentParser(description="Render an experiment Viewer.")
    parser.add_argument("--data", required=True, help="directory containing manifest.json")
    parser.add_argument("--out", required=True, help="output viewer.html path")
    args = parser.parse_args(argv)
    return build_viewer(Path(args.data), Path(args.out), profile=profile)


if __name__ == "__main__":
    raise SystemExit(main())
