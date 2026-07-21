"""Load and validate immutable human-feedback intake and disposition sidecars."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parent
INTAKE_SCHEMA = ROOT / "human-feedback-intake-schema-v1.0.json"
DISPOSITION_SCHEMA = ROOT / "human-feedback-disposition-schema-v1.0.json"
INTAKE_ROOT = PurePosixPath("human-feedback/intake")
DISPOSITION_ROOT = PurePosixPath("human-feedback/dispositions")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _schema_errors(data: object, schema_path: Path) -> list[str]:
    schema = _load_json(schema_path)
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    errors = sorted(
        validator_class(schema, format_checker=jsonschema.FormatChecker()).iter_errors(
            data
        ),
        key=lambda error: list(error.absolute_path),
    )
    messages = []
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{location}: {error.message}")
    return messages


def _sidecars(data_dir: Path, subdirectory: PurePosixPath) -> list[Path]:
    root = data_dir.joinpath(*subdirectory.parts)
    return sorted(root.glob("*.json")) if root.is_dir() else []


def _safe_relative_path(data_dir: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in PurePosixPath(value.replace("\\", "/")).parts:
        return None
    candidate = (data_dir / relative).resolve()
    try:
        candidate.relative_to(data_dir.resolve())
    except ValueError:
        return None
    return candidate


def _manifest_indexes(manifest: Mapping[str, object]) -> tuple[set[str], set[str], set[str]]:
    criteria = {
        str(item.get("id"))
        for item in manifest.get("scorecard", [])
        if isinstance(item, Mapping) and item.get("id")
    }
    loops = {
        str(item.get("id"))
        for item in manifest.get("iterations", [])
        if isinstance(item, Mapping) and item.get("id")
    }
    artifacts = {
        str(artifact.get("id"))
        for loop in manifest.get("iterations", [])
        if isinstance(loop, Mapping)
        for artifact in loop.get("artifacts", [])
        if isinstance(artifact, Mapping) and artifact.get("id")
    }
    return criteria, loops, artifacts


def validate_manifest_feedback(manifest: Mapping[str, object]) -> list[str]:
    """Validate optional Manifest links without requiring local sidecars."""
    errors: list[str] = []
    iterations = {
        str(item.get("id")): item
        for item in manifest.get("iterations", [])
        if isinstance(item, Mapping) and item.get("id")
    }
    artifacts = {
        str(artifact.get("id"))
        for loop in iterations.values()
        for artifact in loop.get("artifacts", [])
        if isinstance(artifact, Mapping) and artifact.get("id")
    }
    links = [
        item
        for item in manifest.get("human_feedback", [])
        if isinstance(item, Mapping)
    ]
    entry_ids = [str(item.get("entry_id", "")) for item in links]
    duplicates = sorted(
        entry_id for entry_id in set(entry_ids) if entry_ids.count(entry_id) > 1
    )
    for entry_id in duplicates:
        errors.append(f"duplicate human feedback entry id: {entry_id}")

    links_by_id = {
        str(item.get("entry_id")): item for item in links if item.get("entry_id")
    }
    for entry_id, link in links_by_id.items():
        verbatim = str(link.get("verbatim", ""))
        target = link.get("target")
        if isinstance(target, Mapping):
            target_id = str(target.get("id", ""))
            known = iterations if target.get("kind") == "loop" else artifacts
            if target_id not in known:
                errors.append(
                    f"human feedback {entry_id} references unknown "
                    f"{target.get('kind')} {target_id}"
                )
        disposition = link.get("disposition")
        if not isinstance(disposition, Mapping):
            continue
        state = str(disposition.get("status", ""))
        consumed = [
            str(value)
            for value in disposition.get("consumed_iteration_refs", [])
        ]
        if state == "accepted" and not consumed:
            errors.append(f"accepted feedback {entry_id} has no consuming Loop")
        if state != "accepted" and consumed:
            errors.append(
                f"non-accepted feedback {entry_id} cannot have consuming Loops"
            )
        for loop_id in consumed:
            loop = iterations.get(loop_id)
            if loop is None:
                errors.append(
                    f"human feedback {entry_id} references unknown consuming Loop {loop_id}"
                )
                continue
            prompt = loop.get("prompt")
            prompt = prompt if isinstance(prompt, Mapping) else {}
            refs = [
                str(value) for value in prompt.get("input_feedback_refs", [])
            ]
            if entry_id not in refs:
                errors.append(
                    f"Loop {loop_id} does not reference accepted feedback {entry_id}"
                )
            if verbatim and verbatim not in str(prompt.get("input_feedback", "")):
                errors.append(
                    f"Loop {loop_id} input_feedback does not preserve verbatim "
                    f"feedback {entry_id}"
                )

    for loop_id, loop in iterations.items():
        prompt = loop.get("prompt")
        prompt = prompt if isinstance(prompt, Mapping) else {}
        for entry_id in prompt.get("input_feedback_refs", []):
            entry_id = str(entry_id)
            link = links_by_id.get(entry_id)
            if link is None:
                errors.append(
                    f"Loop {loop_id} references unknown human feedback {entry_id}"
                )
                continue
            disposition = link.get("disposition")
            disposition = disposition if isinstance(disposition, Mapping) else {}
            if disposition.get("status") != "accepted":
                errors.append(
                    f"Loop {loop_id} references non-accepted human feedback {entry_id}"
                )
            consumed = [
                str(value)
                for value in disposition.get("consumed_iteration_refs", [])
            ]
            if loop_id not in consumed:
                errors.append(
                    f"feedback {entry_id} does not name Loop {loop_id} as a consumer"
                )
    return errors


def validate_feedback_directory(
    data_dir: Path,
    manifest: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate schemas, references, immutable bindings, and consumption chains."""
    errors: list[str] = []
    manifest = manifest or {}
    criteria, loops, artifacts = _manifest_indexes(manifest)
    intakes: dict[str, tuple[dict[str, object], Path]] = {}
    entries: dict[str, tuple[dict[str, object], str]] = {}

    for path in _sidecars(data_dir, INTAKE_ROOT):
        try:
            data = _load_json(path)
            schema_errors = _schema_errors(data, INTAKE_SCHEMA)
        except (OSError, UnicodeError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"{path.name}: cannot validate intake: {exc}")
            continue
        errors.extend(f"{path.name}: {message}" for message in schema_errors)
        if schema_errors or not isinstance(data, dict):
            continue
        review_id = str(data["review_id"])
        if review_id in intakes:
            errors.append(f"duplicate review_id: {review_id}")
            continue
        intakes[review_id] = (data, path)
        if path.stem != review_id:
            errors.append(
                f"{path.name}: filename must match review_id {review_id}"
            )
        if manifest and data.get("experiment_id") != manifest.get("experiment_id"):
            errors.append(f"{path.name}: experiment_id does not match Manifest")
        human = data.get("human")
        human = human if isinstance(human, Mapping) else {}
        preferred = human.get("preferred_iteration_id")
        if preferred is not None and str(preferred) not in loops:
            errors.append(f"{path.name}: preferred Loop {preferred} is unknown")
        for entry in human.get("entries", []):
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("entry_id", ""))
            if entry_id in entries:
                errors.append(f"duplicate entry_id: {entry_id}")
                continue
            entries[entry_id] = (entry, review_id)
            criterion = entry.get("criterion_review")
            if isinstance(criterion, Mapping):
                criterion_id = str(criterion.get("criterion_id", ""))
                if criterion_id not in criteria:
                    errors.append(
                        f"{path.name}: entry {entry_id} references unknown criterion "
                        f"{criterion_id}"
                    )
            target = entry.get("target")
            if isinstance(target, Mapping):
                target_id = str(target.get("id", ""))
                known = loops if target.get("kind") == "loop" else artifacts
                if target_id not in known:
                    errors.append(
                        f"{path.name}: entry {entry_id} references unknown "
                        f"{target.get('kind')} {target_id}"
                    )

    dispositions: dict[str, tuple[dict[str, object], Path]] = {}
    disposition_ids: set[str] = set()
    for path in _sidecars(data_dir, DISPOSITION_ROOT):
        try:
            data = _load_json(path)
            schema_errors = _schema_errors(data, DISPOSITION_SCHEMA)
        except (OSError, UnicodeError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"{path.name}: cannot validate disposition: {exc}")
            continue
        errors.extend(f"{path.name}: {message}" for message in schema_errors)
        if schema_errors or not isinstance(data, dict):
            continue
        disposition_id = str(data["disposition_id"])
        if disposition_id in disposition_ids:
            errors.append(f"duplicate disposition_id: {disposition_id}")
        disposition_ids.add(disposition_id)
        if path.stem != disposition_id:
            errors.append(
                f"{path.name}: filename must match disposition_id {disposition_id}"
            )
        entry_id = str(data["entry_id"])
        if entry_id in dispositions:
            errors.append(f"entry {entry_id} has multiple dispositions")
            continue
        dispositions[entry_id] = (data, path)
        intake = data["intake"]
        review_id = str(intake["review_id"])
        source = intakes.get(review_id)
        entry_source = entries.get(entry_id)
        if source is None:
            errors.append(f"{path.name}: references unknown review {review_id}")
            continue
        if entry_source is None or entry_source[1] != review_id:
            errors.append(
                f"{path.name}: entry {entry_id} is not part of review {review_id}"
            )
        intake_path = _safe_relative_path(data_dir, intake["path"])
        if intake_path is None or intake_path != source[1].resolve():
            errors.append(f"{path.name}: intake.path does not resolve to its review")
        elif intake["sha256"].lower() != _sha256(intake_path):
            errors.append(f"{path.name}: intake.sha256 does not match intake bytes")
        if data.get("experiment_id") != source[0].get("experiment_id"):
            errors.append(f"{path.name}: experiment_id does not match intake")
        for loop_id in data["orchestrator"]["consumed_iteration_refs"]:
            if str(loop_id) not in loops:
                errors.append(
                    f"{path.name}: references unknown consuming Loop {loop_id}"
                )

    manifest_links = {
        str(item.get("entry_id")): item
        for item in manifest.get("human_feedback", [])
        if isinstance(item, Mapping) and item.get("entry_id")
    }
    errors.extend(validate_manifest_feedback(manifest))
    for entry_id, (disposition, disposition_path) in dispositions.items():
        orchestrator = disposition["orchestrator"]
        state = str(orchestrator["disposition"])
        link = manifest_links.get(entry_id)
        if link is None:
            if state == "accepted":
                errors.append(
                    f"accepted feedback {entry_id} is not linked by the Manifest"
                )
            continue
        entry, review_id = entries[entry_id]
        intake_data, intake_path = intakes[review_id]
        expected_path = intake_path.relative_to(data_dir).as_posix()
        if link.get("review_id") != review_id:
            errors.append(f"Manifest feedback {entry_id} has the wrong review_id")
        if link.get("intake_path") != expected_path:
            errors.append(f"Manifest feedback {entry_id} has the wrong intake_path")
        if str(link.get("intake_sha256", "")).lower() != _sha256(intake_path):
            errors.append(f"Manifest feedback {entry_id} has the wrong intake_sha256")
        expected_disposition_path = disposition_path.relative_to(data_dir).as_posix()
        if link.get("disposition_path") != expected_disposition_path:
            errors.append(
                f"Manifest feedback {entry_id} has the wrong disposition_path"
            )
        if (
            str(link.get("disposition_sha256", "")).lower()
            != _sha256(disposition_path)
        ):
            errors.append(
                f"Manifest feedback {entry_id} has the wrong disposition_sha256"
            )
        if link.get("verbatim") != entry.get("verbatim"):
            errors.append(f"Manifest feedback {entry_id} changed verbatim owner text")
        if link.get("feedback_type") != entry.get("feedback_type"):
            errors.append(f"Manifest feedback {entry_id} changed feedback_type")
        if link.get("target") != entry.get("target"):
            errors.append(f"Manifest feedback {entry_id} changed feedback target")
        manifest_disposition = link.get("disposition")
        manifest_disposition = (
            manifest_disposition if isinstance(manifest_disposition, Mapping) else {}
        )
        for source_key, manifest_key in (
            ("disposition_id", "id"),
            ("interpretation", "interpretation"),
            ("rationale", "rationale"),
            ("consumed_iteration_refs", "consumed_iteration_refs"),
            ("owner_response", "owner_response"),
        ):
            expected = (
                disposition.get(source_key)
                if source_key == "disposition_id"
                else orchestrator.get(source_key)
            )
            if manifest_disposition.get(manifest_key) != expected:
                errors.append(
                    f"Manifest feedback {entry_id} does not match disposition "
                    f"{manifest_key}"
                )
        if manifest_disposition.get("status") != state:
            errors.append(
                f"Manifest feedback {entry_id} does not match disposition status"
            )
    return errors


