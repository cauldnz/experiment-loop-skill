import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(__file__).parent
NOW = datetime.now(timezone.utc).isoformat()
JUDGE = "judge-accessibility"
MODEL = "gpt-5.6-terra"
ORDER = ["candidate-a", "candidate-b", "candidate-c"]
LENSES = [
    "discoverability", "navigation", "input_burden", "error_prevention_recovery",
    "feedback_status", "accessibility", "responsive_touch_ergonomics",
    "interruption_resumption", "latency_perception", "destructive_actions",
    "cognitive_load",
]
OBJECTIVE = {
    "acknowledged": True,
    "harness_rerun": False,
    "result": "Each persisted report is terminal: all seven gates pass, failed_gate_ids is empty, and external_requests is empty.",
    "gates": [
        "content-fidelity", "semantic-accessibility-gate", "keyboard-completion-gate",
        "error-recovery-gate", "mobile-touch-gate", "resilience-gate", "offline-safety-gate",
    ],
}


def score(value, evidence):
    return {"score": value, "evidence": evidence}


records = {
    "candidate-a": {
        "scores": {
            "discoverability": score(5, "The visible five-step links, numbered sections, order total, and concise safety copy made the next action apparent."),
            "navigation": score(5, "All five links changed scroll position; keyboard Tab then Enter on the skip link focused checkout-form."),
            "input_burden": score(4, "One-page entry still asks for many fields, but synthetic exemplar text, input modes, and compact completed sections reduce recall and repeat work."),
            "error_prevention_recovery": score(5, "Invalid submit focused error-summary with an actionable 13-item, four-section summary; correction and completion preserved entered data."),
            "feedback_status": score(5, "Observed save status, section status/compact summaries, and local confirmation status with SYN-2048 were explicit."),
            "accessibility": score(5, "Skip target focus, keyboard completion, visible focus/large controls, linked errors, no console errors, and the terminal semantic gate all support this score."),
            "responsive_touch_ergonomics": score(5, "390x844 inspection showed full-width fields and large shipping, edit, and place-order targets; terminal mobile gate passed."),
            "interruption_resumption": score(5, "Manual safe save restored contact and address after reload while card number and security code were empty; confirmation SYN-2048 remained after reload without payment details."),
            "latency_perception": score(4, "Immediate local section, save, validation, and confirmation feedback makes waiting unlikely; the long one-page form remains visually substantial."),
            "destructive_actions": score(5, "Clear progress required an explicit confirmation and both Escape and Cancel preserved work before the affirmative clear path."),
            "cognitive_load": score(4, "Progressive compact summaries, review edits, and error grouping help, though the full five-section single page is dense before compaction."),
        },
        "visual": score(5, "Strong heading hierarchy, repeated numbered section anchors, bordered touch targets, stable totals, and compact summary cards were legible at 390x844."),
        "findings": [
            "Completed the canonical local order once and observed SYN-2048 with no console or external-request signal.",
            "All 25 recorded control operations completed, including step links, both shipping choices, compact/edit paths, correction, confirmation, and post-confirmation reload.",
            "The persisted confirmation is useful resumption evidence, but it should remain clearly distinguishable from a new checkout state.",
        ],
    },
    "candidate-b": {
        "scores": {
            "discoverability": score(5, "Five labeled links, the compact choice, review edits, and a visible progress/status treatment made controls easy to find."),
            "navigation": score(4, "Every step link scrolled to its section and edit controls returned focus to the right input, but activating the skip link produced no identified focused target in this run."),
            "input_burden": score(4, "The same synthetic hints, compact option, and editable review avoid re-entry, while the one-page form still has a high initial field count."),
            "error_prevention_recovery": score(5, "Invalid submit focused error-summary and grouped 13 corrections by four sections while preserving entries; correction then completed."),
            "feedback_status": score(5, "Observed save status, completed-state feedback, shipping updates, and a local SYN-2048 confirmation provided clear state changes."),
            "accessibility": score(4, "Terminal semantic and keyboard gates passed and no console errors occurred, but the observed skip activation did not yield a named focused target."),
            "responsive_touch_ergonomics": score(5, "At 390x844, fields and action buttons were broad and clearly separated; terminal mobile-touch gate passed."),
            "interruption_resumption": score(4, "Safe fields restored and payment secrets cleared after reload, but the local confirmation was not present after a confirmation reload."),
            "latency_perception": score(4, "Immediate, local status and confirmation feedback communicate progress without a spinner or implied remote wait."),
            "destructive_actions": score(5, "Clear confirmation, Escape, Cancel, and affirmative clear paths were all exercised successfully."),
            "cognitive_load": score(4, "Progress feedback and per-section error grouping help orient users; the initial all-at-once layout remains information-dense."),
        },
        "visual": score(5, "Clear status progression, high contrast navy actions, concise copy, and separated review cards support scanability."),
        "findings": [
            "Completed SYN-2048 once, with no console errors or external requests observed.",
            "All 25 recorded operations completed, including safe save/reload and every destructive-action branch.",
            "The skip-link focus observation and nonpersistent confirmation are the meaningful qualitative reservations.",
        ],
    },
    "candidate-c": {
        "scores": {
            "discoverability": score(4, "Core links, fields, shipping choices, compacting, and edits were discoverable, but there was no discoverable save or clear-progress control."),
            "navigation": score(4, "Step links and edit controls worked and moved focus to their inputs; skip activation did not expose an identified target in this run."),
            "input_burden": score(4, "Automatic safe restoration and compact summaries reduce repeated entry, though users lose an explicit moment to choose when saved progress is stored."),
            "error_prevention_recovery": score(5, "Invalid submit focused a detailed, grouped error summary and preserved all entries; corrected canonical completion succeeded."),
            "feedback_status": score(4, "Section and order feedback are clear, but automatic saving is less explicit and there is no observed clear confirmation/status path."),
            "accessibility": score(4, "All objective accessibility gates passed, controls completed by browser automation, and no console errors occurred; the skip-focus observation remains a reservation."),
            "responsive_touch_ergonomics": score(5, "The 390x844 layout kept fields, radios, edits, and submission controls large and separated; the mobile gate passed."),
            "interruption_resumption": score(4, "Contact/address restored while card number and security code cleared on reload; confirmation itself was absent after confirmation reload."),
            "latency_perception": score(4, "Local validation and confirmation were immediate, and automatic resume minimizes explicit save steps."),
            "destructive_actions": score(2, "No clear-progress control or confirmation was discoverable, so clear/cancel/Escape could not be offered or exercised."),
            "cognitive_load": score(4, "Structured errors, compact completed sections, and review edits reduce orientation load; invisible auto-save/clear absence makes persistence less predictable."),
        },
        "visual": score(4, "The visual hierarchy and touch layout are clear, but the error-heavy long page and reduced persistence affordance clarity are less reassuring."),
        "findings": [
            "Canonical SYN-2048 completion succeeded once with no console errors or external requests observed.",
            "Automatic safe restoration preserved contact/address and cleared payment secrets after reload.",
            "No clear-progress control or confirmation was discoverable; this is a qualitative control/reversibility regression despite passed objective gates.",
        ],
    },
}


