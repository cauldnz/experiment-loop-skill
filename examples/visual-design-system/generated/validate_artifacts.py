#!/usr/bin/env python3
"""Deterministically validate a Loop Lab manifest and its local evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_PRIMARY_CONTENT = ("title", "date", "time", "venue", "cta")
OVERALL_METRIC_KEYS = ("overall_pass", "overall_objective_pass")


def local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1].lower()


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def load_json(path: Path, errors: list[str], label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot parse JSON: {exc}")
        return None


def safe_artifact_path(root: Path, relative: Any, errors: list[str], artifact_id: str) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{artifact_id}: artifact path is missing")
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"{artifact_id}: artifact path escapes manifest directory")
        return None
    return candidate


def validate_svg(path: Path, artifact: dict[str, Any], errors: list[str]) -> None:
    artifact_id = artifact.get("id", "<unknown>")
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        errors.append(f"{artifact_id}: invalid SVG/XML: {exc}")
        return

    if local_name(root.tag) != "svg":
        errors.append(f"{artifact_id}: XML root is not svg")
        return

    title_nodes = [node for node in root.iter() if local_name(node.tag) == "title"]
    desc_nodes = [node for node in root.iter() if local_name(node.tag) == "desc"]
    title_text = [" ".join(node.itertext()).strip() for node in title_nodes]
    desc_text = [" ".join(node.itertext()).strip() for node in desc_nodes]
    if not any(title_text):
        errors.append(f"{artifact_id}: accessible SVG title is missing")
    if not any(desc_text):
        errors.append(f"{artifact_id}: accessible SVG description is missing")

    labelled_by = root.attrib.get("aria-labelledby", "").split()
    ids = {node.attrib.get("id") for node in root.iter() if node.attrib.get("id")}
    if not labelled_by or any(ref not in ids for ref in labelled_by):
        errors.append(f"{artifact_id}: aria-labelledby does not reference local title/description IDs")

    for node in root.iter():
        tag = local_name(node.tag)
        if tag in {"script", "foreignobject"}:
            errors.append(f"{artifact_id}: prohibited {tag} element")
        for raw_name, raw_value in node.attrib.items():
            attr = local_name(raw_name)
            value = raw_value.strip()
            if attr.startswith("on"):
                errors.append(f"{artifact_id}: prohibited script event attribute {attr}")
            if attr == "href" and value and not value.startswith("#"):
                errors.append(f"{artifact_id}: external or embedded asset reference {value!r}")
            if attr == "style":
                validate_css(value, artifact_id, errors)
        if tag == "style":
            validate_css("".join(node.itertext()), artifact_id, errors)

    if artifact.get("role") == "primary-output":
        contract = artifact.get("required_content")
        if not isinstance(contract, dict):
            errors.append(f"{artifact_id}: primary card has no required_content contract")
            return
        visible = " ".join(
            " ".join(node.itertext()).strip()
            for node in root.iter()
            if local_name(node.tag) == "text"
        )
        haystack = normalized(visible)
        for field in REQUIRED_PRIMARY_CONTENT:
            expected = contract.get(field)
            if not isinstance(expected, str) or not expected.strip():
                errors.append(f"{artifact_id}: required_content.{field} is missing")
            elif normalized(expected) not in haystack:
                errors.append(f"{artifact_id}: required {field} text not found: {expected!r}")


def validate_css(css: str, artifact_id: str, errors: list[str]) -> None:
    if re.search(r"@import\b", css, flags=re.IGNORECASE):
        errors.append(f"{artifact_id}: external CSS import is prohibited")
    for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", css, flags=re.IGNORECASE):
        target = match.group(2).strip()
        if target and not target.startswith("#"):
            errors.append(f"{artifact_id}: external CSS asset is prohibited: {target!r}")


def metric_overall_pass(metrics: Any) -> bool:
    if not isinstance(metrics, dict):
        return False
    return any(metrics.get(key) is True for key in OVERALL_METRIC_KEYS)


def validate_content_fidelity(
    iteration: dict[str, Any],
    artifact_paths: dict[str, Path],
    errors: list[str],
) -> None:
    loop_id = iteration.get("id", "<unknown>")
    fidelity_artifact = next(
        (
            artifact
            for artifact in iteration.get("artifacts", [])
            if isinstance(artifact, dict) and artifact.get("role") == "context-fidelity"
        ),
        None,
    )
    if fidelity_artifact is None:
        errors.append(f"{loop_id}: passing content_fidelity gate has no external evidence")
        return
    fidelity_path = artifact_paths.get(fidelity_artifact.get("id"))
    evidence = (
        load_json(fidelity_path, errors, f"{loop_id} content fidelity")
        if fidelity_path and fidelity_path.is_file()
        else None
    )
    if not isinstance(evidence, dict):
        return
    expected = evidence.get("expected_primary_title")
    actual = evidence.get("actual_primary_title")
    if (
        not isinstance(expected, str)
        or not expected.strip()
        or actual != expected
        or evidence.get("status") != "pass"
    ):
        errors.append(f"{loop_id}: external content-fidelity evidence does not pass")
        return

    primary_artifact = next(
        (
            artifact
            for artifact in iteration.get("artifacts", [])
            if isinstance(artifact, dict) and artifact.get("role") == "primary-output"
        ),
        None,
    )
    primary_path = (
        artifact_paths.get(primary_artifact.get("id"))
        if isinstance(primary_artifact, dict)
        else None
    )
    if primary_path is None or not primary_path.is_file():
        errors.append(f"{loop_id}: content-fidelity gate has no primary Artifact")
        return
    try:
        root = ET.parse(primary_path).getroot()
    except (OSError, ET.ParseError) as exc:
        errors.append(f"{loop_id}: cannot inspect primary content fidelity: {exc}")
        return
    accessible_titles = [
        " ".join(node.itertext()).strip()
        for node in root.iter()
        if local_name(node.tag) == "title"
    ]
    if not any(expected in title for title in accessible_titles):
        errors.append(
            f"{loop_id}: canonical title is absent from primary SVG metadata: {expected!r}"
        )


def validate_manifest(manifest_path: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"artifacts": 0, "svgs": 0, "gate_qualified": 0}
    manifest = load_json(manifest_path, errors, "manifest")
    if not isinstance(manifest, dict):
        return errors, counts
    if manifest.get("schema_version") != "1.1":
        errors.append("manifest: schema_version must be 1.1")

    iterations = manifest.get("iterations")
    if not isinstance(iterations, list):
        errors.append("manifest: iterations must be an array")
        return errors, counts

    root = manifest_path.parent.resolve()
    seen_ids: set[str] = set()
    artifact_paths: dict[str, Path] = {}
    artifact_records: dict[str, dict[str, Any]] = {}

    for iteration in iterations:
        if not isinstance(iteration, dict):
            errors.append("manifest: non-object iteration")
            continue
        loop_id = iteration.get("id", "<unknown>")
        artifacts = iteration.get("artifacts")
        if not isinstance(artifacts, list):
            errors.append(f"{loop_id}: artifacts must be an array")
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                errors.append(f"{loop_id}: non-object artifact")
                continue
            counts["artifacts"] += 1
            artifact_id = artifact.get("id")
            if not isinstance(artifact_id, str) or not artifact_id:
                errors.append(f"{loop_id}: artifact ID is missing")
                continue
            if artifact_id in seen_ids:
                errors.append(f"{artifact_id}: duplicate artifact ID")
                continue
            seen_ids.add(artifact_id)
            artifact_records[artifact_id] = artifact
            path = safe_artifact_path(root, artifact.get("path"), errors, artifact_id)
            if path is None:
                continue
            artifact_paths[artifact_id] = path
            if not path.is_file():
                errors.append(f"{artifact_id}: file does not exist: {artifact.get('path')}")
                continue
            expected_hash = artifact.get("sha256")
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if expected_hash != actual_hash:
                errors.append(f"{artifact_id}: SHA-256 mismatch")

            presentation = artifact.get("presentation", {})
            if presentation.get("featured") and presentation.get("mode") in {"svg", "image", "interactive_html"}:
                for field in ("caption", "alt_text", "comparison_key"):
                    if not isinstance(presentation.get(field), str) or not presentation[field].strip():
                        errors.append(f"{artifact_id}: featured visual has no {field}")

            if path.suffix.lower() == ".svg":
                counts["svgs"] += 1
                validate_svg(path, artifact, errors)

    aggregate_artifact = next(
        (
            artifact
            for artifact in artifact_records.values()
            if artifact.get("role") == "panel-aggregate"
            and str(artifact.get("path", "")).lower().endswith(".json")
        ),
        None,
    )
    aggregate = None
    if aggregate_artifact is None:
        errors.append("manifest: JSON independent panel aggregate artifact is missing")
    else:
        aggregate_path = artifact_paths.get(aggregate_artifact["id"])
        if aggregate_path and aggregate_path.is_file():
            aggregate = load_json(aggregate_path, errors, "panel aggregate")

    for iteration in iterations:
        if not isinstance(iteration, dict):
            continue
        loop_id = iteration.get("id", "<unknown>")
        gates = iteration.get("quality_gates", {})
        if not isinstance(gates, dict):
            errors.append(f"{loop_id}: quality_gates must be an object")
            continue
        all_gates_pass = bool(gates) and all(
            verdict == "pass" for verdict in gates.values()
        )

        if isinstance(aggregate, dict):
            panel_loop = aggregate.get("loops", {}).get(loop_id)
            if not isinstance(panel_loop, dict):
                errors.append(f"{loop_id}: independent panel verdict is missing")
            else:
                panel_gates = panel_loop.get("objective_gate_verdict", {})
                for gate_id, verdict in gates.items():
                    if panel_gates.get(gate_id) != verdict:
                        errors.append(
                            f"{loop_id}: {gate_id} gate disagrees with independent panel"
                        )

        if iteration.get("decision") == "new_best" and not all_gates_pass:
            errors.append(f"{loop_id}: new_best decision has a failed or missing gate")

        if all_gates_pass:
            counts["gate_qualified"] += 1
            metrics_artifact = next(
                (
                    artifact
                    for artifact in iteration.get("artifacts", [])
                    if isinstance(artifact, dict) and artifact.get("role") == "layout-metrics"
                ),
                None,
            )
            if metrics_artifact is None:
                errors.append(f"{loop_id}: passing loop has no layout metrics")
                continue
            metrics_path = artifact_paths.get(metrics_artifact.get("id"))
            metrics = (
                load_json(metrics_path, errors, f"{loop_id} metrics")
                if metrics_path and metrics_path.is_file()
                else None
            )
            if not metric_overall_pass(metrics):
                errors.append(f"{loop_id}: passing gates lack a true recorded overall metrics verdict")
            panel_loop = aggregate.get("loops", {}).get(loop_id, {}) if isinstance(aggregate, dict) else {}
            panel_gates = panel_loop.get("objective_gate_verdict", {})
            if any(panel_gates.get(gate_id) != "pass" for gate_id in gates):
                errors.append(f"{loop_id}: passing gates lack an independent panel pass verdict")
            if gates.get("content_fidelity") == "pass":
                validate_content_fidelity(iteration, artifact_paths, errors)

    champion = manifest.get("champion")
    champion_id = champion.get("iteration_id") if isinstance(champion, dict) else None
    champion_iteration = next(
        (
            iteration
            for iteration in iterations
            if isinstance(iteration, dict) and iteration.get("id") == champion_id
        ),
        None,
    )
    if not isinstance(champion_iteration, dict):
        errors.append("manifest: Champion iteration is missing")
    else:
        champion_gates = champion_iteration.get("quality_gates", {})
        if not isinstance(champion_gates, dict) or not champion_gates or any(
            verdict != "pass" for verdict in champion_gates.values()
        ):
            errors.append("manifest: Champion has a failed or missing quality gate")

    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="manifest.json", help="manifest path")
    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()
    errors, counts = validate_manifest(manifest_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} validation error(s)", file=sys.stderr)
        return 1
    print(
        "PASS: "
        f"{counts['artifacts']} artifacts, {counts['svgs']} SVGs, "
        f"{counts['gate_qualified']} gate-qualified loops; "
        "layout evidence = recorded metrics + independent panel verdicts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
