#!/usr/bin/env python3
"""Verify that every joke candidate contains all required native-script versions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_LANGUAGES = ("en", "fr", "es", "ja")
JAPANESE_SCRIPT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def check_candidate(path: Path) -> dict[str, object]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    languages = candidate.get("languages", {})
    missing = [language for language in REQUIRED_LANGUAGES if language not in languages]
    empty = [
        language
        for language in REQUIRED_LANGUAGES
        if language in languages
        and not (
            str(languages[language].get("setup", "")).strip()
            and str(languages[language].get("punchline", "")).strip()
        )
    ]
    japanese = languages.get("ja", {})
    japanese_text = " ".join(
        str(japanese.get(field, "")) for field in ("setup", "punchline", "combined")
    )
    japanese_script = bool(JAPANESE_SCRIPT.search(japanese_text))
    passed = not missing and not empty and japanese_script
    return {
        "path": path.as_posix(),
        "pass": passed,
        "missing_languages": missing,
        "empty_languages": empty,
        "japanese_script_present": japanese_script,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = args.data.resolve()
    paths = sorted(
        path
        for path in data.glob("**/candidate.json")
        if "panel" not in path.parts
    )
    checks = [check_candidate(path) for path in paths]
    report = {
        "scorer_id": "native-script-completeness",
        "required_languages": list(REQUIRED_LANGUAGES),
        "candidate_count": len(checks),
        "pass": bool(checks) and all(check["pass"] for check in checks),
        "checks": checks,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
