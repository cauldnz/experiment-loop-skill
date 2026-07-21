from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_experiment_setup import (
    FRICTION_CATEGORIES,
    validate_brief,
    validate_setup,
)


ROOT = Path(__file__).resolve().parents[1]


class ExperimentSetupTests(unittest.TestCase):
    def valid_brief(self) -> dict[str, object]:
        brief = json.loads(
            (ROOT / "templates" / "experiment-brief-template.json").read_text(
                encoding="utf-8"
            )
        )
        brief["status"] = "approved"
        brief["setup_review"] = {
            "critic_model_id": "independent-critic",
            "status": "pass",
            "unresolved_findings": [],
        }
        return brief

    def test_valid_approved_binding_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            brief_path = root / "experiment-brief.json"
            prompt_path = root / "prompt.md"
            approval_path = root / "approval.json"
            brief_path.write_text(
                json.dumps(self.valid_brief(), indent=2) + "\n",
                encoding="utf-8",
            )
            prompt_path.write_text("Use the experiment-loop skill.\n", encoding="utf-8")
            approval = {
                "schema_version": "1.0",
                "experiment_id": "short-stable-id",
                "brief_revision": 1,
                "brief_sha256": hashlib.sha256(brief_path.read_bytes()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
                "status": "approved",
                "approved_at": "2026-07-20T00:00:00Z",
                "approval_source": "explicit_human_confirmation",
                "notes": "",
            }
            approval_path.write_text(
                json.dumps(approval, indent=2) + "\n", encoding="utf-8"
            )
            self.assertEqual(
                [],
                validate_setup(
                    brief_path,
                    prompt_path=prompt_path,
                    approval_path=approval_path,
                    require_approved=True,
                ),
            )

    def test_approval_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            brief_path = root / "experiment-brief.json"
            prompt_path = root / "prompt.md"
            approval_path = root / "approval.json"
            brief_path.write_text(
                json.dumps(self.valid_brief(), indent=2) + "\n",
                encoding="utf-8",
            )
            prompt_path.write_text("Prompt\n", encoding="utf-8")
            approval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "experiment_id": "short-stable-id",
                        "brief_revision": 1,
                        "brief_sha256": "0" * 64,
                        "prompt_sha256": "1" * 64,
                        "status": "approved",
                        "approved_at": "2026-07-20T00:00:00Z",
                        "approval_source": "explicit_human_confirmation",
                        "notes": "",
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_setup(
                brief_path,
                prompt_path=prompt_path,
                approval_path=approval_path,
                require_approved=True,
            )
            self.assertIn("approval brief_sha256 does not match brief", errors)
            self.assertIn("approval prompt_sha256 does not match prompt", errors)

    def test_active_risk_branch_requires_controls(self) -> None:
        brief = self.valid_brief()
        brief["risks"]["deployment"] = True
        errors = validate_brief(brief)
        self.assertTrue(
            any("active risk branch lacks controls" in error for error in errors),
            errors,
        )

    def test_unattended_mode_requires_scratch_root(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["mode"] = "unattended"
        del brief["target"]["scratch_root"]
        self.assertIn(
            "unattended mode requires target.scratch_root",
            validate_brief(brief),
        )

    def test_unattended_mode_requires_attended_transition_protocol(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["mode"] = "unattended"
        del brief["autonomy"]["attended_protocol"]
        self.assertIn(
            "unattended mode requires autonomy.attended_protocol",
            validate_brief(brief),
        )

    def test_unattended_scratch_root_must_be_under_generated_root(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["mode"] = "unattended"
        brief["target"]["scratch_root"] = ".scratch"
        self.assertIn(
            "unattended target.scratch_root must be within target.generated_root",
            validate_brief(brief),
        )

    def test_interactive_legacy_brief_may_omit_scratch_root(self) -> None:
        brief = self.valid_brief()
        del brief["target"]["scratch_root"]
        self.assertEqual([], validate_brief(brief))

    def test_attended_mode_requires_checkpoint_protocol(self) -> None:
        brief = self.valid_brief()
        del brief["autonomy"]["attended_protocol"]
        self.assertIn(
            "attended mode requires autonomy.attended_protocol",
            validate_brief(brief),
        )

    def test_attended_checkpoint_must_be_under_generated_root(self) -> None:
        brief = self.valid_brief()
        brief["autonomy"]["attended_protocol"]["checkpoint_root"] = "outside"
        self.assertIn(
            "attended checkpoint_root must be within target.generated_root",
            validate_brief(brief),
        )

    def test_windows_absolute_target_path_fails(self) -> None:
        brief = self.valid_brief()
        brief["target"]["scratch_root"] = (
            r"C:\outside\generated\harness\scratch"
        )
        self.assertIn(
            "target.scratch_root must be a repository-relative path",
            validate_brief(brief),
        )

    def test_schema_v11_requires_explicit_human_use(self) -> None:
        brief = self.valid_brief()
        del brief["human_use"]
        self.assertTrue(
            any(
                "human_use" in error
                for error in validate_brief(brief)
            )
        )

    def test_legacy_v10_brief_remains_valid_without_human_use(self) -> None:
        brief = self.valid_brief()
        brief["schema_version"] = "1.0"
        del brief["human_use"]
        del brief["risks"]["network_access"]
        self.assertEqual([], validate_brief(brief))

    def test_not_applicable_human_use_requires_rationale(self) -> None:
        brief = self.valid_brief()
        brief["human_use"]["rationale"] = ""
        self.assertTrue(
            any("rationale" in error for error in validate_brief(brief))
        )

    def test_independent_prior_art_search_requires_network_approval(self) -> None:
        brief = self.valid_brief()
        independent = brief["human_use"]["prior_art_review"]["independent_search"]
        independent["performed"] = True
        independent["provenance"] = [
            {
                "query": "functional reference",
                "source": "https://example.invalid/search",
                "retrieved_at": "2026-07-21T00:00:00Z",
                "result": "No relevant references found.",
            }
        ]
        self.assertIn(
            "independent prior-art search cannot be performed without explicit network approval",
            validate_brief(brief),
        )

    def test_applicable_human_use_is_qualitative_and_mapped(self) -> None:
        brief = self.valid_brief()
        brief["scorecard"].append(
            {
                "id": "human-use-friction",
                "label": "Human-use friction",
                "direction": "maximize",
                "primary": False,
                "weight": 1,
                "gate": False,
                "measurement": "Independent qualitative 1-5 rubric with observed-use evidence.",
            }
        )
        brief["scorers"].append(
            {
                "id": "ergonomics-panel",
                "type": "llm_rubric",
                "criterion_ids": ["human-use-friction"],
                "primary": False,
                "judge_panel": "ergonomics-panel",
            }
        )
        analysis = {
            "categories": [
                {
                    "category": "hand_contact_edges",
                    "assessment": "The palm contacts the rim during intended use.",
                    "scenarios": [
                        {
                            "id": "palm-rim-contact",
                            "operation": "Grip and rotate the tool.",
                            "context": "Repeated driver use with bare hands.",
                            "material_friction": "A sharp rim can cause discomfort.",
                            "treatment": "qualitative_scorecard_criterion",
                            "target_id": "human-use-friction",
                            "rationale": "Comfort is qualitative under the approved policy.",
                            "evidence_plan": "Inspect renders and a handled prototype; record edge comfort in judge evidence.",
                        }
                    ],
                }
            ],
            "not_selected_categories": [
                {
                    "category": category,
                    "rationale": "Not relevant to this physical hand-contact scenario.",
                }
                for category in FRICTION_CATEGORIES
                if category != "hand_contact_edges"
            ],
        }
        brief["human_use"] = {
            "applicability": "applicable",
            "rationale": "A person grips and operates the artifact.",
            "friction_analysis": analysis,
            "prior_art_review": {
                "owner_provided_references": [
                    {
                        "source": "Owner-provided reference",
                        "observed_functional_choice": "Rounded hand-contact rim.",
                        "inferred_rationale": "Reduce contact discomfort.",
                        "decision": "adapt",
                        "decision_rationale": "Use the functional lesson without copying geometry.",
                        "originality_implications": "Independent geometry remains required.",
                        "evidence": "Reference image supplied by the owner.",
                    }
                ],
                "independent_search": {
                    "network_approved": False,
                    "approval_source": None,
                    "performed": False,
                    "provenance": [],
                    "reviewed_references": [],
                },
            },
            "qualitative_judging": {
                "criterion_id": "human-use-friction",
                "scorer_id": "ergonomics-panel",
                "evidence_plan": "Judge each Loop from renders, failure logs, and handled-prototype notes.",
                "required_lenses": [
                    "sharp_contact_edges",
                    "comfort",
                    "operability",
                    "degraded_cosmetic_operations",
                ],
            },
        }
        self.assertEqual([], validate_brief(brief))

        scenario = brief["human_use"]["friction_analysis"]["categories"][0][
            "scenarios"
        ][0]
        scenario["treatment"] = "design_invariant"
        scenario["target_id"] = "correctness"
        self.assertEqual([], validate_brief(brief))

        brief["scorecard"][-1]["gate"] = True
        self.assertIn(
            "human-use ergonomics criterion must be qualitative, not an objective gate",
            validate_brief(brief),
        )

    def test_digital_human_use_selects_interaction_categories(self) -> None:
        brief = self.valid_brief()
        brief["scorecard"].append(
            {
                "id": "use-friction",
                "label": "Use friction",
                "direction": "maximize",
                "primary": False,
                "weight": 1,
                "gate": False,
                "measurement": "Independent qualitative interaction rubric.",
            }
        )
        brief["scorers"].append(
            {
                "id": "ux-panel",
                "type": "llm_rubric",
                "criterion_ids": ["use-friction"],
                "primary": False,
                "judge_panel": "ux-panel",
            }
        )
        brief["human_use"] = {
            "applicability": "applicable",
            "rationale": "People directly operate the web workflow.",
            "friction_analysis": {
                "categories": [
                    {
                        "category": "error_prevention_recovery",
                        "assessment": "Submission errors can interrupt the workflow.",
                        "scenarios": [
                            {
                                "id": "recover-submit",
                                "operation": "Submit and correct a rejected form.",
                                "context": "Mobile use after an interrupted session.",
                                "material_friction": "Errors may erase entered data.",
                                "treatment": "qualitative_scorecard_criterion",
                                "target_id": "use-friction",
                                "rationale": "Recovery quality is experienced qualitatively.",
                                "evidence_plan": "Operate the failed-submit path and record preserved state and recovery clarity.",
                            }
                        ],
                    },
                    {
                        "category": "responsive_touch_ergonomics",
                        "assessment": "The workflow is used on narrow touch screens.",
                        "scenarios": [
                            {
                                "id": "touch-navigation",
                                "operation": "Navigate and edit fields by touch.",
                                "context": "One-handed mobile use.",
                                "material_friction": "Dense controls may be hard to operate.",
                                "treatment": "qualitative_scorecard_criterion",
                                "target_id": "use-friction",
                                "rationale": "Touch usability is judged from operated evidence.",
                                "evidence_plan": "Navigate the responsive UI at the pinned mobile viewport.",
                            }
                        ],
                    },
                    {
                        "category": "accessibility",
                        "assessment": "Keyboard and assistive-technology users operate the workflow.",
                        "scenarios": [
                            {
                                "id": "accessible-recovery",
                                "operation": "Find and correct a validation error with assistive technology.",
                                "context": "Keyboard and screen-reader operation.",
                                "material_friction": "Error status may not be announced or reachable.",
                                "treatment": "qualitative_scorecard_criterion",
                                "target_id": "use-friction",
                                "rationale": "Accessible recovery is judged from operated evidence.",
                                "evidence_plan": "Record keyboard navigation and announcement evidence for the recovery path.",
                            }
                        ],
                    },
                ],
                "not_selected_categories": [
                    {
                        "category": category,
                        "rationale": "Not material to this bounded web-flow test.",
                    }
                    for category in FRICTION_CATEGORIES
                    if category
                    not in {
                        "error_prevention_recovery",
                        "responsive_touch_ergonomics",
                        "accessibility",
                    }
                ],
            },
            "prior_art_review": {
                "owner_provided_references": [],
                "independent_search": {
                    "network_approved": False,
                    "approval_source": None,
                    "performed": False,
                    "provenance": [],
                    "reviewed_references": [],
                },
            },
            "qualitative_judging": {
                "criterion_id": "use-friction",
                "scorer_id": "ux-panel",
                "evidence_plan": "Judge navigation transcripts, mobile screenshots, and recovery-state captures.",
                "required_lenses": [
                    "operability",
                    "error_prevention_recovery",
                    "responsive_touch_ergonomics",
                    "accessibility",
                    "interruption_resumption",
                    "cognitive_load",
                ],
            },
        }

        self.assertEqual([], validate_brief(brief))


if __name__ == "__main__":
    unittest.main()
