from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

from ._model import CheckResult, EvidenceReport
from ._static_viewer import (
    check_accessibility,
    check_embedded_json,
    check_javascript,
    check_links,
    check_self_contained,
)


def _pass(name: str, **detail: object) -> CheckResult:
    return CheckResult(name, "pass", detail)


def _fail(name: str, **detail: object) -> CheckResult:
    return CheckResult(name, "fail", detail)


def _blocked(name: str, reason: str) -> CheckResult:
    return CheckResult(name, "blocked", {"reason": reason})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema_check(data: dict[str, object], schema_path: Path) -> CheckResult:
    if importlib.util.find_spec("jsonschema") is None:
        return _blocked(
            "manifest_schema",
            "jsonschema==4.25.1 is required; run `python -m pip install -r requirements.txt`",
        )
    import jsonschema

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
        errors = sorted(
            validator_class(schema).iter_errors(data),
            key=lambda error: list(error.absolute_path),
        )
    except (OSError, json.JSONDecodeError, jsonschema.exceptions.SchemaError) as exc:
        return _blocked("manifest_schema", f"schema unavailable: {exc}")
    if errors:
        messages = []
        for error in errors[:20]:
            location = "/".join(str(part) for part in error.absolute_path) or "<root>"
            messages.append(f"{location}: {error.message}")
        return _fail("manifest_schema", errors=messages)
    return _pass("manifest_schema", schema_version=data.get("schema_version"))