def candidate_doc(label, record):
    numeric = {lens: record["scores"][lens]["score"] for lens in LENSES}
    mean = sum(numeric.values()) / len(LENSES)
    transcript = f"navigation-transcript-{label[-1]}.json"
    return {
        "schema_version": "1.0",
        "label": label,
        "judge": JUDGE,
        "model": MODEL,
        "judged_at": NOW,
        "frozen_contract": {
            "brief_sha256": "ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13",
            "prompt_sha256": "86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928",
        },
        "objective_report": {**OBJECTIVE, "path": f"../blind/{label}/evidence/objective-report.json"},
        "browser_operation": {
            "transcript": transcript,
            "screenshots": f"screenshots/{label[-1]}/",
            "viewport": "390x844",
            "reduced_motion": "reduce",
            "keyboard": "exercised",
            "console_errors": 0,
            "external_requests": 0,
            "control_coverage_count": 25,
        },
        "scores": record["scores"],
        "visual_information_clarity": record["visual"],
        "unrounded_mean_11_lenses": mean,
        "findings": record["findings"],
        "uncertainty": "Qualitative scores reflect one independent browser-based accessibility judgment. Objective reports were accepted as terminal and not rerun.",
        "no_champion_claim": True,
    }


def markdown_candidate(doc):
    lines = [
        f"# Accessibility final judgment: {doc['label']}", "", f"Judge/model: `{JUDGE}` / `{MODEL}`",
        "", "## Objective acknowledgement",
        "Persisted terminal objective report: all seven gates pass; zero external requests; harness not rerun.",
        "", "## Browser evidence",
        f"- `{doc['browser_operation']['transcript']}`; 390x844, reduced motion, keyboard, console and request observation.",
        f"- Screenshots: `{doc['browser_operation']['screenshots']}`",
        "", "## Scores (1–5)",
    ]
    for lens in LENSES:
        item = doc["scores"][lens]
        lines.append(f"- **{lens} — {item['score']}**: {item['evidence']}")
    visual = doc["visual_information_clarity"]
    lines += [
        f"- **visual_information_clarity — {visual['score']}**: {visual['evidence']}",
        f"", f"Unrounded mean (11 lenses): **{doc['unrounded_mean_11_lenses']:.12g}**",
        "", "## Findings",
    ]
    lines += [f"- {finding}" for finding in doc["findings"]]
    lines += ["", f"Uncertainty: {doc['uncertainty']}"]
    return "\n".join(lines) + "\n"


