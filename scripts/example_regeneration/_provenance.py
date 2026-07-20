from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


SKILL_INPUTS = (
    "SKILL.md",
    "CONTEXT.md",
    "references",
    "templates",
    "requirements.txt",
    "docs",
)
IGNORED_NAMES = {"__pycache__", "node_modules", ".DS_Store"}


def files_for_hash(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in SKILL_INPUTS:
        source = root / name
        if source.is_file():
            files.append(source)
        elif source.is_dir():
            files.extend(
                path
                for path in source.rglob("*")
                if path.is_file()
                and not any(part in IGNORED_NAMES for part in path.parts)
                and path.suffix not in {".pyc", ".pyo"}
            )
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in files_for_hash(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def copilot_version() -> str:
    result = subprocess.run(
        ["copilot", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"copilot --version failed: {result.stderr.strip()}")
    return result.stdout.strip()


def expected_provenance(
    root: Path, prompt: Path, *, orchestrator_model: str, cli_version: str
) -> dict[str, object]:
    return {
        "skill_commit": git_commit(root),
        "skill_tree_sha256": tree_sha256(root),
        "prompt_sha256": file_sha256(prompt),
        "copilot_cli_version": cli_version,
        "orchestrator_model": orchestrator_model,
    }


def apply_provenance(
    manifest_path: Path, provenance: dict[str, object]
) -> dict[str, object]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    generation = data.get("generation")
    if not isinstance(generation, dict):
        generation = {}
        data["generation"] = generation
    models = generation.get("models")
    if not isinstance(models, list):
        models = []
    orchestrator_model = str(provenance["orchestrator_model"])
    if not any(
        isinstance(model, dict)
        and model.get("role") == "orchestrator"
        and model.get("model_id") == orchestrator_model
        for model in models
    ):
        models.insert(
            0, {"role": "orchestrator", "model_id": orchestrator_model}
        )
    generation.update(provenance)
    generation["models"] = models
    manifest_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return data
