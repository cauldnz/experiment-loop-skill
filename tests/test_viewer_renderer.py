from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from references.viewer_renderer import ViewerProfile, render_viewer
from references.viewer_renderer.cli import (
    WatchDebouncer,
    build_viewer,
    main,
    poll_watch_inputs,
    snapshot_watch_inputs,
    watch_viewer,
)
from references.viewer_renderer._renderer import canonical_viewer_sha256
from references.viewer_renderer._viewmodel import build_view_model


ROOT = Path(__file__).resolve().parents[1]


class ViewerRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "templates" / "manifest-template.json").read_text(encoding="utf-8")
        )

    def test_render_is_deterministic_and_embeds_contract(self) -> None:
        first = render_viewer(self.manifest)
        second = render_viewer(self.manifest)
        view_model = build_view_model(self.manifest)
        self.assertEqual(first, second)
        self.assertFalse(view_model["status"]["is_in_progress"])
        self.assertIn('id="interaction-contract"', first)
        self.assertIn('id="tab-overview"', first)
        self.assertIn('id="tab-topology"', first)
        self.assertIn('id="tab-compare"', first)
        self.assertIn('"version":"1.1"', first)
        self.assertIn("Original Experiment Prompt", first)
        self.assertIn("Judge feedback", first)
        self.assertIn("--cp-accent: #b11f4b", first)
        binding = re.search(r'"viewer_sha256":"([a-f0-9]{64})"', first)
        self.assertIsNotNone(binding)
        self.assertEqual(binding.group(1), canonical_viewer_sha256(first))

    def test_samples_profile_adds_curated_panel(self) -> None:
        rendered = render_viewer(
            {**self.manifest, "samples": []},
            profile=ViewerProfile(extra_panels=("samples",)),
        )
        self.assertIn('id="tab-samples"', rendered)
        self.assertIn('"selector":"#tab-samples"', rendered)

    def test_profile_rejects_unknown_and_duplicate_panels(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown"):
            ViewerProfile(extra_panels=("unknown",))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ViewerProfile(extra_panels=("samples", "samples"))

    def test_topology_depth_is_scoped_to_each_track(self) -> None:
        self.manifest["tracks"].append(
            {"id": "second-track", "label": "Second", "hypothesis": "Try another path."}
        )
        extra = json.loads(json.dumps(self.manifest["iterations"][0]))
        extra["id"] = "loop-second-001"
        extra["track_id"] = "second-track"
        extra["parent_ids"] = []
        extra["artifacts"][0]["id"] = "second-result"
        self.manifest["iterations"].insert(1, extra)
        view_model = build_view_model(self.manifest)

        depths = {loop["id"]: loop["topology_depth"] for loop in view_model["loops"]}
        self.assertEqual(0, depths["loop-001"])
        self.assertEqual(0, depths["loop-second-001"])
        self.assertEqual(1, depths["loop-002"])

    def test_multi_parent_track_starts_after_both_parent_tracks(self) -> None:
        self.manifest["tracks"].extend(
            [
                {"id": "second", "label": "Second", "hypothesis": "Second parent."},
                {"id": "synthesis", "label": "Synthesis", "hypothesis": "Combine."},
            ]
        )
        second = json.loads(json.dumps(self.manifest["iterations"][0]))
        second.update({"id": "second-001", "track_id": "second", "parent_ids": []})
        second["artifacts"][0]["id"] = "second-result"
        synthesis = json.loads(json.dumps(self.manifest["iterations"][1]))
        synthesis.update(
            {
                "id": "synthesis-001",
                "track_id": "synthesis",
                "parent_ids": ["loop-002", "second-001"],
            }
        )
        synthesis["artifacts"][0]["id"] = "synthesis-result"
        self.manifest["iterations"].extend([second, synthesis])

        view_model = build_view_model(self.manifest)
        loops = {loop["id"]: loop for loop in view_model["loops"]}
        track = next(item for item in view_model["tracks"] if item["id"] == "synthesis")

        self.assertEqual(2, loops["synthesis-001"]["topology_depth"])
        self.assertCountEqual(
            ["Example Track", "Second"],
            track["starts_after"],
        )

    def test_tracks_include_loop_counts_and_explicit_empty_state(self) -> None:
        self.manifest["tracks"].append(
            {"id": "empty-track", "label": "Empty", "hypothesis": "Not started."}
        )

        view_model = build_view_model(self.manifest)
        tracks = {track["id"]: track for track in view_model["tracks"]}

        self.assertEqual(2, tracks["example-track"]["loop_count"])
        self.assertFalse(tracks["example-track"]["is_empty"])
        self.assertEqual(0, tracks["empty-track"]["loop_count"])
        self.assertTrue(tracks["empty-track"]["is_empty"])

    def test_same_depth_loops_in_one_track_receive_distinct_columns(self) -> None:
        branch = json.loads(json.dumps(self.manifest["iterations"][0]))
        branch["id"] = "loop-branch"
        branch["parent_ids"] = []
        branch["artifacts"][0]["id"] = "branch-result"
        self.manifest["iterations"].insert(1, branch)

        view_model = build_view_model(self.manifest)
        loops = {loop["id"]: loop for loop in view_model["loops"]}

        self.assertEqual(0, loops["loop-001"]["topology_column"])
        self.assertEqual(1, loops["loop-branch"]["topology_column"])
        self.assertEqual(2, loops["loop-002"]["topology_column"])

    def test_topology_renders_swimlane_canvas_controls(self) -> None:
        rendered = render_viewer(self.manifest)

        for marker in (
            'id="topology-workspace"',
            'id="graph-viewport"',
            'id="graph-minimap"',
            'id="topology-zoom-in"',
            'id="topology-zoom-out"',
            'id="topology-fit"',
            'id="topology-reset"',
            'id="topology-inspector-toggle"',
            'id="topology-maximize"',
            "track-lane",
            "createCanvasController",
            "loop_count",
        ):
            self.assertIn(marker, rendered)

    def test_bit_quiver_shape_renders_single_loop_tracks_and_synthesis_chain(
        self,
    ) -> None:
        base = self.manifest["iterations"][0]
        tracks = []
        iterations = []
        parent_ids = []
        for index, track_id in enumerate(
            ("openscad", "cadquery", "makerskills", "fusion"),
            start=1,
        ):
            tracks.append(
                {
                    "id": track_id,
                    "label": track_id.title(),
                    "hypothesis": f"Track {index}",
                }
            )
            loop = json.loads(json.dumps(base))
            loop.update(
                {
                    "id": f"{track_id}-loop-01",
                    "track_id": track_id,
                    "parent_ids": [],
                    "decision": "keep_for_synthesis",
                }
            )
            loop["artifacts"][0]["id"] = f"{track_id}-artifact"
            iterations.append(loop)
            parent_ids.append(loop["id"])
        tracks.append(
            {"id": "synthesis", "label": "Synthesis", "hypothesis": "Combine."}
        )
        for number in (1, 2):
            loop = json.loads(json.dumps(base))
            loop.update(
                {
                    "id": f"synthesis-loop-{number:02d}",
                    "track_id": "synthesis",
                    "parent_ids": parent_ids if number == 1 else ["synthesis-loop-01"],
                    "decision": "new_best",
                }
            )
            loop["artifacts"][0]["id"] = f"synthesis-artifact-{number}"
            iterations.append(loop)
        manifest = {
            **self.manifest,
            "tracks": tracks,
            "iterations": iterations,
            "champion": {
                **self.manifest["champion"],
                "iteration_id": "synthesis-loop-02",
            },
        }

        view_model = build_view_model(manifest)
        rendered = render_viewer(manifest)

        self.assertEqual([1, 1, 1, 1, 2], [track["loop_count"] for track in view_model["tracks"]])
        self.assertIn(
            "${tracks.length} Tracks x ${loopDimension} Loops per Track | "
            "${VM.loops.length} iterations total",
            rendered,
        )
        self.assertEqual(
            5,
            sum(len(loop["parent_ids"]) for loop in view_model["loops"]),
        )
        self.assertIn('marker-end="url(#topology-arrow)"', rendered)
        self.assertEqual(
            4,
            sum(
                loop["decision"] == "keep_for_synthesis"
                for loop in view_model["loops"]
            ),
        )
        self.assertIn(".graph-node.keep_for_synthesis", rendered)

    def test_human_review_ui_is_conditional_and_identity_free(self) -> None:
        self.assertNotIn('id="human-review-button"', render_viewer(self.manifest))
        self.manifest["scorers"].append(
            {
                "id": "human",
                "type": "human_review",
                "criterion_ids": ["clarity"],
                "primary": False,
                "weight": 1,
            }
        )

        rendered = render_viewer(self.manifest)

        self.assertIn('id="human-review-button"', rendered)
        self.assertIn("schema-bound JSON sidecar", rendered)
        self.assertIn('"viewer_hash_algorithm":"canonical-html-zeroed-binding-v1"', rendered)
        self.assertNotIn("reviewer identity", rendered.lower().replace("no reviewer identity", ""))

    def test_cli_build_degrades_to_diagnostic_viewer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "viewer.html"
            result = build_viewer(root, output)
            self.assertEqual(0, result)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("manifest.json not found", rendered)
            self.assertIn("<!doctype html>", rendered)

    def test_partial_manifest_is_explicitly_in_progress(self) -> None:
        partial = json.loads(json.dumps(self.manifest))
        partial.pop("story")
        partial["champion"] = {"iteration_id": ""}
        partial["tracks"] = []
        partial["iterations"] = [partial["iterations"][0]]
        loop = partial["iterations"][0]
        loop["track_id"] = "partially-merged-track"
        loop["artifacts"] = []
        loop["scores"] = []
        loop["decision"] = ""
        loop["prompt"]["judge_feedback"] = "PENDING_JUDGES"

        view_model = build_view_model(partial)
        rendered = render_viewer(partial)

        self.assertTrue(view_model["status"]["is_in_progress"])
        self.assertEqual(1, view_model["status"]["iteration_count"])
        self.assertEqual("not_final", view_model["status"]["evidence_gate"])
        self.assertEqual("partially-merged-track", view_model["tracks"][0]["id"])
        self.assertTrue(view_model["tracks"][0]["inferred"])
        self.assertIn("Experiment in progress - ${iterationCount}", rendered)
        self.assertIn('"iteration_count":1', rendered)
        self.assertIn("Only final outputs are gate-verified.", rendered)
        self.assertIn("Awaiting panel", rendered)
        self.assertIn(': "pending";', rendered)
        self.assertIn("Artifact pending or not yet merged.", rendered)
        self.assertIn("No authored milestones have been merged yet.", rendered)
        self.assertTrue(view_model["loops"][0]["judge_feedback_pending"])

    def test_empty_manifest_renders_zero_iteration_progress(self) -> None:
        rendered = render_viewer({})

        self.assertIn("Experiment in progress - ${iterationCount}", rendered)
        self.assertIn('"iteration_count":0', rendered)
        self.assertIn("No Loops merged yet", rendered)
        self.assertIn("No Loops are available to compare yet.", rendered)

    def test_watch_poll_tracks_only_manifest_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            viewer = root / "viewer.html"
            initial = snapshot_watch_inputs(root)

            viewer.write_text("first", encoding="utf-8")
            after_viewer, changed = poll_watch_inputs(root, initial)
            self.assertEqual((), changed)

            manifest = root / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            after_manifest, changed = poll_watch_inputs(root, after_viewer)
            self.assertEqual(("manifest.json",), changed)

            fragment = root / "track-a" / "manifest-fragment.json"
            fragment.parent.mkdir()
            fragment.write_text("{}", encoding="utf-8")
            _, changed = poll_watch_inputs(root, after_manifest)
            self.assertEqual(("track-a/manifest-fragment.json",), changed)

    def test_watch_debouncer_coalesces_bursts(self) -> None:
        debouncer = WatchDebouncer(0.2)

        self.assertFalse(debouncer.observe(True, 1.0))
        self.assertFalse(debouncer.observe(True, 1.1))
        self.assertFalse(debouncer.observe(False, 1.29))
        self.assertTrue(debouncer.observe(False, 1.31))
        self.assertFalse(debouncer.observe(False, 2.0))

    def test_watch_cli_stops_cleanly_on_ctrl_c(self) -> None:
        with patch(
            "references.viewer_renderer.cli.watch_viewer",
            side_effect=KeyboardInterrupt,
        ):
            self.assertEqual(
                0,
                main(["--data", ".", "--out", "viewer.html", "--watch"]),
            )

    def test_watch_rebuilds_after_manifest_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "viewer.html"
            partial = {
                "schema_version": "1.1",
                "experiment_id": "watch-test",
                "title": "Updated while watching",
                "iterations": [],
                "champion": {"iteration_id": ""},
            }
            sleep_calls = 0

            def advance_watch(_seconds: float) -> None:
                nonlocal sleep_calls
                sleep_calls += 1
                if sleep_calls == 1:
                    (root / "manifest.json").write_text(
                        json.dumps(partial),
                        encoding="utf-8",
                    )
                elif sleep_calls == 3:
                    raise KeyboardInterrupt

            with (
                patch("references.viewer_renderer.cli.time.sleep", advance_watch),
                self.assertRaises(KeyboardInterrupt),
            ):
                watch_viewer(root, output, poll_interval=0.01, debounce=0)

            rendered = output.read_text(encoding="utf-8")
            self.assertIn("<title>Updated while watching</title>", rendered)
            self.assertNotIn(".viewer.html.tmp", rendered)

    def test_cli_embeds_hash_verified_visual_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_path = root / "example-track" / "loop-002" / "result.svg"
            artifact_path.parent.mkdir(parents=True)
            payload = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Result</title></svg>'
            artifact_path.write_bytes(payload)
            artifact = self.manifest["iterations"][1]["artifacts"][0]
            artifact["path"] = artifact_path.relative_to(root).as_posix()
            artifact["sha256"] = hashlib.sha256(payload).hexdigest()
            artifact["presentation"].update(
                {
                    "mode": "svg",
                    "alt_text": "A rendered result.",
                    "comparison_key": "primary-output",
                }
            )
            (root / "manifest.json").write_text(
                json.dumps(self.manifest), encoding="utf-8"
            )
            output = root / "viewer.html"

            self.assertEqual(0, build_viewer(root, output))
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("data:image/svg+xml;base64,", rendered)
            self.assertIn('"safe_href":"example-track/loop-002/result.svg"', rendered)

    def test_artifact_path_escape_is_diagnostic_not_embedded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root.parent / "outside-viewer-test.svg"
            payload = b"<svg></svg>"
            outside.write_bytes(payload)
            try:
                artifact = self.manifest["iterations"][1]["artifacts"][0]
                artifact["path"] = "../outside-viewer-test.svg"
                artifact["sha256"] = hashlib.sha256(payload).hexdigest()
                artifact["presentation"].update(
                    {
                        "mode": "svg",
                        "alt_text": "Should not render.",
                        "comparison_key": "primary-output",
                    }
                )
                rendered = render_viewer(self.manifest, data_dir=root)
                self.assertIn(
                    "Artifact path escapes the Experiment data directory.", rendered
                )
                self.assertNotIn("data:image/svg+xml;base64,", rendered)
            finally:
                outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
