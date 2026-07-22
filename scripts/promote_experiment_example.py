#!/usr/bin/env python3
"""Promote one already-gated Experiment snapshot into a maintained Example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from references.evidence_gate import validate_experiment
from scripts.example_regeneration._provenance import (
    apply_provenance,
    copilot_version,
    expected_provenance,
)
from scripts.example_regeneration._workflow import (
    _refresh_artifact_hashes,
    _render_viewer,
    _run_navigation,
    _sanitize_generated_paths,
)

EXPERIMENT_ID = "accessible-mobile-checkout"
EXPECTED_BRIEF_SHA256 = (
    "ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13"
)
EXPECTED_PROMPT_SHA256 = (
    "86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928"
)
MACHINE_PATH_PATTERN = re.compile(
    r"(?i)(?:(?<![A-Za-z0-9])[A-Z](?::|%3A)[\\/]"
    r"|(?<![A-Za-z0-9:])/(?:home|Users|root|private/tmp|tmp)/)"
)
MACHINE_PATH_BYTES_PATTERN = re.compile(
    rb"(?i)(?:(?<![A-Za-z0-9])[A-Z](?::|%3A)[\\/]"
    rb"|(?<![A-Za-z0-9:])/(?:home|Users|root|private/tmp|tmp)/)"
)
PUBLISHED_BINARY_SUFFIXES = frozenset({".png"})

EXAMPLE_PROMPT = """# Accessibility-first mobile checkout Experiment

Use the project-local `experiment-loop` skill to reproduce a self-contained,
synthetic general-retail mobile checkout Experiment. Create three genuinely
distinct accessibility-first UI Tracks:

1. a landmarked single-page checkout,
2. a resumable multi-step wizard, and
3. a task-card or accordion flow.

Run two Loops per Track and two evidence-driven synthesis Loops. Preserve every
failed or rejected Loop. Use only fictional products, people, addresses, payment
details, and transactions. Do not deploy, collect telemetry, use credentials,
contact external users, or make network requests.

Gate every candidate objectively in a mobile Chromium viewport for content
fidelity, semantic accessibility and contrast, keyboard completion,
validation/error recovery, mobile and touch compatibility, interruption and
duplicate-submission resilience, reduced motion, and offline synthetic safety.
Require touch targets of at least 44 by 44 CSS pixels and complete checkout
without weakening correctness or safety. A candidate that fails an objective
gate cannot become Champion.

Independently judge accessibility and human-use friction from operated browser
evidence. Blind identities where practical, preserve raw scores and dissent,
and use flipped pairwise order for the final Champion-versus-strongest-parent
comparison. Synthesize only demonstrated strengths rather than averaging the
three approaches.

Produce Manifest v1.1 with complete lineage, prompts, feedback, commands,
models, scores, objective reports, screenshots, lessons, decisions, provenance,
and evidence-linked Champion reasoning. Build the standard deterministic,
standalone Viewer; run the Navigation Judge against the exact Viewer; rebuild
byte-identically; and run the Evidence Gate last. Treat the Evidence Gate as the
single final blocking result.

The maintained snapshot demonstrates the expected shape and rigor. A future
regeneration is a new Experiment: it must not copy or infer the checked-in
generated evidence.
"""

EXAMPLE_README = """# Accessibility-first mobile checkout

This maintained snapshot demonstrates an eight-Loop, accessibility-first mobile
checkout Experiment using entirely fictional retail data. Three distinct mobile
checkout Tracks were objectively browser-gated, independently judged, and
combined through two synthesis Loops.

Open `generated/viewer.html` directly to inspect the hill-climb, evidence,
scores, dissent, provenance, and final Champion. `generated/evidence-gate.json`
is the final blocking result; `generated/navigation-evidence.json` records
browser operation of the exact Viewer. `promotion-result.json` records the
canonical source bindings and hashes of the promoted, re-gated snapshot.

To run a new Experiment, use `prompt.md` with the project-local
`experiment-loop` skill. Regeneration creates new evidence; it does not replay
or hand-edit this snapshot.

## Feature surface demonstrated

