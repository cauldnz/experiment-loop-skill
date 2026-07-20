from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RunnerResult:
    returncode: int
    output: str


class PromptRunner(Protocol):
    def run(
        self,
        *,
        workspace: Path,
        prompt: str,
        orchestrator_model: str,
        skill_root: Path,
    ) -> RunnerResult: ...


class CopilotCliRunner:
    @staticmethod
    def _disabled_mcp_args() -> list[str]:
        result = subprocess.run(
            ["copilot", "mcp", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"could not enumerate MCP servers: {result.stderr.strip()}"
            )
        names = re.findall(
            r"^\s{2}(.+?)\s+\((?:local|http)\)\s*$",
            result.stdout,
            flags=re.MULTILINE,
        )
        return [
            argument
            for name in names
            for argument in ("--disable-mcp-server", name)
        ]

    def run(
        self,
        *,
        workspace: Path,
        prompt: str,
        orchestrator_model: str,
        skill_root: Path,
    ) -> RunnerResult:
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{skill_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(skill_root)
        )
        env["EXPERIMENT_LOOP_SKILL_ROOT"] = str(skill_root)
        command = [
            "copilot",
            "-C",
            str(workspace),
            "--prompt",
            prompt,
            "--model",
            orchestrator_model,
            "--mode",
            "autopilot",
            "--max-autopilot-continues",
            "15",
            "--allow-all-tools",
            "--disable-builtin-mcps",
            *self._disabled_mcp_args(),
            "--no-auto-update",
            "--no-remote",
            "--no-remote-export",
            "--output-format",
            "text",
        ]
        result = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        return RunnerResult(result.returncode, output)
