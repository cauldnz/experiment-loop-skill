from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from references.evidence_gate import validate_experiment


ROOT = Path(__file__).resolve().parents[1]


class EvidenceGateTests(unittest.TestCase):
    def test_human_judge_export_schema_is_valid(self) -> None:
        import jsonschema

        schema = json.loads(
            (ROOT / "references" / "human-judge-schema-v1.0.json").read_text(
                encoding="utf-8"
            )
        )
        export = {
            "schema_version": "1.0",
            "experiment_id": "example",
            "manifest_sha256": "0" * 64,
            "viewer_sha256": "1" * 64,
            "viewer_hash_algorithm": "canonical-html-zeroed-binding-v1",
            "verdict": "needs_improvement",
            "general_notes": "Review notes.",
            "criterion_reviews": [],
            "loop_notes": [],
            "artifact_notes": [],
            "preferred_iteration_id": None,
            "recommendation": "needs_improvement",
        }
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(export, schema)

    def make_run(self, root: Path) -> None:
        manifest = json.loads(
            (ROOT / "templates" / "manifest-template.json").read_text(encoding="utf-8")
        )
        for iteration in manifest["iterations"]:
            for artifact in iteration["artifacts"]:
                path = root / artifact["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(iteration["id"], encoding="utf-8")
                artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        (root / "build_viewer.py").write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                f"sys.path.insert(0, {str(ROOT)!r})\n"
                "from references.viewer_renderer.cli import main\n"
                "if __name__ == '__main__': raise SystemExit(main())\n"
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(root / "build_viewer.py"),
                "--data",
                str(root),
                "--out",
                str(root / "viewer.html"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        viewer_hash = hashlib.sha256((root / "viewer.html").read_bytes()).hexdigest()
        (root / "navigation-evidence.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "status": "pass",
                    "viewer_sha256": viewer_hash,
                    "browser": {"name": "chromium", "version": "test"},
                    "checks": [{"name": "contract", "status": "pass"}],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_complete_run_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            report = validate_experiment(root)
            self.assertTrue(
                report.passed,
                [(check.name, check.status, check.detail) for check in report.checks],
            )

    def test_stale_viewer_and_navigation_evidence_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            (root / "viewer.html").write_text("stale", encoding="utf-8")
            report = validate_experiment(root)
            statuses = {check.name: check.status for check in report.checks}
            self.assertEqual("fail", statuses["viewer_determinism"])
            self.assertEqual("fail", statuses["navigation_evidence"])

    def test_semantic_cycle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["iterations"][0]["parent_ids"] = ["loop-002"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = validate_experiment(root)
            semantic = next(
                check for check in report.checks if check.name == "manifest_semantics"
            )
            self.assertEqual("fail", semantic.status)
            self.assertIn("cycle", " ".join(semantic.detail["errors"]))

    def test_unknown_champion_evidence_fails_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["champion"]["reasons"][0]["evidence_refs"] = ["invented"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = validate_experiment(root)
            semantic = next(
                check for check in report.checks if check.name == "manifest_semantics"
            )
            self.assertEqual("fail", semantic.status)
            self.assertIn("unknown evidence", " ".join(semantic.detail["errors"]))

    def test_primary_comparison_requires_two_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["iterations"][0]["artifacts"][0]["presentation"].pop(
                "comparison_key"
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = validate_experiment(root)
            semantic = next(
                check for check in report.checks if check.name == "manifest_semantics"
            )
            self.assertEqual("fail", semantic.status)
            self.assertIn("comparison key", " ".join(semantic.detail["errors"]))

    def test_invalid_feedback_sidecar_adds_blocking_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_run(root)
            intake = root / "human-feedback" / "intake" / "invalid.json"
            intake.parent.mkdir(parents=True)
            intake.write_text("{", encoding="utf-8")

            report = validate_experiment(root)
            feedback = next(
                check for check in report.checks if check.name == "human_feedback"
            )

            self.assertEqual("fail", feedback.status)


if __name__ == "__main__":
    unittest.main()