def _duplicates(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            duplicates.add(text)
        seen.add(text)
    return sorted(duplicates)


def _has_cycle(iterations: dict[str, dict[str, object]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(iteration_id: str) -> bool:
        if iteration_id in visiting:
            return True
        if iteration_id in visited:
            return False
        visiting.add(iteration_id)
        parents = iterations.get(iteration_id, {}).get("parent_ids")
        for parent_id in parents if isinstance(parents, list) else []:
            if str(parent_id) in iterations and visit(str(parent_id)):
                return True
        visiting.remove(iteration_id)
        visited.add(iteration_id)
        return False

    return any(visit(iteration_id) for iteration_id in iterations)


def _semantic_check(data: dict[str, object]) -> CheckResult:
    tracks_list = data.get("tracks")
    iterations_list = data.get("iterations")
    tracks = tracks_list if isinstance(tracks_list, list) else []
    iterations = iterations_list if isinstance(iterations_list, list) else []
    errors: list[str] = []

    track_ids = [
        track.get("id") for track in tracks if isinstance(track, dict) and track.get("id")
    ]
    iteration_objects = [
        iteration for iteration in iterations if isinstance(iteration, dict)
    ]
    iteration_ids = [
        iteration.get("id") for iteration in iteration_objects if iteration.get("id")
    ]
    criteria = [
        criterion
        for criterion in (data.get("scorecard") or [])
        if isinstance(criterion, dict)
    ]
    criterion_ids = [
        criterion.get("id") for criterion in criteria if criterion.get("id")
    ]
    scorers = [
        scorer for scorer in (data.get("scorers") or []) if isinstance(scorer, dict)
    ]
    scorer_ids_list = [
        scorer.get("id") for scorer in scorers if scorer.get("id")
    ]
    for duplicate in _duplicates(track_ids):
        errors.append(f"duplicate Track id: {duplicate}")
    for duplicate in _duplicates(iteration_ids):
        errors.append(f"duplicate Loop id: {duplicate}")
    for duplicate in _duplicates(criterion_ids):
        errors.append(f"duplicate criterion id: {duplicate}")
    for duplicate in _duplicates(scorer_ids_list):
        errors.append(f"duplicate scorer id: {duplicate}")

    track_set = {str(value) for value in track_ids}
    iteration_map = {
        str(iteration["id"]): iteration
        for iteration in iteration_objects
        if iteration.get("id")
    }
    for iteration in iteration_objects:
        iteration_id = str(iteration.get("id", "<unknown>"))
        track_id = str(iteration.get("track_id", ""))
        if track_id not in track_set:
            errors.append(f"Loop {iteration_id} references unknown Track {track_id}")
        parent_ids = iteration.get("parent_ids")
        for parent_id in parent_ids if isinstance(parent_ids, list) else []:
            if str(parent_id) not in iteration_map:
                errors.append(f"Loop {iteration_id} references unknown parent {parent_id}")
            if str(parent_id) == iteration_id:
                errors.append(f"Loop {iteration_id} references itself as a parent")

    if _has_cycle(iteration_map):
        errors.append("Loop lineage contains a cycle")

    champion = data.get("champion")
    champion_id = champion.get("iteration_id") if isinstance(champion, dict) else None
    if champion_id not in iteration_map:
        errors.append(f"Champion references unknown Loop {champion_id}")
    elif iteration_map[str(champion_id)].get("decision") != "new_best":
        errors.append(f"Champion Loop {champion_id} is not marked new_best")

    criterion_set = {str(value) for value in criterion_ids}
    scorer_ids = {str(value) for value in scorer_ids_list}
    scorer_criteria: dict[str, set[str]] = {}
    for scorer in scorers:
        scorer_id = str(scorer.get("id", ""))
        assigned = {
            str(value)
            for value in (
                scorer.get("criterion_ids")
                if isinstance(scorer.get("criterion_ids"), list)
                else []
            )
        }
        scorer_criteria[scorer_id] = assigned
        for criterion_id in assigned - criterion_set:
            errors.append(
                f"scorer {scorer_id} references unknown criterion {criterion_id}"
            )

    artifact_ids: list[object] = []
    artifact_owner: dict[str, str] = {}
    comparison_keys: dict[str, int] = {}
    for iteration in iteration_objects:
        primary_artifacts = 0
        for artifact in iteration.get("artifacts") or []:
            if not isinstance(artifact, dict):
                continue
            artifact_id = artifact.get("id")
            if artifact_id:
                artifact_ids.append(artifact_id)
                artifact_owner[str(artifact_id)] = str(iteration.get("id"))
            presentation = artifact.get("presentation")
            if isinstance(presentation, dict):
                if presentation.get("primary") is True:
                    primary_artifacts += 1
                comparison_key = presentation.get("comparison_key")
                if comparison_key:
                    key = str(comparison_key)
                    comparison_keys[key] = comparison_keys.get(key, 0) + 1
        if primary_artifacts != 1:
            errors.append(
                f"Loop {iteration.get('id')} must declare exactly one primary Artifact"
            )
        for score in iteration.get("scores") or []:
            if not isinstance(score, dict):
                continue
            scorer_id = str(score.get("scorer_id", ""))
            if scorer_ids and scorer_id not in scorer_ids:
                errors.append(
                    f"Loop {iteration.get('id')} references unknown scorer {scorer_id}"
                )
            criterion_id = str(score.get("criterion_id", ""))
            if criterion_id not in criterion_set:
                errors.append(
                    f"Loop {iteration.get('id')} references unknown criterion {criterion_id}"
                )
            elif scorer_id in scorer_criteria and criterion_id not in scorer_criteria[scorer_id]:
                errors.append(
                    f"Loop {iteration.get('id')} scorer {scorer_id} is not assigned criterion {criterion_id}"
                )

    for duplicate in _duplicates(artifact_ids):
        errors.append(f"duplicate Artifact id: {duplicate}")
    artifact_set = {str(value) for value in artifact_ids}

    for criterion in criteria:
        baseline = criterion.get("baseline")
        if isinstance(baseline, dict):
            source = str(baseline.get("source_artifact_id", ""))
            if source not in artifact_set:
                errors.append(
                    f"criterion {criterion.get('id')} baseline references unknown Artifact {source}"
                )
    primary_count = sum(criterion.get("primary") is True for criterion in criteria)
    if primary_count != 1:
        errors.append("scorecard must declare exactly one primary criterion")

    story = data.get("story")
    if isinstance(story, dict):
        for milestone in story.get("milestones") or []:
            if isinstance(milestone, dict) and milestone.get("iteration_id") not in iteration_map:
                errors.append(
                    f"story milestone references unknown Loop {milestone.get('iteration_id')}"
                )
        featured_id = str(story.get("featured_artifact_id", ""))
        if featured_id not in artifact_set:
            errors.append(f"story references unknown featured Artifact {featured_id}")
        elif champion_id and artifact_owner.get(featured_id) != str(champion_id):
            errors.append("featured Artifact must belong to the Champion Loop")
        comparison_key = str(story.get("primary_comparison_key", ""))
        if comparison_keys.get(comparison_key, 0) < 2:
            errors.append(
                f"primary comparison key {comparison_key!r} must appear on at least two Artifacts"
            )

    evidence_refs = criterion_set | artifact_set
    if isinstance(champion, dict):
        for section in ("reasons", "caveats"):
            for reason in champion.get(section) or []:
                if not isinstance(reason, dict):
                    continue
                for reference in reason.get("evidence_refs") or []:
                    if str(reference) not in evidence_refs:
                        errors.append(
                            f"Champion {section[:-1]} references unknown evidence {reference}"
                        )

    generation = data.get("generation")
    declared_models = {
        str(model.get("model_id"))
        for model in (
            generation.get("models", [])
            if isinstance(generation, dict)
            else []
        )
        if isinstance(model, dict) and model.get("model_id")
    }
    for iteration in iteration_objects:
        model_id = str(iteration.get("model_id", ""))
        if model_id not in declared_models:
            errors.append(
                f"Loop {iteration.get('id')} uses undeclared model {model_id}"
            )

    if errors:
        return _fail("manifest_semantics", errors=errors[:30])
    return _pass(
        "manifest_semantics",
        tracks=len(track_set),
        loops=len(iteration_map),
        champion=champion_id,
    )


def _artifact_check(data: dict[str, object], run_dir: Path) -> CheckResult:
    missing: list[str] = []
    invalid: list[str] = []
    hash_mismatches: list[str] = []
    checked = 0

    artifact_groups = []
    for iteration in data.get("iterations") or []:
        if isinstance(iteration, dict):
            artifact_groups.append(iteration.get("artifacts") or [])

    run_root = run_dir.resolve()
    for group in artifact_groups:
        for artifact in group:
            if not isinstance(artifact, dict):
                continue
            for key in ("path",):
                value = artifact.get(key)
                if not value:
                    continue
                checked += 1
                relative = Path(str(value))
                if relative.is_absolute():
                    invalid.append(str(value))
                    continue
                resolved = (run_dir / relative).resolve()
                try:
                    resolved.relative_to(run_root)
                except ValueError:
                    invalid.append(str(value))
                    continue
                if not resolved.exists():
                    missing.append(str(value))
                    continue
                expected = artifact.get("sha256")
                if expected and _sha256(resolved).lower() != str(expected).lower():
                    hash_mismatches.append(str(value))
    if missing or invalid or hash_mismatches:
        return _fail(
            "artifact_integrity",
            checked=checked,
            missing=sorted(set(missing)),
            invalid=sorted(set(invalid)),
            hash_mismatches=sorted(set(hash_mismatches)),
        )
    return _pass("artifact_integrity", checked=checked)


def _run_builder(
    build_script: Path, data_dir: Path, output: Path
) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(build_script),
                "--data",
                str(data_dir),
                "--out",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, str(exc)
    return result, None


def _viewer_checks(run_dir: Path) -> tuple[CheckResult, ...]:
    viewer = run_dir / "viewer.html"
    build_script = run_dir / "build_viewer.py"
    if not viewer.exists():
        return (
            _fail("viewer_present", missing="viewer.html"),
            _blocked("viewer_determinism", "viewer.html is missing"),
            _blocked("viewer_static", "viewer.html is missing"),
        )
    present = _pass("viewer_present", bytes=viewer.stat().st_size)
    if not build_script.exists():
        return (
            present,
            _fail("viewer_determinism", missing="build_viewer.py"),
            _blocked("viewer_static", "build_viewer.py is missing"),
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        first, second = temp / "first.html", temp / "second.html"
        result_a, error_a = _run_builder(build_script, run_dir, first)
        result_b, error_b = _run_builder(build_script, run_dir, second)
        if error_a or error_b:
            determinism = _blocked(
                "viewer_determinism", f"could not run build_viewer.py: {error_a or error_b}"
            )
        elif (
            not result_a
            or not result_b
            or result_a.returncode != 0
            or result_b.returncode != 0
            or not first.exists()
            or not second.exists()
        ):
            stderr = ""
            if result_a:
                stderr += result_a.stderr[-500:]
            if result_b:
                stderr += result_b.stderr[-500:]
            determinism = _fail("viewer_determinism", error=stderr or "build failed")
        else:
            first_bytes = first.read_bytes()
            second_bytes = second.read_bytes()
            committed_bytes = viewer.read_bytes()
            if first_bytes != second_bytes:
                determinism = _fail("viewer_determinism", error="two builds differ")
            elif first_bytes != committed_bytes:
                determinism = _fail(
                    "viewer_determinism", error="committed viewer.html is stale"
                )
            else:
                determinism = _pass(
                    "viewer_determinism",
                    sha256=hashlib.sha256(first_bytes).hexdigest(),
                    bytes=len(first_bytes),
                )

    html = viewer.read_text(encoding="utf-8", errors="replace")
    node = shutil.which("node")
    static_results = [
        ("self_contained", check_self_contained(html)),
        ("embedded_json", check_embedded_json(html)),
        ("javascript", check_javascript(html, node_command=node)),
        ("links", check_links(html, viewer)),
        ("accessibility", check_accessibility(html)),
    ]
    failures = {}
    blocked = {}
    for name, (ok, detail) in static_results:
        if ok is None:
            blocked[name] = detail
        elif not ok:
            failures[name] = detail
    if blocked:
        static = _blocked("viewer_static", json.dumps(blocked, sort_keys=True))
    elif failures:
        static = _fail("viewer_static", failures=failures)
    else:
        static = _pass(
            "viewer_static", checks=[name for name, _ in static_results]
        )
    return present, determinism, static


def _navigation_check(run_dir: Path, viewer: Path) -> CheckResult:
    evidence_path = run_dir / "navigation-evidence.json"
    if not evidence_path.exists():
        return _fail("navigation_evidence", missing="navigation-evidence.json")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _fail("navigation_evidence", error=str(exc))
    if not isinstance(evidence, dict):
        return _fail("navigation_evidence", error="root must be an object")
    expected_hash = _sha256(viewer) if viewer.exists() else None
    errors = []
    if evidence.get("status") != "pass":
        errors.append(f"status is {evidence.get('status')!r}")
    if evidence.get("viewer_sha256") != expected_hash:
        errors.append("viewer_sha256 does not match viewer.html")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty array")
    else:
        failed = [
            check.get("name", "<unnamed>")
            for check in checks
            if not isinstance(check, dict) or check.get("status") != "pass"
        ]
        if failed:
            errors.append(f"non-passing checks: {failed}")
    if errors:
        return _fail("navigation_evidence", errors=errors)
    return _pass(
        "navigation_evidence",
        viewer_sha256=expected_hash,
        browser=evidence.get("browser"),
    )


def validate_experiment(run_dir: Path | str) -> EvidenceReport:
    run_path = Path(run_dir).resolve()
    checks: list[CheckResult] = []
    manifest_path = run_path / "manifest.json"
    data: dict[str, object] | None = None

    if not manifest_path.exists():
        checks.append(_fail("manifest_parse", missing="manifest.json"))
    else:
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(_fail("manifest_parse", error=str(exc)))
        else:
            if isinstance(loaded, dict):
                data = loaded
                checks.append(_pass("manifest_parse"))
            else:
                checks.append(_fail("manifest_parse", error="root must be an object"))

    schema_path = Path(__file__).resolve().parents[1] / "manifest-schema-v1.1.json"
    if data is None:
        checks.extend(
            [
                _blocked("manifest_schema", "manifest did not parse"),
                _blocked("manifest_semantics", "manifest did not parse"),
                _blocked("artifact_integrity", "manifest did not parse"),
            ]
        )
    else:
        checks.append(_schema_check(data, schema_path))
        checks.append(_semantic_check(data))
        checks.append(_artifact_check(data, run_path))

    checks.extend(_viewer_checks(run_path))
    checks.append(_navigation_check(run_path, run_path / "viewer.html"))
    return EvidenceReport(".", tuple(checks))