docs = {}
for label in ORDER:
    docs[label] = candidate_doc(label, records[label])
    (OUT / f"{label}.json").write_text(json.dumps(docs[label], indent=2) + "\n", encoding="utf-8")
    (OUT / f"{label}.md").write_text(markdown_candidate(docs[label]), encoding="utf-8")

pairwise = {
    "schema_version": "1.0",
    "judge": JUDGE,
    "model": MODEL,
    "judged_at": NOW,
    "objective_pass_acknowledgement": OBJECTIVE["result"],
    "comparisons": [
        {
            "id": "candidate-a-vs-candidate-b",
            "observed_order": ["candidate-a", "candidate-b"],
            "preferred_label": "candidate-a",
            "confidence": "moderate",
            "rationale": "Both completed all exercised controls and passed all objective gates. A uniquely moved skip-link focus to checkout-form and retained the local SYN-2048 confirmation after reload; B had strong visible progress/status treatment but its skip activation had no identified target and its confirmation disappeared after reload.",
            "regression_assessment": "B is not objectively regressed. The preference is qualitative: focused skip behavior and post-confirmation resumption are stronger in A; B may be preferred by users who value its progress strip.",
            "objective_failure_override": False,
        },
        {
            "id": "candidate-a-vs-candidate-c",
            "required_final_parent_comparison": True,
            "observed_order": ["candidate-a", "candidate-c"],
            "preferred_label": "candidate-a",
            "confidence": "high",
            "rationale": "Both passed the terminal objective reports and completed SYN-2048 without external requests. A provided explicit safe save, confirmed clear with Escape and Cancel paths, focused the skip destination, and preserved confirmation after reload. C safely auto-restored fields but offered no discoverable clear/reversal control and its confirmation did not persist.",
            "regression_assessment": "C's automatic safe restoration is a useful low-effort feature, not an objective failure; the absence of user-visible clear/cancel/Escape makes it qualitatively weaker for reversibility and predictable resumption.",
            "objective_failure_override": False,
        },
        {
            "id": "candidate-b-vs-candidate-c",
            "observed_order": ["candidate-b", "candidate-c"],
            "preferred_label": "candidate-b",
            "confidence": "moderate",
            "rationale": "Both had grouped error recovery, safe payment-secret clearing, large targets, and terminal objective passes. B adds explicit safe save plus clear confirmation/Escape/Cancel controls and stronger visible state feedback; C reduces a step through automatic restoration but omits a discoverable reversal route.",
            "regression_assessment": "C has no objective failure and automatic restore may suit users who dislike save actions. B is preferred for explicit agency and safe destructive-action recovery.",
            "objective_failure_override": False,
        },
    ],
    "uncertainty_and_dissent": "This is one independent accessibility-focused qualitative vote. A different panelist could reasonably value B's more prominent progress treatment or C's automatic restoration more strongly; neither preference changes the acknowledged objective passes.",
    "no_champion_claim": True,
}
(OUT / "pairwise.json").write_text(json.dumps(pairwise, indent=2) + "\n", encoding="utf-8")
pairwise_md = [
    "# Accessibility final pairwise judgment", "",
    f"Judge/model: `{JUDGE}` / `{MODEL}`", "",
    "All persisted objective reports pass all seven gates with zero external requests; the harness was not rerun.",
]
for comparison in pairwise["comparisons"]:
    pairwise_md += [
        "", f"## {comparison['id']}", f"Observed order: {' → '.join(comparison['observed_order'])}",
        f"Preferred: **{comparison['preferred_label']}** ({comparison['confidence']})",
        comparison["rationale"], "", f"Regression assessment: {comparison['regression_assessment']}",
    ]
