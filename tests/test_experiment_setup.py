from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_experiment_setup import validate_brief, validate_setup


ROOT = Path(__file__).resolve().parents[1]


class ExperimentSetupTests(unittest.TestCase):
    def valid_brief(self) -> dict[str, object]:
        brief = json.loads(
            (ROOT / "templates" / "experiment-brief-template.json").read_text(
                encoding="utf-8"
            )
        )
        brief["status"] = "approved"
        brief["setup_review"] = {
            "critic_model_id": "independent-critic",
            "status": "pass",
            "unresolved_findings": [],
        }
        return brief

    def test_valid_approved_binding_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            brief_path = root / "experiment-brief.json"
            prompt_path = root / "prompt.md"
            approval_path = root / "approval.json"
            brief_path.write_text(
                json.dumps(self.valid_brief(), indent=2) + "\n",
                encoding="utf-8",
            )
            prompt_path.write_text("Use the experiment-loop skill.\n", encoding="utf-8")
            approval = {
                "schema_version": "1.0",
                "experiment_id": "short-stable-id",
                "brief_revision": 1,
                "brief_sha256": hashlib.sha256(brief_path.read_bytes()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
                "status": "approved",
                "approved_at": "2026-07-20T00:00:00Z",
                "approval_source": "explicit_human_confirmation",
                "notes": "",
            }
            approval_path.write_text(
                json.dumps(approval, indent=2) + "\n", encoding="utf-8"
            )
            self.assertEqual(
                [],
                validate_setup(
                    brief_path,
                    prompt_path=prompt_path,
                    approval_path=approval_path,
                    require_approved=True,
                ),
            )

    def test_approval_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            brief_path = root / "experiment-brief.json"
            prompt_path = root / "prompt.md"
            approval_path = root / "approval.json"
            brief_path.write_text(
                json.dumps(self.valid_brief(), indent=2) + "\n",
                encoding="utf-8",
            )
            prompt_path.write_text("Prompt\n", encoding="utf-8")
            approval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "experiment_id": "short-stable-id",
                        "brief_revision": 1,
                        "brief_sha256": "0" * 64,
                        "prompt_sha256": "1" * 64,
                        "status": "approved",
                        "approved_at": "2026-07-20T00:00:00Z",
                        "approval_source": "explicit_human_confirmation",
                        "notes": "",
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_setup(
                brief_path,
                prompt_path=prompt_path,
                approval_path=approval_path,
                require_approved=True,
            )
            self.assertIn("approval brief_sha256 does not match brief", errors)
            self.assertIn("approval prompt_sha256 does not match prompt", errors)

    def test_active_risk_branch_requires_controls(self) -> None:
        brief = self.valid_brief()
        brief["risks"]["deployment"] = True
        errors = validate_brief(brief)
        self.assertTrue(
            any("active risk branch lacks controls" in error for error in errors),
            errors,
        )

    def test_unattended_mode_requires_scratch_root(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["mode"] = "unattended"
        del brief["target"]["scratch_root"]
        self.assertIn(
            "unattended mode requires target.scratch_root",
            validate_brief(brief),
        )

    def test_unattended_scratch_root_must_be_under_generated_root(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["mode"] = "unattended"
        brief["target"]["scratch_root"] = ".scratch"
        self.assertIn(
            "unattended target.scratch_root must be within target.generated_root",
            validate_brief(brief),
        )

    def test_interactive_legacy_brief_may_omit_scratch_root(self) -> None:
        brief = self.valid_brief()
        del brief["target"]["scratch_root"]
        self.assertEqual([], validate_brief(brief))


if __name__ == "__main__":
    unittest.main()
