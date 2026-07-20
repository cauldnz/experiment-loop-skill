from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from references.evidence_gate import validate_experiment

from ._copilot import CopilotCliRunner, PromptRunner
from ._provenance import (
    SKILL_INPUTS,
    apply_provenance,
    copilot_version,
    expected_provenance,
)


@dataclass(frozen=True)
class ExampleResult:
    name: str
    status: str
    message: str
    staged_generated: Path | None = None


@dataclass(frozen=True)
class RegenerationResult:
    status: str
    examples: tuple[ExampleResult, ...]

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def _sanitize_generated_paths(
    generated: Path, *, root: Path, workspace: Path, batch_root: Path
) -> None:
    replacements = {
        str(workspace): "<experiment-workspace>",
        workspace.as_posix(): "<experiment-workspace>",
        str(batch_root): "<regeneration-root>",
        batch_root.as_posix(): "<regeneration-root>",
        str(root): "<skill-repository>",
        root.as_posix(): "<skill-repository>",
    }
    for path in generated.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        sanitized = text
        for value, placeholder in replacements.items():
            sanitized = sanitized.replace(value, placeholder)
        if sanitized != text:
            path.write_text(sanitized, encoding="utf-8", newline="\n")


def _refresh_artifact_hashes(manifest_path: Path) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    groups = [data.get("artifacts", [])]
    groups.extend(
        iteration.get("artifacts", [])
        for iteration in data.get("iterations", [])
        if isinstance(iteration, dict)
    )
    root = manifest_path.parent.resolve()
    for group in groups:
        if not isinstance(group, list):
            continue
        for artifact in group:
            if not isinstance(artifact, dict):
                continue
            value = artifact.get("path")
            if not isinstance(value, str):
                continue
            path = (root / value).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if path.is_file():
                artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _copy_skill(root: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in SKILL_INPUTS:
        source = root / name
        target = destination / name
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "node_modules", ".DS_Store"
                ),
            )
        elif source.exists():
            shutil.copy2(source, target)


def _initialize_workspace(root: Path, prompt: Path, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )
    shutil.copy2(prompt, workspace / "prompt.md")
    skill_root = workspace / ".github" / "skills" / "experiment-loop"
    _copy_skill(root, skill_root)
    generated = workspace / "generated"
    generated.mkdir()
    shutil.copy2(
        root / "templates" / "build-viewer-adapter.py",
        generated / "build_viewer.py",
    )
    return skill_root


def _execution_prompt(
    prompt_text: str, provenance: dict[str, object]
) -> str:
    return (
        f"{prompt_text.rstrip()}\n\n"
        "Regeneration contract:\n"
        "- Use the project-local experiment-loop skill.\n"
        "- Write the entire experiment result under generated/ and nowhere else.\n"
        "- Do not modify prompt.md or .github/.\n"
        "- Produce Manifest schema v1.1 with structured Problem framing, exact original "
        "Prompt evidence, at least two Loops, `parent_ids` lineage, scorecard semantics, "
        "Artifact presentation metadata, authored milestones, and evidence-linked "
        "Champion reasons and caveats.\n"
        "- Record actual model IDs for every generator, judge, and synthesis role, and "
        "the complete prompt/input-feedback/judge-feedback/next-prompt chain for every Loop.\n"
        "- Produce generated/example-readme.md for the Example folder. It must explain "
        "the Experiment, topology, judging approach, how to inspect/rerun it, and include "
        "a `## Feature surface demonstrated` section naming the Viewer and Manifest "
        "capabilities this Example teaches.\n"
        "- Use generated/build_viewer.py and the shared Viewer renderer; customize only "
        "its ViewerProfile when a curated extra panel is needed.\n"
        "- Do not copy or infer any prior Generated Example; none is available.\n"
        "- The outer regeneration workflow will run navigation judging and the Evidence Gate.\n"
        "- If topology or model roles are ambiguous, do not guess. Respond exactly "
        "`CLARIFICATION REQUIRED: <question>` and leave generated/ incomplete.\n\n"
        "The regeneration workflow will set these authoritative generation fields after the run:\n"
        f"{json.dumps(provenance, indent=2, sort_keys=True)}\n"
    )


