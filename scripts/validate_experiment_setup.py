#!/usr/bin/env python3
"""Validate a frozen Experiment Setup brief and its explicit approval binding."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parent.parent
BRIEF_SCHEMA = ROOT / "references" / "experiment-brief-schema-v1.0.json"
APPROVAL_SCHEMA = ROOT / "references" / "experiment-approval-schema-v1.0.json"
RISK_CONTROL_FIELDS = (
    "consent",
    "privacy",
    "retention",
    "credentials",
    "rollback",
    "approval_boundaries",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(value)
    return (
        not path.is_absolute()
        and not windows_path.drive
        and ".." not in path.parts
    )


def _path_is_within(child: object, parent: object) -> bool:
    if not _relative_path(child) or not _relative_path(parent):
        return False
    child_path = PurePosixPath(str(child).replace("\\", "/"))
    parent_path = PurePosixPath(str(parent).replace("\\", "/"))
    return child_path == parent_path or parent_path in child_path.parents


def validate_brief(data: object) -> list[str]:
    errors: list[str] = []
    schema = _load(BRIEF_SCHEMA)
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        return [f"schema {location}: {exc.message}"]
    assert isinstance(data, dict)

    for field, value in data["target"].items():
        if not _relative_path(value):
            errors.append(f"target.{field} must be a repository-relative path")

    collections = {
        "invariant": data["invariants"],
        "optimization variable": data["optimization_variables"],
        "criterion": data["scorecard"],
        "scorer": data["scorers"],
        "track": data["topology"]["tracks"],
        "model role": data["models"],
    }
    for label, values in collections.items():
        key = "role" if label == "model role" else "id"
        identifiers = [item[key] for item in values]
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"{label} IDs must be unique")

    criteria = {item["id"]: item for item in data["scorecard"]}
    if sum(item["primary"] is True for item in criteria.values()) != 1:
        errors.append("scorecard must declare exactly one primary criterion")
    gate_ids = {item["id"] for item in criteria.values() if item["gate"] is True}
    if not gate_ids:
        errors.append("scorecard must declare at least one blocking gate")

    covered_objective: set[str] = set()
    for scorer in data["scorers"]:
        unknown = set(scorer["criterion_ids"]) - set(criteria)
        if unknown:
            errors.append(
                f"scorer {scorer['id']} references unknown criteria: {sorted(unknown)}"
            )
        if scorer["type"] == "objective_command":
            if not scorer.get("command", "").strip():
                errors.append(
                    f"objective scorer {scorer['id']} must declare a command"
                )
            covered_objective.update(scorer["criterion_ids"])
    missing_objective = gate_ids - covered_objective
    if missing_objective:
        errors.append(
            f"blocking gates lack objective scorers: {sorted(missing_objective)}"
        )

    if not any(
        invariant["blocking"]
        and invariant["verification"]["type"]
        in {"objective_command", "artifact_assertion"}
        for invariant in data["invariants"]
    ):
        errors.append(
            "at least one invariant must have non-human blocking verification"
        )

    model_roles = {item["role"] for item in data["models"]}
    for track in data["topology"]["tracks"]:
        if track["model_role"] not in model_roles:
            errors.append(
                f"track {track['id']} references unknown model role "
                f"{track['model_role']}"
            )
    synthesis_role = data["topology"].get("synthesis_model_role")
    if data["topology"]["synthesis_required"]:
        if not synthesis_role or synthesis_role not in model_roles:
            errors.append(
                "synthesis_required needs a valid synthesis_model_role"
            )

    autonomy = data["autonomy"]
    attended = autonomy.get("attended_protocol")
    if (
        autonomy["mode"] in {"attended", "unattended"}
        and not isinstance(attended, dict)
    ):
        errors.append(
            f"{autonomy['mode']} mode requires autonomy.attended_protocol"
        )
    if isinstance(attended, dict) and not _path_is_within(
        attended["checkpoint_root"], data["target"]["generated_root"]
    ):
        errors.append(
            "attended checkpoint_root must be within target.generated_root"
        )
    if autonomy["mode"] == "unattended":
        scratch_root = data["target"].get("scratch_root")
        if scratch_root is None:
            errors.append("unattended mode requires target.scratch_root")
        elif not _path_is_within(scratch_root, data["target"]["generated_root"]):
            errors.append(
                "unattended target.scratch_root must be within target.generated_root"
            )
        if not autonomy["pause_conditions"]:
            errors.append("unattended mode requires pause conditions")
        if not autonomy["prohibited_actions"]:
            errors.append("unattended mode requires prohibited actions")

    risks = data["risks"]
    risk_active = any(
        risks[field]
        for field in (
            "external_users",
            "deployment",
            "telemetry",
            "external_services",
            "sensitive_data",
        )
    )
    if risk_active:
        controls = risks["controls"]
        missing = [
            field
            for field in RISK_CONTROL_FIELDS
            if not isinstance(controls.get(field), str) or not controls[field].strip()
        ]
        if missing:
            errors.append(
                f"active risk branch lacks controls: {', '.join(missing)}"
            )

    review = data.get("setup_review")
    if review is not None and (
        review["status"] == "pass" and review["unresolved_findings"]
    ):
        errors.append("passing setup review cannot retain unresolved findings")
    return errors


def validate_setup(
    brief_path: Path,
    *,
    prompt_path: Path | None = None,
    approval_path: Path | None = None,
    require_approved: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        brief = _load(brief_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"cannot parse brief: {exc}"]
    errors.extend(validate_brief(brief))

    if not require_approved and approval_path is None:
        return errors
    if prompt_path is None or approval_path is None:
        return errors + [
            "approved setup requires prompt.md and approval.json paths"
        ]
    try:
        approval = _load(approval_path)
        jsonschema.validate(approval, _load(APPROVAL_SCHEMA))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return errors + [f"cannot parse approval: {exc}"]
    except jsonschema.ValidationError as exc:
        return errors + [f"approval schema: {exc.message}"]

    if not isinstance(brief, dict) or not isinstance(approval, dict):
        return errors + ["brief and approval roots must be objects"]
    if brief.get("status") != "approved":
        errors.append("brief status must be approved")
    if approval.get("experiment_id") != brief.get("experiment_id"):
        errors.append("approval experiment_id does not match brief")
    if approval.get("brief_revision") != brief.get("revision"):
        errors.append("approval revision does not match brief")
    if approval.get("brief_sha256") != _sha256(brief_path):
        errors.append("approval brief_sha256 does not match brief")
    try:
        prompt_hash = _sha256(prompt_path)
    except OSError as exc:
        errors.append(f"cannot read prompt: {exc}")
    else:
        if approval.get("prompt_sha256") != prompt_hash:
            errors.append("approval prompt_sha256 does not match prompt")

    review = brief.get("setup_review")
    if not isinstance(review, dict) or review.get("status") != "pass":
        errors.append("approved brief requires a passing independent setup review")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()
    errors = validate_setup(
        args.brief,
        prompt_path=args.prompt,
        approval_path=args.approval,
        require_approved=args.require_approved,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("EXPERIMENT SETUP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
