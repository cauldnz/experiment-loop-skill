from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import mimetypes
from collections.abc import Mapping
from pathlib import Path

MAX_PREVIEW_BYTES = 1_000_000
MAX_TOTAL_PREVIEW_BYTES = 8_000_000

_TEXT_MODES = {"markdown", "text", "log", "code"}
_JSON_MODES = {"metric_set", "key_value", "structured_json"}


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _dict(value: object) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _judge_feedback_pending(value: object) -> bool:
    normalized = _text(value).strip().upper().replace(" ", "_")
    return not normalized or normalized in {
        "PENDING",
        "PENDING_JUDGE",
        "PENDING_JUDGES",
        "AWAITING_JUDGE",
        "AWAITING_JUDGES",
        "AWAITING_PANEL",
    }


def _loop_track_id(loop: Mapping[str, object]) -> str:
    return _text(loop.get("track_id")) or "unassigned"


def _artifact_preview(
    artifact: dict,
    *,
    data_dir: Path | None,
    remaining_budget: int,
) -> tuple[dict, int]:
    view = dict(artifact)
    presentation = _dict(view.get("presentation"))
    mode = _text(presentation.get("mode")) or "download"
    view["presentation"] = presentation
    view["preview"] = None
    view["safe_href"] = ""
    diagnostics: list[str] = []
    view["diagnostics"] = diagnostics

    if data_dir is None:
        return view, 0

    relative_path = Path(_text(view.get("path")))
    root = data_dir.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        diagnostics.append("Artifact path escapes the Experiment data directory.")
        return view, 0
    view["safe_href"] = relative_path.as_posix()

    if not candidate.is_file():
        diagnostics.append("Artifact file is missing.")
        return view, 0

    size = candidate.stat().st_size
    if size > MAX_PREVIEW_BYTES:
        diagnostics.append("Preview omitted because the Artifact exceeds the 1 MB limit.")
        return view, 0
    if size > remaining_budget:
        diagnostics.append("Preview omitted because the Experiment reached its 8 MB preview budget.")
        return view, 0

    payload = candidate.read_bytes()
    declared_hash = _text(view.get("sha256")).lower()
    actual_hash = hashlib.sha256(payload).hexdigest()
    if declared_hash and declared_hash != actual_hash:
        diagnostics.append("Preview omitted because the Artifact hash does not match the Manifest.")
        return view, 0

    try:
        if mode in {"image", "svg"}:
            mime = "image/svg+xml" if mode == "svg" else (
                mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            )
            if not mime.startswith("image/"):
                diagnostics.append("Preview omitted because the declared image has an unsafe media type.")
                return view, 0
            view["preview"] = {
                "kind": "image",
                "data_uri": f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}",
            }
        elif mode == "interactive_html":
            view["preview"] = {
                "kind": "interactive_html",
                "data_uri": (
                    "data:text/html;base64,"
                    + base64.b64encode(payload).decode("ascii")
                ),
                "sandbox": "allow-scripts",
            }
        elif mode in _JSON_MODES:
            view["preview"] = {
                "kind": "json",
                "value": json.loads(payload.decode("utf-8")),
            }
        elif mode == "table":
            text = payload.decode("utf-8")
            rows = list(csv.reader(io.StringIO(text)))
            view["preview"] = {
                "kind": "table",
                "headers": rows[0] if rows else [],
                "rows": rows[1:101],
                "truncated": len(rows) > 101,
            }
        elif mode in _TEXT_MODES:
            view["preview"] = {
                "kind": "text",
                "language": candidate.suffix.removeprefix("."),
                "value": payload.decode("utf-8"),
            }
        else:
            diagnostics.append("No inline preview is defined for this Artifact presentation mode.")
            return view, 0
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
        diagnostics.append(f"Artifact preview could not be decoded: {exc}.")
        return view, 0

    return view, size


