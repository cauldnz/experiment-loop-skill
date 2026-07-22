# Prompt history — single-page-loop-01

`human_use.applicability = applicable`. Rationale: The Artifact is a human-operated mobile checkout. Its success depends on discoverability, navigation, input burden, error recovery, feedback, accessibility, touch ergonomics, interruption recovery, perceived latency, destructive-action safety, and cognitive load across cross-disability use.

## Complete Track instruction acted on

Run exactly one candidate Loop as model role `generator-single-page` for approved experiment `accessible-mobile-checkout`, revision 1. Own only `.experiments\accessible-mobile-checkout\generated\track-single-page\**`. Do not edit setup, the frozen harness, `build_viewer.py`, another Track, examples, repository source, dependencies, `node_modules`, lockfiles, git history, commits, pull requests, or anything outside the Track. Do not use a network, server, external resource, package, framework, font, image, browser installation, or dependency installation.

Use Loop ID `single-page-loop-01` with `parent_ids: []`. Test the hypothesis: “A single landmarked checkout with a persistent order summary minimizes context switching while headings, fieldsets, error summary, and skip or landmark navigation preserve nonvisual orientation.” Preserve a single-page interaction paradigm: every required section remains present and landmarked, and the order summary remains persistent or sticky at mobile widths without clipping or overflow.

Before coding, read and preserve:

- approved brief SHA-256 `ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13`;
- setup Prompt SHA-256 `86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928`;
- frozen `canonical-fixture.json`, `candidate-contract.json`, `frozen-hashes.json`, and harness;
- exact scratch root `.experiments\accessible-mobile-checkout\generated\harness\scratch`, avoiding writes there unless unavoidable.

Build standalone local `index.html`, `styles.css`, and `app.js`. Use the complete exact synthetic fixture and visibly identify all products, people, contact, address, payment, and order data as fictional and synthetic. Provide every required candidate hook. Prefer native semantics; provide accessible labels, descriptions, errors, status, headings, fieldsets, landmarks, and keyboard-visible focus. All interactive targets must be at least 24 by 24 CSS pixels. Pin tested text, UI, and focus contrast. Under reduced motion, nonessential durations must be no more than 10 milliseconds. Restore only approved non-sensitive contact, address, and shipping state. Never persist card number, expiry, security code, or payment state. Require explicit review and explicit Place order. Keep placement local, deterministic, duplicate-safe, network-free, and produce exactly one confirmation ID `SYN-2048`.

The required tasks are contact, delivery address, shipping method, synthetic payment, review, explicit Place order, and confirmation. The exact cart is Northstar Insulated Bottle, quantity 1, AUD 32.00, plus Willow Cotton Throw, quantity 1, AUD 48.00. Subtotal is AUD 80.00. Standard — 3 to 5 business days is AUD 5.00 and totals AUD 93.50. Express — 1 to 2 business days is AUD 12.00 and totals AUD 100.50. Tax is AUD 8.50. The synthetic customer is Alex Morgan, alex.morgan@example.invalid, +61 400 000 000. The synthetic address is 42 Fiction Lane, Sampleton NSW 2000, Australia. The synthetic card is 4111 1111 1111 1111, expiry 12/34, security code 123, name Alex Morgan. Guest checkout only. Do not add account creation, sign-in, coupon, recommendation, upsell, stock, real payment, real transaction, external request, or real or sensitive data.

### Frozen friction mapping

- Foreseeable misuse: repeated, invalid, premature, or uncertain placement can create duplicate or premature confirmation; require explicit, single, synthetic completion and objective repeated-submit evidence.
- Accessibility and safety interaction: keyboard and assistive semantics must not weaken payment privacy, validation, confirmation, or transaction correctness; expose names, roles, labels, descriptions, focus, status, and confirmation through the same path.
- Accessibility: screen-reader semantics, keyboard operation, visible focus, contrast, reduced motion, and accessible error handling are blocking technical requirements; residual experience quality remains qualitative.
- Discoverability: first-use mobile users must understand the task, required information, progress, totals, and primary action; assess contextually from operable and rendered evidence.
- Navigation: landmarks, headings, section movement, edit actions, focus order, and review access must remain coherent for keyboard and nonvisual operation.
- Input burden: avoid repeated entry, redundant controls, and unnecessary decisions without removing required information; objective interaction counts are non-gating context only.
- Error prevention and recovery: prevent and explain invalid or missing values, focus actionable errors, preserve valid entries, and permit successful correction.
- Feedback and status: saved state, validation, placement, and confirmation must be timely and programmatically exposed; clarity and confidence remain qualitative.
- Responsive touch ergonomics: no clipping or page overflow at 320x568, 360x800, or 390x844; all checkout targets meet the frozen 24x24 technical minimum, while touch comfort remains qualitative.
- Interruption and resumption: restore safe progress after reload and never retain synthetic payment secrets.
- Latency perception: expose a stable busy state during bounded local placement and prevent duplicate activation; perceived reassurance remains qualitative.
- Destructive actions: edit and placement must not silently discard work or create an external transaction.
- Cognitive load: use stable grouping, plain language, visible totals, review, and error presentation; cognitive load remains a qualitative judgement, not a numeric technical gate.

Physical grip, load, insertion, inversion, repetitive-strain geometry, contact-edge, and assembly categories do not apply to this software Artifact. Repeated digital traversal is covered under input burden and navigation.

### Prior-art decision

The owner provided no prior-art references. Independent prior-art search was not approved, was not performed, and has no provenance or reviewed references.

### Evidence and judgement rules

Qualitative use-friction is not an objective ergonomics gate. Objective browser assertions cover only frozen technical correctness and compatibility requirements. Independent judges must later assess exactly: `discoverability`, `navigation`, `input_burden`, `error_prevention_recovery`, `feedback_status`, `accessibility`, `responsive_touch_ergonomics`, `interruption_resumption`, `latency_perception`, `destructive_actions`, and `cognitive_load`. Severe qualitative friction must remain visible in later scores, findings, caveats, and dissent, but cannot override or masquerade as an objective result. Failed or degraded digital operations are defects and cannot be hidden by visual polish.

Write `status.json` at start, update its UTC heartbeat at least once, and finish it terminally. Run the exact frozen objective command from repository root. If it fails, preserve each failed evidence attempt under a separately named evidence directory and repair only clear implementation defects within this Loop. Keep final passing output under `loop-01\evidence`. Create complete `metadata.json`, this Prompt history, `self-observation.md`, and Track-level `manifest-fragment.json`, including stable Artifact IDs, SHA-256 values, `interactive_html`, comparison key `checkout-ui`, objective-only scores, complete prompt chain, one lesson, frozen hashes, and decision `needs_human_review`.

Do not self-promote to `new_best`, run an independent judge, create Loop 02, merge a top-level Manifest, or build the Viewer.

## Input feedback

None.

## Provisional self-observation — non-authoritative

The unchanged frozen objective harness passed on the third preserved attempt with exit code `0`, all seven gate states passing, no failed gate IDs, and no blocking failure. This is objective evidence only. The generator did not score visual or human-use quality, did not compare against another candidate, and does not claim promotion.

## Proposed next Prompt

After independent judges inspect the same candidate, objective reports, mobile screenshots, interaction behavior, and all required qualitative lenses, provide their identity-blind findings as input to `generator-single-page`. If and only if the orchestrator authorizes Loop 02, preserve this single-page paradigm and make one evidence-backed improvement without changing the fixture, harness, scope, objective thresholds, or privacy and safety behavior.
