from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path


W3_ALLOW = ("www.w3.org", "://www.w3.org")
GATE_SIDECAR = "evidence-gate.json"


def _scripts(html: str, *, json_only: bool) -> list[tuple[str, str]]:
    scripts = []
    for match in re.finditer(r"<script\b([^>]*)>(.*?)</script>", html, re.S | re.I):
        attrs, body = match.group(1), match.group(2)
        is_json = bool(
            re.search(r'type\s*=\s*["\']application/json["\']', attrs, re.I)
        )
        if is_json == json_only:
            scripts.append((attrs, body))
    return scripts


def check_self_contained(html: str) -> tuple[bool, dict[str, object]]:
    scrubbed = re.sub(r'xmlns(:\w+)?\s*=\s*"[^"]*"', "", html)
    hits = []
    for match in re.finditer(
        r'(?:src|href|data-src)\s*=\s*"([^"]+)"', scrubbed, re.I
    ):
        url = match.group(1).strip()
        if re.match(r"(?:https?:)?//", url) and not any(
            allowed in url for allowed in W3_ALLOW
        ):
            hits.append(url)
    for pattern in (
        r'@import\s+(?:url\()?["\']?(https?:)?//[^"\')]+',
        r'from\s+["\'](https?:)?//[^"\']+["\']',
        r'\bfetch\s*\(\s*["\'](https?:)?//[^"\']+',
    ):
        for match in re.finditer(pattern, scrubbed, re.I):
            fragment = match.group(0)
            if not any(allowed in fragment for allowed in W3_ALLOW):
                hits.append(fragment[:80])
    unique = sorted(set(hits))
    return not unique, {"external_refs": unique[:10]}


def check_embedded_json(html: str) -> tuple[bool, dict[str, object]]:
    errors = []
    scripts = _scripts(html, json_only=True)
    for index, (_, body) in enumerate(scripts):
        try:
            json.loads(body)
        except json.JSONDecodeError as exc:
            errors.append(f"block[{index}]: {exc}")
    return not errors, {"json_blocks": len(scripts), "errors": errors}


def check_javascript(
    html: str, *, node_command: str | None
) -> tuple[bool | None, dict[str, object]]:
    if not node_command:
        return None, {
            "error": "Node.js is required; install Node.js 20+ and rerun the Evidence Gate"
        }
    errors = []
    scripts = _scripts(html, json_only=False)
    with tempfile.TemporaryDirectory() as temp_dir:
        for index, (attrs, body) in enumerate(scripts):
            if not body.strip():
                continue
            is_module = bool(
                re.search(r'type\s*=\s*["\']module["\']', attrs, re.I)
                or re.search(r"\b(?:import|export)\b", body)
            )
            script = Path(temp_dir) / f"script-{index}.{'mjs' if is_module else 'js'}"
            script.write_text(body, encoding="utf-8")
            try:
                result = subprocess.run(
                    [node_command, "--check", str(script)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError as exc:
                return None, {"error": f"could not run Node.js: {exc}"}
            if result.returncode != 0:
                output = (result.stderr or result.stdout).strip()
                errors.append(
                    f"block[{index}]: {output.splitlines()[-1] if output else 'parse error'}"
                )
    return not errors, {"js_blocks": len(scripts), "errors": errors}


def check_links(html: str, viewer_path: Path) -> tuple[bool, dict[str, object]]:
    markup = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>", "", html, flags=re.S | re.I
    )
    missing = []
    for match in re.finditer(r'(?:src|href)\s*=\s*"([^"]+)"', markup, re.I):
        url = match.group(1).strip()
        if (
            not url
            or url == GATE_SIDECAR
            or url.startswith("#")
            or url.startswith("data:")
            or re.match(r"(?:https?:)?//", url)
            or ":" in url.split("/")[0]
            or "${" in url
            or "{{" in url
        ):
            continue
        if not (viewer_path.parent / url).exists():
            missing.append(url)
    unique = sorted(set(missing))
    return not unique, {"missing": unique[:10]}


def check_accessibility(html: str) -> tuple[bool, dict[str, object]]:
    issues = []
    if not re.search(r"<html\b[^>]*\blang\s*=", html, re.I):
        issues.append("no <html lang>")
    if not re.search(r"<title\b[^>]*>\s*\S", html, re.I):
        issues.append("no non-empty <title>")
    if not re.search(r"<(main|nav|header|footer)\b", html, re.I) and not re.search(
        r"\brole\s*=", html, re.I
    ):
        issues.append("no landmark element or role")
    uses_motion = re.search(r"@keyframes|animation\s*:|transition\s*:", html, re.I)
    if uses_motion and not re.search(r"prefers-reduced-motion", html, re.I):
        issues.append("motion without prefers-reduced-motion guard")
    return not issues, {"issues": issues}
