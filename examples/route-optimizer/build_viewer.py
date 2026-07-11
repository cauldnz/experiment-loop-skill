#!/usr/bin/env python3
"""Deterministic, manifest-driven viewer generator for a worked example.

This is the ``<build> --data DIR --out FILE`` generator that ``run_example.py``
uses to emit ``viewer.html``, and that ``scripts/check_viewer.py`` drives for the
determinism and robustness checks (see SKILL.md sec 9). It is a pure function of
the manifest: no wall-clock, no randomness, no network, so building twice is
byte-identical. It degrades gracefully — a missing, empty, or malformed
``manifest.json`` still yields a parseable page with a visible diagnostic
instead of crashing.

The renderer is generic over the v0.2 manifest schema
(``references/manifest-schema-v0.2.json``): it reads ``tracks``, ``iterations``
(with ``decision``/``parent_id``/``scores``/``artifacts``/``lesson``),
``scorecard``, ``scorers``, ``judge_panels``, ``best``, ``rules`` and
``synthesis``, so the same file works across the worked examples.

Usage:
    python build_viewer.py --data DIR --out FILE
    # DIR must contain manifest.json; FILE is the viewer written out.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", system-ui, Arial, sans-serif; margin: 0; background: #f4f6fb; color: #1f2933; }
header { background: #0f172a; color: #fff; padding: 26px 34px; }
header h1 { margin: 0 0 6px; font-size: 22px; }
header p { margin: 0; color: #cbd5e1; max-width: 70ch; }
main { padding: 20px 34px 56px; }
nav.tabs { display: flex; flex-wrap: wrap; gap: 4px; border-bottom: 2px solid #d9e2ec; margin: 18px 0 22px; }
.tab { appearance: none; border: 0; background: transparent; font: inherit; color: #475569; padding: 10px 16px; cursor: pointer; border-radius: 8px 8px 0 0; position: relative; transition: color .15s ease, background .15s ease; }
.tab:hover { background: #e8eefc; }
.tab[aria-selected="true"] { color: #1d4ed8; font-weight: 700; }
.tab[aria-selected="true"]::after { content: ""; position: absolute; left: 8px; right: 8px; bottom: -2px; height: 3px; background: #1d4ed8; border-radius: 3px; }
.tab:focus-visible { outline: 3px solid #93c5fd; outline-offset: 2px; }
[role="tabpanel"][hidden] { display: none; }
.card { background: #fff; border: 1px solid #d9e2ec; border-radius: 14px; padding: 18px 20px; box-shadow: 0 8px 24px rgba(15,23,42,.06); margin-bottom: 18px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.stat { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; }
.stat .k { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.stat .v { font-size: 16px; font-weight: 600; margin-top: 4px; }
table { border-collapse: collapse; width: 100%; margin-top: 8px; }
td, th { border-bottom: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 14px; }
th { color: #475569; }
code { font-family: "Cascadia Code", Consolas, monospace; font-size: 13px; background: #eef2ff; padding: 1px 5px; border-radius: 5px; }
.pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; margin: 0 6px 6px 0; background: #e0f2fe; color: #075985; }
.pill.new_best { background: #dcfce7; color: #166534; }
.pill.reject { background: #fee2e2; color: #991b1b; }
.pill.keep_for_synthesis { background: #fef3c7; color: #92400e; }
.pill.needs_human_review { background: #ede9fe; color: #5b21b6; }
.pill.failed { background: #fee2e2; color: #991b1b; }
.pill.core { background: #ede9fe; color: #5b21b6; }
.loop { border-left: 5px solid #2563eb; }
.loop.new_best { border-left-color: #16a34a; }
.loop.reject { border-left-color: #dc2626; }
.loop.failed { border-left-color: #dc2626; }
.loop.keep_for_synthesis { border-left-color: #d97706; }
.loop.needs_human_review { border-left-color: #7c3aed; }
.meta { color: #52606d; font-size: 13px; }
.bars { display: grid; gap: 6px; margin-top: 8px; }
.bar-row { display: grid; grid-template-columns: 180px 1fr 84px; gap: 10px; align-items: center; font-size: 13px; }
.bar-track { height: 12px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
.bar-fill { height: 100%; background: #2563eb; border-radius: 999px; }
.graph-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
#graph { min-width: 780px; width: 100%; height: 300px; display: block; }
.arts { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-top: 6px; }
figure.art { margin: 0; }
figure.art img { width: 100%; border: 1px solid #d9e2ec; border-radius: 10px; background: #fff; }
figure.art figcaption { margin-top: 4px; }
pre { white-space: pre-wrap; overflow: auto; background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 12px; }
summary { cursor: pointer; font-weight: 600; }
a { color: #1d4ed8; }
.diag { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; border-radius: 10px; padding: 10px 14px; margin: 12px 0; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <p>__GOAL__</p>
</header>
<main>
  <div id="diagnostic"></div>
  <nav class="tabs" role="tablist" aria-label="Experiment views">
    <button class="tab" role="tab" id="tab-overview" aria-controls="panel-overview" data-tab="overview">Overview</button>
    <button class="tab" role="tab" id="tab-lineage" aria-controls="panel-lineage" data-tab="lineage">Tracks &amp; lineage</button>
    <button class="tab" role="tab" id="tab-loops" aria-controls="panel-loops" data-tab="loops">Loops</button>
  </nav>

  <section role="tabpanel" id="panel-overview" aria-labelledby="tab-overview" tabindex="0">
    <div class="card">
      <h2>Summary</h2>
      <div class="grid">
        <div class="stat"><div class="k">Champion</div><div class="v" id="best"></div></div>
        <div class="stat"><div class="k">Loops</div><div class="v" id="loopCount"></div></div>
        <div class="stat"><div class="k">Tracks</div><div class="v" id="trackCount"></div></div>
        <div class="stat"><div class="k">Judging</div><div class="v" id="judgeSummary"></div></div>
      </div>
    </div>
    <div class="card">
      <h2>Scorecard</h2>
      <table><thead><tr><th>Criterion</th><th>Weight</th><th>Scored by</th></tr></thead><tbody id="scorecard"></tbody></table>
    </div>
    <div class="card">
      <h2>Scorers</h2>
      <table><thead><tr><th>Scorer</th><th>Type</th><th>Command</th></tr></thead><tbody id="scorers"></tbody></table>
    </div>
    <div class="card">
      <h2>Synthesis</h2>
      <p id="synthesis" class="meta"></p>
      <table id="rules"><thead><tr><th>Trigger</th><th>Action</th></tr></thead><tbody></tbody></table>
    </div>
  </section>

  <section role="tabpanel" id="panel-lineage" aria-labelledby="tab-lineage" tabindex="0" hidden>
    <div class="card">
      <h2>Experiment graph</h2>
      <p class="meta">Lineage comes from each loop's <code>parent_id</code>. Colours mark decisions (green = new_best, amber = keep_for_synthesis, red = reject/failed, violet = needs_human_review) and the star marks the champion.</p>
      <div class="graph-wrap"><svg id="graph" role="img" aria-label="Experiment lineage graph"></svg></div>
    </div>
    <div class="card">
      <h2>Score timeline</h2>
      <div class="bars" id="timeline"></div>
    </div>
  </section>

  <section role="tabpanel" id="panel-loops" aria-labelledby="tab-loops" tabindex="0" hidden>
    <div id="loops"></div>
  </section>
</main>

<script type="application/json" id="manifest-data">__MANIFEST_JSON__</script>
<script>
(function () {
  "use strict";
  var raw = document.getElementById("manifest-data").textContent;
  var manifest = {};
  try { manifest = JSON.parse(raw) || {}; } catch (e) { manifest = {}; }

  var esc = function (v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  };
  var byId = function (id) { return document.getElementById(id); };
  var iterations = Array.isArray(manifest.iterations) ? manifest.iterations : [];
  var tracks = Array.isArray(manifest.tracks) ? manifest.tracks : [];
  var bestId = manifest.best && manifest.best.iteration_id;

  if (!iterations.length) {
    var d = byId("diagnostic");
    if (d) { d.innerHTML = '<div class="diag">No experiment data found in this viewer. The manifest was missing, empty, or malformed.</div>'; }
  }

  var scoreFor = function (it) {
    var s = (it.scores || []).filter(function (x) { return typeof x.value === "number"; });
    return s.length ? s[s.length - 1].value : null;
  };
  var critOf = function (it) {
    var arr = it.scores || [];
    for (var k = 0; k < arr.length; k++) {
      var pc = arr[k].per_criterion;
      if (pc && typeof pc === "object" && Object.keys(pc).length) {
        return { scorer: arr[k].scorer_id || "", pc: pc };
      }
    }
    return { scorer: "", pc: {} };
  };

  // ---- Overview ----
  if (byId("best")) byId("best").textContent = manifest.best ? (manifest.best.iteration_id + " (score " + manifest.best.score + ")") : "none";
  if (byId("loopCount")) byId("loopCount").textContent = String(iterations.length);
  if (byId("trackCount")) byId("trackCount").textContent = tracks.map(function (t) { return t.label || t.id; }).join(", ") || "none";
  if (byId("judgeSummary")) {
    var jp = manifest.judge_panels || [];
    if (!jp.length) { byId("judgeSummary").textContent = "objective only"; }
    else {
      var p = jp[0];
      byId("judgeSummary").textContent = p.mode ? (p.mode + " judge") : ((p.judges && p.judges.length) ? (p.judges.length + "-model panel") : "judge panel");
    }
  }
  if (byId("scorecard")) {
    byId("scorecard").innerHTML = (manifest.scorecard || []).map(function (c) {
      return "<tr><th>" + esc(c.label) + "</th><td>" + esc(c.weight) + "</td><td>" + esc(c.scored_by || "") + "</td></tr>";
    }).join("");
  }
  if (byId("scorers")) {
    byId("scorers").innerHTML = (manifest.scorers || []).map(function (s) {
      return "<tr><td>" + esc(s.id) + (s.primary ? ' <span class="pill core">primary</span>' : "") + "</td><td>" + esc(s.type) + "</td><td><code>" + esc(s.command || "") + "</code></td></tr>";
    }).join("");
  }
  if (byId("synthesis")) byId("synthesis").textContent = manifest.synthesis || "";
  if (byId("rules")) {
    var rb = byId("rules").querySelector("tbody");
    if (rb) rb.innerHTML = (manifest.rules || []).map(function (r) {
      return "<tr><td>" + esc(r.trigger) + "</td><td>" + esc(r.action) + "</td></tr>";
    }).join("");
  }

  // ---- Lineage graph ----
  function renderGraph() {
    var g = byId("graph");
    if (!g) return;
    var trackIds = tracks.map(function (t) { return t.id; });
    var nodeById = {};
    var width = Math.max(760, iterations.length * 210 + 140);
    var height = Math.max(220, trackIds.length * 108 + 96);
    iterations.forEach(function (it, i) {
      var ti = Math.max(0, trackIds.indexOf(it.track_id));
      nodeById[it.id] = { it: it, x: 100 + i * 200, y: 66 + ti * 108 };
    });
    var color = function (dec) {
      return { new_best: "#16a34a", keep_for_synthesis: "#d97706", reject: "#dc2626", failed: "#dc2626", needs_human_review: "#7c3aed" }[dec] || "#2563eb";
    };
    var lines = [], nodes = [];
    Object.keys(nodeById).forEach(function (id) {
      var node = nodeById[id];
      var parent = node.it.parent_id ? nodeById[node.it.parent_id] : null;
      if (parent) {
        lines.push('<line x1="' + (parent.x + 70) + '" y1="' + parent.y + '" x2="' + (node.x - 70) + '" y2="' + node.y + '" stroke="#64748b" stroke-width="2" marker-end="url(#arw)"/>');
      }
      var sc = scoreFor(node.it);
      var label = esc(node.it.id.replace(/^loop-/, ""));
      nodes.push('<g><rect x="' + (node.x - 72) + '" y="' + (node.y - 34) + '" width="144" height="68" rx="12" fill="#fff" stroke="' + color(node.it.decision) + '" stroke-width="3"/>' +
        '<text x="' + node.x + '" y="' + (node.y - 12) + '" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0f172a">' + label + (node.it.id === bestId ? " \u2605" : "") + "</text>" +
        '<text x="' + node.x + '" y="' + (node.y + 6) + '" text-anchor="middle" font-size="11" fill="#475569">' + esc(node.it.decision) + "</text>" +
        '<text x="' + node.x + '" y="' + (node.y + 23) + '" text-anchor="middle" font-size="11" fill="#475569">' + (sc == null ? "no score" : "score " + sc) + "</text></g>");
    });
    g.setAttribute("viewBox", "0 0 " + width + " " + height);
    g.innerHTML = '<defs><marker id="arw" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#64748b"/></marker></defs>' + lines.join("") + nodes.join("");
  }
  function renderTimeline() {
    var t = byId("timeline");
    if (!t) return;
    var maxV = Math.max.apply(null, [5].concat(iterations.map(function (i) { return scoreFor(i) || 0; })));
    t.innerHTML = iterations.map(function (i) {
      var v = scoreFor(i) || 0;
      var w = Math.max(2, Math.round(v / maxV * 100));
      return '<div class="bar-row"><div><code>' + esc(i.id.replace(/^loop-/, "")) + '</code></div><div class="bar-track"><div class="bar-fill" style="width:' + w + '%"></div></div><div>' + esc(v) + " / 5</div></div>";
    }).join("");
  }

  // ---- Loops ----
  function renderLoops() {
    var host = byId("loops");
    if (!host) return;
    host.innerHTML = iterations.map(function (i) {
      var crit = critOf(i);
      var pc = crit.pc;
      var scoreRows = (i.scores || []).map(function (s) {
        return "<tr><td>" + esc(s.scorer_id) + "</td><td>" + esc(s.value) + "</td><td>" + esc(s.notes || "") + "</td></tr>";
      }).join("");
      var critRows = Object.keys(pc).map(function (k) {
        return "<tr><td>" + esc(k) + "</td><td>" + esc(pc[k]) + "</td></tr>";
      }).join("");
      var imgs = (i.artifacts || []).filter(function (a) { return a.kind === "image"; }).map(function (a) {
        return '<figure class="art"><img src="' + esc(a.path) + '" alt="' + esc(a.label) + '" loading="lazy"><figcaption class="meta">' + esc(a.label) + "</figcaption></figure>";
      }).join("");
      var links = (i.artifacts || []).map(function (a) {
        return '<a href="' + esc(a.path) + '">' + esc(a.label) + " (" + esc(a.kind) + ")</a>";
      }).join(" &middot; ");
      var lesson = i.lesson || {};
      var lessonText = lesson.trigger ? (lesson.trigger + "\\nAction: " + (lesson.action || "") + "\\nEvidence: " + (lesson.evidence || "") + "\\nConfidence: " + (lesson.confidence || "")) : "";
      return '<div class="card loop ' + esc(i.decision) + '">' +
        "<h2>" + esc(i.id) + (i.id === bestId ? " \u2605" : "") + "</h2>" +
        '<p><span class="pill ' + esc(i.decision) + '">' + esc(i.decision) + '</span><span class="pill">' + esc(i.track_id) + '</span><span class="pill">parent: ' + esc(i.parent_id || "root") + '</span><span class="pill">value ' + esc(scoreFor(i)) + "</span></p>" +
        "<p>" + esc(i.hypothesis) + "</p>" +
        "<table><thead><tr><th>Scorer</th><th>Value</th><th>Notes</th></tr></thead><tbody>" + scoreRows + "</tbody></table>" +
        (critRows ? ("<h3>Criteria (" + esc(crit.scorer) + ")</h3><table><thead><tr><th>Criterion</th><th>Score</th></tr></thead><tbody>" + critRows + "</tbody></table>") : "") +
        (imgs ? ('<h3>Artifacts</h3><div class="arts">' + imgs + "</div>") : "") +
        '<p class="meta">Files: ' + links + "</p>" +
        "<h3>Lesson</h3><pre>" + esc(lessonText) + "</pre>" +
        "<details><summary>Raw loop JSON</summary><pre>" + esc(JSON.stringify(i, null, 2)) + "</pre></details>" +
        "</div>";
    }).join("");
  }

  renderGraph();
  renderTimeline();
  renderLoops();

  // ---- Keyboard-operable tabs + hash deep-links ----
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  var names = tabs.map(function (t) { return t.getAttribute("data-tab"); });

  function activate(name, focusTab) {
    if (names.indexOf(name) === -1) name = names[0];
    tabs.forEach(function (tab) {
      var on = tab.getAttribute("data-tab") === name;
      tab.setAttribute("aria-selected", on ? "true" : "false");
      tab.setAttribute("tabindex", on ? "0" : "-1");
      var panel = byId(tab.getAttribute("aria-controls"));
      if (panel) { if (on) { panel.removeAttribute("hidden"); } else { panel.setAttribute("hidden", ""); } }
      if (on && focusTab) tab.focus();
    });
    if (("#tab=" + name) !== location.hash) {
      try { history.replaceState(null, "", "#tab=" + name); } catch (e) { location.hash = "tab=" + name; }
    }
  }

  tabs.forEach(function (tab, idx) {
    tab.addEventListener("click", function () { activate(tab.getAttribute("data-tab"), false); });
    tab.addEventListener("keydown", function (ev) {
      var i = idx;
      if (ev.key === "ArrowRight" || ev.key === "ArrowDown") { i = (idx + 1) % tabs.length; }
      else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") { i = (idx - 1 + tabs.length) % tabs.length; }
      else if (ev.key === "Home") { i = 0; }
      else if (ev.key === "End") { i = tabs.length - 1; }
      else if (ev.key === "Enter" || ev.key === " ") { activate(tab.getAttribute("data-tab"), true); ev.preventDefault(); return; }
      else { return; }
      ev.preventDefault();
      activate(tabs[i].getAttribute("data-tab"), true);
    });
  });

  function fromHash() {
    var m = /tab=([a-z]+)/.exec(location.hash || "");
    return m ? m[1] : names[0];
  }
  window.addEventListener("hashchange", function () { activate(fromHash(), false); });
  activate(fromHash(), false);
})();
</script>
</body>
</html>
"""


