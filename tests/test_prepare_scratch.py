from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.prepare_scratch import (
    SCRATCH_GITIGNORE,
    contains_windows_short_path,
    expand_windows_long_path,
    prepare_experiment_scratch,
)


ROOT = Path(__file__).resolve().parents[1]


class PrepareScratchTests(unittest.TestCase):
    def test_detects_only_83_style_components(self) -> None:
        self.assertTrue(
            contains_windows_short_path(
                r"C:\Users\CHRISA~1\AppData\Local\Temp\scratch"
            )
        )
        self.assertTrue(contains_windows_short_path(r"C:\PROGRA~1\tool"))
        self.assertFalse(contains_windows_short_path(r"C:\Users\chris~archive\tool"))

    def test_expands_short_component_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            short_path = root / "CHRISA~1" / "scratch"
            short_path.mkdir(parents=True)
            long_path = Path(r"C:\Users\Christopher\scratch")

            result = expand_windows_long_path(
                short_path,
                windows=True,
                resolver=lambda _: long_path,
            )

            self.assertEqual(long_path, result)

    def test_rejects_unexpanded_short_component(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            short_path = Path(temp_dir) / "CHRISA~1"
            short_path.mkdir()
            with self.assertRaisesRegex(
                RuntimeError, "retained an 8.3 component"
            ):
                expand_windows_long_path(
                    short_path,
                    windows=True,
                    resolver=lambda path: path,
                )

    def test_prepares_gitignored_experiment_local_scratch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            generated_root = Path(temp_dir) / "generated"

            scratch_root = prepare_experiment_scratch(generated_root)

            self.assertEqual(("harness", "scratch"), scratch_root.parts[-2:])
            self.assertFalse(contains_windows_short_path(scratch_root))
            self.assertEqual(
                SCRATCH_GITIGNORE,
                (scratch_root / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_both_installers_ship_helper_to_setup_skill(self) -> None:
        for installer in ("install.ps1", "install.sh"):
            contents = (ROOT / "scripts" / installer).read_text(encoding="utf-8")
            self.assertIn("prepare_scratch.py", contents)

    def test_both_installers_ship_feedback_contracts_to_setup_skill(self) -> None:
        for installer in ("install.ps1", "install.sh"):
            contents = (ROOT / "scripts" / installer).read_text(encoding="utf-8")
            self.assertIn("human-feedback-intake-schema-v1.0.json", contents)
            self.assertIn("human-feedback-disposition-schema-v1.0.json", contents)


if __name__ == "__main__":
    unittest.main()
