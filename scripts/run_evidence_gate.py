#!/usr/bin/env python3
"""Run the bundled Evidence Gate from any working directory."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from references.evidence_gate.__main__ import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
