from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

from scripts import install_dependencies


class InstallDependenciesTests(unittest.TestCase):
    def test_windows_uses_cmd_shims(self) -> None:
        completed = SimpleNamespace(returncode=0)
        with (
            patch.object(install_dependencies.os, "name", "nt"),
            patch.object(
                install_dependencies.shutil,
                "which",
                side_effect=["C:\\tools\\npm.cmd", "C:\\tools\\npx.cmd"],
            ) as which,
            patch.object(
                install_dependencies.subprocess,
                "run",
                return_value=completed,
            ) as run,
        ):
            self.assertEqual(0, install_dependencies.main([]))

        self.assertEqual([call("npm.cmd"), call("npx.cmd")], which.call_args_list)
        commands = [invocation.args[0] for invocation in run.call_args_list]
        self.assertEqual("C:\\tools\\npm.cmd", commands[1][0])
        self.assertEqual("C:\\tools\\npx.cmd", commands[2][0])


if __name__ == "__main__":
    unittest.main()
