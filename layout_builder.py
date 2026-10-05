from dataclasses import dataclass
from pathlib import Path

from comiccraft.schemas import Comic


@dataclass(frozen=True)
class PanelLayout:
    title: str
    narration: str
    image_path: Path


def build_panel_layout(comic: Comic) -> list[PanelLayout]:
    """Bind each panel's heading, illustration, and narration for PDF export."""
    return [
        PanelLayout(
            title=panel.title,
            narration=panel.narration,
            image_path=Path(panel.image_path),
        )
        for panel in comic.panels
    ]

