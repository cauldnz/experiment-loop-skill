from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from references.human_feedback import (
    load_feedback_view,
    validate_feedback_directory,
    validate_manifest_feedback,
)
from scripts.validate_human_feedback import main


ROOT = Path(__file__).resolve().parents[1]


class HumanFeedbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "templates" / "manifest-template.json").read_text(
                encoding="utf-8"
            )
        )

    def write_feedback(
        self,
        root: Path,
        *,
        disposition: str = "accepted",
        verbatim: str = "Make the next Loop easier to scan.",
    ) -> tuple[Path, Path]:
        intake = {
            "schema_version": "1.0",
            "kind": "human_feedback_intake",
            "review_id": "review-001",
            "experiment_id": self.manifest["experiment_id"],
            "submitted_at": "2026-07-21T00:00:00Z",
            "provenance": {
                "surface": "viewer_native",
                "export_mode": "local_download",
            },
            "binding": {
                "manifest_sha256": "0" * 64,
                "viewer_sha256": "1" * 64,
                "viewer_hash_algorithm": "canonical-html-zeroed-binding-v1",
            },
            "human": {
                "verdict": "needs_improvement",
                "recommendation": "needs_improvement",
                "preferred_iteration_id": "loop-002",
                "entries": [
                    {
                        "entry_id": "feedback-001",
                        "feedback_type": "loop",
                        "verbatim": verbatim,
                        "target": {"kind": "loop", "id": "loop-002"},
                    }
                ],
            },
        }
        intake_path = root / "human-feedback" / "intake" / "review-001.json"
        intake_path.parent.mkdir(parents=True)
        intake_path.write_text(
            json.dumps(intake, indent=2) + "\n", encoding="utf-8"
        )
        consumed = ["loop-002"] if disposition == "accepted" else []
        orchestrator = {
            "interpretation": "Improve scanability in the next bounded iteration.",
            "disposition": disposition,
            "rationale": "This is inside the approved presentation scope.",
            "consumed_iteration_refs": consumed,
        }
        if disposition == "answered_conflicts_with_frozen_invariant":
            orchestrator["owner_response"] = (
                "The frozen invariant prevents this change in the current run."
            )
        disposition_data = {
            "schema_version": "1.0",
            "kind": "human_feedback_disposition",
            "disposition_id": "disposition-001",
            "experiment_id": self.manifest["experiment_id"],
            "entry_id": "feedback-001",
            "recorded_at": "2026-07-21T00:05:00Z",
            "intake": {
                "review_id": "review-001",
                "path": "human-feedback/intake/review-001.json",
                "sha256": hashlib.sha256(intake_path.read_bytes()).hexdigest(),
            },
            "orchestrator": orchestrator,
        }
        disposition_path = (
            root / "human-feedback" / "dispositions" / "disposition-001.json"
        )
        disposition_path.parent.mkdir(parents=True)
        disposition_path.write_text(
            json.dumps(disposition_data, indent=2) + "\n", encoding="utf-8"
        )
        if disposition == "accepted":
            self.manifest["iterations"][1]["prompt"]["input_feedback"] = verbatim
            self.manifest["iterations"][1]["prompt"]["input_feedback_refs"] = [
                "feedback-001"
            ]
        self.manifest["human_feedback"] = [
            {
                "entry_id": "feedback-001",
                "review_id": "review-001",
                "intake_path": "human-feedback/intake/review-001.json",
                "intake_sha256": hashlib.sha256(intake_path.read_bytes()).hexdigest(),
                "disposition_path": (
                    "human-feedback/dispositions/disposition-001.json"
                ),
                "disposition_sha256": hashlib.sha256(
                    disposition_path.read_bytes()
                ).hexdigest(),
                "feedback_type": "loop",
                "verbatim": verbatim,
                "target": {"kind": "loop", "id": "loop-002"},
                "disposition": {
                    "id": "disposition-001",
                    "status": disposition,
                    "interpretation": orchestrator["interpretation"],
                    "rationale": orchestrator["rationale"],
                    "consumed_iteration_refs": consumed,
                    **(
                        {"owner_response": orchestrator["owner_response"]}
                        if "owner_response" in orchestrator
                        else {}
                    ),
                },
            }
        ]
        (root / "manifest.json").write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )
        return intake_path, disposition_path

    def test_templates_conform_to_canonical_schemas(self) -> None:
        for stem in ("intake", "disposition"):
            schema = json.loads(
                (
                    ROOT
                    / "references"
                    / f"human-feedback-{stem}-schema-v1.0.json"
                ).read_text(encoding="utf-8")
            )
            template = json.loads(
                (
                    ROOT
                    / "templates"
                    / f"human-feedback-{stem}-template.json"
                ).read_text(encoding="utf-8")
            )
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.Draft202012Validator(
                schema, format_checker=jsonschema.FormatChecker()
            ).validate(template)

    def test_accepted_feedback_validates_complete_consumption_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_feedback(root)

            self.assertEqual([], validate_feedback_directory(root, self.manifest))
            manifest_schema = json.loads(
                (
                    ROOT / "references" / "manifest-schema-v1.1.json"
                ).read_text(encoding="utf-8")
            )
            jsonschema.validate(self.manifest, manifest_schema)
            self.assertEqual(0, main(["--data", str(root)]))

    def test_conflicting_feedback_is_answered_and_never_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_feedback(
                root,
                disposition="answered_conflicts_with_frozen_invariant",
            )

            self.assertEqual([], validate_feedback_directory(root, self.manifest))

    def test_manifest_rejects_missing_reciprocal_prompt_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_feedback(root)
            self.manifest["iterations"][1]["prompt"]["input_feedback_refs"] = []

            errors = validate_manifest_feedback(self.manifest)

            self.assertIn(
                "Loop loop-002 does not reference accepted feedback feedback-001",
                errors,
            )

    def test_validator_rejects_changed_verbatim_text_and_intake_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            intake_path, _ = self.write_feedback(root)
            self.manifest["human_feedback"][0]["verbatim"] = "Changed summary"
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            intake["human"]["entries"][0]["verbatim"] = "Edited after export"
            intake_path.write_text(json.dumps(intake), encoding="utf-8")

            errors = validate_feedback_directory(root, self.manifest)

            self.assertTrue(any("intake.sha256" in error for error in errors), errors)
            self.assertTrue(any("changed verbatim" in error for error in errors), errors)

    def test_view_records_pending_intake_during_partial_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_feedback(root)
            disposition = (
                root / "human-feedback" / "dispositions" / "disposition-001.json"
            )
            disposition.unlink()

            records, diagnostics = load_feedback_view(root, self.manifest)

            self.assertEqual([], diagnostics)
            self.assertEqual("pending", records[0]["status"])
            self.assertEqual(
                "Make the next Loop easier to scan.", records[0]["verbatim"]
            )


if __name__ == "__main__":
    unittest.main()
