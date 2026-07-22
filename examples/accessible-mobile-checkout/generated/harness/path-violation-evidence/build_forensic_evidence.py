#!/usr/bin/env python3
"""Build deterministic forensic records for the approved path remediation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_ROOT = Path(__file__).resolve().parent
HARNESS_ROOT = EVIDENCE_ROOT.parent
GENERATED_ROOT = HARNESS_ROOT.parent
EXPERIMENT_ROOT = GENERATED_ROOT.parent
REPO_ROOT = EXPERIMENT_ROOT.parents[1]
RECOVERED_ROOT = EVIDENCE_ROOT / "root-scripts"
SCRATCH_ROOT = HARNESS_ROOT / "scratch"

SNAPSHOT_UTC = "2026-07-21T08:11:58.1477408Z"
OWNER_AUTHORIZATION_UTC = "2026-07-21T08:11:36.118Z"
SESSION_ID = "7f1c73a6-e8a1-4424-aa61-74c07fd35f32"

RECOVERED_FILES = {
    "modify.py": {
        "sha256": "0600c43f7536a2a2c2563823fc95ae17d104153718523767bbfcb90f974d4d0a",
        "length": 1007,
        "creation_utc": "2026-07-21T06:43:08.9529926Z",
        "modified_utc": "2026-07-21T06:43:08.9539890Z",
        "capture_call_id": "call_vhq5IXl9lQS3z6qgsjM2JkjM",
    },
    "modify2.py": {
        "sha256": "0d3cde4db1f821d633146f12e47b8599b359a3ab64f030c43f8351d8c2d74292",
        "length": 942,
        "creation_utc": "2026-07-21T06:46:12.0808978Z",
        "modified_utc": "2026-07-21T06:46:12.0820431Z",
        "capture_call_id": "call_Ob0HAifJ4wLtx1U21isMPcWy",
    },
    "modify3.py": {
        "sha256": "7806a617712df81ab8e6fcbe096d8c16f2af1663a421a64f4ed9940d795cdce7",
        "length": 479,
        "creation_utc": "2026-07-21T06:47:52.6999423Z",
        "modified_utc": "2026-07-21T06:47:52.7020442Z",
        "capture_call_id": "call_4vcBCBEyTrjAqCa80kBJ8d1B",
    },
    "test-focus-why.py": {
        "sha256": "df3f7bb89363160d65c3415b8a8c4c41a39ac38b8bd44b428cfd7d36851d9a94",
        "length": 989,
        "creation_utc": "2026-07-21T06:43:45.7584816Z",
        "modified_utc": "2026-07-21T06:43:45.7606361Z",
        "capture_call_id": "call_WYaVQSmTPcSAGukUHosWV87H",
    },
    "test-focus.js": {
        "sha256": "25b6afbccfad2049e53bf9407177201061dcb708b64fe452fa251639a20b1979",
        "length": 696,
        "creation_utc": "2026-07-21T06:41:15.3926359Z",
        "modified_utc": "2026-07-21T06:41:15.3958722Z",
        "capture_call_id": "call_vbpcCEN0RMTqzFjBo25RVvcg",
    },
    "test-focus.py": {
        "sha256": "477b81045ae7ba634b9cd2245f34d42f75586e8f0b6d5087ddb0e881a3b2edd3",
        "length": 892,
        "creation_utc": "2026-07-21T06:41:22.0212946Z",
        "modified_utc": "2026-07-21T06:41:22.0212946Z",
        "capture_call_id": "call_FsaiiDxDeAjdwinvUDyeH056",
    },
    "test-gates.py": {
        "sha256": "de51a917b14aa9e0d003efb5e84fc98cf42b089e31448bcaf9f4889d3b060563",
        "length": 49175,
        "creation_utc": "2026-07-21T06:42:34.5380911Z",
        "modified_utc": "2026-07-21T06:42:34.5860424Z",
        "capture_call_id": None,
        "recovery_source": "Byte-identical frozen harness run_checkout_gates.py.",
    },
    "test-harness-condition.py": {
        "sha256": "b3a2b817fd87e865eff831340a0aaae552892e44216674fbd8af0dc40b79e953",
        "length": 2044,
        "creation_utc": "2026-07-21T06:42:14.8432109Z",
        "modified_utc": "2026-07-21T06:42:14.8562608Z",
        "capture_call_id": "call_BM3qLoZNpqGYULzhibfGx2DE",
    },
    "test-harness-focus.py": {
        "sha256": "5e9b1d2bb8df4623fd6a919bc5fe77c2808d52cae6b6f846f3f217007338d973",
        "length": 928,
        "creation_utc": "2026-07-21T06:41:58.2372475Z",
        "modified_utc": "2026-07-21T06:41:58.2382479Z",
        "capture_call_id": "call_P55IpEkws9qAOP2BR35qQBRS",
    },
    "test-harness.py": {
        "sha256": "f89bc80f124c5fdb417b3b78b928a036207e8726b7b4250c131f9770866333cb",
        "length": 962,
        "creation_utc": "2026-07-21T06:41:32.3469555Z",
        "modified_utc": "2026-07-21T06:41:32.3469555Z",
        "capture_call_id": "call_XAGB16WdBd10EMNcMnXuYXxT",
    },
    "test-html.py": {
        "sha256": "98881735d43584f2d82170641a6c706392b7f8b8eb2777e839162bbaf802eb0a",
        "length": 813,
        "creation_utc": "2026-07-21T06:48:16.8676819Z",
        "modified_utc": "2026-07-21T06:48:16.8701989Z",
        "capture_call_id": "call_iOR7pfHYtSkydvuJIdtytCnZ",
    },
    "test-paint.py": {
        "sha256": "7007ec7bd1ad6258fcd9c4f8f71c7c368930fb54496c4659bd07c7f291a15a91",
        "length": 2373,
        "creation_utc": "2026-07-21T06:45:35.3758352Z",
        "modified_utc": "2026-07-21T06:45:35.3764138Z",
        "capture_call_id": "call_Fec2EK3jZuUabZmMQm3JFIQg",
    },
    "test-visibility-viewport.py": {
        "sha256": "8106fcb3afcf069cf0ef27bb50f61c561620f517d4988a7344e3e83f5afa27a8",
        "length": 797,
        "creation_utc": "2026-07-21T06:46:51.9061804Z",
        "modified_utc": "2026-07-21T06:46:51.9071799Z",
        "capture_call_id": "call_X2H7tWzJoQXpu6kn7zMXD3p1",
    },
    "test-visibility.py": {
        "sha256": "197925dac416d45aad67db01ebc76f9c4836c17f570f12b75c38547c70b694a4",
        "length": 700,
        "creation_utc": "2026-07-21T06:45:22.8771850Z",
        "modified_utc": "2026-07-21T06:45:22.8782686Z",
        "capture_call_id": "call_gFwLqJFD4YaGTW3qw0R7Sje5",
    },
    "test-visible-why.py": {
        "sha256": "630c1b913e65890dcc3c0bb82260eebb270b991888ccfb63d207993f06a3a205",
        "length": 924,
        "creation_utc": "2026-07-21T06:47:38.2723580Z",
        "modified_utc": "2026-07-21T06:47:38.2757169Z",
        "capture_call_id": "call_5FBe7sfY9KS4lAiax7E87Y5I",
    },
}

SCRATCH_FILES = {
    ".gitignore": {
        "sha256": "4bb38be6d6d9ef0d2f9bcc339850ff48d821eccfa739369402b354c9ba946ea2",
        "length": 16,
        "creation_utc": "2026-07-21T05:58:25.7648806Z",
        "modified_utc": "2026-07-21T05:58:25.7658886Z",
        "origin": "approved preflight scratch-root setup",
    },
    "loop02-gate-detail.txt": {
        "sha256": "32df846d2dbea8a1cec9a8cf3dc686f5de3e62abbe38ff65918727c929601490",
        "length": 2875,
        "creation_utc": "2026-07-21T07:52:28.9667389Z",
        "modified_utc": "2026-07-21T07:52:29.2031076Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe.py": {
        "sha256": "bdfb87980ac9843455d4b5a23f12909b916abb85a1ac4804d6197179eae55334",
        "length": 1366,
        "creation_utc": "2026-07-21T07:53:54.2193718Z",
        "modified_utc": "2026-07-21T07:53:54.2203710Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe2.py": {
        "sha256": "d886c353da6346291e1d868e1ebdd57c7ed1fc396dd2d93a04f2ce2a43773ed8",
        "length": 700,
        "creation_utc": "2026-07-21T07:54:29.1933142Z",
        "modified_utc": "2026-07-21T07:54:29.1964821Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe3.py": {
        "sha256": "35918a5207c2d6f4e8e3f81ff25dc0f5c7b1b5bd4f1408d881822cba5687da51",
        "length": 1691,
        "creation_utc": "2026-07-21T07:55:36.8319492Z",
        "modified_utc": "2026-07-21T07:55:36.8335110Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe4.py": {
        "sha256": "413d186abbd322ed54567f67d1ca7cde8c8a13ab141540d2b742ba1db34d522b",
        "length": 2236,
        "creation_utc": "2026-07-21T07:56:33.5352712Z",
        "modified_utc": "2026-07-21T07:56:33.5362683Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe5.py": {
        "sha256": "1b5aff482887aa4805c451d1293ec148776817b39cfc0cdb2128dde82561274b",
        "length": 1955,
        "creation_utc": "2026-07-21T07:58:15.9521151Z",
        "modified_utc": "2026-07-21T07:58:15.9521151Z",
        "origin": "resumable-wizard-loop-02",
    },
    "debug_probe6.py": {
        "sha256": "eed439aada9758539e4fa08d28d7eeafa99a0d8351d0d67e5c5cf33354c6f29d",
        "length": 642,
        "creation_utc": "2026-07-21T07:58:29.3041520Z",
        "modified_utc": "2026-07-21T07:58:29.3041520Z",
        "origin": "resumable-wizard-loop-02",
    },
}

FROZEN_FILES = {
    EXPERIMENT_ROOT / "setup" / "experiment-brief.json": "ddec5caa3b16f4b11f2eb62d089c1375cd19d1ab1b3aeb31a834654628ebda13",
    EXPERIMENT_ROOT / "setup" / "prompt.md": "86d73090fa414abcb6c33721cfc10177b4482b2516bb897750ea188e95f99928",
    GENERATED_ROOT / "build_viewer.py": "bc4a4096a076144199e472ed3232e1e76eca36b033f47e85b349f47a9cd006eb",
    HARNESS_ROOT / "canonical-fixture.json": "e6622cd3f97964aad041603f53ffe2b1f9360a4bcee7bb6624e0d662e8b5b894",
    HARNESS_ROOT / "run_checkout_gates.py": "de51a917b14aa9e0d003efb5e84fc98cf42b089e31448bcaf9f4889d3b060563",
    HARNESS_ROOT / "self-test-invalid" / "index.html": "243d78b65b167bdf8c912d3f40c46072ed4bb4b712915de852094ec4a525807b",
}

FRAGMENT_SELF_HASHES = {
    GENERATED_ROOT / "track-resumable-wizard" / "manifest-fragment.json": "63d61ec5fa375a73990c9c1e061740f959221c6e658bd445cc6423549d3cca72",
    GENERATED_ROOT / "track-single-page" / "manifest-fragment.json": "945e35117c221b9c255ebfcf51061d6f03931c0d3977b060d005762708f477e5",
    GENERATED_ROOT / "track-task-cards" / "manifest-fragment.json": "7e0de14597aef4e85a87dd4b32f2fb5832ed6ce5fe2a223419b79dd382d4504e",
}

UNDECLARED_REPORT_HASHES = {
    GENERATED_ROOT / "track-task-cards" / "loop-01" / "evidence" / "objective-report.json": "9b5f13de9737815faf89e6a8a5608060908a22d3ff227df9a9f974bc947eafba",
    GENERATED_ROOT / "track-task-cards" / "loop-02" / "evidence" / "objective-report.json": "cd08b3b470117eccca9086765cbd8c779a124c12cd7df319ea8e9c538c44c6b6",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def verify(path: Path, expected: str, source: str) -> dict[str, Any]:
    actual = sha256(path) if path.is_file() else None
    return {
        "path": relative(path),
        "source": source,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "match": actual == expected,
    }


def resolve_declared_path(fragment: Path, value: str) -> Path:
    raw = value.replace("\\", "/")
    marker = ".experiments/accessible-mobile-checkout/generated/"
    if marker in raw:
        raw = raw.split(marker, 1)[1]
    raw = raw.removeprefix("./")
    if raw.startswith(("track-", "synthesis/")):
        return GENERATED_ROOT / raw
    return fragment.parent / raw


def declared_artifact_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for fragment in sorted(GENERATED_ROOT.glob("track-*/manifest-fragment.json")):
        data = json.loads(fragment.read_text(encoding="utf-8"))

        def visit(value: Any) -> None:
            if isinstance(value, dict):
                path = value.get("path")
                expected = value.get("sha256")
                if isinstance(path, str) and isinstance(expected, str):
                    checks.append(
                        verify(
                            resolve_declared_path(fragment, path),
                            expected,
                            relative(fragment),
                        )
                    )
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(data)
    return checks


def root_snapshot() -> dict[str, Any]:
    files = []
    for path in sorted(item for item in REPO_ROOT.iterdir() if item.is_file()):
        stat = path.stat()
        files.append(
            {
                "path": path.name,
                "sha256": sha256(path),
                "length": stat.st_size,
                "creation_utc": datetime.fromtimestamp(
                    stat.st_ctime, timezone.utc
                ).isoformat().replace("+00:00", "Z"),
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat().replace("+00:00", "Z"),
            }
        )
    status = git("status", "--short").splitlines()
    root_violations = []
    for entry in status:
        candidate = entry[3:].replace("\\", "/")
        if "/" not in candidate and candidate not in {".experiments"}:
            root_violations.append(candidate)
    return {
        "schema_version": "1.0",
        "captured_utc": SNAPSHOT_UTC,
        "branch": git("branch", "--show-current"),
        "git_status": status,
        "root_files": files,
        "root_violation_files_present": root_violations,
    }


def recovered_checks() -> list[dict[str, Any]]:
    result = []
    for name, record in RECOVERED_FILES.items():
        path = RECOVERED_ROOT / name
        actual = sha256(path) if path.is_file() else None
        result.append(
            {
                "original_path": name,
                "recovered_path": relative(path),
                **record,
                "actual_sha256": actual,
                "actual_length": path.stat().st_size if path.is_file() else None,
                "match": (
                    actual == record["sha256"]
                    and path.stat().st_size == record["length"]
                    if path.is_file()
                    else False
                ),
            }
        )
    return result


def scratch_checks() -> list[dict[str, Any]]:
    result = []
    actual_names = {path.name for path in SCRATCH_ROOT.iterdir() if path.is_file()}
    expected_names = set(SCRATCH_FILES)
    if actual_names != expected_names:
        raise RuntimeError(
            f"Scratch inventory changed: expected {sorted(expected_names)}, got {sorted(actual_names)}"
        )
    for name, record in SCRATCH_FILES.items():
        path = SCRATCH_ROOT / name
        result.append(
            {
                "path": relative(path),
                **record,
                "actual_sha256": sha256(path),
                "actual_length": path.stat().st_size,
                "match": (
                    sha256(path) == record["sha256"]
                    and path.stat().st_size == record["length"]
                ),
            }
        )
    return result


def build_provenance(
    recovered: list[dict[str, Any]], scratch: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "remediated_with_procedural_caveat",
        "owner_authorization_utc": OWNER_AUTHORIZATION_UTC,
        "attribution": {
            "originating_task": "task-cards-loop-01",
            "task_call_id": "call_QJI0iLw1cMlBEjyyE86tO0R7",
            "model": "gemini-3.1-pro-preview",
            "task_window_utc": {
                "start": "2026-07-21T06:17:48.702Z",
                "end": "2026-07-21T06:50:37.7732408Z",
            },
            "confidence": "high",
            "basis": [
                "All original timestamps fall inside the recorded task window.",
                "Every browser probe targets track-task-cards/loop-01.",
                "The task launch restricted writes to track-task-cards/**.",
            ],
        },
        "violations": [
            {
                "id": "task-cards-loop-01-root-scratch",
                "summary": "Fifteen diagnostics were written at repository root outside the task write scope.",
                "recovered_files": recovered,
            },
            {
                "id": "resumable-wizard-loop-02-unapproved-deletion",
                "summary": "The already-live wizard task deleted the fifteen root diagnostics after the procedural pause and before quarantine.",
                "task_call_id": "call_PNnxF0twhYllpjhAqxuI90So",
                "model": "claude-sonnet-5",
                "authorized_at_time": False,
                "evidence": "Terminal task report plus post-terminal absence check.",
            },
            {
                "id": "resumable-wizard-loop-02-omitted-scratch-provenance",
                "summary": "The wizard wrote surviving scratch diagnostics while metadata falsely claimed the scratch root was not written and omitted exact commands.",
                "scratch_files": scratch,
                "exact_shell_commands_recovered": False,
            },
        ],
        "inferred_absent_debug_copy_caveat": {
            "path": ".experiments/accessible-mobile-checkout/generated/harness/run_checkout_gates_debug.py",
            "status": "not_present",
            "statement": "modify.py, modify2.py, and modify3.py target this path, so a temporary debug harness copy may have existed. No surviving file or command transcript proves creation or execution; the inference is preserved without being promoted to fact.",
        },
        "dependency_assessment": {
            "direct_artifact_dependency": False,
            "runtime_dependency": False,
            "causal_development_influence": True,
            "statement": "No approved Artifact, report, fragment, or metadata referenced a root filename. Final objective reports record the frozen harness and fixture. The diagnostics likely informed later candidate fixes, so the procedural provenance caveat remains.",
        },
        "sensitivity_assessment": {
            "generated_secrets_found": False,
            "external_data_found": False,
            "environment_or_credential_reads_found": False,
            "network_hosts_found": False,
            "statement": "The files contain local Playwright probes and the explicitly synthetic checkout fixture. test-gates.py contains only the byte-identical frozen harness, including external-request detection code and fictional payment values.",
        },
        "validity_assessment": {
            "functional_hash_validity": "preserved",
            "procedural_validity": "remediated_with_permanent_caveat",
            "candidate_disposition": "retain; do not rerun solely for remediation",
        },
        "task_transcript_references": {
            "session_id": SESSION_ID,
            "task_launch_call_ids": [
                "call_QJI0iLw1cMlBEjyyE86tO0R7",
                "call_PNnxF0twhYllpjhAqxuI90So",
            ],
            "content_capture_call_ids": sorted(
                record["capture_call_id"]
                for record in RECOVERED_FILES.values()
                if record.get("capture_call_id")
            ),
        },
        "records": {
            "snapshot": "worktree-snapshot.json",
            "hash_verification": "hash-verification.json",
            "report": "forensic-report.md",
        },
    }


def build_report(provenance: dict[str, Any]) -> str:
    lines = [
        "# Path violation forensic report",
        "",
        "Status: remediated with a permanent procedural caveat.",
        "",
        "## Attribution",
        "",
        "All 15 root diagnostics are attributed with high confidence to "
        "`task-cards-loop-01` (`gemini-3.1-pro-preview`, task call "
        "`call_QJI0iLw1cMlBEjyyE86tO0R7`). Their timestamps fall inside the "
        "recorded task window and their probes target only task-card Loop 01.",
        "",
        "## Recovery",
        "",
        "The already-live wizard task deleted the originals after the pause. "
        "Each file was reconstructed only from captured full text, except "
        "`test-gates.py`, which was restored from the byte-identical frozen "
        "harness. Every recovered basename, byte length, and SHA-256 matches "
        "the pre-deletion inventory.",
        "",
        "## Missing temporary debug copy",
        "",
        "`modify.py`, `modify2.py`, and `modify3.py` target "
        "`generated/harness/run_checkout_gates_debug.py`. That file is absent. "
        "Its former existence or execution is inferred but not proven.",
        "",
        "## Dependency and sensitivity",
        "",
        "No approved Artifact or report directly references the root files. "
        "They likely influenced development diagnosis, so the provenance caveat "
        "is permanent. No credentials, environment secrets, external-user data, "
        "or external hosts were found; all fixture values are explicitly synthetic.",
        "",
        "## Validity",
        "",
        "Frozen inputs and every declared completed candidate/report Artifact "
        "retain their recorded hashes. Functional evidence remains valid. "
        "Procedural validity is remediated but the deviation and omitted command "
        "provenance remain visible in the Manifest and Viewer.",
        "",
        "Machine-readable details: `provenance.json`, `hash-verification.json`, "
        "and `worktree-snapshot.json`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    snapshot = root_snapshot()
    recovered = recovered_checks()
    scratch = scratch_checks()
    functional = [
        verify(path, expected, "frozen")
        for path, expected in FROZEN_FILES.items()
    ]
    functional.extend(declared_artifact_checks())
    functional.extend(
        verify(path, expected, "fragment-self")
        for path, expected in FRAGMENT_SELF_HASHES.items()
    )
    functional.extend(
        verify(path, expected, "undeclared-objective-report")
        for path, expected in UNDECLARED_REPORT_HASHES.items()
    )
    all_match = (
        all(item["match"] for item in recovered)
        and all(item["match"] for item in scratch)
        and all(item["match"] for item in functional)
        and snapshot["git_status"] == ["?? .experiments/"]
        and snapshot["root_violation_files_present"] == []
    )
    verification = {
        "schema_version": "1.0",
        "owner_authorization_utc": OWNER_AUTHORIZATION_UTC,
        "all_match": all_match,
        "recovered_root_files": recovered,
        "surviving_scratch_files": scratch,
        "functional_files": functional,
    }
    if not all_match:
        raise RuntimeError("Forensic verification failed; records were not written.")

    provenance = build_provenance(recovered, scratch)
    write_json(EVIDENCE_ROOT / "worktree-snapshot.json", snapshot)
    write_json(EVIDENCE_ROOT / "hash-verification.json", verification)
    write_json(EVIDENCE_ROOT / "provenance.json", provenance)
    (EVIDENCE_ROOT / "forensic-report.md").write_text(
        build_report(provenance),
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