def _run_navigation(root: Path, generated: Path) -> tuple[bool, str]:
    package = root / "references" / "navigation_judge"
    result = subprocess.run(
        [
            "node",
            str(package / "cli.mjs"),
            "--viewer",
            str(generated / "viewer.html"),
            "--out",
            str(generated),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def _render_viewer(root: Path, generated: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["EXPERIMENT_LOOP_SKILL_ROOT"] = str(root)
    result = subprocess.run(
        [
            sys.executable,
            str(generated / "build_viewer.py"),
            "--data",
            str(generated),
            "--out",
            str(generated / "viewer.html"),
        ],
        cwd=generated,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def _regenerate_one(
    *,
    root: Path,
    prompt: Path,
    batch_root: Path,
    runner: PromptRunner,
    orchestrator_model: str,
    cli_version: str,
) -> ExampleResult:
    name = prompt.parent.name
    workspace = batch_root / name / "workspace"
    skill_root = _initialize_workspace(root, prompt, workspace)
    provenance = expected_provenance(
        root,
        prompt,
        orchestrator_model=orchestrator_model,
        cli_version=cli_version,
    )
    result = runner.run(
        workspace=workspace,
        prompt=_execution_prompt(
            prompt.read_text(encoding="utf-8"), provenance
        ),
        orchestrator_model=orchestrator_model,
        skill_root=skill_root,
    )
    (workspace / "copilot-output.txt").write_text(
        result.output, encoding="utf-8", newline="\n"
    )
    if "CLARIFICATION REQUIRED:" in result.output:
        clarification = result.output.split("CLARIFICATION REQUIRED:", 1)[1].strip()
        return ExampleResult(name, "fail", f"clarification required: {clarification}")
    if result.returncode != 0:
        return ExampleResult(
            name, "fail", f"Copilot CLI exited {result.returncode}: {result.output[-1000:]}"
        )

    generated = workspace / "generated"
    manifest_path = generated / "manifest.json"
    if not manifest_path.exists():
        return ExampleResult(name, "fail", "Copilot did not produce generated/manifest.json")
    example_readme = generated / "example-readme.md"
    if not example_readme.exists():
        return ExampleResult(name, "fail", "Copilot did not produce generated/example-readme.md")
    if "## Feature surface demonstrated" not in example_readme.read_text(
        encoding="utf-8"
    ):
        return ExampleResult(
            name,
            "fail",
            "generated/example-readme.md is missing `## Feature surface demonstrated`",
        )
    _sanitize_generated_paths(
        generated, root=root, workspace=workspace, batch_root=batch_root
    )
    try:
        apply_provenance(manifest_path, provenance)
        _refresh_artifact_hashes(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return ExampleResult(name, "fail", f"could not apply provenance: {exc}")

    if not (generated / "build_viewer.py").exists():
        return ExampleResult(name, "fail", "generated/build_viewer.py is missing")
    rendered, render_output = _render_viewer(root, generated)
    if not rendered:
        return ExampleResult(name, "fail", f"Viewer build failed: {render_output}")

    navigated, navigation_output = _run_navigation(root, generated)
    if not navigated:
        return ExampleResult(
            name, "fail", f"navigation judge failed: {navigation_output[-1500:]}"
        )

    gate = validate_experiment(generated)
    (generated / "evidence-gate.json").write_text(
        json.dumps(gate.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not gate.passed:
        failures = [
            f"{check.name}: {check.status} {check.detail}"
            for check in gate.checks
            if check.status != "pass"
        ]
        return ExampleResult(name, "fail", "; ".join(failures))
    return ExampleResult(name, "pass", "generated and gated", generated)


def _promote(root: Path, results: tuple[ExampleResult, ...]) -> None:
    transaction = uuid.uuid4().hex
    backups: list[tuple[Path, Path]] = []
    readme_backups: list[tuple[Path, Path]] = []
    created_readmes: list[Path] = []
    attempted: list[Path] = []
    try:
        for result in results:
            if not result.staged_generated:
                raise RuntimeError(f"{result.name} has no staged Generated Example")
            target = root / "examples" / result.name / "generated"
            backup = target.with_name(f".generated-backup-{transaction}")
            if target.exists():
                target.rename(backup)
                backups.append((target, backup))
            readme = target.parent / "README.md"
            readme_backup = target.parent / f".README-backup-{transaction}.md"
            if readme.exists():
                shutil.copy2(readme, readme_backup)
                readme_backups.append((readme, readme_backup))
            else:
                created_readmes.append(readme)
            attempted.append(target)
            shutil.copytree(result.staged_generated, target)
            staged_readme = target / "example-readme.md"
            shutil.copy2(staged_readme, readme)
            staged_readme.unlink()
    except (OSError, RuntimeError):
        for target in reversed(attempted):
            shutil.rmtree(target, ignore_errors=True)
        for target, backup in reversed(backups):
            if backup.exists():
                backup.rename(target)
        for readme, backup in reversed(readme_backups):
            if backup.exists():
                shutil.copy2(backup, readme)
        for readme in created_readmes:
            readme.unlink(missing_ok=True)
        raise
    finally:
        for _, backup in backups:
            shutil.rmtree(backup, ignore_errors=True)
        for _, backup in readme_backups:
            backup.unlink(missing_ok=True)


def regenerate_examples(
    repo_root: Path | str,
    *,
    names: tuple[str, ...] = (),
    jobs: int = 1,
    orchestrator_model: str = "gpt-5.6-sol",
    runner: PromptRunner | None = None,
) -> RegenerationResult:
    root = Path(repo_root).resolve()
    prompts = sorted((root / "examples").glob("*/prompt.md"))
    if names:
        selected = set(names)
        prompts = [prompt for prompt in prompts if prompt.parent.name in selected]
        missing = sorted(selected - {prompt.parent.name for prompt in prompts})
        if missing:
            return RegenerationResult(
                "fail",
                tuple(
                    ExampleResult(name, "fail", "Example Prompt not found")
                    for name in missing
                ),
            )
    if not prompts:
        return RegenerationResult("fail", ())
    if jobs < 1:
        raise ValueError("jobs must be at least 1")

    active_runner = runner or CopilotCliRunner()
    cli_version = copilot_version()
    with tempfile.TemporaryDirectory(
        prefix=".regeneration-", dir=root
    ) as temp_dir:
        batch_root = Path(temp_dir)
        futures: dict[Future[ExampleResult], str] = {}
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            for prompt in prompts:
                future = executor.submit(
                    _regenerate_one,
                    root=root,
                    prompt=prompt,
                    batch_root=batch_root,
                    runner=active_runner,
                    orchestrator_model=orchestrator_model,
                    cli_version=cli_version,
                )
                futures[future] = prompt.parent.name
            results = tuple(
                sorted(
                    (future.result() for future in as_completed(futures)),
                    key=lambda result: result.name,
                )
            )
        if any(result.status != "pass" for result in results):
            return RegenerationResult("fail", results)
        _promote(root, results)
        return RegenerationResult("pass", results)
