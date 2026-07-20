from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.example_regeneration._workflow import (
    ExampleResult,
    _promote,
    _refresh_artifact_hashes,
    _sanitize_generated_paths,
)


class ExampleRegenerationTests(unittest.TestCase):
    def test_rollback_removes_partial_target_before_restoring_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            example = root / "examples" / "sample"
            target = example / "generated"
            target.mkdir(parents=True)
            (target / "old.txt").write_text("old", encoding="utf-8")
            (example / "README.md").write_text("old readme", encoding="utf-8")
            staged = root / "staged"
            staged.mkdir()
            (staged / "example-readme.md").write_text(
                "new readme", encoding="utf-8"
            )

            def partial_copy(_source: Path, destination: Path) -> None:
                destination.mkdir()
                (destination / "partial.txt").write_text(
                    "partial", encoding="utf-8"
                )
                raise OSError("simulated copy failure")

            result = ExampleResult("sample", "pass", "ok", staged)
            with patch(
                "scripts.example_regeneration._workflow.shutil.copytree",
                side_effect=partial_copy,
            ):
                with self.assertRaises(OSError):
                    _promote(root, (result,))

            self.assertEqual("old", (target / "old.txt").read_text(encoding="utf-8"))
            self.assertFalse((target / "partial.txt").exists())
            self.assertEqual(
                "old readme", (example / "README.md").read_text(encoding="utf-8")
            )
            self.assertFalse(any(example.glob(".generated-backup-*")))
            self.assertFalse(any(example.glob(".README-backup-*")))

    def test_sanitization_refreshes_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / "repo"
            workspace = base / "batch" / "sample" / "workspace"
            generated = workspace / "generated"
            generated.mkdir(parents=True)
            artifact = generated / "result.txt"
            artifact.write_text(f"built in {workspace}", encoding="utf-8")
            manifest_path = generated / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "iterations": [
                            {
                                "artifacts": [
                                    {
                                        "path": "result.txt",
                                        "sha256": "0" * 64,
                                    }
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _sanitize_generated_paths(
                generated,
                root=root,
                workspace=workspace,
                batch_root=base / "batch",
            )
            _refresh_artifact_hashes(manifest_path)

            self.assertEqual(
                "built in <experiment-workspace>",
                artifact.read_text(encoding="utf-8"),
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
                manifest["iterations"][0]["artifacts"][0]["sha256"],
            )

    def test_rollback_removes_new_readme(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_example = root / "examples" / "first"
            first_staged = root / "first-staged"
            first_staged.mkdir(parents=True)
            (first_staged / "example-readme.md").write_text(
                "new readme", encoding="utf-8"
            )
            (first_staged / "artifact.txt").write_text("ok", encoding="utf-8")
            second_staged = root / "second-staged"
            second_staged.mkdir()
            (second_staged / "example-readme.md").write_text(
                "second readme", encoding="utf-8"
            )
            real_copytree = __import__("shutil").copytree
            calls = 0

            def fail_second_copy(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated second promotion failure")
                real_copytree(source, destination)

            results = (
                ExampleResult("first", "pass", "ok", first_staged),
                ExampleResult("second", "pass", "ok", second_staged),
            )
            with patch(
                "scripts.example_regeneration._workflow.shutil.copytree",
                side_effect=fail_second_copy,
            ):
                with self.assertRaises(OSError):
                    _promote(root, results)

            self.assertFalse((first_example / "README.md").exists())
            self.assertFalse((first_example / "generated").exists())


if __name__ == "__main__":
    unittest.main()