- Manifest v1.1 lineage across parallel Tracks and multi-parent synthesis
- objective browser, task, accessibility, resilience, and offline-safety gates
- independent blind accessibility and human-use judges with preserved dissent
- flipped pairwise Champion comparison and evidence-linked winning rationale
- deterministic standalone Viewer, Navigation Evidence, and final Evidence Gate
- reboot recovery and path-scope remediation preserved as provenance
"""


class PromotionError(RuntimeError):
    """Raised when a promotion precondition or blocking gate fails."""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PromotionError(f"{path} must contain a JSON object")
    return value


def _require_sha(path: Path, expected: str) -> None:
    actual = file_sha256(path)
    if actual != expected:
        raise PromotionError(
            f"{path} SHA-256 mismatch: expected {expected}, observed {actual}"
        )


def validate_source(experiment: Path) -> dict[str, object]:
    setup = experiment / "setup"
    generated = experiment / "generated"
    brief = setup / "experiment-brief.json"
    prompt = setup / "prompt.md"
    approval = setup / "approval.json"
    required = (
        brief,
        prompt,
        approval,
        generated / "manifest.json",
        generated / "viewer.html",
        generated / "navigation-evidence.json",
        generated / "evidence-gate.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise PromotionError(f"canonical source is incomplete: {', '.join(missing)}")

    _require_sha(brief, EXPECTED_BRIEF_SHA256)
    _require_sha(prompt, EXPECTED_PROMPT_SHA256)
    approval_data = _load_object(approval)
    if approval_data.get("status") != "approved":
        raise PromotionError("canonical setup approval is not approved")
    if approval_data.get("brief_sha256") != EXPECTED_BRIEF_SHA256:
        raise PromotionError("approval does not bind the expected brief")
    if approval_data.get("prompt_sha256") != EXPECTED_PROMPT_SHA256:
        raise PromotionError("approval does not bind the expected Prompt")

    gate = _load_object(generated / "evidence-gate.json")
    if gate.get("status") != "pass":
        raise PromotionError("canonical Evidence Gate is not passing")
    navigation = _load_object(generated / "navigation-evidence.json")
    if navigation.get("status") != "pass":
        raise PromotionError("canonical Navigation Evidence is not passing")
    viewer_sha = file_sha256(generated / "viewer.html")
    if navigation.get("viewer_sha256") != viewer_sha:
        raise PromotionError("canonical Navigation Evidence is not bound to the Viewer")

    return {
        "experiment_id": EXPERIMENT_ID,
        "revision": 1,
        "brief_sha256": EXPECTED_BRIEF_SHA256,
        "prompt_sha256": EXPECTED_PROMPT_SHA256,
        "approval_sha256": file_sha256(approval),
        "source_tree_sha256": tree_sha256(generated),
        "source_manifest_sha256": file_sha256(generated / "manifest.json"),
        "source_viewer_sha256": viewer_sha,
        "source_navigation_evidence_sha256": file_sha256(
            generated / "navigation-evidence.json"
        ),
        "source_evidence_gate_sha256": file_sha256(
            generated / "evidence-gate.json"
        ),
        "source_navigation_status": "pass",
        "source_evidence_gate_status": "pass",
        "procedural_caveat": (
            "The canonical run includes preserved path-scope-remediation and "
            "reboot-recovery provenance. Promotion copied the gated functional "
            "outputs and did not rerun a model Experiment."
        ),
    }


def _png_text_metadata(path: Path) -> bytes:
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise PromotionError(f"{path} is not a valid PNG")
    offset = 8
    metadata: list[bytes] = []
    while offset + 12 <= len(payload):
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        if end + 4 > len(payload):
            raise PromotionError(f"{path} has a truncated PNG chunk")
        chunk = payload[start:end]
        if chunk_type == b"tEXt":
            metadata.append(chunk)
        elif chunk_type == b"zTXt":
            parts = chunk.split(b"\0", 2)
            if len(parts) == 3 and parts[1] == b"":
                metadata.append(parts[0] + b"\0" + zlib.decompress(parts[2]))
        elif chunk_type == b"iTXt":
            keyword_end = chunk.find(b"\0")
            if keyword_end >= 0 and keyword_end + 3 <= len(chunk):
                flag = chunk[keyword_end + 1]
                fields = chunk[keyword_end + 3 :].split(b"\0", 2)
                if len(fields) == 3:
                    text = zlib.decompress(fields[2]) if flag == 1 else fields[2]
                    metadata.append(chunk[:keyword_end] + b"\0" + text)
        offset = end + 4
        if chunk_type == b"IEND":
            break
    return b"\n".join(metadata)


def sanitize_machine_paths(generated: Path, *, root: Path, experiment: Path) -> None:
    _sanitize_generated_paths(
        generated,
        root=root,
        workspace=experiment,
        batch_root=experiment.parent,
    )
    user_home = str(Path.home())
    replacements = {
        user_home: "<local-user>",
        Path(user_home).as_posix(): "<local-user>",
    }
    escaped_replacements = {
        value.replace("\\", "\\\\"): placeholder
        for value, placeholder in {
            str(root): "<skill-repository>",
            str(experiment): "<experiment-workspace>",
            str(experiment.parent): "<regeneration-root>",
            user_home: "<local-user>",
        }.items()
    }
    url_replacements = {
        value.as_posix().replace(":", "%3A", 1): placeholder
        for value, placeholder in {
            root: "<skill-repository>",
            experiment: "<experiment-workspace>",
            experiment.parent: "<regeneration-root>",
            Path(user_home): "<local-user>",
        }.items()
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
        for value, placeholder in escaped_replacements.items():
            sanitized = sanitized.replace(value, placeholder)
        for value, placeholder in url_replacements.items():
            sanitized = sanitized.replace(value, placeholder)
        sanitized = re.sub(
            r"(?i)[A-Z]:\\Users\\[^\\/\s\"']+(?=[\\/])",
            "<local-user>",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)[A-Z]:\\\\Users\\\\[^\\/\s\"']+(?=\\\\)",
            "<local-user>",
            sanitized,
        )
        path.write_text(sanitized, encoding="utf-8", newline="\n")

    leaks: list[str] = []
    for path in generated.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            if path.suffix.casefold() not in PUBLISHED_BINARY_SUFFIXES:
                leaks.append(path.relative_to(generated).as_posix())
                continue
            try:
                metadata = _png_text_metadata(path)
            except (OSError, PromotionError, zlib.error):
                leaks.append(path.relative_to(generated).as_posix())
                continue
            if MACHINE_PATH_BYTES_PATTERN.search(metadata):
                leaks.append(path.relative_to(generated).as_posix())
            continue
        if MACHINE_PATH_PATTERN.search(text):
            leaks.append(path.relative_to(generated).as_posix())
    if leaks:
        raise PromotionError(
            "machine/worktree paths remain after sanitization: " + ", ".join(leaks)
        )


def _record_promotion(
    manifest_path: Path,
    provenance_path: Path,
    source_binding: dict[str, object],
) -> None:
    manifest = _load_object(manifest_path)
    manifest["promotion"] = source_binding
    iterations = manifest.get("iterations")
    champion = manifest.get("champion")
    if not isinstance(iterations, list) or not isinstance(champion, dict):
        raise PromotionError("manifest is missing iterations or Champion")
    champion_id = champion.get("iteration_id")
    champion_iteration = next(
        (
            item
            for item in iterations
            if isinstance(item, dict) and item.get("id") == champion_id
        ),
        None,
    )
    if champion_iteration is None:
        raise PromotionError("manifest Champion iteration does not exist")
    artifacts = champion_iteration.get("artifacts")
    if not isinstance(artifacts, list):
        raise PromotionError("Champion iteration artifacts are invalid")
    artifact_id = "promotion-provenance"
    if not any(
        isinstance(item, dict) and item.get("id") == artifact_id
        for item in artifacts
    ):
        artifacts.append(
            {
                "id": artifact_id,
                "kind": "json",
                "role": "provenance",
                "label": "Maintained Example promotion provenance",
                "path": "promotion-provenance.json",
                "sha256": file_sha256(provenance_path),
                "presentation": {
                    "mode": "text",
                    "featured": False,
                    "primary": False,
                    "caption": (
                        "Binds the maintained snapshot to its approved canonical "
                        "source and records the no-regeneration promotion."
                    ),
                    "alt_text": "Promotion provenance JSON",
                    "comparison_key": "promotion-provenance",
                },
            }
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _build_and_gate(root: Path, generated: Path) -> dict[str, object]:
    ok, detail = _render_viewer(root, generated)
    if not ok:
        raise PromotionError(f"first Viewer rebuild failed: {detail}")
    first = (generated / "viewer.html").read_bytes()
    ok, detail = _render_viewer(root, generated)
    if not ok:
        raise PromotionError(f"second Viewer rebuild failed: {detail}")
    second = (generated / "viewer.html").read_bytes()
    if first != second:
        raise PromotionError("promoted Viewer rebuild is not byte-identical")

    ok, detail = _run_navigation(root, generated)
    if not ok:
        raise PromotionError(f"promoted Navigation Judge failed: {detail}")

    report = validate_experiment(generated)
    _write_json(generated / "evidence-gate.json", report.to_dict())
    if not report.passed:
        failed = [
            check.name
            for check in report.checks
            if check.required and check.status != "pass"
        ]
        raise PromotionError(
            "promoted Evidence Gate failed: " + ", ".join(failed)
        )
    return {
        "promoted_viewer_sha256": file_sha256(generated / "viewer.html"),
        "promoted_navigation_evidence_sha256": file_sha256(
            generated / "navigation-evidence.json"
        ),
        "promoted_evidence_gate_sha256": file_sha256(
            generated / "evidence-gate.json"
        ),
        "promoted_evidence_gate_status": "pass",
    }


def promote(
    *,
    root: Path,
    experiment: Path,
    target: Path,
    orchestrator_model: str,
    cli_version: str,
) -> dict[str, object]:
    root = root.resolve()
    experiment = experiment.resolve()
    target = target.resolve()
    if target.exists():
        raise PromotionError(f"target already exists: {target}")

    source_binding = validate_source(experiment)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{target.name}-promotion-", dir=target.parent
    ) as temporary:
        staged_example = Path(temporary) / target.name
        staged_generated = staged_example / "generated"
        staged_example.mkdir()
        shutil.copytree(
            experiment / "generated",
            staged_generated,
            ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", "*.pyo", "node_modules", ".DS_Store"
            ),
        )
        prompt = staged_example / "prompt.md"
        prompt.write_text(EXAMPLE_PROMPT, encoding="utf-8", newline="\n")
        (staged_example / "README.md").write_text(
            EXAMPLE_README, encoding="utf-8", newline="\n"
        )

        sanitize_machine_paths(
            staged_generated,
            root=root,
            experiment=experiment,
        )
        source_binding["maintained_prompt_sha256"] = file_sha256(prompt)
        source_binding["repository_provenance"] = expected_provenance(
            root,
            prompt,
            orchestrator_model=orchestrator_model,
            cli_version=cli_version,
        )
        provenance_path = staged_generated / "promotion-provenance.json"
        _write_json(provenance_path, source_binding)
        manifest_path = staged_generated / "manifest.json"
        apply_provenance(
            manifest_path,
            source_binding["repository_provenance"],
        )
        _record_promotion(manifest_path, provenance_path, source_binding)
        _refresh_artifact_hashes(manifest_path)

        result = _build_and_gate(root, staged_generated)
        result["promoted_tree_sha256"] = tree_sha256(staged_generated)
        result["source_binding"] = source_binding
        _write_json(staged_example / "promotion-result.json", result)

        final_report = validate_experiment(staged_generated)
        _write_json(staged_generated / "evidence-gate.json", final_report.to_dict())
        if not final_report.passed:
            raise PromotionError("final promoted Evidence Gate reconciliation failed")
        if (
            file_sha256(staged_generated / "evidence-gate.json")
            != result["promoted_evidence_gate_sha256"]
        ):
            raise PromotionError("final promoted Evidence Gate was not deterministic")
        os.replace(staged_example, target)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment",
        type=Path,
        default=ROOT / ".experiments" / EXPERIMENT_ID,
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=ROOT / "examples" / EXPERIMENT_ID,
    )
    parser.add_argument("--orchestrator-model", default="gpt-5.6-sol")
    parser.add_argument("--cli-version", default=copilot_version())
    args = parser.parse_args(argv)
    try:
        result = promote(
            root=ROOT,
            experiment=args.experiment,
            target=args.target,
            orchestrator_model=args.orchestrator_model,
            cli_version=args.cli_version,
        )
    except PromotionError as error:
        print(f"PROMOTION: FAIL\n{error}", file=sys.stderr)
        return 1
    print("PROMOTION: PASS")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