def build_view_model(
    manifest: Mapping[str, object] | object,
    *,
    data_dir: Path | None = None,
    diagnostic: str = "",
) -> dict:
    """Build the deterministic, presentation-safe model consumed by the Viewer."""
    source = dict(manifest) if isinstance(manifest, Mapping) else {}
    criteria = [_dict(item) for item in _list(source.get("scorecard"))]
    criteria_by_id = {_text(item.get("id")): item for item in criteria}
    primary_criterion = next(
        (item for item in criteria if item.get("primary") is True),
        criteria[0] if criteria else {},
    )
    raw_iterations = [_dict(item) for item in _list(source.get("iterations"))]
    tracks = [_dict(item) for item in _list(source.get("tracks"))]
    known_track_ids = {_text(track.get("id")) for track in tracks}
    for loop in raw_iterations:
        track_id = _loop_track_id(loop)
        if track_id in known_track_ids:
            continue
        tracks.append(
            {
                "id": track_id,
                "label": track_id if track_id != "unassigned" else "Unassigned",
                "hypothesis": "Track definition has not been merged yet.",
                "inferred": True,
            }
        )
        known_track_ids.add(track_id)
    track_by_id = {_text(item.get("id")): item for item in tracks}
    champion = _dict(source.get("champion"))
    champion_id = _text(champion.get("iteration_id"))
    diagnostics = [diagnostic] if diagnostic else []

    preview_budget = MAX_TOTAL_PREVIEW_BYTES
    artifact_index: dict[str, dict] = {}
    loops: list[dict] = []
    track_positions: dict[str, int] = {}
    for index, loop in enumerate(raw_iterations):
        artifacts: list[dict] = []
        for raw_artifact in _list(loop.get("artifacts")):
            artifact, used = _artifact_preview(
                _dict(raw_artifact),
                data_dir=data_dir,
                remaining_budget=preview_budget,
            )
            preview_budget -= used
            artifact_id = _text(artifact.get("id"))
            if artifact_id:
                artifact_index[artifact_id] = artifact
            artifacts.append(artifact)

        scores = [_dict(item) for item in _list(loop.get("scores"))]
        score_values = {
            _text(score.get("criterion_id")): score.get("value")
            for score in scores
        }
        track_id = _loop_track_id(loop)
        track_index = track_positions.get(track_id, 0)
        track_positions[track_id] = track_index + 1
        primary_artifact = next(
            (
                artifact
                for artifact in artifacts
                if _dict(artifact.get("presentation")).get("primary") is True
            ),
            artifacts[0] if artifacts else None,
        )
        prompt = _dict(loop.get("prompt"))
        pending_fields = []
        if not artifacts:
            pending_fields.append("artifacts")
        if not scores:
            pending_fields.append("scores")
        if _judge_feedback_pending(prompt.get("judge_feedback")):
            pending_fields.append("judge feedback")
        loops.append(
            {
                **loop,
                "index": index,
                "track_index": track_index,
                "label": _text(loop.get("label")) or _text(loop.get("id")),
                "track_label": _text(track_by_id.get(track_id, {}).get("label")) or track_id,
                "parent_ids": _list(loop.get("parent_ids")),
                "is_champion": _text(loop.get("id")) == champion_id,
                "artifacts": artifacts,
                "primary_artifact": primary_artifact,
                "scores": scores,
                "score_values": score_values,
                "primary_value": score_values.get(_text(primary_criterion.get("id"))),
                "judge_feedback_pending": "judge feedback" in pending_fields,
                "pending_fields": pending_fields,
                "is_pending": bool(pending_fields),
            }
        )

    loop_index = {_text(loop.get("id")): loop for loop in loops}
    topology_depths: dict[str, int] = {}

    def topology_depth(loop_id: str, visiting: frozenset[str] = frozenset()) -> int:
        if loop_id in topology_depths:
            return topology_depths[loop_id]
        if loop_id in visiting:
            return 0
        loop = loop_index.get(loop_id, {})
        parent_depths = [
            topology_depth(str(parent_id), visiting | {loop_id})
            for parent_id in _list(loop.get("parent_ids"))
            if str(parent_id) in loop_index
        ]
        depth = max(parent_depths, default=-1) + 1
        topology_depths[loop_id] = depth
        return depth

    for loop in loops:
        loop["topology_depth"] = topology_depth(_text(loop.get("id")))

    champion_is_merged = bool(champion_id and champion_id in loop_index)
    has_pending_evidence = any(bool(loop.get("is_pending")) for loop in loops)
    is_in_progress = not champion_is_merged or has_pending_evidence
    if champion_id and not champion_is_merged:
        diagnostics.append(
            f"Champion Loop {champion_id!r} has not been merged; "
            "the Viewer remains in progress."
        )

    for track in tracks:
        column = -1
        track_id = _text(track.get("id"))
        for loop in (item for item in loops if item.get("track_id") == track_id):
            column = max(column + 1, int(loop["topology_depth"]))
            loop["topology_column"] = column

    enriched_tracks: list[dict] = []
    for track in tracks:
        track_id = _text(track.get("id"))
        track_loops = [loop for loop in loops if loop.get("track_id") == track_id]
        first_loop = min(
            track_loops,
            key=lambda loop: (loop.get("topology_depth", 0), loop.get("index", 0)),
            default=None,
        )
        starts_after: list[str] = []
        if first_loop:
            for parent_id in _list(first_loop.get("parent_ids")):
                parent = loop_index.get(str(parent_id))
                if parent and parent.get("track_id") != track_id:
                    label = _text(parent.get("track_label")) or _text(parent.get("id"))
                    if label not in starts_after:
                        starts_after.append(label)
        enriched_tracks.append(
            {
                **track,
                "starts_after": starts_after,
                "loop_count": len(track_loops),
                "is_empty": not track_loops,
            }
        )

    story = _dict(source.get("story"))
    featured_id = _text(story.get("featured_artifact_id"))
    featured_artifact = artifact_index.get(featured_id)
    if featured_id and featured_artifact is None:
        diagnostics.append(f"Featured Artifact {featured_id!r} was not found.")

    human_scorers = [
        scorer
        for scorer in (_dict(item) for item in _list(source.get("scorers")))
        if scorer.get("type") == "human_review"
    ]
    human_criterion_ids = {
        _text(criterion_id)
        for scorer in human_scorers
        for criterion_id in _list(scorer.get("criterion_ids"))
    }
    if data_dir is not None and (data_dir / "manifest.json").is_file():
        manifest_sha256 = hashlib.sha256(
            (data_dir / "manifest.json").read_bytes()
        ).hexdigest()
    else:
        manifest_sha256 = hashlib.sha256(
            json.dumps(
                source,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    return {
        "schema_version": _text(source.get("schema_version")),
        "experiment_id": _text(source.get("experiment_id")),
        "title": _text(source.get("title")) or "Experiment Viewer",
        "problem": _dict(source.get("problem")),
        "generation": _dict(source.get("generation")),
        "criteria": criteria,
        "primary_criterion": primary_criterion,
        "scorers": [_dict(item) for item in _list(source.get("scorers"))],
        "tracks": enriched_tracks,
        "loops": loops,
        "champion": champion,
        "story": story,
        "featured_artifact": featured_artifact,
        "status": {
            "is_in_progress": is_in_progress,
            "iteration_count": len(loops),
            "pending_iteration_count": sum(
                bool(loop.get("is_pending")) for loop in loops
            ),
            "evidence_gate": (
                "not_final"
                if is_in_progress
                else "final_output_requires_verification"
            ),
        },
        "human_review_enabled": bool(human_scorers),
        "human_review_criteria": [
            criterion
            for criterion in criteria
            if _text(criterion.get("id")) in human_criterion_ids
        ],
        "binding": {
            "manifest_sha256": manifest_sha256,
            "viewer_sha256": "0" * 64,
            "viewer_hash_algorithm": "canonical-html-zeroed-binding-v1",
        },
        "diagnostics": diagnostics,
        "raw_manifest": source,
        "preview_budget": {
            "limit": MAX_TOTAL_PREVIEW_BYTES,
            "used": MAX_TOTAL_PREVIEW_BYTES - preview_budget,
        },
    }
