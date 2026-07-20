from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelAdapter:
    panel_id: str
    label: str
    markup: str
    render_function: str

    def interaction(self) -> dict[str, object]:
        return {
            "selector": f"#tab-{self.panel_id}",
            "kind": "tab",
            "actions": [{"type": "click", "expect_hash": f"#view={self.panel_id}"}],
        }


CORE_PANELS = (
    PanelAdapter(
        "overview",
        "Overview",
        '<section role="tabpanel" id="panel-overview" aria-labelledby="tab-overview" tabindex="0"></section>',
        "renderOverview",
    ),
    PanelAdapter(
        "topology",
        "Topology",
        '<section role="tabpanel" id="panel-topology" aria-labelledby="tab-topology" tabindex="0" hidden></section>',
        "renderTopology",
    ),
    PanelAdapter(
        "compare",
        "Compare",
        '<section role="tabpanel" id="panel-compare" aria-labelledby="tab-compare" tabindex="0" hidden></section>',
        "renderCompare",
    ),
)

EXTRA_PANELS = {
    "samples": PanelAdapter(
        "samples",
        "Samples",
        (
            '<section role="tabpanel" id="panel-samples" aria-labelledby="tab-samples" tabindex="0" hidden>'
            '<div class="card"><h2>Sample evidence</h2><div class="table-wrap">'
            '<table><thead id="samples-head"></thead><tbody id="samples-body"></tbody></table>'
            '</div></div></section>'
        ),
        "renderSamples",
    ),
}

EXTRA_PANEL_IDS = frozenset(EXTRA_PANELS)


def panels_for(extra_panel_ids: tuple[str, ...]) -> tuple[PanelAdapter, ...]:
    return CORE_PANELS + tuple(EXTRA_PANELS[panel_id] for panel_id in extra_panel_ids)
