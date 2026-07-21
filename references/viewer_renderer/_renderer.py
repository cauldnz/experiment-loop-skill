from __future__ import annotations

import html
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from ._model import DEFAULT_PROFILE, ViewerProfile
from ._panels import panels_for
from ._viewmodel import build_view_model


def _json_for_script(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_viewer(
    manifest: Mapping[str, object] | object,
    *,
    profile: ViewerProfile = DEFAULT_PROFILE,
    diagnostic: str = "",
    data_dir: Path | None = None,
) -> str:
    """Render a deterministic standalone Experiment Viewer."""
    if not isinstance(profile, ViewerProfile):
        raise TypeError("profile must be a ViewerProfile")
    view_model = build_view_model(manifest, data_dir=data_dir, diagnostic=diagnostic)
    panels = panels_for(profile.extra_panels)
    panel_ids = [panel.panel_id for panel in panels]
    tabs = "\n".join(
        (
            f'<button class="tab" role="tab" id="tab-{panel.panel_id}" '
            f'aria-controls="panel-{panel.panel_id}" data-tab="{panel.panel_id}">'
            f"{html.escape(panel.label)}</button>"
        )
        for panel in panels
    )
    controls = [
        panel.interaction() for panel in panels
    ] + [
        {
            "selector": ".graph-node",
            "kind": "graph",
            "actions": [
                {"type": "arrow_navigation", "expect": "single_tab_stop"},
                {"type": "enter", "expect": "loop_inspector_visible"},
            ],
        },
        {
            "selector": "#track-filter,#decision-filter,#loop-search,#champion-filter",
            "kind": "filter",
            "actions": [{"type": "change", "expect": "graph_nodes_dimmed"}],
        },
        {
            "selector": "#topology-zoom-in,#topology-zoom-out,#topology-fit,#topology-reset,#topology-inspector-toggle,#topology-inspector-close,#topology-maximize,#graph-minimap",
            "kind": "topology_viewport",
            "actions": [
                {"type": "operate", "expect": "viewport_drawer_and_maximize_changed"}
            ],
        },
        {
            "selector": "[data-open-loop]",
            "kind": "loop_link",
            "actions": [{"type": "click", "expect": "topology_loop_selected"}],
        },
        {
            "selector": "#theme-select",
            "kind": "select",
            "actions": [{"type": "each_option", "expect": "theme_applied"}],
        },
        {
            "selector": "#manifest-search",
            "kind": "search",
            "actions": [{"type": "input", "expect": "tree_filtered"}],
        },
        {
            "selector": ".expand-artifact",
            "kind": "dialog",
            "actions": [{"type": "click", "expect": "focus_contained_and_restored"}],
        },
        {
            "selector": "#compare-a,#compare-b",
            "kind": "select",
            "actions": [{"type": "each_option", "expect": "comparison_updated"}],
        },
        {
            "selector": "details > summary",
            "kind": "disclosure",
            "actions": [{"type": "toggle", "expect": "expanded_state_changed"}],
        },
        {
            "selector": "#dialog-close",
            "kind": "dialog_close",
            "actions": [{"type": "click", "expect": "dialog_closed"}],
        },
        {
            "selector": "a.button[href]",
            "kind": "link",
            "actions": [{"type": "inspect", "expect": "local_target"}],
        },
    ]
    human_button = ""
    human_dialog = ""
    if view_model["human_review_enabled"]:
        controls.append(
            {
                "selector": "#human-review-button,#human-close,#human-export",
                "kind": "human_review",
                "actions": [
                    {"type": "review_and_export", "expect": "schema_bound_download"}
                ],
            }
        )
        human_button = '<button class="button" id="human-review-button">Human Judge</button>'
        human_dialog = """
<dialog id="human-dialog" aria-labelledby="human-title">
  <div class="dialog-head"><strong id="human-title">Human Judge</strong><button class="button" id="human-close">Close</button></div>
  <div class="dialog-body" id="human-body"></div>
</dialog>"""
    interaction_contract = {
        "version": "1.1",
        "state": "hash",
        "controls": controls,
    }
    title = html.escape(str(view_model["title"]), quote=True)
    def render_document() -> str:
        return (
        _DOCUMENT.replace("__TITLE__", title)
        .replace("__TABS__", tabs)
        .replace("__PANELS__", "\n".join(panel.markup for panel in panels))
        .replace("__HUMAN_BUTTON__", human_button)
        .replace("__HUMAN_DIALOG__", human_dialog)
        .replace("__PANEL_IDS__", _json_for_script(panel_ids))
        .replace("__VIEW_MODEL__", _json_for_script(view_model))
        .replace("__INTERACTION_CONTRACT__", _json_for_script(interaction_contract))
        )

    canonical = render_document()
    viewer_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    view_model["binding"]["viewer_sha256"] = viewer_hash
    return render_document()


def canonical_viewer_sha256(rendered: str) -> str:
    """Hash a Viewer after zeroing its embedded self-binding hash."""
    marker = '"viewer_sha256":"'
    start = rendered.find(marker)
    if start < 0:
        raise ValueError("Viewer binding hash is missing")
    value_start = start + len(marker)
    value_end = value_start + 64
    normalized = rendered[:value_start] + ("0" * 64) + rendered[value_end:]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


_DOCUMENT = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; frame-src data: blob:; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>__TITLE__</title>
<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("scoutTheme");
    const theme =
      param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>
<style>
:root {
  color-scheme: light;
  --cp-bg: #f7f4ef;
  --cp-bg-elevated: #fcfbf8;
  --cp-surface: #ffffff;
  --cp-surface-soft: #f5f5f5;
  --cp-border: #dedede;
  --cp-border-strong: #919191;
  --cp-text: #242424;
  --cp-text-muted: #5c5c5c;
  --cp-text-soft: #6f6f6f;
  --cp-accent: #b11f4b;
  --cp-accent-hover: #9a1a41;
  --cp-accent-soft: rgba(177, 31, 75, 0.08);
  --cp-accent-fg: #ffffff;
  --cp-success: #16a34a;
  --cp-danger: #dc2626;
  --cp-warning: #f59e0b;
  --cp-link: #0078d4;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.12);
  --cp-overlay: rgba(255, 255, 255, 0.8);
  --cp-panel: rgba(255, 255, 255, 0.86);
  --cp-panel-strong: rgba(255, 255, 255, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.55);
  --cp-highlight: rgba(177, 31, 75, 0.12);
}
html[data-theme="dark"] {
  color-scheme: dark;
  --cp-bg: #3d3b3a;
  --cp-bg-elevated: #343231;
  --cp-surface: #292929;
  --cp-surface-soft: #2e2e2e;
  --cp-border: #474747;
  --cp-border-strong: #5f5f5f;
  --cp-text: #dedede;
  --cp-text-muted: #919191;
  --cp-text-soft: #b0b0b0;
  --cp-accent: #fd8ea1;
  --cp-accent-hover: #fb7b91;
  --cp-accent-soft: rgba(253, 142, 161, 0.14);
  --cp-accent-fg: #1a1a1a;
  --cp-success: #4ade80;
  --cp-danger: #f87171;
  --cp-warning: #fbbf24;
  --cp-link: #4da6ff;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
  --cp-overlay: rgba(41, 41, 41, 0.88);
  --cp-panel: rgba(41, 41, 41, 0.72);
  --cp-panel-strong: rgba(41, 41, 41, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.04);
  --cp-highlight: rgba(253, 142, 161, 0.12);
}
* { box-sizing: border-box; }
html { background: var(--cp-bg); }
body {
  margin: 0;
  background: var(--cp-bg);
  color: var(--cp-text);
  font: 14px/1.5 "Segoe UI", Aptos, Calibri, -apple-system, BlinkMacSystemFont, sans-serif;
}
button, select, input { font: inherit; }
button, select, input, summary, a { outline-offset: 3px; }
:focus-visible { outline: 2px solid var(--cp-accent); }
a { color: var(--cp-link); }
.mono, code, pre { font-family: Consolas, "Courier New", Courier, monospace; }
.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: end;
  padding: 18px 28px 0;
  background: var(--cp-bg-elevated);
  border-bottom: 1px solid var(--cp-border);
}
.repo-path { color: var(--cp-text-muted); font-size: 12px; }
h1 { margin: 2px 0 10px; font-size: 20px; }
h2 { margin: 0 0 8px; font-size: 18px; }
h3 { margin: 0 0 8px; font-size: 15px; }
p { margin: 0 0 10px; }
.tabs { display: flex; gap: 4px; grid-column: 1 / -1; }
.tab {
  border: 0;
  border-bottom: 3px solid transparent;
  padding: 8px 14px;
  background: transparent;
  color: var(--cp-text-muted);
  cursor: pointer;
}
.tab[aria-selected="true"] { border-color: var(--cp-accent); color: var(--cp-text); font-weight: 650; }
.header-tools { display: flex; gap: 8px; align-items: center; padding-bottom: 12px; }
select, input {
  min-height: 34px;
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 6px 10px;
  background: var(--cp-surface);
  color: var(--cp-text);
}
main { max-width: 1800px; margin: 0 auto; padding: 22px 28px 56px; }
[role="tabpanel"][hidden] { display: none; }
.stack { display: grid; gap: 16px; }
.card {
  background: var(--cp-surface);
  border: 1px solid var(--cp-border);
  border-radius: 16px;
  padding: 18px 20px;
}
.card.compact { padding: 14px 16px; }
.eyebrow {
  color: var(--cp-text-muted);
  font: 600 11px/1.3 Consolas, "Courier New", Courier, monospace;
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.lede { max-width: 82ch; font-size: 16px; color: var(--cp-text-soft); }
.muted { color: var(--cp-text-muted); }
.grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.problem-facts { margin: 12px 0 0; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }
.problem-facts > div { border-top: 1px solid var(--cp-border); padding-top: 10px; }
ul { margin: 6px 0 0; padding-left: 20px; }
li + li { margin-top: 6px; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--cp-border);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
}
.badge.champion { border-color: var(--cp-accent); color: var(--cp-accent); }
.badge.pass, .new_best { color: var(--cp-success); border-color: var(--cp-success); }
.badge.fail, .reject, .failed { color: var(--cp-danger); border-color: var(--cp-danger); }
.badge.pending { color: var(--cp-warning); border-color: var(--cp-warning); }
.run-status {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px 20px;
  border: 1px solid var(--cp-warning);
  border-radius: 12px;
  padding: 12px 16px;
  background: color-mix(in srgb, var(--cp-warning) 10%, var(--cp-surface));
}
.run-status span { color: var(--cp-text-muted); }
.metric-row { display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 10px; margin-top: 12px; }
.metric {
  background: var(--cp-surface-soft);
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 10px 12px;
}
.metric strong { display: block; font: 700 20px/1.25 Consolas, "Courier New", Courier, monospace; }
.metric span { color: var(--cp-text-muted); font-size: 12px; }
.journey { display: grid; grid-template-columns: repeat(auto-fit,minmax(160px,1fr)); gap: 8px; margin-top: 12px; }
.milestone {
  text-align: left;
  background: var(--cp-surface-soft);
  color: var(--cp-text);
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 10px;
  cursor: pointer;
}
.milestone:hover { border-color: var(--cp-accent); }
details { border-top: 1px solid var(--cp-border); padding-top: 10px; margin-top: 12px; }
summary { cursor: pointer; color: var(--cp-link); }
pre {
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  background: var(--cp-surface-soft);
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 12px;
  font-size: 12px;
}
.toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; margin-bottom: 12px; }
.toolbar label { display: grid; gap: 4px; color: var(--cp-text-muted); font-size: 12px; }
.toolbar input[type="checkbox"] { min-height: 0; }
.topology-workspace {
  position: relative;
  min-width: 0;
  background: var(--cp-bg);
}
.topology-workspace.is-maximized {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  padding: 12px;
}
.topology-summary {
  margin-right: auto;
  align-self: center;
  color: var(--cp-text-muted);
  font: 12px/1.35 Consolas, "Courier New", Courier, monospace;
}
.topology-canvas-tools { display: flex; gap: 6px; margin-left: auto; align-items: center; }
.topology-canvas-tools .button { min-width: 34px; }
.topology-layout { position: relative; min-width: 0; min-height: 680px; overflow: hidden; }
.topology-workspace.is-maximized .topology-layout { min-height: 0; height: 100%; }
.graph-shell {
  position: absolute;
  inset: 0;
  overflow: hidden;
  min-height: 680px;
  padding: 0;
  cursor: grab;
  touch-action: none;
  user-select: none;
}
.graph-shell.is-panning { cursor: grabbing; }
.graph-stage {
  position: absolute;
  top: 0;
  left: 0;
  display: grid;
  min-width: 720px;
  min-height: 420px;
  transform-origin: 0 0;
  background: var(--cp-surface-soft);
  will-change: transform;
}
.track-lane {
  z-index: 0;
  align-self: stretch;
  border-bottom: 1px solid var(--cp-border);
  background: color-mix(in srgb, var(--cp-surface-soft) 92%, var(--cp-accent) 8%);
}
.track-lane.is-alt { background: var(--cp-surface-soft); }
.track-label {
  z-index: 3;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 12px 14px;
  border-right: 1px solid var(--cp-border-strong);
  border-bottom: 1px solid var(--cp-border);
  background: var(--cp-panel-strong);
  color: var(--cp-text-muted);
  font-weight: 650;
}
.track-label small { display: block; margin-top: 3px; color: var(--cp-accent); font-weight: 500; line-height: 1.25; }
.track-label .track-count { color: var(--cp-text-muted); }
.track-label.is-empty { border-left: 3px solid var(--cp-warning); }
.empty-lane {
  z-index: 2;
  align-self: center;
  margin-left: 18px;
  color: var(--cp-text-muted);
  font: 12px/1.4 Consolas, "Courier New", Courier, monospace;
}
.edge-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.edge-layer line { stroke: var(--cp-border-strong); stroke-width: 2; }
.graph-node {
  z-index: 4;
  align-self: center;
  justify-self: center;
  width: 190px;
  min-height: 76px;
  text-align: left;
  background: var(--cp-surface);
  color: var(--cp-text);
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 9px 10px;
  cursor: pointer;
}
.graph-node[aria-pressed="true"] { border: 2px solid var(--cp-accent); background: var(--cp-accent-soft); }
.graph-node.new_best { border-left: 5px solid var(--cp-success); }
.graph-node.keep_for_synthesis { border-left: 5px solid var(--cp-accent); }
.graph-node.reject, .graph-node.failed { border-left: 5px solid var(--cp-danger); }
.graph-node.needs_human_review { border-left: 5px solid var(--cp-warning); }
.graph-node.failed { border-style: dashed; }
.graph-node.is-dimmed { opacity: .28; }
.node-title { display: flex; justify-content: space-between; gap: 6px; font-weight: 650; }
.node-meta { margin-top: 8px; color: var(--cp-text-muted); font: 12px Consolas, "Courier New", Courier, monospace; }
.graph-minimap {
  position: absolute;
  right: 14px;
  bottom: 14px;
  z-index: 10;
  width: 190px;
  height: 122px;
  border: 1px solid var(--cp-border-strong);
  border-radius: .625rem;
  background: var(--cp-panel-strong);
  box-shadow: var(--cp-shadow);
  cursor: crosshair;
}
.graph-minimap .lane { fill: var(--cp-surface-soft); stroke: var(--cp-border); }
.graph-minimap .node { fill: var(--cp-accent); }
.graph-minimap .viewport { fill: color-mix(in srgb, var(--cp-accent) 12%, transparent); stroke: var(--cp-accent); stroke-width: 3; }
.graph-scale {
  position: absolute;
  left: 14px;
  bottom: 14px;
  z-index: 10;
  padding: 4px 7px;
  border: 1px solid var(--cp-border);
  border-radius: 999px;
  background: var(--cp-panel-strong);
  color: var(--cp-text-muted);
  font: 11px Consolas, "Courier New", Courier, monospace;
}
.inspector-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  width: min(440px, calc(100% - 32px));
  min-height: 0;
  overflow: auto;
  border-radius: 0;
  border-block: 0;
  border-right: 0;
  transform: translateX(102%);
  transition: transform 160ms ease;
  box-shadow: var(--cp-shadow);
}
.inspector-drawer.is-open { transform: translateX(0); }
.inspector-head {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  padding: 8px;
  margin: -18px -18px 12px;
  border-bottom: 1px solid var(--cp-border);
  background: var(--cp-panel-strong);
}
.inspector .artifact { margin-top: 12px; }
.feedback {
  border-left: 3px solid var(--cp-accent);
  background: var(--cp-accent-soft);
  padding: 10px 12px;
  margin-top: 12px;
}
.artifact {
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  overflow: hidden;
  background: var(--cp-surface-soft);
}
.artifact-head, .artifact-tools {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  border-bottom: 1px solid var(--cp-border);
}
.artifact-body { padding: 10px; overflow: auto; }
.artifact img { display: block; max-width: 100%; max-height: 460px; margin: auto; }
.artifact iframe { display: block; width: 100%; height: 420px; border: 1px solid var(--cp-border); background: var(--cp-surface); }
figcaption { padding: 8px 10px; border-top: 1px solid var(--cp-border); color: var(--cp-text-muted); font-size: 12px; }
.button {
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 5px 9px;
  background: var(--cp-surface);
  color: var(--cp-text);
  text-decoration: none;
  cursor: pointer;
}
.button:hover { border-color: var(--cp-accent); }
.diagnostic { border-left: 3px solid var(--cp-danger); padding: 9px 11px; background: var(--cp-surface-soft); }
.all-loops { margin-top: 12px; }
.all-loops-list { display: grid; gap: 6px; margin-top: 8px; }
.loop-list-button { width: 100%; display: flex; justify-content: space-between; text-align: left; }
.progression { display: grid; gap: 8px; margin-top: 12px; }
.progress-row { display: grid; grid-template-columns: 110px 1fr 100px; gap: 10px; align-items: center; }
.progress-track { height: 12px; border: 1px solid var(--cp-border); background: var(--cp-surface-soft); }
.progress-fill { height: 100%; background: var(--cp-accent); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 9px; border-bottom: 1px solid var(--cp-border); text-align: left; vertical-align: top; }
th { color: var(--cp-text-muted); font-weight: 650; }
.table-wrap { overflow: auto; }
.compare-artifacts { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }
.compare-summary { margin-top: 12px; }
.tree details { margin: 2px 0 2px 14px; padding: 0; border: 0; }
.tree summary { color: var(--cp-text); font-family: Consolas, "Courier New", Courier, monospace; }
.tree-value { color: var(--cp-text-muted); font-family: Consolas, "Courier New", Courier, monospace; }
dialog {
  width: min(1100px, calc(100vw - 32px));
  max-height: calc(100vh - 32px);
  padding: 0;
  border: 1px solid var(--cp-border-strong);
  border-radius: 16px;
  background: var(--cp-surface);
  color: var(--cp-text);
  box-shadow: var(--cp-shadow);
}
dialog::backdrop { background: var(--cp-overlay); }
.dialog-head { position: sticky; top: 0; z-index: 2; display: flex; justify-content: space-between; padding: 12px; background: var(--cp-panel-strong); border-bottom: 1px solid var(--cp-border); }
.dialog-body { padding: 14px; }
.review-form { display: grid; gap: 14px; }
.review-form label { display: grid; gap: 5px; color: var(--cp-text-muted); font-size: 12px; }
.review-form textarea {
  min-height: 84px;
  resize: vertical;
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
  padding: 8px 10px;
  background: var(--cp-surface);
  color: var(--cp-text);
  font: inherit;
}
.criterion-review {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) 120px 140px minmax(220px, 2fr);
  gap: 8px;
  align-items: end;
  padding: 10px;
  border: 1px solid var(--cp-border);
  border-radius: 0.625rem;
}
.binding { word-break: break-all; font: 11px/1.5 Consolas, "Courier New", Courier, monospace; color: var(--cp-text-muted); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
@media (max-width: 820px) {
  .app-header { padding-inline: 16px; }
  main { padding-inline: 14px; }
  .grid-2, .grid-3, .problem-facts, .compare-artifacts, .criterion-review { grid-template-columns: 1fr; }
  .topology-layout { min-height: 520px; }
  .graph-shell { min-height: 520px; }
  .graph-minimap { width: 136px; height: 92px; }
  .topology-summary { width: 100%; order: -1; }
  .topology-canvas-tools { margin-left: 0; overflow-x: auto; }
  .inspector-drawer { width: 100%; }
  .all-loops > summary { font-size: 0; }
  .all-loops > summary::after { content: "All Loops"; font-size: 14px; }
}
@media print {
  .app-header, .toolbar, dialog { display: none !important; }
  main { max-width: none; padding: 0; }
  .card { break-inside: avoid; }
}
@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
}
</style>
</head>
<body>
<header class="app-header">
  <div>
    <div class="repo-path mono">Experiment / <span id="experiment-id"></span> / Viewer</div>
    <h1>__TITLE__</h1>
  </div>
  <div class="header-tools">
    __HUMAN_BUTTON__
    <label class="sr-only" for="theme-select">Theme</label>
    <select id="theme-select" aria-label="Theme">
      <option value="system">System</option>
      <option value="dark">Dark</option>
      <option value="light">Light</option>
    </select>
  </div>
  <nav class="tabs" role="tablist" aria-label="Experiment views">__TABS__</nav>
