#!/usr/bin/env python3
"""Objective reproducibility + robustness + a11y gate for an experiment viewer.

Inspired by create-canvas-app's deterministic graders (file-exists, node --check
parse, no-forbidden-pattern) layered under an LLM rubric. This is the *objective*
backbone for an interactive experiment viewer: a candidate viewer cannot become
champion unless it passes this gate (see SKILL.md §9). Reference implementation —
stdlib only (plus `node` for the JS parse check).

Static checks (always, on the rendered viewer.html):
  self_contained   no external CDN/network refs (http(s):// or //host) in
                   src/href/import/@import/fetch (w3.org XML namespaces allowed)
  embedded_json    every <script type="application/json"> block JSON.parses
  js_parse         every inline <script> block passes `node --check`
  link_integrity   every local href/src (non-#, non-data:, non-http) resolves
  a11y_static      <html lang>, non-empty <title>, a landmark/role, and a
                   prefers-reduced-motion guard when animation/transition is used

Generator checks (when --build is given; the reproducibility core):
  determinism      running `<build> --data DATA --out X` twice is byte-identical
  robustness       `<build> --data DEGRADED --out X` exits 0 and the output still
                   passes the static parse checks (graceful on missing/empty data)

Usage:
  check_viewer.py --viewer V.html [--build "python build.py"] [--data DIR]
                  [--degraded DIR] [--json]

Exit 0 iff all *required* checks pass. Stdlib only (+ node for --check).
"""
from __future__ import annotations
import argparse, hashlib, json, re, shlex, subprocess, sys, tempfile
from pathlib import Path

W3_ALLOW = ("www.w3.org", "://www.w3.org")

def _scripts(html: str, want_json: bool):
    out = []
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", html, re.S | re.I):
        attrs, body = m.group(1), m.group(2)
        is_json = re.search(r'type\s*=\s*["\']application/json["\']', attrs, re.I)
        if bool(is_json) == want_json:
            out.append((attrs, body))
    return out

def check_self_contained(html: str):
    # strip XML namespace decls + xlink local refs (not network fetches)
    scrubbed = re.sub(r'xmlns(:\w+)?\s*=\s*"[^"]*"', "", html)
    hits = []
    for m in re.finditer(r'(?:src|href|data-src)\s*=\s*"([^"]+)"', scrubbed, re.I):
        u = m.group(1).strip()
        if re.match(r'(?:https?:)?//', u) and not any(a in u for a in W3_ALLOW):
            hits.append(u)
    for pat in (r'@import\s+(?:url\()?["\']?(https?:)?//[^"\')]+',
                r'from\s+["\'](https?:)?//[^"\']+["\']',
                r'\bfetch\s*\(\s*["\'](https?:)?//[^"\']+'):
        for m in re.finditer(pat, scrubbed, re.I):
            frag = m.group(0)
            if not any(a in frag for a in W3_ALLOW):
                hits.append(frag[:60])
    return (len(hits) == 0, {"external_refs": sorted(set(hits))[:10]})

def check_embedded_json(html: str):
    blocks = _scripts(html, want_json=True)
    errs = []
    for i, (attrs, b) in enumerate(blocks):
        try:
            json.loads(b)
        except Exception as e:
            errs.append(f"block[{i}]: {e}")
    # not having any application/json block is allowed (data may be inline JS)
    return (len(errs) == 0, {"json_blocks": len(blocks), "errors": errs})

