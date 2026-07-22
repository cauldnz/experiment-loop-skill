from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

ROOT = Path(r"<skill-repository>")
OUT = ROOT / ".experiments" / "accessible-mobile-checkout" / "generated" / "judging" / "synthesis-loop-01" / "judge-accessibility"
now = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
base = ".experiments/accessible-mobile-checkout/generated"
evidence = [
  {"ref":f"{base}/synthesis/loop-01/evidence/objective-report.json", "observation":"Persisted objective terminal result is acknowledged as pass; failed gate IDs are empty and external requests are zero. It was not rerun."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/navigation-transcript-a.json#actions[Keyboard Enter on empty Place order]", "observation":"Empty submit produced a focused, grouped error summary for 13 items in four sections and 13 invalid fields."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/navigation-transcript-a.json#actions[Reload restores safe fields only]", "observation":"All eight safe contact/delivery fields restored after reload; four payment fields were empty."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/navigation-transcript-a.json#actions[Keyboard Space enables compact completed sections]", "observation":"Contact, delivery, shipping and payment compacted with zero exposed focusable descendants in hidden bodies."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/navigation-transcript-a.json#actions[Observe local confirmation]", "observation":"One SYN-2048 confirmation was focused after local busy feedback."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/navigation-transcript-a.json#checks", "observation":"390px viewport had no horizontal overflow, target minima were 24x24px, reduced-motion matched with 0.01ms motion, zero console errors, and zero external requests."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/screenshots/01-initial-390x844.png", "observation":"Initial mobile state."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/screenshots/02-error-recovery-390x844.png", "observation":"Error-recovery state."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/screenshots/03-save-clear-confirmation-390x844.png", "observation":"Save/clear confirmation state."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/screenshots/04-compact-edit-390x844.png", "observation":"Compact/edit state."},
  {"ref":f"{base}/judging/synthesis-loop-01/judge-accessibility/screenshots/05-confirmation-390x844.png", "observation":"Confirmation state."}
]
lenses = {
 "discoverability":{"score":5,"finding":"The synthetic banner, clear H1, five named section links, numbered section headings, progressbar, visible order summary, and direct labels make the checkout’s purpose and available tasks explicit."},
 "navigation":{"score":4,"finding":"All five anchor links changed hash/position; compact and review Edit controls opened the exact section and focused its first control; Tab/Shift+Tab order was logical. Deduction: Enter on the skip link set #checkout-form but focus landed on BODY because the form target is not programmatically focusable."},
 "input_burden":{"score":4,"finding":"Field-level synthetic examples, input modes, persistent totals, direct section edits, radio shipping and a single review confirmation reduce hesitation. The full 13-field, five-section form remains long at 390px."},
 "error_prevention_recovery":{"score":5,"finding":"Empty submit focused an actionable grouped summary (13 items, four sections); its first link focused contact-name. Invalid fields received messages/aria-invalid; a later invalid-payment submit retained valid contact/delivery values."},
 "feedback_status":{"score":5,"finding":"Progress exposes completed/next section text, saving/restoring/clearing status is announced, a short local busy state appears before confirmation, and successful placement reports SYN-2048."},
 "accessibility":{"score":4,"finding":"Observed landmark structure, labelled native fields/fieldsets, semantic status/alert/progressbar, visible keyboard focus, native radio arrows, no trap, safe compaction, and reduced-motion behavior are strong. The non-focused skip destination prevents a top score."},
 "responsive_touch_ergonomics":{"score":4,"finding":"At 390x844 there was no horizontal overflow; cards/buttons/inputs are generally generous and measured minimum interactive dimensions were 24x24px. The exact-minimum native radio/checkbox footprint and long one-page reach keep this below excellent."},
 "interruption_resumption":{"score":5,"finding":"Explicit save preserved only eight safe fields plus shipping; reload restored them and left all four payment fields blank. Clear uses confirmation, Cancel and Escape, then correctly clears/reloads."},
 "latency_perception":{"score":4,"finding":"Placement exposes an immediate 'Placing local synthetic order' busy status and resolves to a focused confirmation after the short local delay. Focus temporarily fell to BODY while the disabled action handed off, so feedback is good but not seamless."},
 "destructive_actions":{"score":5,"finding":"Clear is explicit, describes scope and irreversibility, focuses Cancel, supports Escape and preserves data on cancellation. Confirming clear erased storage. Placement disabled its button and a duplicate native submit kept exactly one confirmation."},
 "cognitive_load":{"score":4,"finding":"One-page orientation, five-step progress, compact completed sections and concise section status reduce re-orientation. Initial completion still exposes a long multi-section mobile form; the full error panorama can be demanding despite its grouping."}
}
scores={key:value['score'] for key,value in lenses.items()}
mean=sum(scores.values())/len(scores)
record={
 "schema_version":"1.0",
 "label":"candidate-a",
 "iteration_id":"synthesis-loop-01",
 "judge_id":"judge-accessibility",
 "model_id":"gpt-5.6-terra",
 "role":"approved independent accessibility-focused blind judge",
 "evaluated_at":now,
 "objective_gate":{"acknowledged":"pass","source":f"{base}/synthesis/loop-01/evidence/objective-report.json","rerun":False,"note":"Objective result accepted as terminal and not used to erase qualitative defects."},
 "viewport":{"width":390,"height":844},
 "scores":scores,
 "mean_11_lenses_unrounded":mean,
 "visual_information_clarity":{"score":4,"finding":"Clear typography, restrained high-contrast navy/cream hierarchy, grouped cards and prominent total/status surfaces are legible in the captured 390px states. The dense full-form initial state and many visible panels prevent a 5."},
 "lens_findings":lenses,
 "strengths":[
   "Strong semantic and keyboard recovery path: focused grouped error summary, field links, preserved values and visible invalid states.",
   "Safe interruption model: explicit save/restore, payment exclusion from storage, confirmed cancellable clear and Escape recovery.",
   "Direct single-page navigation remains available after compaction; hidden completed bodies yielded zero exposed focusable descendants.",
   "Atomic local order placement gave one focused SYN-2048 confirmation, with no observed console or external-request issue."
 ],
 "defects":[
   "The skip link changes the fragment but leaves focus on BODY because #checkout-form is not focusable; keyboard/screen-reader users do not land at a named form start.",
   "The otherwise capable one-page layout remains vertically dense at a 390px mobile viewport, especially before completion or when an all-section error summary is shown.",
   "The smallest measured interactive targets are exactly 24x24px, meeting the frozen minimum but leaving limited motor-error margin for radio/checkbox affordances."
 ],
 "uncertainty":[
   "Observed with local Chromium/Playwright at 390x844 only; no speech output from a real screen reader, switch device, magnifier, or cross-browser/assistive-technology combination was exercised.",
   "Latency perception is based on the local 180ms synthetic hand-off, not real payment/network latency.",
   "Objective gates are accepted terminal evidence; they were not rerun by this judge."
 ],
 "preserved_prior_hypothesis":"Prior dissent proposed combining direct one-page orientation with explicit save/restore and confirmed clearing. This candidate was judged on its own observed behavior; no prior score was inherited.",
 "evidence_refs":evidence,
 "improvement_instruction_for_synthesis_loop_02":"Make the skip destination programmatically focusable and move focus to the named checkout/form start on skip activation. Then test a progress-anchored compact/resume presentation at 320px and 390px that reduces the initial/error-state vertical panorama without introducing wizard steps or exposing descendants of compacted sections to keyboard focus. Preserve the observed grouped recovery, safe storage boundary, Escape-cancellable clear flow, and single SYN-2048 confirmation.",
 "decision":"qualitative evidence submitted; no Champion claim"
}
(OUT/'candidate-a.json').write_text(json.dumps(record,indent=2)+"\n",encoding='utf-8')
manifest={
 "schema_version":"1.0",
 "records":[record]
}
(OUT/'manifest-ready.json').write_text(json.dumps(manifest,indent=2)+"\n",encoding='utf-8')
pairwise={
 "schema_version":"1.0","judge_id":"judge-accessibility","model_id":"gpt-5.6-terra","iteration_id":"synthesis-loop-01",
 "state":"deferred","preference":None,"compared_labels":["candidate-a"],
 "reason":"Only one synthesis candidate is present. No A/B preference is fabricated; pairwise evaluation is deferred to Synthesis Loop 02/final comparison.","evidence_refs":[f"{base}/synthesis/loop-01/index.html",f"{base}/judging/synthesis-loop-01/judge-accessibility/candidate-a.json"]
}
(OUT/'pairwise.json').write_text(json.dumps(pairwise,indent=2)+"\n",encoding='utf-8')
md=f'''# Accessibility judge — candidate-a\n\n**Judge:** `judge-accessibility` · **Model:** `gpt-5.6-terra` · **Iteration:** `synthesis-loop-01`\n\n## Objective gate\nPersisted objective evidence is acknowledged as a terminal pass; it was not rerun. Qualitative findings below do not override that result.\n\n## Scores\n| Lens | Score | Finding |\n| --- | ---: | --- |\n'''
for k,v in lenses.items(): md += f"| {k} | {v['score']} | {v['finding']} |\n"
md += f'''\n**Unrounded mean (11 lenses):** {mean:.15f}\n\n**Visual/information clarity:** 4/5 — clear typographic and color hierarchy across captured 390px states; the initial full-form density holds it below excellent.\n\n## Observed evidence\n- 36 discoverable controls were exercised; the transcript records 56 actions and 17 keyboard actions.\n- Empty keyboard submission focused the error summary; its grouped first link focused `contact-name`; later invalid payment preserved valid safe values.\n- Save/reload restored eight safe fields and shipping; four payment fields were empty, and stored data had only `fields` and `shipping`.\n- Clear was opened, Escape-dismissed, Cancelled, then confirmed; the compact mode hid completed bodies with zero remaining focusable descendants.\n- Local placement announced busy state, focused one `SYN-2048` confirmation, and rejected a duplicate native submit.\n- At 390×844: no horizontal overflow; minimum measured target 24×24px; reduced motion matched with 0.01ms transition duration; console errors and external requests were zero.\n\nEvidence: `navigation-transcript-a.json`; `screenshots/01-initial-390x844.png`, `02-error-recovery-390x844.png`, `03-save-clear-confirmation-390x844.png`, `04-compact-edit-390x844.png`, and `05-confirmation-390x844.png`; persisted `../../../synthesis/loop-01/evidence/objective-report.json`.\n\n## Strengths\n- Semantically rich, keyboard-operable recovery and progress feedback.\n- Excellent safe resumption boundary and cancellable destructive action.\n- Safe progressive disclosure and duplicate-safe confirmation.\n\n## Defects and uncertainty\n- Skip activation left focus on `BODY` rather than the named form start.\n- The full five-section form/error panorama is still vertically dense on mobile; exact-minimum 24px native affordances give little motor margin.\n- Chromium/Playwright cannot establish real screen-reader speech or broader AT/browser behavior; local delay is not real payment latency.\n\n## Feedback for Synthesis Loop 02\nMake the skip destination focusable and focus it on activation. Then test a progress-anchored compact/resume pattern at 320px and 390px that reduces initial/error-state vertical density without wizard steps or keyboard-focusable hidden descendants. Preserve the grouped recovery, safe storage boundary, Escape cancellation, and one `SYN-2048` confirmation.\n\n## Pairwise\nDeferred: only one synthesis candidate is present, so no A/B preference is fabricated.\n'''
(OUT/'candidate-a.md').write_text(md,encoding='utf-8')
(OUT/'pairwise.md').write_text('# Pairwise assessment — deferred\n\nOnly `candidate-a` exists for `synthesis-loop-01`. No preference is fabricated. Pairwise assessment is deferred until Synthesis Loop 02/final comparison.\n',encoding='utf-8')
# hashes all complete artifacts excluding status due self-reference
files=['candidate-a.json','candidate-a.md','manifest-ready.json','pairwise.json','pairwise.md','navigation-transcript-a.json']+[str(Path('screenshots')/p.name) for p in sorted((OUT/'screenshots').glob('*.png'))]
hashes={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files}
status={
 "state":"completed","judge_id":"judge-accessibility","model_id":"gpt-5.6-terra","started_at":json.loads((OUT/'status.json').read_text(encoding='utf-8-sig')).get('started_at'),"heartbeat_at":now,"completed_at":now,
 "phase":"completed","blockers":[],"evaluation_order":["candidate-a"],"objective_gate_acknowledged":"pass","objective_harness_rerun":False,
 "output_paths":files+['status.json'],"output_hashes_sha256":hashes,
 "browser_operation":{"viewport":"390x844","controls_exercised":36,"actions_recorded":56,"keyboard_actions_recorded":17,"console_errors":0,"external_requests":0,"one_confirmation":True}
}
(OUT/'status.json').write_text(json.dumps(status,indent=2)+"\n",encoding='utf-8')
