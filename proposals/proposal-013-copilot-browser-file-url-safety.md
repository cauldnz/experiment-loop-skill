# Proposal 013: Avoid unsafe file URLs in the Copilot Browser canvas

## Trigger

On Windows, an agent opened a generated Experiment Viewer through the GitHub
Copilot App Browser canvas with a valid `file:///C:/.../viewer.html` URL. The
Viewer rendered, then Wry 0.55.1's WebView2 IPC handler raised a native
**Fatal Error**:

```text
called `Result::unwrap()` on an `Err` value:
http::Error(InvalidUri(InvalidFormat))
```

The main GitHub Copilot App 1.0.25 process then terminated with Windows BEX64
exception `0xc0000409`. The Viewer itself loaded successfully in isolated
Chromium over both `file://` and loopback HTTP.

## Owner decisions

Approved in the current conversation on 2026-07-22:

1. While affected Wry versions remain deployed in the Windows GitHub Copilot
   App, agents must not open Experiment Viewers in its Browser canvas through
   `file://`.
2. For Browser-canvas review, serve the generated root on `127.0.0.1` with an
   ephemeral port, use the printed loopback HTTP URL, and stop the server after
   review.
3. Ordinary browsers may continue opening the self-contained Viewer directly
   from disk.
4. Loopback transport does not change Viewer generation, determinism,
   Navigation Evidence, or the Evidence Gate.

## Proposed change

- Add a mandatory Browser-canvas safety rule to `SKILL.md`.
- Add the same scoped warning and workaround to the Viewer reference and
  quickstart documentation.
- Preserve direct disk-opening guidance for ordinary browsers.
- Scope the warning to Windows GitHub Copilot App builds that still deploy the
  affected Wry URI-handling path; do not assert that all future app versions
  remain affected.

## Files to change

- `SKILL.md`
- `docs/viewer.md`
- `docs/quickstart.md`
- `proposals/proposal-013-copilot-browser-file-url-safety.md`

No generated Experiment, Example, Manifest, Viewer, schema, or Evidence Gate
output changes.

## Exact intended diff or snippet

`SKILL.md` requires:

```text
When opening a Viewer in the GitHub Copilot App Browser canvas on Windows,
never use a file:// URL while affected Wry versions remain deployed. Serve the
generated root on loopback:

python -m http.server 0 --bind 127.0.0.1 --directory <generated-root>

Open http://127.0.0.1:<printed-port>/viewer.html using the ephemeral port
printed by Python, then stop the server after review.
```

`docs/viewer.md` explains that direct disk opening remains supported in an
ordinary browser, identifies the affected GitHub Copilot App/Wry path, and
documents loopback HTTP as transport only.

`docs/quickstart.md` repeats the operational rule at the point where users are
told to inspect `viewer.html`.

## Evidence

- Exact matching GitHub Copilot App 1.0.25 report:
  [github/app#2177](https://github.com/github/app/issues/2177)
- Related Wry `InvalidUri` runtime and containment variant:
  [github/app#1171](https://github.com/github/app/issues/1171)
- Upstream Wry file-URI panic:
  [tauri-apps/wry#1255](https://github.com/tauri-apps/wry/issues/1255)
- Open, unmerged Wry fix targeting 0.56.0:
  [tauri-apps/wry#1772](https://github.com/tauri-apps/wry/pull/1772)
- Local safe parser repro: Wry's `http::Request` construction rejects
  `file:///C:/tmp/viewer.html` with `InvalidUri(InvalidFormat)` and accepts
  `http://127.0.0.1:<port>/viewer.html`.
- Local isolated browser matrix: the exact 11,290,226-byte Viewer, minimal HTML,
  and an 11 MB synthetic page all loaded successfully over both `file://` and
  loopback HTTP in pinned Chromium.
- Loopback command validation: Python selected an ephemeral `127.0.0.1` port,
  and `viewer.html` returned HTTP 200 with the expected title and byte length.

## Expected benefit

Agents retain the convenience of an in-app Browser canvas without risking a
native Wry panic that can terminate the GitHub Copilot App host. The workaround
is dependency-free, binds only to loopback, avoids fixed-port conflicts, and
leaves the durable Viewer artifact and all evidence contracts unchanged.

## Risks / regressions

- **Version staleness:** the warning may outlive the affected Wry deployment.
  Revisit it after the GitHub Copilot App ships a Wry version containing
  tauri-apps/wry#1772 (currently targeted for 0.56.0) and a Windows Browser-canvas
  regression confirms `file://` no longer panics. Until then, the conservative
  loopback path remains safe.
- A temporary HTTP server is an additional review-time process. Binding to
  `127.0.0.1`, choosing an ephemeral port, and stopping it immediately after
  review limit exposure and lifecycle risk.
- The printed ephemeral port must be copied into the Browser-canvas URL.
- This guidance does not make `file://` unsafe in ordinary browsers; wording
  must remain specific to the affected Copilot App Browser-canvas path.

## Rollback

After a shipped GitHub Copilot App version is verified to contain the upstream
Wry fix and passes a Windows `file://` Browser-canvas regression, remove the
mandatory loopback warning from `SKILL.md`, `docs/viewer.md`, and
`docs/quickstart.md`. Retain this proposal as the historical decision record.
No generated artifacts or evidence formats require migration.

## Validation

- `python -m unittest discover -s tests`: 64 tests passed.
- `python scripts/skill_selftest.py`: the same four committed Generated Examples
  fail on pre-existing Artifact hash mismatches and stale deterministic Viewers
  recorded in Proposal 012. This proposal does not regenerate or modify those
  Examples.
- `python -m http.server 0 --bind 127.0.0.1 --directory <generated-root>`:
  selected an ephemeral loopback port; the exact Viewer returned HTTP 200 with
  the expected title and 11,290,226-byte content length.
- `git diff --check`: passed.

## Approval status

approved - the owner explicitly approved durable Proposal 013 and its scoped
loopback-HTTP mitigation in the current conversation on 2026-07-22.

## Applied result

Applied to `SKILL.md`, `docs/viewer.md`, and `docs/quickstart.md`. The guidance
is scoped to affected Wry deployments in the Windows GitHub Copilot App Browser
canvas, uses an ephemeral `127.0.0.1` port, preserves ordinary browser disk
opening, and leaves Viewer determinism and Evidence Gate semantics unchanged.