pairwise_md += ["", f"Uncertainty/dissent: {pairwise['uncertainty_and_dissent']}"]
(OUT / "pairwise.md").write_text("\n".join(pairwise_md) + "\n", encoding="utf-8")

manifest = {
    "schema_version": "1.0",
    "experiment_id": "accessible-mobile-checkout",
    "artifact": "independent accessibility-focused final blind judgment",
    "judge": {"id": JUDGE, "model": MODEL},
    "evaluation_order": ORDER,
    "objective_reports_acknowledged": OBJECTIVE,
    "records": [
        {
            "label": label,
            "judge": JUDGE,
            "model": MODEL,
            "lens_scores": docs[label]["scores"],
            "visual_information_clarity": docs[label]["visual_information_clarity"],
            "unrounded_mean_11_lenses": docs[label]["unrounded_mean_11_lenses"],
            "findings": docs[label]["findings"],
            "evidence": [f"{label}.json", f"navigation-transcript-{label[-1]}.json", f"screenshots/{label[-1]}/"],
            "pairwise_result_refs": [comparison["id"] for comparison in pairwise["comparisons"] if label in comparison["id"]],
        }
        for label in ORDER
    ],
    "pairwise_results": "pairwise.json",
    "champion": None,
    "no_champion_claim": True,
}
(OUT / "manifest-ready.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

hashes = {}
for path in sorted(OUT.rglob("*")):
    if path.is_file() and path.name not in {"status.json", "write_judgment.py"}:
        hashes[str(path.relative_to(OUT)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()

status = {
    "status": "completed",
    "started_at": "2026-07-22T08:35:58.592+10:00",
    "completed_at": NOW,
    "heartbeat_at": NOW,
    "phase": "finalized",
    "judge": JUDGE,
    "model": MODEL,
    "fixed_evaluation_order": ORDER,
    "blockers": [],
    "harness_rerun": False,
    "objective_reports_acknowledged": {
        "all_seven_gates_pass": True,
        "zero_external_requests": True,
        "terminal_reports": True,
    },
    "browser_summary": {
        "engine": "local Chromium via Python Playwright",
        "viewport": "390x844",
        "reduced_motion": "reduce",
        "keyboard": "exercised",
        "candidate_a_control_coverage": 25,
        "candidate_b_control_coverage": 25,
        "candidate_c_control_coverage": 25,
        "console_errors": 0,
        "observed_external_requests": 0,
        "candidate_c_clear_control": "not discoverable; recorded as a qualitative finding",
    },
    "output_hashes_sha256": hashes,
}
(OUT / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
