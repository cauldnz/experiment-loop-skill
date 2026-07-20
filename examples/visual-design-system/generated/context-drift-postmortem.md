# Context-drift postmortem

## Incident

`synthesis-02` replaced the preceding primary headline, **Designing with
Feedback Loops**, with the long stress-test copy, **Facilitating
Cross-Functional Decision-Making**. Three independent judges then ranked the
drifted Artifact first and the panel promoted it as Champion.

This was specification drift, not a model context-window failure.

## Deterministic reproduction

The defect exists when the expected headline is absent from the primary SVG
while the panel still declares the Loop Champion-eligible and `new_best`:

```text
{
  'canonical_title_present': False,
  'champion_eligible': True,
  'decision': 'new_best',
  'objective_gates': {
    'svg_validity': 'pass',
    'layout_quality': 'pass'
  },
  'judge_panel_missed_content_drift': True
}
```

## Causal chain

1. **The Experiment never separated fixed content from design variables.**
   The original Prompt required an event title but did not name one, and the
   scorecard measured hierarchy, distinctiveness, clarity, coherence, polish,
   SVG validity, and layout quality. Different Tracks therefore used different
   event copy without violating the recorded contract.
2. **The headline became important state without becoming an invariant.**
   `synthesis-01` introduced **Designing with Feedback Loops**, but neither the
   Manifest nor subsequent Loop Prompts froze that content.
3. **The next Prompt explicitly requested replacement-shaped evidence.**
   `synthesis-01/prompt-chain.json` asked for a display stress event with a
   three-line title. It did not say that stress content must remain a secondary
   fixture or that the primary headline must be preserved.
4. **The repair Loop adopted its own output as ground truth.**
   `synthesis-02/layout-metrics.json` recorded the replacement headline under
   `required_content`. The check proved that a title was present, not that it
   matched a canonical source.
5. **All judges received the same incomplete contract.**
   Their evidence lists include candidate Artifacts, Prompt chains, generated
   metrics, and the synthesis Manifest fragment, but not a frozen canonical
   brief. Blindness hid other judges' opinions; it did not give judges an
   independent source of truth.
6. **The panel had no content-fidelity gate.**
   `panel-aggregate.json` could veto only `svg_validity` and `layout_quality`.
   The aggregate rewarded the three-line title as proof of density resilience.
7. **Validation checked consistency, not correctness.**
   `validate_artifacts.py` confirmed that Manifest and panel gate values agreed.
   Because both omitted content fidelity, the incorrect promotion was internally
   consistent and passed.

## Why three judges did not provide three independent safeguards

The panel was independent only in model identity and private scoring. All three
judges were correlated on the failure that mattered:

- the same incomplete scorecard;
- the same generator-authored Prompt chain;
- the same self-declared required-content evidence;
- the same missing canonical brief;
- the same two available objective vetoes.

One judge explicitly described the long title as a deliberate stress fixture
and called the repair “not a content substitution.” Another scored how well the
dense title fit. Those conclusions were reasonable against the evidence bundle
they received, but that bundle defined the wrong acceptance contract.

## Repair

`synthesis-03` preserves the useful width-aware layout repair from
`synthesis-02`, restores **Designing with Feedback Loops** in the primary card,
keeps the long title only in a visibly labelled `STRESS FIXTURE`, and records a
machine-readable `context-fidelity.json` result. The judge panel now receives
the immutable headline and treats a mismatch as a blocking veto.

## Prevention rules proposed

1. Freeze an Experiment brief before the first Loop and distinguish invariants
   from optimization variables.
2. Inject the frozen brief and explicit allowed-change scope into every
   generation, synthesis, repair, and judge Prompt.
3. Keep stress, localization, adversarial, and capacity fixtures secondary and
   visibly labelled; they must not silently become primary candidates.
4. Compute invariant gates from an external canonical source, never from values
   declared by the candidate being judged.
5. Blind candidate identity and order, not the acceptance contract.
6. Block Champion promotion when any invariant gate is missing, failed, or
   unverified.
7. Treat panel diversity as protection against subjective bias, not as a
   substitute for objective correctness gates.

