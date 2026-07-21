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
        self.assertIn("Human use / friction", first)
        self.assertIn("Not applicable", first)
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

    def test_human_feedback_intake_is_always_available_and_identity_free(self) -> None:
        rendered = render_viewer(self.manifest)

        self.assertIn('id="human-review-button"', rendered)
        self.assertIn("immutable canonical JSON sidecar", rendered)
        self.assertIn("human_feedback_intake", rendered)
        self.assertIn("Validate and download intake JSON", rendered)
        self.assertIn("Human steering", rendered)
        self.assertIn("Model judge feedback", rendered)
        self.assertIn('"viewer_hash_algorithm":"canonical-html-zeroed-binding-v1"', rendered)
        self.assertNotIn(
            "reviewer identity",
            rendered.lower().replace("no reviewer identity", ""),
        )

    def test_applicable_human_use_renders_qualitative_evidence(self) -> None:
        self.manifest["scorecard"].append(
            {
                "id": "human-use-friction",
                "label": "Human-use friction",
                "weight": 1,
                "direction": "maximize",
                "unit": "qualitative points",
                "comparable_across_tracks": True,
                "primary": False,
            }
        )
        self.manifest["scorers"].append(
            {
                "id": "ergonomics-panel",
                "type": "llm_rubric",
                "criterion_ids": ["human-use-friction"],
                "judge_panel": "ergonomics-panel",
                "primary": False,
                "weight": 1,
            }
        )
        findings = [
            {
                "lens": "sharp_contact_edges",
                "finding": "No sharp contact edge observed.",
            },
            {
                "lens": "comfort",
                "finding": "Grip appears comfortable for the intended short use.",
            },
            {
                "lens": "retention",
                "finding": "Inversion evidence shows the retained part stays seated.",
            },
            {
                "lens": "strength_confidence_under_intended_loads",
                "finding": "Section and slicer evidence support qualitative confidence.",
            },
            {
                "lens": "operability",
                "finding": "Insertion and removal remain finger-operable.",
            },
            {
                "lens": "degraded_cosmetic_operations",
                "finding": "No failed fillet or chamfer operation is present.",
            },
        ]
        evidence = []
        for iteration in self.manifest["iterations"]:
            iteration["scores"].append(
                {
                    "scorer_id": "ergonomics-panel",
                    "criterion_id": "human-use-friction",
                    "value": 4,
                    "notes": "Qualitative human-use rubric.",
                }
            )
            evidence.append(
                {
                    "iteration_id": iteration["id"],
                    "criterion_id": "human-use-friction",
                    "scorer_id": "ergonomics-panel",
                    "kind": "qualitative_rubric",
                    "objective_gate": False,
                    "score": 4,
                    "evidence_refs": [iteration["artifacts"][0]["id"]],
                    "lens_findings": findings,
                }
            )
        self.manifest["human_use"] = {
            "applicability": "applicable",
            "rationale": "The artifact is gripped and operated by hand.",
            "friction_scenarios": [
                {
                    "id": "rim-contact",
                    "category": "hand_contact_edges",
                    "operation": "Grip and turn",
                    "context": "Repeated bare-hand use",
                    "material_friction": "A sharp rim may be uncomfortable.",
                    "treatment": "qualitative_scorecard_criterion",
                    "target": "human-use-friction",
                    "rationale": "Ergonomics is qualitatively judged.",
                    "evidence_plan": "Inspect renders and handled-prototype notes.",
                }
            ],
            "prior_art_learnings": [
                {
                    "provenance": "owner_provided",
                    "source": "Owner reference",
                    "observed_functional_choice": "Rounded hand-contact rim.",
                    "inferred_rationale": "Reduce contact discomfort.",
                    "decision": "adapt",
                    "decision_rationale": "Use the function without copying geometry.",
                    "originality_implications": "Independent form remains required.",
                    "evidence": "Owner-supplied image.",
                }
            ],
            "qualitative_criterion_id": "human-use-friction",
            "qualitative_scorer_id": "ergonomics-panel",
            "required_lenses": [
                "sharp_contact_edges",
                "comfort",
                "retention",
                "strength_confidence_under_intended_loads",
                "operability",
                "degraded_cosmetic_operations",
            ],
            "judging_evidence": evidence,
        }

        view_model = build_view_model(self.manifest)
        rendered = render_viewer(self.manifest)

        self.assertEqual(
            "applicable",
            view_model["human_use"]["applicability"],
        )
        self.assertEqual(
            "loop-001",
            view_model["loops"][0]["human_use_evidence"]["iteration_id"],
        )
        self.assertIn("Material friction scenarios", rendered)
        self.assertIn("Prior-art functional learnings", rendered)
        self.assertIn("not an objective gate", rendered)
        self.assertIn("Degraded fillet / chamfer / cosmetic operations", rendered)

    def test_digital_human_use_evidence_renders_selected_lenses(self) -> None:
        self.manifest["human_use"] = {
            "applicability": "applicable",
            "rationale": "People directly operate the web workflow.",
            "friction_scenarios": [
                {
                    "id": "recover-submit",
                    "category": "error_prevention_recovery",
                    "operation": "Recover from a rejected submission",
                    "context": "Interrupted mobile session",
                    "material_friction": "Entered data may be lost.",
                    "treatment": "qualitative_scorecard_criterion",
                    "target": "clarity",
                    "rationale": "Recovery quality is experienced qualitatively.",
                    "evidence_plan": "Operate the rejected-submit path.",
                }
            ],
            "prior_art_learnings": [],
            "qualitative_criterion_id": "clarity",
            "qualitative_scorer_id": "objective-check",
            "required_lenses": [
                "error_prevention_recovery",
                "responsive_touch_ergonomics",
                "cognitive_load",
            ],
            "judging_evidence": [
                {
                    "iteration_id": "loop-001",
                    "criterion_id": "clarity",
                    "scorer_id": "objective-check",
                    "kind": "qualitative_rubric",
                    "objective_gate": False,
                    "score": 1,
                    "evidence_refs": ["baseline-result"],
                    "lens_findings": [
                        {
                            "lens": "error_prevention_recovery",
                            "finding": "State preservation is unclear.",
                        },
                        {
                            "lens": "responsive_touch_ergonomics",
                            "finding": "Controls crowd at the mobile viewport.",
                        },
                        {
                            "lens": "cognitive_load",
                            "finding": "Recovery instructions require rereading.",
                        },
                    ],
                }
            ],
        }

        rendered = render_viewer(self.manifest)

        self.assertIn("Error prevention / recovery", rendered)
        self.assertIn("Responsive / touch ergonomics", rendered)
        self.assertIn("Cognitive load", rendered)

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

    def test_watch_poll_tracks_manifest_and_feedback_inputs(self) -> None:
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

            after_fragment = snapshot_watch_inputs(root)
            intake = root / "human-feedback" / "intake" / "review-001.json"
            intake.parent.mkdir(parents=True)
            intake.write_text("{}", encoding="utf-8")
            _, changed = poll_watch_inputs(root, after_fragment)
            self.assertEqual(
                ("human-feedback/intake/review-001.json",),
                changed,
            )

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
