#!/usr/bin/env python3
"""Prepare deterministic identity-blind Loop 02 judging bundles."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


GENERATED_ROOT = Path(__file__).resolve().parents[2]
JUDGING_ROOT = Path(__file__).resolve().parent
BLIND_ROOT = GENERATED_ROOT / "judging" / "blind-loop-02"
ORCHESTRATOR_ROOT = JUDGING_ROOT / "orchestrator"

MAPPING = {
    "candidate-a": {
        "track_id": "single-page",
        "loop_id": "single-page-loop-02",
        "source": GENERATED_ROOT / "track-single-page" / "loop-02",
    },
    "candidate-b": {
        "track_id": "resumable-wizard",
        "loop_id": "resumable-wizard-loop-02",
        "source": GENERATED_ROOT / "track-resumable-wizard" / "loop-02",
    },
    "candidate-c": {
        "track_id": "task-cards",
        "loop_id": "task-cards-loop-02",
        "source": GENERATED_ROOT / "track-task-cards" / "loop-02",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def expected_files(source: Path) -> list[Path]:
    result = [source / name for name in ("index.html", "styles.css", "app.js")]
    result.extend(sorted(path for path in (source / "evidence").rglob("*") if path.is_file()))
    return result


def copy_or_verify(label: str, source: Path) -> list[dict[str, str]]:
    target = BLIND_ROOT / label
    records = []
    for source_path in expected_files(source):
        relative = source_path.relative_to(source)
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            if sha256(target_path) != sha256(source_path):
                raise RuntimeError(f"Existing blind bundle differs: {target_path}")
        else:
            shutil.copyfile(source_path, target_path)
        records.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256(target_path),
            }
        )
    manifest = {
        "schema_version": "1.0",
        "label": label,
        "identity_blind": True,
        "objective_report_pass_required": True,
        "files": records,
    }
    write_json(target / "bundle-manifest.json", manifest)
    return records


def main() -> int:
    ORCHESTRATOR_ROOT.mkdir(parents=True, exist_ok=True)
    bundles = {}
    for label, record in MAPPING.items():
        bundles[label] = copy_or_verify(label, record["source"])

    hidden_map = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "loop": "loop-02",
        "mapping_fixed_before_judging": True,
        "mappings": [
            {
                "label": label,
                "loop_id": record["loop_id"],
                "track_id": record["track_id"],
                "source_path": record["source"].relative_to(GENERATED_ROOT).as_posix(),
                "bundle_manifest_sha256": sha256(
                    BLIND_ROOT / label / "bundle-manifest.json"
                ),
            }
            for label, record in MAPPING.items()
        ],
        "judge_orders": {
            "judge-accessibility": ["candidate-a", "candidate-b", "candidate-c"],
            "judge-human-use": ["candidate-c", "candidate-b", "candidate-a"],
        },
        "visibility": "orchestrator-only until both independent judges are terminal",
    }
    write_json(ORCHESTRATOR_ROOT / "blinding-map.pending.json", hidden_map)
    print(
        json.dumps(
            {
                "bundle_root": str(BLIND_ROOT),
                "labels": sorted(bundles),
                "mapping_path": str(
                    ORCHESTRATOR_ROOT / "blinding-map.pending.json"
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
