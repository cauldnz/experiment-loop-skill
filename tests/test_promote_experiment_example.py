from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import promote_experiment_example as promotion


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class PromoteExperimentExampleTests(unittest.TestCase):
    def _source(self, root: Path) -> tuple[Path, str, str]:
        experiment = root / ".experiments" / promotion.EXPERIMENT_ID
        setup = experiment / "setup"
        generated = experiment / "generated"
        setup.mkdir(parents=True)
        generated.mkdir()
        brief = setup / "experiment-brief.json"
        prompt = setup / "prompt.md"
        brief.write_text("{}\n", encoding="utf-8")
        prompt.write_text("Prompt\n", encoding="utf-8")
        brief_sha = hashlib.sha256(brief.read_bytes()).hexdigest()
        prompt_sha = hashlib.sha256(prompt.read_bytes()).hexdigest()
        _write_json(
            setup / "approval.json",
            {
                "status": "approved",
                "brief_sha256": brief_sha,
                "prompt_sha256": prompt_sha,
            },
        )
        (generated / "viewer.html").write_text(
            "<html></html>\n", encoding="utf-8"
        )
        viewer_sha = promotion.file_sha256(generated / "viewer.html")
        _write_json(
            generated / "navigation-evidence.json",
            {"status": "pass", "viewer_sha256": viewer_sha},
        )
        _write_json(generated / "evidence-gate.json", {"status": "pass"})
        _write_json(generated / "manifest.json", {"schema_version": "1.1"})
        return experiment, brief_sha, prompt_sha

    def test_validate_source_binds_approved_passing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            experiment, brief_sha, prompt_sha = self._source(Path(temporary))
            with (
                mock.patch.object(
                    promotion, "EXPECTED_BRIEF_SHA256", brief_sha
                ),
                mock.patch.object(
                    promotion, "EXPECTED_PROMPT_SHA256", prompt_sha
                ),
            ):
                binding = promotion.validate_source(experiment)

            self.assertEqual(binding["brief_sha256"], brief_sha)
            self.assertEqual(binding["prompt_sha256"], prompt_sha)
            self.assertEqual(binding["source_evidence_gate_status"], "pass")
            self.assertEqual(len(str(binding["source_tree_sha256"])), 64)
            self.assertEqual(
                binding["source_viewer_sha256"],
                promotion.file_sha256(
                    experiment / "generated" / "viewer.html"
                ),
            )

    def test_validate_source_rejects_failed_canonical_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            experiment, brief_sha, prompt_sha = self._source(Path(temporary))
            _write_json(
                experiment / "generated" / "evidence-gate.json",
                {"status": "fail"},
            )
            with (
                mock.patch.object(
                    promotion, "EXPECTED_BRIEF_SHA256", brief_sha
                ),
                mock.patch.object(
                    promotion, "EXPECTED_PROMPT_SHA256", prompt_sha
                ),
                self.assertRaisesRegex(
                    promotion.PromotionError, "Evidence Gate"
                ),
            ):
                promotion.validate_source(experiment)

    def test_sanitize_machine_paths_removes_worktree_and_user_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "copilot-worktrees" / "skill" / "worktree"
            experiment = root / ".experiments" / promotion.EXPERIMENT_ID
            generated = experiment / "generated"
            generated.mkdir(parents=True)
            user = Path(temporary) / "Users" / "person"
            evidence = generated / "evidence.txt"
            escaped_root = str(root).replace("\\", "\\\\")
            evidence.write_bytes(
                (
                    f"{root}\\scripts\\run.py\r\n"
                    f"{user}\\AppData\\log.txt\r\n"
                    "C:\\Users\\SOMEON~1\\AppData\\short-name.log\r\n"
                    f"{escaped_root}\\\\scripts\\\\escaped.py\r\n"
                ).encode("utf-8")
            )

            with mock.patch.object(Path, "home", return_value=user):
                promotion.sanitize_machine_paths(
                    generated, root=root, experiment=experiment
                )

            text = evidence.read_text(encoding="utf-8")
            self.assertNotIn("copilot-worktrees", text)
            self.assertNotIn(str(user), text)
            self.assertNotIn("SOMEON~1", text)
            self.assertIn("<skill-repository>", text)
            self.assertIn("<local-user>", text)
            self.assertNotIn(b"\r\n", evidence.read_bytes())

    def test_sanitize_rejects_residual_ci_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            experiment = root / ".experiments" / promotion.EXPERIMENT_ID
            generated = experiment / "generated"
            generated.mkdir(parents=True)
            (generated / "leak.txt").write_text(
                "D:\\a\\experiment-loop-skill\\generated\\viewer.html\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                promotion.PromotionError, "paths remain"
            ):
                promotion.sanitize_machine_paths(
                    generated, root=root, experiment=experiment
                )

    def test_sanitize_rejects_unexpected_binary_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            experiment = root / ".experiments" / promotion.EXPERIMENT_ID
            generated = experiment / "generated"
            generated.mkdir(parents=True)
            (generated / "unexpected.pyc").write_bytes(b"\xff\xfe\x00\x00")

            with self.assertRaisesRegex(
                promotion.PromotionError, "unexpected.pyc"
            ):
                promotion.sanitize_machine_paths(
                    generated, root=root, experiment=experiment
                )

    def test_promote_refuses_to_replace_existing_example(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "examples" / promotion.EXPERIMENT_ID
            target.mkdir(parents=True)

            with self.assertRaisesRegex(
                promotion.PromotionError, "already exists"
            ):
                promotion.promote(
                    root=root,
                    experiment=root
                    / ".experiments"
                    / promotion.EXPERIMENT_ID,
                    target=target,
                    orchestrator_model="test",
                    cli_version="test",
                )


if __name__ == "__main__":
    unittest.main()
