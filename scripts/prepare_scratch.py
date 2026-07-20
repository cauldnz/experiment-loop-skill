#!/usr/bin/env python3
"""Prepare a prompt-safe scratch directory for an Experiment."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path, PureWindowsPath
from typing import Callable


SHORT_PATH_COMPONENT = re.compile(r"^[^\\/]*~\d+(?:\.[^\\/]*)?$", re.IGNORECASE)
SCRATCH_GITIGNORE = "*\n!.gitignore\n"


def contains_windows_short_path(path: Path | str) -> bool:
    """Return whether a path contains an 8.3-style component such as USERNA~1."""
    return any(
        SHORT_PATH_COMPONENT.fullmatch(part) is not None
        for part in PureWindowsPath(str(path)).parts
    )


def _get_windows_long_path(path: Path) -> Path:
    import ctypes

    get_long_path_name = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetLongPathNameW
    required = get_long_path_name(str(path), None, 0)
    if required == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    buffer = ctypes.create_unicode_buffer(required)
    copied = get_long_path_name(str(path), buffer, required)
    if copied == 0 or copied >= required:
        raise ctypes.WinError(ctypes.get_last_error())
    return Path(buffer.value)


def expand_windows_long_path(
    path: Path,
    *,
    windows: bool | None = None,
    resolver: Callable[[Path], Path] | None = None,
) -> Path:
    """Resolve an existing path and expand any Windows 8.3 components."""
    resolved = path.resolve(strict=True)
    is_windows = os.name == "nt" if windows is None else windows
    if not is_windows or not contains_windows_short_path(resolved):
        return resolved

    expanded = (resolver or _get_windows_long_path)(resolved)
    if contains_windows_short_path(expanded):
        raise RuntimeError(
            f"Windows long-path expansion retained an 8.3 component: {expanded}"
        )
    return expanded


def prepare_experiment_scratch(generated_root: Path) -> Path:
    """Create the preferred experiment-local scratch directory."""
    scratch_root = generated_root / "harness" / "scratch"
    scratch_root.mkdir(parents=True, exist_ok=True)
    ignore_file = scratch_root / ".gitignore"
    if not ignore_file.exists():
        ignore_file.write_text(SCRATCH_GITIGNORE, encoding="utf-8")
    return expand_windows_long_path(scratch_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--generated-root",
        type=Path,
        help="Experiment generated root; creates harness/scratch beneath it.",
    )
    mode.add_argument(
        "--session-scratch",
        type=Path,
        help="Existing session scratch directory to expand to its long Windows path.",
    )
    args = parser.parse_args(argv)

    if args.generated_root is not None:
        scratch_root = prepare_experiment_scratch(args.generated_root)
    else:
        scratch_root = expand_windows_long_path(args.session_scratch)
    print(scratch_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
