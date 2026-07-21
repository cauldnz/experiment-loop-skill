#!/usr/bin/env python3
"""Standard Viewer adapter, including deterministic one-shot and local watch modes."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_skill_root() -> Path:
    configured = os.environ.get("EXPERIMENT_LOOP_SKILL_ROOT")
    if configured:
        root = Path(configured).resolve()
        if (root / "references" / "viewer_renderer").is_dir():
            return root
    for parent in Path(__file__).resolve().parents:
        if (parent / "references" / "viewer_renderer").is_dir():
            return parent
        project_skill = parent / ".github" / "skills" / "experiment-loop"
        if (project_skill / "references" / "viewer_renderer").is_dir():
            return project_skill
    raise RuntimeError(
        "experiment-loop skill not found; set EXPERIMENT_LOOP_SKILL_ROOT"
    )


sys.path.insert(0, str(_find_skill_root()))

from references.viewer_renderer import ViewerProfile  # noqa: E402
from references.viewer_renderer.cli import main  # noqa: E402


PROFILE = ViewerProfile(extra_panels=())


if __name__ == "__main__":
    raise SystemExit(main(profile=PROFILE))
