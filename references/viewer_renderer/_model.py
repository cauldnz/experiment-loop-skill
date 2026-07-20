from __future__ import annotations

from dataclasses import dataclass

from ._panels import EXTRA_PANEL_IDS


@dataclass(frozen=True)
class ViewerProfile:
    """Selects curated panels in addition to the fixed core Viewer panels."""

    extra_panels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        duplicates = sorted(
            panel_id for panel_id in set(self.extra_panels)
            if self.extra_panels.count(panel_id) > 1
        )
        unknown = sorted(set(self.extra_panels) - EXTRA_PANEL_IDS)
        if duplicates:
            raise ValueError(f"duplicate Viewer panels: {duplicates}")
        if unknown:
            raise ValueError(f"unknown Viewer panels: {unknown}")


DEFAULT_PROFILE = ViewerProfile()
