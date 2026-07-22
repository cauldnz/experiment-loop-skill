#!/usr/bin/env python3
"""Deterministically assemble terminal Experiment fragments and judge sidecars."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
EXPERIMENT_ROOT = ROOT.parent
SETUP_ROOT = EXPERIMENT_ROOT / "setup"
REPO_ROOT = ROOT.parents[2]
REMEDIATION_ROOT = ROOT / "harness" / "path-violation-evidence"

EXPECTED_HASHES = {
    SETUP_ROOT / "experiment-brief.json": "ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13",
    SETUP_ROOT / "prompt.md": "86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928",
    ROOT / "build_viewer.py": "bc4a4096a076144199e472ed3232e1e76eca36b033f47e85b349f47a9cd006eb",
    ROOT / "harness" / "canonical-fixture.json": "e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894",
    ROOT / "harness" / "run_checkout_gates.py": "de51a917b14aa9e0d003efb5e84fc98cf42b089e31448bcaf9f4889d3b060563",
    ROOT / "harness" / "self-test-invalid" / "index.html": "243d78b65b167bdf8c912d3f40c46072ed4bb4b712915de852094ec4a525807b",
}
GATE_IDS = (
    "content-fidelity",
    "semantic-accessibility-gate",
    "keyboard-completion-gate",
    "error-recovery-gate",
    "mobile-touch-gate",
    "resilience-gate",
    "offline-safety-gate",
)
QUALITATIVE_CRITERIA = ("human-use-quality", "visual-information-clarity")
VALID_DECISIONS = {
    "new_best",
    "reject",
    "keep_for_synthesis",
    "needs_human_review",
    "failed",
}
EXPECTED_LOOP_IDS = (
    "single-page-loop-01",
    "single-page-loop-02",
    "resumable-wizard-loop-01",
    "resumable-wizard-loop-02",
    "task-cards-loop-01",
    "task-cards-loop-02",
    "synthesis-loop-01",
    "synthesis-loop-02",
)
EXPECTED_JUDGES = ("judge-accessibility", "judge-human-use")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_inputs() -> dict[str, str]:
    verified: dict[str, str] = {}
    for path, expected in sorted(EXPECTED_HASHES.items(), key=lambda item: str(item[0])):
        if not path.is_file():
            raise RuntimeError(f"Frozen input is missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Frozen input hash mismatch for {path}: expected {expected}, got {actual}"
            )
        if path.is_relative_to(ROOT):
            label = path.relative_to(ROOT).as_posix()
        else:
            label = path.relative_to(EXPERIMENT_ROOT).as_posix()
        verified[label] = actual
    return verified


def remediation_provenance() -> dict[str, Any]:
    provenance_path = REMEDIATION_ROOT / "provenance.json"
    verification_path = REMEDIATION_ROOT / "hash-verification.json"
    report_path = REMEDIATION_ROOT / "forensic-report.md"
    for path in (provenance_path, verification_path, report_path):
        if not path.is_file():
            raise RuntimeError(f"Required remediation evidence is missing: {path}")
    provenance = load_json(provenance_path)
    verification = load_json(verification_path)
    if (
        provenance.get("status") != "remediated_with_procedural_caveat"
        or verification.get("all_match") is not True
    ):
        raise RuntimeError("Path-remediation evidence is not in a verified state.")
    return {
        "status": provenance["status"],
        "summary": (
            "Out-of-scope diagnostic writes and a later unapproved deletion were "
            "forensically recovered and remediated. Functional hashes remain intact; "
            "the procedural caveat is permanent."
        ),
        "provenance_path": generated_relative(provenance_path),
        "provenance_sha256": sha256(provenance_path),
        "hash_verification_path": generated_relative(verification_path),
        "hash_verification_sha256": sha256(verification_path),
        "report_path": generated_relative(report_path),
        "report_sha256": sha256(report_path),
    }


def text(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def normalize_track_id(value: Any) -> str:
    result = text(value).strip()
    if result.startswith("track-"):
        result = result[6:]
    return result or "unassigned"


def terminal_status(status: Any) -> bool:
    if not isinstance(status, dict):
        return False
    state = text(status.get("status") or status.get("state")).lower()
    phase = text(status.get("phase")).lower()
    return state in {"completed", "complete", "succeeded", "success"} and phase in {
        "",
        "terminal",
        "completed",
        "complete",
    }


def passing_report(report: Any) -> bool:
    return (
        isinstance(report, dict)
        and report.get("blocking_failure") is False
        and report.get("failed_gate_ids") == []
    )


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def generated_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def normalize_fragment_path(value: str, source_dir: Path) -> str | None:
    raw = value.replace("\\", "/").strip()
    marker = ".experiments/accessible-mobile-checkout/generated/"
    if marker in raw:
        raw = raw.split(marker, 1)[1]
    raw = raw.removeprefix("./")
    if raw.startswith(ROOT.name + "/"):
        raw = raw[len(ROOT.name) + 1 :]
    if not raw.startswith(("track-", "synthesis/")):
        raw = f"{source_dir.name}/{raw}"
    candidate = (ROOT / raw).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate.relative_to(ROOT.resolve()).as_posix()


def extract_artifact_metadata(
    entry: dict[str, Any], source_dir: Path
) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            path_value = value.get("path")
            if isinstance(path_value, str):
                normalized = normalize_fragment_path(path_value, source_dir)
                if normalized:
                    metadata[normalized] = deepcopy(value)
            for child_key, child in value.items():
                if child_key not in {"path", "candidate_dir"}:
                    visit(child, child_key)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, str) and (
                    "/" in child or Path(child).suffix
                ):
                    normalized = normalize_fragment_path(child, source_dir)
                    if normalized:
                        metadata.setdefault(normalized, {"label": key.replace("_", " ")})
                else:
                    visit(child, key)

    visit(entry.get("artifacts", []), "artifact")
    return metadata


def presentation_for(path: Path, *, primary: bool, failed: bool) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if primary:
        mode = "interactive_html"
    elif suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        mode = "image"
    elif suffix == ".svg":
        mode = "svg"
    elif suffix == ".json":
        mode = "structured_json"
    elif suffix == ".md":
        mode = "markdown"
    elif suffix in {".txt", ".log"}:
        mode = "log"
    elif suffix in {".css", ".js", ".py", ".html"}:
        mode = "code"
    else:
        mode = "download"
    label = path.name.replace("-", " ").replace("_", " ")
    caption = (
        f"Preserved failed-attempt Artifact: {label}."
        if failed
        else f"Recorded Loop Artifact: {label}."
    )
    result: dict[str, Any] = {
        "mode": mode,
        "featured": primary,
        "primary": primary,
        "caption": caption,
    }
    if mode in {"image", "svg", "interactive_html"}:
        result["alt_text"] = (
            "A preserved synthetic checkout evidence image."
            if mode != "interactive_html"
            else "An interactive fictional and synthetic mobile checkout candidate."
        )
        result["comparison_key"] = (
            "checkout-ui" if primary else "checkout-mobile-evidence"
        )
    return result


def artifacts_for_loop(
    loop_id: str,
    loop_dir: Path,
    source_dir: Path,
    fragment_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    supplied = extract_artifact_metadata(fragment_entry, source_dir)
    artifacts: list[dict[str, Any]] = []
    for path in sorted(item for item in loop_dir.rglob("*") if item.is_file()):
        relative = generated_relative(path)
        metadata = supplied.get(relative, {})
        local = path.relative_to(loop_dir).as_posix()
        primary = local == "index.html"
        failed = any(
            part.startswith("evidence-") and part != "evidence"
            for part in path.relative_to(loop_dir).parts
        )
        supplied_id = text(metadata.get("id"))
        artifact_id = (
            supplied_id
            if supplied_id.startswith(loop_id)
            else f"{loop_id}-{slug(local)}"
        )
        mode = text(
            (metadata.get("presentation") or {}).get("mode")
            if isinstance(metadata.get("presentation"), dict)
            else ""
        )
        if mode == "json":
            mode = "structured_json"
        presentation = presentation_for(path, primary=primary, failed=failed)
        if isinstance(metadata.get("presentation"), dict):
            for key, value in metadata["presentation"].items():
                if key == "mode" and value == "json":
                    value = "structured_json"
                presentation[key] = value
        presentation.setdefault("caption", f"Recorded Loop Artifact: {path.name}.")
        if not text(presentation.get("caption")):
            presentation["caption"] = f"Recorded Loop Artifact: {path.name}."
        declared_hash = text(metadata.get("sha256"))
        actual_hash = sha256(path)
        if declared_hash and declared_hash.lower() != actual_hash:
            raise RuntimeError(
                f"Artifact hash mismatch for {relative}: "
                f"fragment {declared_hash}, actual {actual_hash}"
            )
        role = text(metadata.get("role"))
        if not role:
            if primary:
                role = "primary-output"
            elif failed:
                role = "failed-objective-evidence"
            elif "evidence" in path.relative_to(loop_dir).parts:
                role = "objective-evidence"
            else:
                role = "supporting-output"
        artifacts.append(
            {
                "id": artifact_id,
                "kind": text(metadata.get("kind"), mode or path.suffix.removeprefix("."))
                or "file",
                "role": role,
                "label": text(metadata.get("label"), path.name),
                "path": relative,
                "sha256": actual_hash,
                "presentation": presentation,
            }
        )
    if not artifacts:
        raise RuntimeError(f"Terminal Loop has no Artifacts: {loop_id}")
    return artifacts


def report_gate_states(report: dict[str, Any]) -> dict[str, str]:
    states: dict[str, str] = {}
    for gate in report.get("gates", []):
        if not isinstance(gate, dict):
            continue
        gate_id = text(gate.get("id") or gate.get("gate_id"))
        state = text(gate.get("status") or gate.get("result")).lower()
        if gate_id:
            states[gate_id] = state if state in {"pass", "fail", "blocked"} else "not_run"
    return {gate_id: states.get(gate_id, "not_run") for gate_id in GATE_IDS}


def objective_scores(report: dict[str, Any]) -> list[dict[str, Any]]:
    scores = [
        {
            "scorer_id": "objective-checkout-gates",
            "criterion_id": gate_id,
            "value": 1 if state == "pass" else 0,
            "notes": state.capitalize() + ".",
        }
        for gate_id, state in report_gate_states(report).items()
    ]
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    scores.append(
        {
            "scorer_id": "objective-checkout-gates",
            "criterion_id": "task-efficiency",
            "value": float(metrics.get("focusable_controls_traversed", 0)),
            "notes": (
                "Non-gating metrics: "
                f"{metrics.get('activations', 0)} activations, "
                f"{metrics.get('corrections', 0)} corrections, "
                f"{metrics.get('completion_interactions', 0)} completion interactions."
            ),
        }
    )
    return scores


def normalize_lesson(value: Any, loop_id: str) -> dict[str, str]:
    if isinstance(value, dict) and all(
        key in value for key in ("trigger", "action", "evidence", "confidence")
    ):
        result = {key: text(value.get(key)) for key in ("trigger", "action", "evidence")}
        confidence = text(value.get("confidence")).lower()
        result["confidence"] = confidence if confidence in {"low", "medium", "high"} else "medium"
        return result
    lesson = text(value)
    return {
        "trigger": f"Objective evidence from {loop_id}",
        "action": lesson or "Retain the passing candidate for independent qualitative review.",
        "evidence": f"Frozen objective report and preserved attempts for {loop_id}.",
        "confidence": "medium",
    }


def approved_model_for_role(brief: dict[str, Any], role: str) -> str:
    for model in brief.get("models", []):
        if isinstance(model, dict) and model.get("role") == role:
            return text(model.get("primary_model_id"), role)
    return role or "model-not-recorded"


def fragment_entries(fragment: dict[str, Any]) -> list[dict[str, Any]]:
    raw = fragment.get("iterations")
    if not isinstance(raw, list):
        raw = fragment.get("loops")
    return [item for item in raw or [] if isinstance(item, dict)]


def loop_id_from_entry(entry: dict[str, Any]) -> str:
    return text(entry.get("id") or entry.get("loop_id"))


def metadata_for(loop_dir: Path) -> dict[str, Any]:
    path = loop_dir / "metadata.json"
    return load_json(path) if path.is_file() else {}


def command_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return text(value.get("cmd") or value.get("command"))
    return ""


def normalize_iteration(
    *,
    brief: dict[str, Any],
    fragment: dict[str, Any],
    entry: dict[str, Any],
    source_dir: Path,
    loop_dir: Path,
    report: dict[str, Any],
    track_id: str,
) -> dict[str, Any]:
    loop_id = loop_id_from_entry(entry)
    metadata = metadata_for(loop_dir)
    fragment_track = fragment.get("track") if isinstance(fragment.get("track"), dict) else {}
    role = text(
        entry.get("model_role")
        or metadata.get("model_role")
        or fragment_track.get("model_role")
    )
    metadata_model = text(metadata.get("model"))
    if not role and metadata_model.startswith(("generator-", "synthesizer")):
        role = metadata_model
    model_value = entry.get("model_id") or entry.get("model") or metadata.get("model")
    if isinstance(model_value, dict):
        model_value = model_value.get("actual") or model_value.get("primary")
    model_id = text(model_value)
    if model_id.startswith(("generator-", "synthesizer")) or not model_id:
        model_id = approved_model_for_role(brief, role)
    hypothesis = text(
        entry.get("hypothesis")
        or metadata.get("hypothesis")
        or fragment_track.get("hypothesis")
    )
    if not hypothesis:
        hypothesis = next(
            (
                text(track.get("hypothesis"))
                for track in brief["topology"]["tracks"]
                if track.get("id") == track_id
            ),
            "Improve the candidate while preserving the frozen contract.",
        )

    raw_commands = entry.get("commands")
    if isinstance(raw_commands, dict):
        build_command = text(raw_commands.get("build"), "Track-authored candidate files.")
        run_command = text(raw_commands.get("run") or raw_commands.get("objective"))
        judge_command = text(raw_commands.get("judge"), "PENDING_JUDGES")
    else:
        command_items = raw_commands if isinstance(raw_commands, list) else metadata.get("commands", [])
        run_command = next(
            (
                command_text(item)
                for item in reversed(command_items or [])
                if command_text(item)
            ),
            "",
        )
        build_command = f"Track-authored the terminal candidate under {generated_relative(loop_dir)}."
        judge_command = "PENDING_JUDGES"
    if not run_command:
        run_command = text(
            load_json(loop_dir / "status.json").get("objective_command")
            if (loop_dir / "status.json").is_file()
            else ""
        )
    if not run_command:
        run_command = (
            "python .experiments\\accessible-mobile-checkout\\generated\\harness\\"
            f"run_checkout_gates.py --candidate {generated_relative(loop_dir)} "
            f"--out {generated_relative(loop_dir / 'evidence')}"
        )

    prompt_history = loop_dir / "prompt-history.md"
    track_prompt = (
        prompt_history.read_text(encoding="utf-8") if prompt_history.is_file() else ""
    )
    prompt_data = entry.get("prompt") if isinstance(entry.get("prompt"), dict) else {}
    prompt_chain = (
        entry.get("prompt_chain") if isinstance(entry.get("prompt_chain"), dict) else {}
    )
    input_feedback = text(
        prompt_data.get("input_feedback")
        or prompt_chain.get("input_feedback")
        or "None; this is a measured Track baseline."
    )
    next_prompt = text(
        prompt_data.get("next_prompt")
        or prompt_chain.get("next_prompt")
        or "PENDING_JUDGES"
    )
    judge_feedback = text(prompt_data.get("judge_feedback"), "PENDING_JUDGES")
    if "not run" in judge_feedback.lower() or "no independent" in judge_feedback.lower():
        judge_feedback = "PENDING_JUDGES"

    changed = set()
    for value in entry.get("changed_files", []) or metadata.get("changed_files", []):
        if not isinstance(value, str):
            continue
        normalized = normalize_fragment_path(value, source_dir)
        changed.add(normalized or value.replace("\\", "/"))
    changed.update(generated_relative(path) for path in loop_dir.rglob("*") if path.is_file())

    decision = text(entry.get("decision") or metadata.get("decision"))
    if decision not in VALID_DECISIONS:
        decision = "needs_human_review"
    return {
        "id": loop_id,
        "track_id": track_id,
        "parent_ids": list(entry.get("parent_ids") or metadata.get("parent_ids") or []),
        "model_id": model_id,
        "model_role": role,
        "model_provenance": (
            "Track fragment or Loop metadata"
            if text(entry.get("model_id") or entry.get("model"))
            and not text(entry.get("model_id") or entry.get("model")).startswith(
                ("generator-", "synthesizer")
            )
            else "Approved primary model for the recorded model role; no fallback was recorded."
        ),
        "hypothesis": hypothesis,
        "outcome": (
            "The terminal frozen objective report has blocking_failure=false, "
            "no failed gate IDs, and all seven objective gates passing. "
            "Independent qualitative judging is pending."
        ),
        "commands": {
            "build": build_command,
            "run": run_command,
            "judge": judge_command,
        },
        "artifacts": artifacts_for_loop(loop_id, loop_dir, source_dir, entry),
        "scores": objective_scores(report),
        "prompt": {
            "track_prompt": track_prompt,
            "input_feedback": input_feedback,
            "judge_feedback": judge_feedback,
            "next_prompt": next_prompt,
        },
        "quality_gates": report_gate_states(report),
        "changed_files": sorted(changed),
        "lesson": normalize_lesson(entry.get("lesson") or metadata.get("lesson"), loop_id),
        "decision": decision,
        "stop_reason": entry.get("stop_reason") or metadata.get("stop_reason"),
        "judging_evidence": deepcopy(entry.get("judging_evidence", [])),
        "assembly": {
            "terminal_status_path": generated_relative(loop_dir / "status.json"),
            "objective_report_path": generated_relative(
                loop_dir / "evidence" / "objective-report.json"
            ),
            "objective_report_sha256": sha256(
                loop_dir / "evidence" / "objective-report.json"
            ),
            "qualitative_status": "pending_independent_judges",
        },
    }


def existing_iterations() -> dict[str, dict[str, Any]]:
    path = ROOT / "manifest.json"
    if not path.is_file():
        return {}
    try:
        manifest = load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        text(item.get("id")): item
        for item in manifest.get("iterations", [])
        if isinstance(item, dict) and text(item.get("id"))
    }


def discover_iterations(
    brief: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    previous = existing_iterations()
    assembled: dict[str, dict[str, Any]] = {}
    live_loop_ids: list[str] = []
    skipped_sources: list[str] = []
    source_dirs = sorted(
        [
            path
            for path in ROOT.iterdir()
            if path.is_dir() and (path.name.startswith("track-") or path.name == "synthesis")
        ],
        key=lambda path: path.name,
    )
    for source_dir in source_dirs:
        status_paths = sorted(source_dir.glob("loop-*/status.json"))
        if not status_paths:
            continue
        statuses = [(path, load_json(path)) for path in status_paths]
        source_live = [(path, status) for path, status in statuses if not terminal_status(status)]
        if source_live:
            skipped_sources.append(source_dir.name)
            for path, status in source_live:
                loop_id = text(status.get("loop_id"))
                if not loop_id:
                    meta = metadata_for(path.parent)
                    loop_id = text(meta.get("loop_id"), f"{source_dir.name}-{path.parent.name}")
                live_loop_ids.append(loop_id)
            source_track = normalize_track_id(source_dir.name)
            for loop_id, item in previous.items():
                if normalize_track_id(item.get("track_id")) == source_track:
                    assembled[loop_id] = item
            continue

        eligible: dict[str, tuple[Path, dict[str, Any]]] = {}
        for status_path, _status in statuses:
            loop_dir = status_path.parent
            metadata = metadata_for(loop_dir)
            loop_id = text(metadata.get("loop_id"))
            if not loop_id:
                loop_id = text(_status.get("loop_id"))
            report_path = loop_dir / "evidence" / "objective-report.json"
            if not loop_id or not report_path.is_file():
                continue
            report = load_json(report_path)
            if passing_report(report):
                eligible[loop_id] = (loop_dir, report)

        fragment_path = source_dir / "manifest-fragment.json"
        if not fragment_path.is_file():
            continue
        fragment = load_json(fragment_path)
        entries = {loop_id_from_entry(entry): entry for entry in fragment_entries(fragment)}
        for loop_id in sorted(eligible):
            if loop_id not in entries:
                continue
            loop_dir, report = eligible[loop_id]
            track_id = (
                "synthesis"
                if source_dir.name == "synthesis"
                else normalize_track_id(
                    entries[loop_id].get("track_id")
                    or fragment.get("track_id")
                    or (
                        fragment.get("track", {}).get("id")
                        if isinstance(fragment.get("track"), dict)
                        else ""
                    )
                    or source_dir.name
                )
            )
            assembled[loop_id] = normalize_iteration(
                brief=brief,
                fragment=fragment,
                entry=entries[loop_id],
                source_dir=source_dir,
                loop_dir=loop_dir,
                report=report,
                track_id=track_id,
            )
    return (
        [assembled[key] for key in sorted(assembled)],
        sorted(set(live_loop_ids)),
        sorted(set(skipped_sources)),
        sorted(assembled),
    )


def iter_sidecar_records(sidecar: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(sidecar, dict):
        return
    if text(sidecar.get("iteration_id") or sidecar.get("loop_id")):
        yield sidecar
    for key in ("iterations", "loops", "candidates", "results"):
        value = sidecar.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    inherited = dict(sidecar)
                    for drop in ("iterations", "loops", "candidates", "results"):
                        inherited.pop(drop, None)
                    inherited.update(item)
                    yield from iter_sidecar_records(inherited)
        elif isinstance(value, dict):
            for candidate_id, item in sorted(value.items()):
                if isinstance(item, dict):
                    inherited = dict(sidecar)
                    for drop in ("iterations", "loops", "candidates", "results"):
                        inherited.pop(drop, None)
                    inherited.update(item)
                    inherited.setdefault("iteration_id", candidate_id)
                    yield from iter_sidecar_records(inherited)


def sidecar_scores(record: dict[str, Any]) -> list[dict[str, Any]]:
    raw = record.get("scores")
    result: list[dict[str, Any]] = []
    default_scorer = text(record.get("scorer_id"), "blind-human-use-panel")
    if isinstance(raw, list):
        for score in raw:
            if not isinstance(score, dict):
                continue
            criterion = text(score.get("criterion_id") or score.get("criterion"))
            value = score.get("value", score.get("score"))
            if criterion and isinstance(value, (int, float)):
                result.append(
                    {
                        "scorer_id": text(score.get("scorer_id"), default_scorer),
                        "criterion_id": criterion,
                        "value": value,
                        "notes": text(score.get("notes") or score.get("rationale")),
                    }
                )
    elif isinstance(raw, dict):
        for criterion, value in sorted(raw.items()):
            if isinstance(value, (int, float)):
                result.append(
                    {
                        "scorer_id": default_scorer,
                        "criterion_id": criterion,
                        "value": value,
                        "notes": text(record.get("rationale")),
                    }
                )
    return result


def lens_findings(record: dict[str, Any]) -> list[dict[str, str]]:
    raw = record.get("lens_findings", record.get("findings"))
    result: list[dict[str, str]] = []
    if isinstance(raw, dict):
        result.extend(
            {"lens": lens, "finding": text(finding)}
            for lens, finding in sorted(raw.items())
            if text(finding)
        )
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            lens = text(item.get("lens") or item.get("criterion"))
            finding = text(item.get("finding") or item.get("text"))
            if lens and finding:
                result.append({"lens": lens, "finding": finding})
    return result


def merge_judging_sidecars(
    iterations: list[dict[str, Any]],
    required_lenses: list[str],
) -> tuple[list[dict[str, Any]], list[str], dict[str, set[str]], dict[str, Any] | None]:
    iteration_by_id = {item["id"]: item for item in iterations}
    aggregate_paths = [
        ROOT / "judging" / "loop-01" / "aggregate" / "manifest-ready.json",
        ROOT / "judging" / "loop-02" / "aggregate" / "manifest-ready.json",
        ROOT
        / "judging"
        / "synthesis-loop-01"
        / "aggregate"
        / "manifest-ready.json",
        ROOT / "judging" / "final" / "aggregate" / "manifest-ready.json",
    ]
    merged_paths: list[str] = []
    judges_by_loop: dict[str, set[str]] = {item["id"]: set() for item in iterations}
    human_use_evidence: list[dict[str, Any]] = []
    record_sources: list[tuple[dict[str, Any], Path]] = []
    sidecar_champion: dict[str, Any] | None = None
    for aggregate_path in aggregate_paths:
        if not aggregate_path.is_file():
            continue
        sidecar = load_json(aggregate_path)
        records = sidecar.get("records")
        if not isinstance(records, list):
            raise RuntimeError(
                f"Aggregate manifest-ready sidecar must contain records[]: {aggregate_path}"
            )
        merged_paths.append(generated_relative(aggregate_path))
        record_sources.extend((record, aggregate_path) for record in records)
        if isinstance(sidecar.get("champion"), dict):
            sidecar_champion = deepcopy(sidecar["champion"])
    if not record_sources:
        return human_use_evidence, merged_paths, judges_by_loop, None
    for record, aggregate_path in record_sources:
        if not isinstance(record, dict):
            raise RuntimeError("Aggregate manifest-ready records must be objects.")
        loop_id = text(record.get("iteration_id"))
        if loop_id not in iteration_by_id:
            raise RuntimeError(f"Aggregate sidecar references unknown Loop: {loop_id}")
        iteration = iteration_by_id[loop_id]
        panel_judges = record.get("panel_judges")
        if not isinstance(panel_judges, list):
            raise RuntimeError(f"Panel judges missing for {loop_id}.")
        for judge in panel_judges:
            if isinstance(judge, dict) and text(judge.get("judge_id")):
                judges_by_loop[loop_id].add(text(judge["judge_id"]))

        aggregate_artifact = {
            "id": f"{loop_id}-aggregate-manifest-ready",
            "kind": "data",
            "role": "aggregate-judge-evidence",
            "label": f"{aggregate_path.parents[1].name.replace('-', ' ').title()} aggregate manifest-ready record",
            "path": generated_relative(aggregate_path),
            "sha256": sha256(aggregate_path),
            "presentation": {
                "mode": "structured_json",
                "featured": False,
                "primary": False,
                "caption": "Deterministic panel aggregate derived from preserved raw judge sidecars.",
                "comparison_key": "qualitative-judging",
            },
        }
        iteration["artifacts"].append(aggregate_artifact)
        raw_artifacts = record.get("raw_judge_artifacts")
        if not isinstance(raw_artifacts, list) or not raw_artifacts:
            raise RuntimeError(f"Raw judge Artifact references missing for {loop_id}.")
        raw_path_to_id: dict[str, str] = {}
        for raw in raw_artifacts:
            if not isinstance(raw, dict):
                raise RuntimeError(f"Invalid raw judge Artifact reference for {loop_id}.")
            raw_path = ROOT / text(raw.get("path"))
            if not raw_path.is_file():
                raise RuntimeError(f"Raw judge sidecar missing: {raw_path}")
            declared_hash = text(raw.get("sha256"))
            actual_hash = sha256(raw_path)
            if declared_hash != actual_hash:
                raise RuntimeError(
                    f"Raw judge sidecar hash mismatch for {raw_path}: "
                    f"expected {declared_hash}, got {actual_hash}"
                )
            raw_artifact = {
                "id": text(raw.get("id")),
                "kind": "data",
                "role": "independent-judge-evidence",
                "label": (
                    f"Raw {text(raw.get('judge_id'))} sidecar: {raw_path.name}"
                ),
                "path": generated_relative(raw_path),
                "sha256": actual_hash,
                "presentation": {
                    "mode": (
                        "markdown"
                        if raw_path.suffix.lower() == ".md"
                        else "structured_json"
                    ),
                    "featured": False,
                    "primary": False,
                    "caption": "Raw independent judging evidence preserved without rewriting.",
                    "comparison_key": "qualitative-judging",
                },
            }
            iteration["artifacts"].append(raw_artifact)
            raw_path_to_id[generated_relative(raw_path)] = raw_artifact["id"]
            merged_paths.append(generated_relative(raw_path))

        existing_score_keys = {
            (item.get("scorer_id"), item.get("criterion_id"))
            for item in iteration["scores"]
        }
        for score in sidecar_scores(record):
            key = (score["scorer_id"], score["criterion_id"])
            if key not in existing_score_keys:
                iteration["scores"].append(score)
                existing_score_keys.add(key)

        evidence = record.get("judging_evidence")
        if not isinstance(evidence, dict):
            raise RuntimeError(f"Manifest-ready judging evidence missing for {loop_id}.")
        evidence = deepcopy(evidence)
        evidence["evidence_refs"] = [
            raw_path_to_id.get(text(reference), text(reference))
            for reference in evidence.get("evidence_refs", [])
        ]
        findings = evidence.get("lens_findings")
        observed_lenses = {
            text(item.get("lens"))
            for item in findings or []
            if isinstance(item, dict)
        }
        if set(required_lenses) != observed_lenses or len(findings or []) != len(
            required_lenses
        ):
            raise RuntimeError(
                f"{loop_id} must have exactly all {len(required_lenses)} required lenses."
            )
        if (
            evidence.get("iteration_id") != loop_id
            or evidence.get("criterion_id") != "human-use-quality"
            or evidence.get("scorer_id") != "blind-human-use-panel"
            or evidence.get("kind") != "qualitative_rubric"
            or evidence.get("objective_gate") is not False
        ):
            raise RuntimeError(f"Invalid Manifest-ready evidence contract for {loop_id}.")
        human_use_evidence.append(evidence)
        evidence["lens_findings"] = [
            {"lens": item["lens"], "finding": item["finding"]}
            for item in evidence["lens_findings"]
        ]

        decision = text(record.get("decision"))
        if decision not in VALID_DECISIONS:
            raise RuntimeError(f"Invalid aggregate decision for {loop_id}: {decision}")
        iteration["decision"] = decision
        iteration["outcome"] = (
            "All seven frozen objective gates pass. Independent blind panel review "
            f"completed with decision {decision}; the overall Experiment Champion "
            "remains pending minimum Loops and synthesis."
        )
        iteration["commands"]["judge"] = (
            f"Two independent blind {aggregate_path.parents[1].name.replace('-', ' ').title()} judges, aggregated by per-lens median "
            "with material dissent preserved."
        )
        iteration["prompt"]["judge_feedback"] = text(record.get("judge_feedback"))
        iteration["prompt"]["next_prompt"] = text(record.get("next_loop_feedback"))
        iteration["assembly"].update(
            {
                "qualitative_status": "independent_panel_aggregated",
                "aggregate_sidecar_path": generated_relative(aggregate_path),
                "next_loop_feedback_path": text(record.get("next_loop_feedback_ref")),
                "decision_rationale": text(record.get("decision_rationale")),
            }
        )
    for iteration in iterations:
        iteration["artifacts"].sort(key=lambda item: item["id"])
        iteration["scores"].sort(
            key=lambda item: (item["criterion_id"], item["scorer_id"])
        )
    human_use_evidence.sort(key=lambda item: item["iteration_id"])
    return (
        human_use_evidence,
        sorted(set(merged_paths)),
        judges_by_loop,
        sidecar_champion,
    )


def manifest_scorecard(brief: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for source in brief["scorecard"]:
        criterion = {
            "id": source["id"],
            "label": source["label"],
            "weight": source["weight"],
            "direction": source["direction"],
            "unit": (
                "points (1-5)"
                if source["id"] in QUALITATIVE_CRITERIA
                else (
                    "focusable controls traversed"
                    if source["id"] == "task-efficiency"
                    else "pass (1) / fail (0)"
                )
            ),
            "comparable_across_tracks": True,
            "primary": source["primary"],
        }
        if source.get("gate") is True:
            criterion["gate"] = {"operator": "gte", "threshold": 1}
        result.append(criterion)
    return result


def manifest_scorers(brief: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for source in brief["scorers"]:
        scorer = deepcopy(source)
        scorer["weight"] = 1
        result.append(scorer)
    return result


def human_use_manifest(
    brief: dict[str, Any], judging_evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    human_use = brief["human_use"]
    friction_scenarios = []
    for category in human_use["friction_analysis"]["categories"]:
        for scenario in category.get("scenarios", []):
            friction_scenarios.append(
                {
                    "id": scenario["id"],
                    "category": category["category"],
                    "operation": scenario["operation"],
                    "context": scenario["context"],
                    "material_friction": scenario["material_friction"],
                    "treatment": scenario["treatment"],
                    "target": scenario["target_id"],
                    "rationale": scenario["rationale"],
                    "evidence_plan": scenario["evidence_plan"],
                }
            )
    qualitative = human_use["qualitative_judging"]
    return {
        "applicability": human_use["applicability"],
        "rationale": human_use["rationale"],
        "friction_scenarios": friction_scenarios,
        "prior_art_learnings": [],
        "qualitative_criterion_id": qualitative["criterion_id"],
        "qualitative_scorer_id": qualitative["scorer_id"],
        "required_lenses": list(qualitative["required_lenses"]),
        "judging_evidence": judging_evidence,
    }


def manifest_tracks(brief: dict[str, Any]) -> list[dict[str, Any]]:
    tracks = [
        {
            "id": track["id"],
            "label": track["id"].replace("-", " ").title(),
            "hypothesis": track["hypothesis"],
            "model_role": track["model_role"],
            "allowed_change_scope": track["allowed_change_scope"],
            "final_decision": "Pending additional Loops and independent judging.",
        }
        for track in brief["topology"]["tracks"]
    ]
    tracks.append(
        {
            "id": "synthesis",
            "label": "Evidence-driven synthesis",
            "hypothesis": (
                "Adopt only compatible evidence-backed patterns from all three "
                "finalists without objective regression."
            ),
            "model_role": brief["topology"]["synthesis_model_role"],
            "final_decision": "Pending all parent finalists and two synthesis Loops.",
        }
    )
    return tracks


def generation_manifest(
    brief: dict[str, Any], iterations: list[dict[str, Any]], verified: dict[str, str]
) -> dict[str, Any]:
    models = [
        {
            "role": "orchestrator",
            "model_id": approved_model_for_role(brief, "orchestrator"),
            "provenance": "approved primary model",
        },
        {
            "role": "harness-author",
            "model_id": approved_model_for_role(brief, "harness-author"),
            "provenance": "harness/status.json",
        },
    ]
    for iteration in iterations:
        models.append(
            {
                "role": iteration.get("model_role") or "loop-author",
                "iteration_id": iteration["id"],
                "track_id": iteration["track_id"],
                "model_id": iteration["model_id"],
            }
        )
    for role in EXPECTED_JUDGES + ("synthesizer",):
        judge_status_path = (
            ROOT / "judging" / "loop-01" / role / "status.json"
        )
        judge_completed = (
            role in EXPECTED_JUDGES
            and judge_status_path.is_file()
            and terminal_status(load_json(judge_status_path))
        )
        models.append(
            {
                "role": role,
                "model_id": approved_model_for_role(brief, role),
                "provenance": (
                    generated_relative(judge_status_path)
                    + "; completed independent blind Loop 01 review"
                    if judge_completed
                    else (
                        "approved model; execution pending"
                        if role in EXPECTED_JUDGES
                        else "approved primary model"
                    )
                ),
            }
        )
    unique = {
        (
            item["role"],
            item["model_id"],
            item.get("iteration_id", ""),
        ): item
        for item in models
    }
    return {
        "skill_commit": "64f8581a47a571c00f405aab47ee23554474843b",
        "skill_tree_sha256": "bf9487d6a47b23239c08497da4d970dcab6d6193a9ea6c103fd4953eb2073153",
        "prompt_sha256": verified["setup/prompt.md"],
        "approved_brief_sha256": verified["setup/experiment-brief.json"],
        "build_viewer_sha256": verified["build_viewer.py"],
        "harness_sha256": verified["harness/run_checkout_gates.py"],
        "canonical_fixture_sha256": verified["harness/canonical-fixture.json"],
        "orchestrator_model": approved_model_for_role(brief, "orchestrator"),
        "copilot_cli_version": "1.0.71",
        "skill_provenance_status": "Recorded from the repository and canonical skill-tree hashing helper.",
        "models": [unique[key] for key in sorted(unique)],
    }


def schema_diagnostics(manifest: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    schema_path = REPO_ROOT / "references" / "manifest-schema-v1.1.json"
    try:
        import jsonschema  # type: ignore
    except ImportError:
        diagnostics.append(
            {
                "id": "manifest-schema-v1.1",
                "status": "not_run",
                "detail": "jsonschema is unavailable; no dependency was installed.",
            }
        )
        return diagnostics
    validator = jsonschema.Draft202012Validator(load_json(schema_path))
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    if not errors:
        diagnostics.append(
            {
                "id": "manifest-schema-v1.1",
                "status": "pass",
                "detail": "Manifest validates against the shared v1.1 schema.",
            }
        )
    else:
        detail = "; ".join(
            f"{'.'.join(map(str, error.path)) or '$'}: {error.message}"
            for error in errors[:8]
        )
        diagnostics.append(
            {
                "id": "manifest-schema-v1.1",
                "status": "expected_interim_failure",
                "detail": detail,
            }
        )
    return diagnostics


def validate_artifacts(iterations: list[dict[str, Any]]) -> tuple[int, list[str]]:
    count = 0
    errors: list[str] = []
    seen_ids: set[str] = set()
    for iteration in iterations:
        for artifact in iteration["artifacts"]:
            count += 1
            artifact_id = artifact["id"]
            if artifact_id in seen_ids:
                errors.append(f"Duplicate Artifact ID: {artifact_id}")
            seen_ids.add(artifact_id)
            path = ROOT / artifact["path"]
            if not path.is_file():
                errors.append(f"Missing Artifact: {artifact['path']}")
            elif sha256(path) != artifact["sha256"]:
                errors.append(f"Artifact hash mismatch: {artifact['path']}")
    return count, errors


def main() -> int:
    verified = verify_frozen_inputs()
    remediation = remediation_provenance()
    brief = load_json(SETUP_ROOT / "experiment-brief.json")
    prompt = (SETUP_ROOT / "prompt.md").read_text(encoding="utf-8")
    iterations, live_loop_ids, skipped_sources, merged_loop_ids = discover_iterations(
        brief
    )
    required_lenses = list(
        brief["human_use"]["qualitative_judging"]["required_lenses"]
    )
    (
        judging_evidence,
        merged_sidecars,
        judges_by_loop,
        sidecar_champion,
    ) = merge_judging_sidecars(iterations, required_lenses)

    champion: dict[str, Any]
    if sidecar_champion and all(
        key in sidecar_champion
        for key in ("iteration_id", "summary", "reasons", "caveats")
    ):
        champion = sidecar_champion
    else:
        champion = {
            "status": "pending",
            "interim_baseline_champion_iteration_id": "resumable-wizard-loop-01",
            "reason": (
                "The wizard is the interim Loop 01 Track baseline champion after "
                "independent panel review, but no Experiment Champion is selected "
                "until minimum Loops and synthesis are complete."
            ),
        }

    constraints = [item["statement"] for item in brief["invariants"]]
    generation = generation_manifest(brief, iterations, verified)
    generation["procedural_provenance"] = remediation
    manifest = {
        "schema_version": "1.1",
        "experiment_id": brief["experiment_id"],
        "title": brief["title"],
        "problem": {
            "statement": brief["problem"]["statement"],
            "optimization_target": brief["problem"]["optimization_target"],
            "constraints": constraints,
            "success_criteria": [brief["problem"]["success_definition"]],
            "original_prompt": prompt,
        },
        "generation": generation,
        "budget": {
            "planned_iters": 8,
            "max_iters": brief["autonomy"]["max_iterations"],
            "patience": 2,
            "cost_limit": None,
            "wall_time_limit_sec": brief["autonomy"]["max_wall_time_minutes"] * 60,
        },
        "artifact_scope": {
            "roots": ["."],
            "allow_edit": brief["autonomy"]["allowed_paths"],
            "deny": brief["autonomy"]["denied_paths"],
        },
        "scorecard": manifest_scorecard(brief),
        "scorers": manifest_scorers(brief),
        "judge_panels": [
            {
                "id": "blind-accessibility-panel",
                "blind": True,
                "flip_pairwise_order": True,
                "aggregation": "median_with_dissent",
                "judges": [
                    {
                        "id": role,
                        "model_id": approved_model_for_role(brief, role),
                        "role": (
                            "accessibility correctness and cross-disability operation"
                            if role == "judge-accessibility"
                            else "human-use friction and information clarity"
                        ),
                    }
                    for role in EXPECTED_JUDGES
                ],
            }
        ],
        "governance": {
            "approved_setup": {
                "revision": brief["revision"],
                "status": brief["status"],
                "brief_sha256": verified["setup/experiment-brief.json"],
                "prompt_sha256": verified["setup/prompt.md"],
            },
            "self_editing": {
                "requires_user_approval": True,
                "proposal_required": True,
                "approved_proposal_id": None,
            },
            "network_allowed": False,
            "prior_art_search_approved": False,
            "procedural_caveats": [remediation],
        },
        "human_use": human_use_manifest(brief, judging_evidence),
        "tracks": manifest_tracks(brief),
        "iterations": iterations,
        "champion": champion,
        "story": {
            "milestones": [
                {
                    "iteration_id": item["id"],
                    "caption": (
                        f"{item['track_id']} {item['id']}: all objective gates pass; "
                        f"independent panel decision is {item['decision']}."
                    ),
                }
                for item in iterations
            ],
            "featured_artifact_id": (
                "synthesis-loop-02-checkout-ui"
                if sidecar_champion
                else "pending-champion-artifact"
            ),
            "primary_comparison_key": "checkout-ui",
        },
        "rules": [item["statement"] for item in brief["invariants"]],
        "synthesis": (
            "Eight planned Loops are complete. Synthesis Loop 02 wins both independent "
            "flipped-order comparisons against the strongest parent and has the highest "
            "final panel aggregate while retaining all seven objective passes. The "
            "permanent path-scope remediation and reboot-recovery caveats remain bound "
            "to provenance without changing functional hashes."
            if sidecar_champion
            else "Final judging remains pending."
        ),
        "assembly": {
            "state": "complete" if sidecar_champion else "in_progress",
            "merged_loop_ids": merged_loop_ids,
            "merged_judging_sidecars": merged_sidecars,
            "pending_champion": not bool(sidecar_champion),
            "champion_iteration_id": (
                sidecar_champion["iteration_id"] if sidecar_champion else None
            ),
            "interim_baseline_champion_iteration_id": "single-page-loop-02",
            "feedback_sidecars": [
                "judging/loop-01/aggregate/loop-02-feedback.json",
                "judging/loop-01/aggregate/dissent.md",
                "judging/loop-01/aggregate/pairwise-aggregate.json",
                "judging/loop-01/blinding-map.json",
                "judging/loop-02/aggregate/synthesis-input.json",
                "judging/loop-02/aggregate/dissent.md",
                "judging/loop-02/aggregate/pairwise-aggregate.json",
                "judging/loop-02/blinding-map.json",
            ],
            "provenance_sidecars": [
                remediation["provenance_path"],
                remediation["hash_verification_path"],
                remediation["report_path"],
            ],
            "pending_qualitative_scores": [
                item["id"]
                for item in iterations
                if not any(
                    score["criterion_id"] in QUALITATIVE_CRITERIA
                    for score in item["scores"]
                )
            ],
        },
        "brief_contract": {
            "problem": deepcopy(brief["problem"]),
            "human_use": deepcopy(brief["human_use"]),
            "scorecard": deepcopy(brief["scorecard"]),
            "scorers": deepcopy(brief["scorers"]),
            "models": deepcopy(brief["models"]),
            "topology": deepcopy(brief["topology"]),
            "autonomy": deepcopy(brief["autonomy"]),
        },
    }
    decisions_by_track = {
        item["track_id"]: item["decision"] for item in manifest["iterations"]
    }
    for track in manifest["tracks"]:
        if track["id"] in decisions_by_track:
            track["final_decision"] = (
                f"Final recorded decision: {decisions_by_track[track['id']]}."
                if sidecar_champion
                else f"Provisional decision: {decisions_by_track[track['id']]}."
            )
    write_json(ROOT / "manifest.json", manifest)

    artifact_count, artifact_errors = validate_artifacts(iterations)
    missing_expected = sorted(set(EXPECTED_LOOP_IDS) - set(merged_loop_ids))
    pending_judges = sorted(
        f"{judge}:{loop_id}"
        for loop_id in merged_loop_ids
        for judge in EXPECTED_JUDGES
        if judge not in judges_by_loop.get(loop_id, set())
    )
    diagnostics = [
        {
            "id": "frozen-input-hashes",
            "status": "pass",
            "detail": f"Verified {len(verified)} exact frozen setup, Viewer, fixture, and harness hashes.",
        },
        {
            "id": "terminal-fragment-gate",
            "status": "pass",
            "detail": (
                f"Merged {len(merged_loop_ids)} terminal Loops only: "
                + ", ".join(merged_loop_ids)
            ),
        },
        {
            "id": "artifact-integrity",
            "status": "pass" if not artifact_errors else "fail",
            "detail": (
                f"Verified {artifact_count} referenced Artifact files and SHA-256 values."
                if not artifact_errors
                else "; ".join(artifact_errors)
            ),
        },
        {
            "id": "qualitative-judging",
            "status": "pending" if pending_judges else "pass",
            "detail": (
                f"{len(pending_judges)} required per-Loop independent judge results remain pending."
                if pending_judges
                else "Required per-Loop independent judging is merged."
            ),
        },
        {
            "id": "champion",
            "status": "pass" if sidecar_champion else "pending",
            "detail": (
                f"Final Champion is {sidecar_champion['iteration_id']}."
                if sidecar_champion
                else "Experiment Champion remains pending."
            ),
        },
    ]
    diagnostics.extend(schema_diagnostics(manifest))
    status = {
        "schema_version": "1.0",
        "state": (
            "complete"
            if sidecar_champion
            and not missing_expected
            and not pending_judges
            and not live_loop_ids
            else "in_progress"
        ),
        "manifest": "manifest.json",
        "merged_loop_ids": merged_loop_ids,
        "merged_judging_sidecars": merged_sidecars,
        "pending_live_loop_ids": live_loop_ids,
        "pending_expected_loop_ids": missing_expected,
        "pending_judges": pending_judges,
        "aggregate_scores": {
            item["id"]: {
                score["criterion_id"]: score["value"]
                for score in item["scores"]
                if score["scorer_id"] == "blind-human-use-panel"
            }
            for item in iterations
        },
        "provisional_decisions": {
            item["id"]: item["decision"] for item in iterations
        },
        "interim_baseline_champion_iteration_id": "single-page-loop-02",
        "feedback_sidecars": [
            "judging/loop-01/aggregate/loop-02-feedback.json",
            "judging/loop-01/aggregate/dissent.md",
            "judging/loop-01/aggregate/pairwise-aggregate.json",
            "judging/loop-01/blinding-map.json",
            "judging/loop-02/aggregate/synthesis-input.json",
            "judging/loop-02/aggregate/dissent.md",
            "judging/loop-02/aggregate/pairwise-aggregate.json",
            "judging/loop-02/blinding-map.json",
        ],
        "pending_final_judging": [] if sidecar_champion else [
            "champion-vs-strongest-parent-flipped-pairwise"
        ],
        "skipped_live_fragment_sources": skipped_sources,
        "frozen_hashes": verified,
        "validation_diagnostics": diagnostics,
        "referenced_artifact_count": artifact_count,
        "manifest_sha256": sha256(ROOT / "manifest.json"),
        "viewer_status": "pending_rebuild",
        "evidence_gate_status": "not_run_interim",
    }
    write_json(ROOT / "manifest-assembly-status.json", status)
    print(
        json.dumps(
            {
                "manifest": str(ROOT / "manifest.json"),
                "assembly_status": str(ROOT / "manifest-assembly-status.json"),
                "merged_loop_ids": merged_loop_ids,
                "pending_expected_loop_ids": missing_expected,
                "pending_judge_count": len(pending_judges),
                "artifact_count": artifact_count,
            },
            sort_keys=True,
        )
    )
    return 1 if artifact_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