</header>
<main>__PANELS__</main>
<dialog id="artifact-dialog" aria-labelledby="dialog-title">
  <div class="dialog-head"><strong id="dialog-title">Artifact</strong><button class="button" id="dialog-close">Close</button></div>
  <div class="dialog-body" id="dialog-body"></div>
</dialog>
__HUMAN_DIALOG__
<script type="application/json" id="viewer-data">__VIEW_MODEL__</script>
<script type="application/json" id="interaction-contract">__INTERACTION_CONTRACT__</script>
<script>
(() => {
  "use strict";
  const VM = JSON.parse(document.getElementById("viewer-data").textContent || "{}");
  const PANEL_IDS = __PANEL_IDS__;
  const byId = id => document.getElementById(id);
  const esc = value => String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const list = value => Array.isArray(value) ? value : [];
  const object = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const loopById = id => VM.loops.find(loop => loop.id === id);
  const artifactById = id => VM.loops.flatMap(loop => loop.artifacts || []).find(artifact => artifact.id === id);
  const criterionById = id => VM.criteria.find(criterion => criterion.id === id) || {};
  const primaryId = VM.primary_criterion.id || "";
  const formatValue = (value, criterion = {}) => value == null ? "—" : `${Number.isFinite(value) ? Number(value).toLocaleString(undefined, {maximumFractionDigits: 6}) : value}${criterion.unit ? ` ${criterion.unit}` : ""}`;
  const hashState = () => Object.fromEntries(new URLSearchParams(location.hash.replace(/^#/, "")));
  const updateHash = changes => {
    const state = {...hashState(), ...changes};
    Object.keys(state).forEach(key => (state[key] == null || state[key] === "") && delete state[key]);
    history.replaceState(null, "", `#${new URLSearchParams(state)}`);
  };
  const button = (label, attrs = "") => `<button class="button" ${attrs}>${esc(label)}</button>`;

  function artifactMarkup(artifact, expanded = false) {
    if (!artifact) return '<div class="diagnostic">Artifact pending or not yet merged.</div>';
    const presentation = object(artifact.presentation);
    const preview = object(artifact.preview);
    let body = '<div class="diagnostic">No inline preview is available.</div>';
    if (preview.kind === "image") {
      body = `<img src="${esc(preview.data_uri)}" alt="${esc(presentation.alt_text || artifact.label)}">`;
    } else if (preview.kind === "interactive_html") {
      body = `<iframe src="${esc(preview.data_uri)}" sandbox="${esc(preview.sandbox || "allow-scripts")}" title="${esc(artifact.label)}"></iframe>`;
    } else if (preview.kind === "text") {
      body = `<pre>${esc(preview.value)}</pre>`;
    } else if (preview.kind === "json") {
      body = `<div class="tree">${renderTree(preview.value, "value", "")}</div>`;
    } else if (preview.kind === "table") {
      body = `<div class="table-wrap"><table><thead><tr>${list(preview.headers).map(cell => `<th>${esc(cell)}</th>`).join("")}</tr></thead><tbody>${list(preview.rows).map(row => `<tr>${list(row).map(cell => `<td>${esc(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table>${preview.truncated ? '<p class="muted">Preview limited to 100 rows.</p>' : ""}</div>`;
    }
    const diagnostics = list(artifact.diagnostics).map(item => `<div class="diagnostic">${esc(item)}</div>`).join("");
    const tools = [
      !expanded && preview.kind ? `<button class="button expand-artifact" data-artifact="${esc(artifact.id)}">Expand</button>` : "",
      artifact.safe_href ? `<a class="button" href="${esc(artifact.safe_href)}">Original file</a>` : ""
    ].join("");
    return `<figure class="artifact">
      <div class="artifact-head"><strong>${esc(artifact.label || artifact.id)}</strong><span class="badge">${esc(presentation.mode || artifact.kind)}</span></div>
      ${tools ? `<div class="artifact-tools">${tools}</div>` : ""}
      <div class="artifact-body">${body}${diagnostics}</div>
      <figcaption>${esc(presentation.caption || "Artifact evidence.")}</figcaption>
    </figure>`;
  }

  function metricCards(loop) {
    return `<div class="metric-row">${VM.criteria.map(criterion => {
      const value = object(loop.score_values)[criterion.id];
      const gate = object(criterion.gate);
      let state = "";
      if (gate.operator) state = typeof value === "number" ? (gatePass(value, gate) ? "pass" : "fail") : "pending";
      return `<div class="metric"><span>${esc(criterion.label || criterion.id)}</span><strong>${esc(formatValue(value, criterion))}</strong>${state ? `<span class="badge ${state}">${state} gate</span>` : ""}</div>`;
    }).join("")}</div>`;
  }

  function gatePass(value, gate) {
    if (typeof value !== "number" || typeof gate.threshold !== "number") return false;
    return ({eq: value === gate.threshold, ne: value !== gate.threshold, gt: value > gate.threshold, gte: value >= gate.threshold, lt: value < gate.threshold, lte: value <= gate.threshold})[gate.operator] || false;
  }

  function renderOverview() {
    const problem = object(VM.problem);
    const inProgress = Boolean(object(VM.status).is_in_progress);
    const iterationCount = Number(object(VM.status).iteration_count || 0);
    const championLoop = loopById(VM.champion.iteration_id) || VM.loops.at(-1) || {};
    const milestones = list(VM.story.milestones);
    byId("panel-overview").innerHTML = `<div class="stack">
      ${inProgress ? `<section class="run-status" role="status"><strong>Experiment in progress - ${iterationCount} ${iterationCount === 1 ? "iteration" : "iterations"} so far</strong><span>This interim Viewer is not Evidence Gate completion. Only final outputs are gate-verified.</span></section>` : ""}
      ${list(VM.diagnostics).map(item => `<div class="diagnostic" role="alert">${esc(item)}</div>`).join("")}
      <section class="card">
        <div class="eyebrow">01 / Problem</div>
        <h2>${esc(problem.statement || "Problem framing was not recorded.")}</h2>
        <p class="lede">${esc(problem.optimization_target || "")}</p>
        <div class="problem-facts">
          <div><h3>Constraints</h3><ul>${list(problem.constraints).map(item => `<li>${esc(item)}</li>`).join("")}</ul></div>
          <div><h3>Success criteria</h3><ul>${list(problem.success_criteria).map(item => `<li>${esc(item)}</li>`).join("")}</ul></div>
        </div>
        <details><summary>Original Experiment Prompt</summary><pre>${esc(problem.original_prompt || "")}</pre></details>
      </section>
      <section class="card">
        <div class="eyebrow">02 / ${inProgress ? "Current state" : "Champion"}</div>
        <div class="grid-2">
          <div><h2>${esc(championLoop.label || championLoop.id || (inProgress ? "No Loops merged yet" : "Champion"))}</h2><p class="lede">${esc(VM.champion.summary || championLoop.outcome || (inProgress ? "Current evidence will appear as Loops are merged." : ""))}</p>${metricCards(championLoop)}</div>
          <div>${artifactMarkup(VM.featured_artifact || championLoop.primary_artifact)}</div>
        </div>
      </section>
      <section class="card">
        <div class="eyebrow">03 / Experiment journey</div>
        <h2>How the Experiment progressed</h2>
        <div class="journey">${milestones.length ? milestones.map((milestone, index) => `<button class="milestone" data-open-loop="${esc(milestone.iteration_id)}"><span class="eyebrow">${String(index + 1).padStart(2, "0")} / ${esc(milestone.iteration_id)}</span><strong>${esc(milestone.caption)}</strong></button>`).join("") : '<p class="muted">No authored milestones have been merged yet.</p>'}</div>
      </section>
      <section class="card">
        <div class="eyebrow">04 / ${inProgress ? "Interim evidence" : "Why it won"}</div>
        <div class="grid-2">
          <div><h2>${inProgress ? "Current observations" : "Evidence-backed reasons"}</h2><ul>${list(VM.champion.reasons).map(reason => `<li>${esc(reason.text)} <span class="muted mono">${list(reason.evidence_refs).map(ref => esc(ref)).join(" · ")}</span></li>`).join("") || `<li>${inProgress ? "Champion reasons are pending finalization." : "No winning reasons were recorded."}</li>`}</ul></div>
          <div><h2>${inProgress ? "Pending final evidence" : "Caveats and dissent"}</h2><ul>${list(VM.champion.caveats).map(reason => `<li>${esc(reason.text)} <span class="muted mono">${list(reason.evidence_refs).map(ref => esc(ref)).join(" · ")}</span></li>`).join("") || `<li>${inProgress ? "Final caveats, Navigation Evidence, and Evidence Gate results are not available yet." : "No caveats were recorded."}</li>`}</ul></div>
        </div>
        <details><summary>Experiment evidence and provenance</summary>${provenanceMarkup()}${manifestExplorer()}</details>
      </section>
    </div>`;
  }

  function provenanceMarkup() {
    const generation = object(VM.generation);
    const fields = [
      ["Skill commit", generation.skill_commit],
      ["CLI", generation.copilot_cli_version],
      ["Orchestrator", generation.orchestrator_model],
      ["Prompt integrity", generation.prompt_sha256],
      ["Skill integrity", generation.skill_tree_sha256]
    ];
    return `<div class="grid-3">${fields.map(([label, value]) => `<div class="metric"><span>${esc(label)}</span><strong class="mono" style="font-size:13px">${esc(value || "not recorded")}</strong></div>`).join("")}</div>`;
  }

  function manifestExplorer() {
    return `<div class="card compact" style="margin-top:12px"><h3>Structured Manifest</h3><label class="sr-only" for="manifest-search">Search Manifest</label><input id="manifest-search" placeholder="Search keys or values"><div id="manifest-tree" class="tree">${renderTree(VM.raw_manifest, "manifest", "")}</div></div>`;
  }

  const GRAPH = {header: 220, column: 230, lane: 148, nodeWidth: 190, nodeHeight: 82};
  let topologyController = null;

  function renderTopology() {
    const tracks = VM.tracks;
    const decisions = [...new Set(VM.loops.map(loop => loop.decision).filter(Boolean))];
    const trackLoopCounts = tracks.map(track => Number(track.loop_count || 0));
    const minTrackLoops = Math.min(...trackLoopCounts, 0);
    const maxTrackLoops = Math.max(...trackLoopCounts, 0);
    const loopDimension = minTrackLoops === maxTrackLoops
      ? String(minTrackLoops)
      : `${minTrackLoops}–${maxTrackLoops}`;
    byId("panel-topology").innerHTML = `${VM.loops.length ? "" : '<div class="card diagnostic">No Loops have been merged yet. Track lanes may still be incomplete.</div>'}<div class="topology-workspace" id="topology-workspace">
      <div class="toolbar card compact">
        <label>Track<select id="track-filter"><option value="">All Tracks</option>${tracks.map(track => `<option value="${esc(track.id)}">${esc(track.label || track.id)}</option>`).join("")}</select></label>
        <label>Decision<select id="decision-filter"><option value="">All decisions</option>${decisions.map(value => `<option value="${esc(value)}">${esc(value)}</option>`).join("")}</select></label>
        <label>Search<input id="loop-search" type="search" placeholder="Loop, hypothesis, outcome"></label>
        <label><span>Champion</span><span><input id="champion-filter" type="checkbox"> only</span></label>
        <div class="topology-summary">${tracks.length} Tracks x ${loopDimension} Loops per Track | ${VM.loops.length} iterations total</div>
        <div class="topology-canvas-tools" aria-label="Topology canvas controls">
          <button class="button" id="topology-zoom-out" aria-label="Zoom out">−</button>
          <button class="button" id="topology-zoom-in" aria-label="Zoom in">+</button>
          <button class="button" id="topology-fit">Fit</button>
          <button class="button" id="topology-reset">100%</button>
          <button class="button" id="topology-inspector-toggle" aria-pressed="false">Inspector</button>
          <button class="button" id="topology-maximize" aria-pressed="false">Maximize</button>
        </div>
      </div>
      <div class="topology-layout">
        <section class="card graph-shell" id="graph-viewport" aria-label="Experiment topology graph. Drag the background to pan and use the mouse wheel to zoom.">
          <div class="graph-stage" id="graph-stage"></div>
          <svg class="graph-minimap" id="graph-minimap" role="button" tabindex="0" aria-label="Topology overview navigator"></svg>
          <output class="graph-scale" id="graph-scale" aria-live="polite">100%</output>
        </section>
        <aside class="card inspector inspector-drawer" id="loop-inspector" aria-live="polite" tabindex="-1"></aside>
      </div>
    </div>
    <details class="card all-loops"><summary>All Loops — complete accessible list</summary><div class="all-loops-list">${VM.loops.map(loop => `<button class="button loop-list-button" data-open-loop="${esc(loop.id)}"><span>${esc(loop.label || loop.id)}</span><span class="mono">${esc(formatValue(loop.primary_value, VM.primary_criterion))}</span></button>`).join("")}</div></details>`;
    const dimensions = renderGraph();
    topologyController = createCanvasController(byId("graph-viewport"), byId("graph-stage"), dimensions);
    wireTopologyControls();
    const state = hashState();
    const selected = loopById(state.loop) || loopById(VM.champion.iteration_id) || VM.loops[0];
    if (state.x != null && state.y != null && state.scale != null) {
      topologyController.set(
        {x: Number(state.x), y: Number(state.y), scale: Number(state.scale)},
        {persist: false, unclamped: true}
      );
    } else {
      topologyController.fit({persist: false});
    }
    if (selected) {
      selectLoop(selected.id, false, {
        focus: Boolean(state.loop),
        openInspector: Boolean(state.loop),
      });
    }
    ["track-filter", "decision-filter", "loop-search", "champion-filter"].forEach(id => byId(id).addEventListener("input", applyGraphFilters));
  }

  function graphPosition(loop) {
    const trackIndex = Math.max(0, VM.tracks.findIndex(track => track.id === loop.track_id));
    const depth = loop.topology_column ?? loop.topology_depth ?? loop.index;
    return {
      x: GRAPH.header + depth * GRAPH.column + GRAPH.column / 2,
      y: trackIndex * GRAPH.lane + GRAPH.lane / 2,
    };
  }

  function renderGraph() {
    const stage = byId("graph-stage");
    const maxDepth = Math.max(0, ...VM.loops.map(loop => loop.topology_column ?? loop.topology_depth ?? loop.index));
    const width = Math.max(920, GRAPH.header + (maxDepth + 1) * GRAPH.column);
    const height = Math.max(420, VM.tracks.length * GRAPH.lane);
    stage.style.width = `${width}px`;
    stage.style.height = `${height}px`;
    stage.style.gridTemplateColumns = `${GRAPH.header}px repeat(${maxDepth + 1}, ${GRAPH.column}px)`;
    stage.style.gridTemplateRows = `repeat(${Math.max(1, VM.tracks.length)}, ${GRAPH.lane}px)`;
    const lanes = VM.tracks.map((track, index) => {
      const startsAfter = list(track.starts_after).length
        ? `Starts after ${track.starts_after.map(value => esc(value)).join(" + ")} complete`
        : "Starts independently";
      const count = Number(track.loop_count || 0);
      return `<div class="track-lane${index % 2 ? " is-alt" : ""}" style="grid-row:${index + 1};grid-column:1 / -1" aria-hidden="true"></div>
        <div class="track-label${track.is_empty ? " is-empty" : ""}" style="grid-row:${index + 1};grid-column:1">
          <strong>${esc(track.label || track.id)}</strong>
          <small class="track-count">${count} ${count === 1 ? "Loop" : "Loops"}</small>
          <small>${startsAfter}</small>
        </div>
        ${track.is_empty ? `<div class="empty-lane" style="grid-row:${index + 1};grid-column:2 / -1">No Loops recorded · Track incomplete</div>` : ""}`;
    }).join("");
    const edges = VM.loops.flatMap(loop => list(loop.parent_ids).map(parentId => {
      const parent = loopById(parentId);
      if (!parent) return "";
      const from = graphPosition(parent), to = graphPosition(loop);
      return `<line x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" marker-end="url(#topology-arrow)"></line>`;
    })).join("");
    const nodes = VM.loops.map(loop => {
      const trackIndex = Math.max(0, VM.tracks.findIndex(track => track.id === loop.track_id));
      const depth = loop.topology_column ?? loop.topology_depth ?? loop.index;
      return `<button class="graph-node ${esc(loop.decision)}" data-loop="${esc(loop.id)}" style="grid-row:${trackIndex + 1};grid-column:${depth + 2}" aria-pressed="false" tabindex="-1">
        <span class="node-title"><span>${esc(loop.label || loop.id)}</span>${loop.is_champion ? '<span class="badge champion">Champion</span>' : ""}</span>
        <span class="node-meta"><span class="badge ${esc(loop.decision || "pending")}">${esc(loop.decision || "pending")}</span> · ${esc(formatValue(loop.primary_value, VM.primary_criterion))}</span>
      </button>`;
    }).join("");
    stage.innerHTML = `${lanes}<svg class="edge-layer" viewBox="0 0 ${width} ${height}" aria-hidden="true"><defs><marker id="topology-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--cp-border-strong)"></path></marker></defs>${edges}</svg>${nodes}`;
    stage.querySelectorAll(".graph-node").forEach(node => {
      node.addEventListener("click", () => selectLoop(node.dataset.loop, true));
      node.addEventListener("keydown", graphKeydown);
    });
    renderMinimap(width, height);
    return {width, height};
  }

  function renderMinimap(width, height) {
    const minimap = byId("graph-minimap");
    const lanes = VM.tracks.map((track, index) =>
      `<rect class="lane" x="0" y="${index * GRAPH.lane}" width="${width}" height="${GRAPH.lane}"></rect>`
    ).join("");
    const nodes = VM.loops.map(loop => {
      const pos = graphPosition(loop);
      return `<rect class="node" x="${pos.x - GRAPH.nodeWidth / 2}" y="${pos.y - 16}" width="${GRAPH.nodeWidth}" height="32" rx="5"></rect>`;
    }).join("");
    minimap.setAttribute("viewBox", `0 0 ${width} ${height}`);
    minimap.innerHTML = `${lanes}${nodes}<rect class="viewport" id="minimap-viewport" rx="8"></rect>`;
  }

  function createCanvasController(viewport, stage, dimensions) {
    const bounds = {minScale: .08, maxScale: 2.5, padding: 24};
    let state = {x: 0, y: 0, scale: 1};

    function clampAxis(value, viewSize, contentSize) {
      if (contentSize <= viewSize) return (viewSize - contentSize) / 2;
      return Math.min(bounds.padding, Math.max(viewSize - contentSize - bounds.padding, value));
    }

    function updateMinimap() {
      const lens = byId("minimap-viewport");
      if (!lens) return;
      lens.setAttribute("x", String(Math.max(0, -state.x / state.scale)));
      lens.setAttribute("y", String(Math.max(0, -state.y / state.scale)));
      lens.setAttribute("width", String(Math.min(dimensions.width, viewport.clientWidth / state.scale)));
      lens.setAttribute("height", String(Math.min(dimensions.height, viewport.clientHeight / state.scale)));
      byId("graph-scale").textContent = `${Math.round(state.scale * 100)}%`;
    }

    function set(partial, options = {}) {
      const requestedScale = Number(partial.scale ?? state.scale);
      const scale = Math.min(
        bounds.maxScale,
        Math.max(bounds.minScale, Number.isFinite(requestedScale) ? requestedScale : state.scale)
      );
      const rawX = Number(partial.x ?? state.x);
      const rawY = Number(partial.y ?? state.y);
      const nextX = Number.isFinite(rawX) ? rawX : state.x;
      const nextY = Number.isFinite(rawY) ? rawY : state.y;
      const next = {
        scale,
        x: options.unclamped
          ? nextX
          : clampAxis(nextX, viewport.clientWidth, dimensions.width * scale),
        y: options.unclamped
          ? nextY
          : clampAxis(nextY, viewport.clientHeight, dimensions.height * scale),
      };
      const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
      stage.style.transition = options.animate && !reduceMotion ? "transform 180ms ease" : "none";
      stage.style.transform = `translate(${next.x}px, ${next.y}px) scale(${next.scale})`;
      state = next;
      updateMinimap();
      if (options.persist !== false) {
        updateHash({
          x: Math.round(state.x),
          y: Math.round(state.y),
          scale: Number(state.scale.toFixed(3)),
        });
      }
      if (stage.style.transition !== "none") {
        setTimeout(() => { stage.style.transition = "none"; }, 200);
      }
      return get();
    }

    function get() {
      return {...state};
    }

    function fit(options = {}) {
      const scale = Math.min(
        1.2,
        Math.max(bounds.minScale, Math.min(
          (viewport.clientWidth - bounds.padding * 2) / dimensions.width,
          (viewport.clientHeight - bounds.padding * 2) / dimensions.height,
        ))
      );
      return set({
        scale,
        x: (viewport.clientWidth - dimensions.width * scale) / 2,
        y: (viewport.clientHeight - dimensions.height * scale) / 2,
      }, {...options, animate: options.animate !== false});
    }

    function reset(options = {}) {
      return set({x: bounds.padding, y: bounds.padding, scale: 1}, {...options, animate: true});
    }

    function focus(elementOrBounds, options = {}) {
      const target = elementOrBounds instanceof Element
        ? {x: elementOrBounds.offsetLeft, y: elementOrBounds.offsetTop, width: elementOrBounds.offsetWidth, height: elementOrBounds.offsetHeight}
        : elementOrBounds;
      if (!target) return get();
      const scale = Math.max(state.scale, Math.min(1, bounds.maxScale));
      return set({
        scale,
        x: viewport.clientWidth / 2 - (target.x + target.width / 2) * scale,
        y: viewport.clientHeight / 2 - (target.y + target.height / 2) * scale,
      }, {...options, animate: options.animate !== false, unclamped: true});
    }

    return {set, focus, get, fit, reset};
  }

  function wireTopologyControls() {
    const viewport = byId("graph-viewport");
    const workspace = byId("topology-workspace");
    const drawer = byId("loop-inspector");
    const minimap = byId("graph-minimap");
    let pan = null;

    function zoom(multiplier, clientX = viewport.getBoundingClientRect().left + viewport.clientWidth / 2, clientY = viewport.getBoundingClientRect().top + viewport.clientHeight / 2) {
      const rect = viewport.getBoundingClientRect();
      const current = topologyController.get();
      const nextScale = Math.min(2.5, Math.max(.08, current.scale * multiplier));
      const pointX = (clientX - rect.left - current.x) / current.scale;
      const pointY = (clientY - rect.top - current.y) / current.scale;
      topologyController.set({
        scale: nextScale,
        x: clientX - rect.left - pointX * nextScale,
        y: clientY - rect.top - pointY * nextScale,
      });
    }

    function setDrawer(open) {
      drawer.classList.toggle("is-open", open);
      byId("topology-inspector-toggle").setAttribute("aria-pressed", String(open));
    }

    byId("topology-zoom-in").addEventListener("click", () => zoom(1.2));
    byId("topology-zoom-out").addEventListener("click", () => zoom(1 / 1.2));
    byId("topology-fit").addEventListener("click", () => topologyController.fit());
    byId("topology-reset").addEventListener("click", () => topologyController.reset());
    byId("topology-inspector-toggle").addEventListener("click", () => setDrawer(!drawer.classList.contains("is-open")));
    byId("topology-maximize").addEventListener("click", () => {
      const maximized = workspace.classList.toggle("is-maximized");
      document.body.style.overflow = maximized ? "hidden" : "";
      byId("topology-maximize").setAttribute("aria-pressed", String(maximized));
      byId("topology-maximize").textContent = maximized ? "Restore" : "Maximize";
      requestAnimationFrame(() => topologyController.set(topologyController.get(), {persist: false}));
    });
    viewport.addEventListener("wheel", event => {
      event.preventDefault();
      zoom(Math.exp(-event.deltaY * .0015), event.clientX, event.clientY);
    }, {passive: false});
    viewport.addEventListener("pointerdown", event => {
      if (event.target.closest(".graph-node,.graph-minimap,button,a,input,select")) return;
      const current = topologyController.get();
      pan = {pointerId: event.pointerId, x: event.clientX, y: event.clientY, tx: current.x, ty: current.y};
      viewport.setPointerCapture(event.pointerId);
      viewport.classList.add("is-panning");
    });
    viewport.addEventListener("pointermove", event => {
      if (!pan || event.pointerId !== pan.pointerId) return;
      topologyController.set({x: pan.tx + event.clientX - pan.x, y: pan.ty + event.clientY - pan.y});
    });
    viewport.addEventListener("pointerup", event => {
      if (!pan || event.pointerId !== pan.pointerId) return;
      pan = null;
      viewport.classList.remove("is-panning");
      viewport.releasePointerCapture(event.pointerId);
    });

    function navigateMinimap(clientX, clientY) {
      const rect = minimap.getBoundingClientRect();
      const point = {
        x: (clientX - rect.left) / rect.width * minimap.viewBox.baseVal.width,
        y: (clientY - rect.top) / rect.height * minimap.viewBox.baseVal.height,
      };
      const state = topologyController.get();
      topologyController.set({
        x: viewport.clientWidth / 2 - point.x * state.scale,
        y: viewport.clientHeight / 2 - point.y * state.scale,
      });
    }
    minimap.addEventListener("pointerdown", event => {
      minimap.setPointerCapture(event.pointerId);
      navigateMinimap(event.clientX, event.clientY);
    });
    minimap.addEventListener("pointermove", event => {
      if (minimap.hasPointerCapture(event.pointerId)) navigateMinimap(event.clientX, event.clientY);
    });
    minimap.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        topologyController.fit();
      }
    });
    window.addEventListener("resize", () => topologyController.set(topologyController.get(), {persist: false}));
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && workspace.classList.contains("is-maximized")) byId("topology-maximize").click();
    });
    drawer._setOpen = setDrawer;
  }

  function selectLoop(loopId, writeHash = true, options = {}) {
    const loop = loopById(loopId);
    if (!loop) return;
    document.querySelectorAll(".graph-node").forEach(node => {
      const selected = node.dataset.loop === loopId;
      node.setAttribute("aria-pressed", String(selected));
      node.tabIndex = selected ? 0 : -1;
    });
    renderInspector(loop);
    const node = document.querySelector(`.graph-node[data-loop="${CSS.escape(loopId)}"]`);
    if (options.openInspector !== false && byId("loop-inspector")._setOpen) byId("loop-inspector")._setOpen(true);
    if (options.focus !== false && node && topologyController) topologyController.focus(node);
    if (writeHash) updateHash({view: "topology", loop: loopId});
  }

  function graphKeydown(event) {
    const current = loopById(event.currentTarget.dataset.loop);
    if (!current) return;
    const candidates = VM.loops.filter(loop => loop.id !== current.id);
    const currentPos = graphPosition(current);
    const directional = candidates.filter(loop => {
      const pos = graphPosition(loop);
      if (event.key === "ArrowUp") return pos.y < currentPos.y;
      if (event.key === "ArrowDown") return pos.y > currentPos.y;
      if (event.key === "ArrowLeft") return pos.x < currentPos.x;
      if (event.key === "ArrowRight") return pos.x > currentPos.x;
      return false;
    });
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectLoop(current.id, true);
      byId("loop-inspector").focus();
      return;
    }
    if (!directional.length) return;
    event.preventDefault();
    directional.sort((a, b) => {
      const ap = graphPosition(a), bp = graphPosition(b);
      return (Math.abs(ap.x-currentPos.x)+Math.abs(ap.y-currentPos.y)) - (Math.abs(bp.x-currentPos.x)+Math.abs(bp.y-currentPos.y));
    });
    selectLoop(directional[0].id, true);
    document.querySelector(`.graph-node[data-loop="${CSS.escape(directional[0].id)}"]`).focus();
  }

  function applyGraphFilters() {
    const track = byId("track-filter").value;
    const decision = byId("decision-filter").value;
    const query = byId("loop-search").value.toLowerCase();
    const championOnly = byId("champion-filter").checked;
    document.querySelectorAll(".graph-node").forEach(node => {
      const loop = loopById(node.dataset.loop);
      const haystack = `${loop.id} ${loop.hypothesis} ${loop.outcome}`.toLowerCase();
      const match = (!track || loop.track_id === track) && (!decision || loop.decision === decision) && (!query || haystack.includes(query)) && (!championOnly || loop.is_champion);
      node.classList.toggle("is-dimmed", !match);
    });
  }

  function renderInspector(loop) {
    const prompt = object(loop.prompt);
    const lesson = object(loop.lesson);
    const secondary = list(loop.artifacts).filter(artifact => !loop.primary_artifact || artifact.id !== loop.primary_artifact.id);
    byId("loop-inspector").innerHTML = `<div class="inspector-head"><button class="button" id="topology-inspector-close" aria-label="Close Loop inspector">Close</button></div>
      <div class="eyebrow">${esc(loop.track_label)} / ${esc(loop.id)}</div>
      <h2>${esc(loop.label || loop.id)} ${loop.is_champion ? '<span class="badge champion">Champion</span>' : ""}</h2>
      <p><span class="badge ${esc(loop.decision || "pending")}">${esc(loop.decision || "pending")}</span> <span class="badge">${esc(loop.model_id || "model pending")}</span></p>
      <h3>Hypothesis</h3><p>${esc(loop.hypothesis)}</p>
      <h3>Outcome</h3><p>${esc(loop.outcome)}</p>
      ${artifactMarkup(loop.primary_artifact)}
      ${metricCards(loop)}
      <div class="feedback"><div class="eyebrow">Judge feedback</div>${loop.judge_feedback_pending ? '<p><span class="badge pending">Awaiting panel</span> Judge feedback has not been merged yet.</p>' : `<p>${esc(prompt.judge_feedback)}</p>`}</div>
      <h3 style="margin-top:14px">Lesson</h3><p>${esc(lesson.action || "")}</p><p class="muted">${esc(lesson.evidence || "")}</p>
      ${secondary.length ? `<details><summary>Other Artifacts (${secondary.length})</summary><div class="stack">${secondary.map(artifact => artifactMarkup(artifact)).join("")}</div></details>` : ""}
      <details><summary>Prompt and feedback chain</summary>
        <h3>Track prompt</h3><pre>${esc(prompt.track_prompt || "")}</pre>
        <h3>Input feedback</h3><pre>${esc(prompt.input_feedback || "")}</pre>
        <h3>Judge feedback</h3><pre>${esc(prompt.judge_feedback || "")}</pre>
        <h3>Next prompt</h3><pre>${esc(prompt.next_prompt || "")}</pre>
      </details>
      <details><summary>Advanced Loop evidence</summary><pre>${esc(JSON.stringify({commands: loop.commands, quality_gates: loop.quality_gates, changed_files: loop.changed_files}, null, 2))}</pre></details>`;
    byId("topology-inspector-close").addEventListener("click", () => byId("loop-inspector")._setOpen(false));
  }

  function renderCompare() {
    const first = VM.loops[0] || {};
    const champion = loopById(VM.champion.iteration_id) || VM.loops.at(-1) || first;
    if (!VM.loops.length) {
      byId("panel-compare").innerHTML = '<section class="card diagnostic">No Loops are available to compare yet.</section>';
      return;
    }
    byId("panel-compare").innerHTML = `<div class="stack">
      <section class="card"><div class="eyebrow">Metric progression</div><h2>${esc(VM.primary_criterion.label || primaryId || "Primary criterion")}</h2><div id="progression"></div><div class="table-wrap" id="progression-table"></div></section>
      <section class="card">
        <div class="toolbar">
          <label>Loop A<select id="compare-a"></select></label>
          <label>Loop B<select id="compare-b"></select></label>
        </div>
        <div id="comparison"></div>
      </section>
    </div>`;
    const options = VM.loops.map(loop => `<option value="${esc(loop.id)}">${esc(loop.label || loop.id)}</option>`).join("");
    byId("compare-a").innerHTML = options;
    byId("compare-b").innerHTML = options;
    const state = hashState();
    byId("compare-a").value = loopById(state.a) ? state.a : first.id;
    byId("compare-b").value = loopById(state.b) ? state.b : champion.id;
    renderProgression();
    renderComparison();
    ["compare-a", "compare-b"].forEach(id => byId(id).addEventListener("change", () => {
      updateHash({view: "compare", a: byId("compare-a").value, b: byId("compare-b").value});
      renderComparison();
    }));
  }

  function renderProgression() {
    const values = VM.loops.map(loop => Number(loop.primary_value)).filter(Number.isFinite);
    const min = Math.min(...values), max = Math.max(...values), span = Math.max(1, max - min);
    byId("progression").innerHTML = `<div class="progression">${VM.loops.map(loop => {
      const value = Number(loop.primary_value);
      const width = Number.isFinite(value) ? 12 + ((value - min) / span) * 88 : 0;
      return `<div class="progress-row"><span class="mono">${esc(loop.id)}</span><div class="progress-track"><div class="progress-fill" style="width:${width}%"></div></div><strong class="mono">${esc(formatValue(loop.primary_value, VM.primary_criterion))}</strong></div>`;
    }).join("")}</div>`;
    byId("progression-table").innerHTML = `<table><caption class="sr-only">Metric progression for every Loop</caption><thead><tr><th>Loop</th>${VM.criteria.map(c => `<th>${esc(c.label || c.id)}</th>`).join("")}<th>Decision</th></tr></thead><tbody>${VM.loops.map(loop => `<tr><td>${esc(loop.id)}</td>${VM.criteria.map(c => `<td class="mono">${esc(formatValue(object(loop.score_values)[c.id], c))}</td>`).join("")}<td>${esc(loop.decision)}</td></tr>`).join("")}</tbody></table>`;
  }

  function comparableArtifact(loop) {
    const key = VM.story.primary_comparison_key;
    return (key ? list(loop.artifacts).find(artifact => object(artifact.presentation).comparison_key === key) : null) || loop.primary_artifact;
  }

  function renderComparison() {
    const a = loopById(byId("compare-a").value), b = loopById(byId("compare-b").value);
    if (!a || !b) return;
    const difference = typeof a.primary_value === "number" && typeof b.primary_value === "number" ? b.primary_value - a.primary_value : null;
    byId("comparison").innerHTML = `<div class="compare-artifacts"><div><div class="eyebrow">A / ${esc(a.id)}</div>${artifactMarkup(comparableArtifact(a))}</div><div><div class="eyebrow">B / ${esc(b.id)}</div>${artifactMarkup(comparableArtifact(b))}</div></div>
      <div class="grid-3 compare-summary">
        <div class="metric"><span>${esc(VM.primary_criterion.label || primaryId)}</span><strong>${difference == null ? "—" : esc(`${difference > 0 ? "+" : ""}${difference.toLocaleString(undefined, {maximumFractionDigits:6})}`)}</strong><span>B minus A · ${esc(VM.primary_criterion.direction || "")}</span></div>
        <div class="card compact"><h3>Loop A lesson</h3><p>${esc(object(a.lesson).action || "")}</p></div>
        <div class="card compact"><h3>Loop B lesson</h3><p>${esc(object(b.lesson).action || "")}</p></div>
      </div>`;
  }

  function renderSamples() {
    const panel = byId("panel-samples");
    if (!panel) return;
    const samples = list(VM.raw_manifest.samples);
    panel.innerHTML = `<div class="card"><h2>Sample evidence</h2><div class="table-wrap"><table><thead><tr><th>Sample</th><th>Result</th></tr></thead><tbody>${samples.map(sample => `<tr><td>${esc(sample.id || sample.label)}</td><td><pre>${esc(JSON.stringify(sample.results || sample, null, 2))}</pre></td></tr>`).join("")}</tbody></table></div></div>`;
  }

  function renderTree(value, key = "value", query = "") {
    const haystack = `${key} ${typeof value === "object" ? JSON.stringify(value) : value}`.toLowerCase();
    if (query && !haystack.includes(query.toLowerCase())) return "";
    if (value && typeof value === "object") {
      const entries = Array.isArray(value) ? value.map((item, index) => [index, item]) : Object.entries(value);
      return `<details open><summary>${esc(key)} <span class="muted">${Array.isArray(value) ? `[${entries.length}]` : `{${entries.length}}`}</span></summary>${entries.map(([childKey, child]) => renderTree(child, childKey, query)).join("")}</details>`;
    }
    return `<div class="tree-value"><strong>${esc(key)}:</strong> ${esc(JSON.stringify(value))}</div>`;
  }

  function activate(panelId, writeHash = true) {
    const selected = PANEL_IDS.includes(panelId) ? panelId : PANEL_IDS[0];
    PANEL_IDS.forEach(id => {
      const tab = byId(`tab-${id}`), panel = byId(`panel-${id}`);
      tab.setAttribute("aria-selected", String(id === selected));
      tab.tabIndex = id === selected ? 0 : -1;
      panel.hidden = id !== selected;
    });
    if (writeHash) updateHash({view: selected});
    if (selected === "topology" && !byId("graph-stage")) renderTopology();
    if (selected === "compare" && !byId("comparison")) renderCompare();
    if (selected === "samples" && byId("panel-samples") && !byId("panel-samples").children.length) renderSamples();
  }

  function applyTheme(value) {
    const resolved = value === "system" ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : value;
    document.documentElement.setAttribute("data-theme", resolved);
  }

  function openArtifact(id, invoker) {
    const artifact = artifactById(id);
    if (!artifact) return;
    const dialog = byId("artifact-dialog");
    dialog.dataset.invoker = id;
    dialog._invoker = invoker;
    byId("dialog-title").textContent = artifact.label || artifact.id;
    byId("dialog-body").innerHTML = artifactMarkup(artifact, true);
    dialog.showModal();
    byId("dialog-close").focus();
  }

  function humanReviewMarkup() {
    const loopOptions = VM.loops.map(loop => `<option value="${esc(loop.id)}">${esc(loop.label || loop.id)}</option>`).join("");
    const artifactOptions = VM.loops.flatMap(loop => list(loop.artifacts).map(artifact => `<option value="${esc(artifact.id)}">${esc(loop.id)} / ${esc(artifact.label || artifact.id)}</option>`)).join("");
    const criteria = list(VM.human_review_criteria).map((criterion, index) => `
      <div class="criterion-review" data-review-criterion="${esc(criterion.id)}">
        <div><strong>${esc(criterion.label || criterion.id)}</strong><div class="muted">${esc(criterion.unit || "rating")}</div></div>
        <label>Score<input id="human-score-${index}" type="number" step="any" inputmode="decimal"></label>
        <label>Rating<select id="human-rating-${index}"><option value="">Not rated</option><option value="weak">Weak</option><option value="acceptable">Acceptable</option><option value="strong">Strong</option></select></label>
        <label>Criterion notes<textarea id="human-criterion-notes-${index}"></textarea></label>
      </div>`).join("");
    return `<div class="review-form">
      <div><div class="eyebrow">Export-only review</div><h2>Judge this Experiment</h2><p class="muted">Your review is downloaded as a schema-bound JSON sidecar. It contains no reviewer identity and is not imported by this Viewer.</p></div>
      <div class="grid-2">
        <label>Overall verdict<select id="human-verdict"><option value="needs_improvement">Needs improvement</option><option value="approve">Approve</option><option value="reject">Reject</option></select></label>
        <label>Recommendation<select id="human-recommendation"><option value="needs_improvement">Needs improvement</option><option value="keep">Keep</option><option value="reject">Reject</option></select></label>
      </div>
      <label>General notes<textarea id="human-general-notes"></textarea></label>
      <section><h3>Assigned criteria</h3><div class="stack">${criteria}</div></section>
      <div class="grid-2">
        <label>Preferred Loop<select id="human-preferred-loop"><option value="">No preference</option>${loopOptions}</select></label>
        <span></span>
        <label>Loop note for<select id="human-loop-note-id">${loopOptions}</select></label>
        <label>Loop notes<textarea id="human-loop-notes"></textarea></label>
        <label>Artifact note for<select id="human-artifact-note-id">${artifactOptions}</select></label>
        <label>Artifact notes<textarea id="human-artifact-notes"></textarea></label>
      </div>
      <div class="card compact"><h3>Evidence binding</h3><div class="binding">Experiment: ${esc(VM.experiment_id)}<br>Manifest SHA-256: ${esc(VM.binding.manifest_sha256)}<br>Viewer SHA-256: ${esc(VM.binding.viewer_sha256)}<br>Algorithm: ${esc(VM.binding.viewer_hash_algorithm)}</div></div>
      <div><button class="button" id="human-export">Download review JSON</button></div>
    </div>`;
  }

  function openHumanReview(invoker) {
    const dialog = byId("human-dialog");
    if (!dialog) return;
    dialog._invoker = invoker;
    byId("human-body").innerHTML = humanReviewMarkup();
    const selectedLoop = loopById(hashState().loop) || loopById(VM.champion.iteration_id);
    if (selectedLoop) byId("human-loop-note-id").value = selectedLoop.id;
    if (VM.story.featured_artifact_id) byId("human-artifact-note-id").value = VM.story.featured_artifact_id;
    byId("human-export").addEventListener("click", exportHumanReview);
    dialog.showModal();
    byId("human-verdict").focus();
  }

  function exportHumanReview() {
    const criterionReviews = list(VM.human_review_criteria).map((criterion, index) => {
      const scoreText = byId(`human-score-${index}`).value;
      const rating = byId(`human-rating-${index}`).value;
      return {
        criterion_id: criterion.id,
        score: scoreText === "" ? null : Number(scoreText),
        rating: rating || null,
        notes: byId(`human-criterion-notes-${index}`).value
      };
    });
    const loopNotes = byId("human-loop-notes").value.trim();
    const artifactNotes = byId("human-artifact-notes").value.trim();
    const review = {
      schema_version: "1.0",
      experiment_id: VM.experiment_id,
      manifest_sha256: VM.binding.manifest_sha256,
      viewer_sha256: VM.binding.viewer_sha256,
      viewer_hash_algorithm: VM.binding.viewer_hash_algorithm,
      verdict: byId("human-verdict").value,
      general_notes: byId("human-general-notes").value,
      criterion_reviews: criterionReviews,
      loop_notes: loopNotes ? [{iteration_id: byId("human-loop-note-id").value, notes: loopNotes}] : [],
      artifact_notes: artifactNotes ? [{artifact_id: byId("human-artifact-note-id").value, notes: artifactNotes}] : [],
      preferred_iteration_id: byId("human-preferred-loop").value || null,
      recommendation: byId("human-recommendation").value
    };
    const blob = new Blob([`${JSON.stringify(review, null, 2)}\n`], {type: "application/json"});
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `${VM.experiment_id}-human-review.json`;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(href), 0);
  }

  byId("experiment-id").textContent = VM.experiment_id;
  renderOverview();
  document.querySelectorAll('[role="tab"]').forEach((tab, index, tabs) => {
    tab.addEventListener("click", () => activate(tab.dataset.tab));
    tab.addEventListener("keydown", event => {
      let next = index;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = tabs.length - 1;
      else return;
      event.preventDefault();
      tabs[next].focus();
    });
  });
  document.addEventListener("click", event => {
    const loopButton = event.target.closest("[data-open-loop]");
    if (loopButton) {
      activate("topology");
      selectLoop(loopButton.dataset.openLoop, true);
    }
    const expand = event.target.closest(".expand-artifact");
    if (expand) openArtifact(expand.dataset.artifact, expand);
  });
  document.addEventListener("input", event => {
    if (event.target.id === "manifest-search") {
      byId("manifest-tree").innerHTML = renderTree(VM.raw_manifest, "manifest", event.target.value);
    }
  });
  byId("dialog-close").addEventListener("click", () => byId("artifact-dialog").close());
  byId("artifact-dialog").addEventListener("close", event => event.currentTarget._invoker && event.currentTarget._invoker.focus());
  if (byId("human-review-button")) {
    byId("human-review-button").addEventListener("click", event => openHumanReview(event.currentTarget));
    byId("human-close").addEventListener("click", () => byId("human-dialog").close());
    byId("human-dialog").addEventListener("close", event => event.currentTarget._invoker && event.currentTarget._invoker.focus());
  }
  byId("theme-select").addEventListener("change", event => applyTheme(event.target.value));
  const requestedTheme = new URLSearchParams(location.search).get("scoutTheme");
  byId("theme-select").value = requestedTheme === "dark" || requestedTheme === "light" ? requestedTheme : "system";
  applyTheme(byId("theme-select").value);
  const initial = hashState();
  activate(initial.view || "overview", false);
  window.addEventListener("hashchange", () => {
    const state = hashState();
    activate(state.view || "overview", false);
    if (state.view === "topology" && topologyController) {
      const hasViewport = state.x != null && state.y != null && state.scale != null;
      if (hasViewport) {
        topologyController.set(
          {x: Number(state.x), y: Number(state.y), scale: Number(state.scale)},
          {persist: false, unclamped: true}
        );
      }
      if (state.loop) {
        selectLoop(state.loop, false, {focus: !hasViewport, openInspector: true});
      }
    }
  });
})();
</script>
</body>
</html>
"""