def load_feedback_view(
    data_dir: Path | None,
    manifest: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[str]]:
    """Build presentation records from sidecars, falling back to Manifest links."""
    diagnostics: list[str] = []
    records: dict[str, dict[str, object]] = {}
    if data_dir is not None:
        intake_files = _sidecars(data_dir, INTAKE_ROOT)
        disposition_files = _sidecars(data_dir, DISPOSITION_ROOT)
        dispositions: dict[str, dict[str, object]] = {}
        for path in disposition_files:
            try:
                data = _load_json(path)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                diagnostics.append(f"Human feedback disposition {path.name} is unreadable: {exc}")
                continue
            if isinstance(data, dict) and data.get("entry_id"):
                dispositions[str(data["entry_id"])] = data
        for path in intake_files:
            try:
                data = _load_json(path)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                diagnostics.append(f"Human feedback intake {path.name} is unreadable: {exc}")
                continue
            if not isinstance(data, dict):
                diagnostics.append(f"Human feedback intake {path.name} is not an object.")
                continue
            human = data.get("human")
            human = human if isinstance(human, Mapping) else {}
            for entry in human.get("entries", []):
                if not isinstance(entry, Mapping) or not entry.get("entry_id"):
                    continue
                entry_id = str(entry["entry_id"])
                disposition = dispositions.get(entry_id, {})
                authored = disposition.get("orchestrator")
                authored = authored if isinstance(authored, Mapping) else {}
                records[entry_id] = {
                    **dict(entry),
                    "review_id": data.get("review_id"),
                    "intake_path": path.relative_to(data_dir).as_posix(),
                    "disposition_id": disposition.get("disposition_id"),
                    "status": authored.get("disposition", "pending"),
                    "interpretation": authored.get("interpretation", ""),
                    "rationale": authored.get("rationale", ""),
                    "owner_response": authored.get("owner_response", ""),
                    "consumed_iteration_refs": list(
                        authored.get("consumed_iteration_refs", [])
                    ),
                }

    for link in manifest.get("human_feedback", []):
        if not isinstance(link, Mapping) or not link.get("entry_id"):
            continue
        entry_id = str(link["entry_id"])
        disposition = link.get("disposition")
        disposition = disposition if isinstance(disposition, Mapping) else {}
        fallback = {
            "entry_id": entry_id,
            "review_id": link.get("review_id"),
            "feedback_type": link.get("feedback_type", "general"),
            "verbatim": link.get("verbatim", ""),
            "target": link.get("target"),
            "intake_path": link.get("intake_path"),
            "disposition_path": link.get("disposition_path"),
            "disposition_id": disposition.get("id"),
            "status": disposition.get("status", "pending"),
            "interpretation": disposition.get("interpretation", ""),
            "rationale": disposition.get("rationale", ""),
            "owner_response": disposition.get("owner_response", ""),
            "consumed_iteration_refs": list(
                disposition.get("consumed_iteration_refs", [])
            ),
        }
        records.setdefault(entry_id, fallback)
    return list(records.values()), diagnostics