def render_viewer(manifest: dict, diagnostic: str = "") -> str:
    """Render the viewer HTML for a manifest. Pure and deterministic."""
    if not isinstance(manifest, dict):
        manifest = {}
    title = str(manifest.get("title") or "Experiment viewer")
    goal = str(manifest.get("goal") or "")
    data = json.dumps(manifest, indent=2, ensure_ascii=False).replace("</", "<\\/")
    html_out = (
        _TEMPLATE
        .replace("__TITLE__", _escape(title))
        .replace("__GOAL__", _escape(goal))
        .replace("__MANIFEST_JSON__", data)
    )
    if diagnostic:
        html_out = html_out.replace("<body>", "<body>\n<!-- diagnostic: " + _escape(diagnostic) + " -->", 1)
    return html_out


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&#39;")
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render an experiment viewer from a manifest.")
    ap.add_argument("--data", required=True, help="directory containing manifest.json")
    ap.add_argument("--out", required=True, help="output viewer.html path")
    args = ap.parse_args(argv)

    data_dir = Path(args.data)
    manifest_path = data_dir / "manifest.json"
    diagnostic = ""
    manifest: dict = {}
    if not manifest_path.exists():
        diagnostic = f"manifest.json not found in {data_dir}"
        print(diagnostic, file=sys.stderr)
    else:
        text = manifest_path.read_text(encoding="utf-8")
        if not text.strip():
            diagnostic = "manifest.json is empty"
            print(diagnostic, file=sys.stderr)
        else:
            try:
                loaded = json.loads(text)
                manifest = loaded if isinstance(loaded, dict) else {}
                if not isinstance(loaded, dict):
                    diagnostic = "manifest.json is not a JSON object"
                    print(diagnostic, file=sys.stderr)
            except json.JSONDecodeError as exc:
                diagnostic = f"manifest.json did not parse: {exc}"
                print(diagnostic, file=sys.stderr)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_viewer(manifest, diagnostic), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
