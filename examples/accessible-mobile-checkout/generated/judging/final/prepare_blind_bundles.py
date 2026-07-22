#!/usr/bin/env python3
"""Create fixed identity-blind final comparison bundles."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT.parents[1]
BLIND_ROOT = ROOT / "blind"
ORCHESTRATOR_ROOT = ROOT / "orchestrator"
MAPPING = {
    "candidate-a": {
        "iteration_id": "synthesis-loop-02",
        "source": GENERATED_ROOT / "synthesis" / "loop-02",
    },
    "candidate-b": {
        "iteration_id": "synthesis-loop-01",
        "source": GENERATED_ROOT / "synthesis" / "loop-01",
    },
    "candidate-c": {
        "iteration_id": "single-page-loop-02",
        "source": GENERATED_ROOT / "track-single-page" / "loop-02",
    },
}
FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "evidence/objective-report.json",
    "evidence/objective-report.txt",
    "evidence/initial.png",
    "evidence/keyboard-completion.png",
    "evidence/final.png",
    "evidence/viewport-320x568.png",
    "evidence/viewport-360x800.png",
    "evidence/viewport-390x844.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if BLIND_ROOT.exists():
        shutil.rmtree(BLIND_ROOT)
    BLIND_ROOT.mkdir(parents=True)
    records = []
    for label, config in MAPPING.items():
        target = BLIND_ROOT / label
        artifacts = []
        for relative in FILES:
            source = config["source"] / relative
            if not source.is_file():
                raise RuntimeError(f"Missing source Artifact: {source}")
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            if sha256(source) != sha256(destination):
                raise RuntimeError(f"Blind copy hash mismatch: {relative}")
            artifacts.append(
                {
                    "path": f"judging/final/blind/{label}/{relative}",
                    "sha256": sha256(destination),
                }
            )
        records.append(
            {
                "label": label,
                "iteration_id": config["iteration_id"],
                "artifacts": artifacts,
            }
        )
    ORCHESTRATOR_ROOT.mkdir(parents=True, exist_ok=True)
    pending = {
        "schema_version": "1.0",
        "experiment_id": "accessible-mobile-checkout",
        "mapping_fixed_before_judging": True,
        "visibility": "orchestrator-only until both judges terminal",
        "mappings": records,
        "judge_orders": {
            "judge-accessibility": [
                "candidate-a",
                "candidate-b",
                "candidate-c",
            ],
            "judge-human-use": [
                "candidate-c",
                "candidate-b",
                "candidate-a",
            ],
        },
        "required_pairwise": {
            "champion_candidate_vs_strongest_parent": [
                "candidate-a",
                "candidate-c",
            ],
            "order_flipped_between_judges": True,
        },
    }
    path = ORCHESTRATOR_ROOT / "blinding-map.pending.json"
    path.write_text(
        json.dumps(pending, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "bundle_count": len(records),
                "mapping_sha256": sha256(path),
                "artifact_count": sum(len(item["artifacts"]) for item in records),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
