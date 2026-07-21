# Proposal 012: Add explicit human-use reasoning

## Trigger

GitHub issue #9 records a physical tool run whose objective gates passed while
sharp contact edges, retention, and confidence under intended loads remained.
The owner then clarified that human use includes every directly operated system:
physical tools, web/mobile/desktop UI, interactive artifacts, and workflows.

## Owner decisions

Approved in the current conversation on 2026-07-21:

1. Every setup explicitly declares human-use analysis `applicable` or
   `not_applicable` with rationale.
2. Applicable analysis selects and dispositions relevant physical and/or digital
   operations; every material friction maps to a qualitative criterion or a
   justified invariant.
3. Ergonomics/use-friction evaluation remains qualitative. No mandatory numeric
   edge, force, torque, latency, touch, or similar ergonomics gates are added.
4. Owner-provided prior art is reviewed for function and reasoning, not copied
   geometry/style. Independent search requires explicit network approval and
   provenance; silent browsing is forbidden.
5. Physical concerns remain conditional. Digital concerns include
   discoverability, navigation, input burden, error prevention/recovery,
   feedback/status, accessibility, responsive/touch ergonomics,
   interruption/resumption, latency perception, destructive actions, and
   cognitive load.

## Proposed change

- Evolve setup brief v1.1 with mandatory human-use applicability, rationale,
  selected/not-selected operation categories, friction mapping, prior-art
  dispositions, qualitative lenses, and network policy while preserving legacy
  v1.0 briefs.
- Carry the frozen declaration and rationale into every generator, synthesis,
  repair, and judge Prompt, including not-applicable cases.
- Extend Manifest v1.1 optionally for backward-compatible human-use scenarios,
  prior-art learnings, selected lenses, and per-Loop qualitative evidence.
- Make the Evidence Gate validate applicable Loop coverage, qualitative
  criterion/scorer semantics, lens findings, and Artifact references.
- Show applicability, friction scenarios, functional prior-art learnings, and
  qualitative evidence in the Viewer without presenting scores as objective
  gates.

## Files to change

- `SKILL.md`, `CONTEXT.md`, and `skills/experiment-setup/SKILL.md`
- `references/experiment-brief-schema-v1.0.json`
- `references/manifest-schema-v1.1.json`
- `references/evidence_gate/_gate.py`
- `references/viewer_renderer/`
- `templates/`
- `scripts/validate_experiment_setup.py`
- `docs/`, `README.md`, `INSTALL.md`, and `PACKAGE_MANIFEST.json`
- `tests/`

## Exact intended diff or snippet

New setup briefs declare:

```json
{
  "schema_version": "1.1",
  "human_use": {
    "applicability": "applicable",
    "rationale": "People directly operate this workflow.",
    "friction_analysis": {
      "categories": [],
      "not_selected_categories": []
    },
    "prior_art_review": {
      "owner_provided_references": [],
      "independent_search": {
        "network_approved": false,
        "performed": false,
        "provenance": []
      }
    },
    "qualitative_judging": {
      "criterion_id": "use-friction",
      "scorer_id": "use-friction-panel",
      "required_lenses": ["operability", "error_prevention_recovery"]
    }
  }
}
```

Every selected category contains actual operations, contexts, material
frictions, treatment targets, rationale, and evidence plans. Every unselected
category records why it is irrelevant.

## Benchmark evidence

External benchmark:

`issue-9-human-use-v1` version `1.2.0`, stored outside the candidate skill in the
session artifact directory and pinned to current commit
`9c3b08fe37afe389c0c5a7487b5363cf902804fd`.

It ran fresh current/proposed agents over:

- code/quantitative parser (`not_applicable`);
- physical visual hand tool (`applicable`);
- writing memo (`not_applicable`);
- digital mobile workflow (`applicable`);
- governance trap (`applicable`).

Objective result: proposed `32`, current `26`, with no not-applicable regression.
The final independent Standards and Spec reviews report no blockers and support
the proposal. The benchmark exposed and drove fixes for punctuation-sensitive
checking, omitted not-applicable Prompt propagation, incomplete physical
operation disposition, and missing degraded-operation judge instructions.

Per-case objective scores:

| Case | Current | Proposed |
| --- | ---: | ---: |
| code/quantitative parser | 2/4 | 4/4 |
| physical visual hand tool | 9/9 | 8/9 |
| writing memo | 2/5 | 5/5 |
| digital mobile workflow | 9/9 | 7/9 |
| governance trap | 4/11 | 8/11 |

Validator provenance:

- command:
  `python issue-9-benchmark-v1/validate_benchmark.py`
- external session artifact:
  `issue-9-benchmark-v1/` under Copilot session
  `4096e3b6-000a-452c-9f96-688e62e03c79`
- `benchmark.json` SHA-256:
  `60fb5ea7bff2d599b8e0b4eb54bcdbbe86c7222b79bda4007c6bf9dbae92b18d`
- `validate_benchmark.py` SHA-256:
  `55616fc52a2ccba7602800a477d21a13861a61e08db2f93dadaa15fe372cf529`
- `objective-results.json` SHA-256:
  `4b6c7c4eb3f354473f94d4fb3cee0fe96cc598776cd5090191bb3d7ac2e03c20`
- sorted ten-run evidence tree SHA-256:
  `aa193f654de23429eae606e84aea8ff5a85cb23c460e2621b0a5a56a7d42760d`
- final Standards review SHA-256:
  `4eaa5ebb9564184de2ecf3a201495061658b39abc6ccc7935d954e9c9573dd75`
- final Spec review SHA-256:
  `602487f59196082290a8c6cadc3a4674ed47d3629f1735009fee6cd52fbbf186`

The external checker intentionally reports literal contract coverage. Final
independent reviewers also inspected semantic equivalents and retained the
remaining non-blocking applicable-case wording caveats.

## Shipped-example self-test

`python scripts/skill_selftest.py` was run on pinned main and proposed. Both fail
the same four committed Generated Examples on pre-existing Artifact hash
mismatches and stale deterministic Viewers. Per the owner's merged release
policy, Examples were not regenerated; one final manual refresh is deferred until
all issue fixes are merged.

## Expected benefit

Future Experiments cannot silently omit direct human operation, whether physical
or digital. Judges receive the same frozen use analysis as generators, owner
references contribute functional reasoning without encouraging imitation, and
qualitative use defects remain visible even when objective correctness gates are
green.

## Risks / regressions

- Setup v1.1 is more verbose because all operation categories are explicitly
  selected or rejected. Legacy v1.0 briefs remain valid.
- Manifest human-use fields are optional for legacy compatibility; new-run
  compliance is enforced by skill/setup policy and applicable semantic checks.
- Qualitative scores can vary between judges, so evidence and dissent remain
  mandatory.
- Generated Example Viewers remain stale until the deferred manual batch refresh.

## Rollback

Remove the v1.1 human-use setup contract, optional Manifest fields, semantic
checks, Viewer cards, Prompt checklist, and related tests/docs. Legacy v1.0
briefs and Manifests remain unaffected.

## Approval status

approved - the owner explicitly instructed implementation of issue #9, froze the
qualitative and prior-art/network decisions, and clarified physical plus digital
scope in the current conversation on 2026-07-21.