def check_js_parse(html: str):
    blocks = _scripts(html, want_json=False)
    errs = []
    with tempfile.TemporaryDirectory() as td:
        for i, (attrs, b) in enumerate(blocks):
            if not b.strip():
                continue
            is_mod = (re.search(r'type\s*=\s*["\']module["\']', attrs, re.I)
                      or re.search(r'\b(?:import|export)\b', b))
            f = Path(td) / f"s{i}.{'mjs' if is_mod else 'js'}"
            f.write_text(b, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                errs.append(f"block[{i}]: {(r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else 'parse error'}")
    return (len(errs) == 0, {"js_blocks": len(blocks), "errors": errs})

def check_link_integrity(html: str, viewer: Path):
    # Only static markup has real links; strip <script>/<style> so JS template
    # literals (e.g. `${esc(a.path)}`) and CSS aren't misread as broken links.
    markup = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    missing = []
    for m in re.finditer(r'(?:src|href)\s*=\s*"([^"]+)"', markup, re.I):
        u = m.group(1).strip()
        if (not u or u.startswith("#") or u.startswith("data:")
                or re.match(r'(?:https?:)?//', u) or ":" in u.split("/")[0]):
            continue
        if "${" in u or "{{" in u:  # unresolved template placeholder, not a static link
            continue
        if not (viewer.parent / u).exists():
            missing.append(u)
    return (len(missing) == 0, {"missing": sorted(set(missing))[:10]})

def check_a11y(html: str):
    issues = []
    if not re.search(r'<html\b[^>]*\blang\s*=', html, re.I):
        issues.append("no <html lang>")
    if not re.search(r'<title\b[^>]*>\s*\S', html, re.I):
        issues.append("no non-empty <title>")
    if not re.search(r'<(main|nav|header|footer)\b', html, re.I) and not re.search(r'\brole\s*=', html, re.I):
        issues.append("no landmark element or role=")
    uses_motion = re.search(r'@keyframes|animation\s*:|transition\s*:', html, re.I)
    if uses_motion and not re.search(r'prefers-reduced-motion', html, re.I):
        issues.append("animation/transition without prefers-reduced-motion guard")
    return (len(issues) == 0, {"issues": issues})

def _run_build(build_cmd: str, data: Path, out: Path):
    cmd = shlex.split(build_cmd) + ["--data", str(data), "--out", str(out)]
    return subprocess.run(cmd, capture_output=True, text=True)

def check_determinism(build_cmd: str, data: Path):
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.html", Path(td) / "b.html"
        r1 = _run_build(build_cmd, data, a)
        r2 = _run_build(build_cmd, data, b)
        if r1.returncode != 0 or r2.returncode != 0:
            return (False, {"error": "build failed", "stderr": (r1.stderr or r2.stderr)[-400:]})
        if not a.exists() or not b.exists():
            return (False, {"error": "no output produced"})
        ha = hashlib.sha256(a.read_bytes()).hexdigest()
        hb = hashlib.sha256(b.read_bytes()).hexdigest()
        return (ha == hb, {"sha_a": ha[:12], "sha_b": hb[:12], "bytes": a.stat().st_size})

def check_robustness(build_cmd: str, degraded: Path):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "deg.html"
        r = _run_build(build_cmd, degraded, out)
        if r.returncode != 0:
            return (False, {"error": "build crashed on degraded input", "stderr": (r.stderr or r.stdout)[-400:]})
        if not out.exists() or out.stat().st_size == 0:
            return (False, {"error": "no/empty output on degraded input"})
        html = out.read_text(encoding="utf-8", errors="replace")
        okj, dj = check_embedded_json(html)
        oks, ds = check_js_parse(html)
        return (okj and oks, {"json_ok": okj, "js_ok": oks, "detail": {**dj, **ds}})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viewer", required=True)
    ap.add_argument("--build", default=None, help='e.g. "python build.py"')
    ap.add_argument("--data", default=None)
    ap.add_argument("--degraded", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    viewer = Path(a.viewer)
    report, required_ok = {}, True
    def add(name, ok, detail, required=True):
        nonlocal required_ok
        report[name] = {"pass": bool(ok), "required": required, **detail}
        if required and not ok:
            required_ok = False

    if not viewer.exists() or viewer.stat().st_size == 0:
        print(json.dumps({"error": f"viewer missing/empty: {viewer}"}))
        sys.exit(2)
    html = viewer.read_text(encoding="utf-8", errors="replace")

    add("self_contained", *check_self_contained(html))
    add("embedded_json", *check_embedded_json(html))
    add("js_parse", *check_js_parse(html))
    add("link_integrity", *check_link_integrity(html, viewer))
    add("a11y_static", *check_a11y(html))

    if a.build and a.data:
        add("determinism", *check_determinism(a.build, Path(a.data)))
    if a.build and a.degraded:
        add("robustness", *check_robustness(a.build, Path(a.degraded)))

    summary = {"viewer": str(viewer), "bytes": viewer.stat().st_size,
               "all_required_pass": required_ok,
               "checks": {k: v["pass"] for k, v in report.items()}}
    if a.json:
        print(json.dumps({"summary": summary, "report": report}, indent=2))
    else:
        print(f"VIEWER GATE: {'PASS' if required_ok else 'FAIL'}  ({viewer})")
        for k, v in report.items():
            mark = "ok " if v["pass"] else "XX "
            extra = "" if v["pass"] else f"  -> {json.dumps({x: v[x] for x in v if x not in ('pass','required')})[:160]}"
            print(f"  [{mark}] {k}{extra}")
    sys.exit(0 if required_ok else 1)

if __name__ == "__main__":
    main()
