from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from comiccraft.layout_builder import build_panel_layout
from comiccraft.schemas import Comic


def _pdf_text(text: str) -> str:
    return text.translate(
        str.maketrans(
            {
                "\u2018": "'",
                "\u2019": "'",
                "\u201c": '"',
                "\u201d": '"',
                "\u2013": "-",
                "\u2014": "-",
                "\u2026": "...",
            }
        )
    )


def export_comic_pdf(comic: Comic, destination: Path) -> Path:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_title(comic.title)
    for panel in build_panel_layout(comic):
        if not panel.image_path.is_file():
            raise FileNotFoundError(f"Panel illustration is missing: {panel.image_path.name}")
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 11, _pdf_text(comic.title))
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 9, _pdf_text(panel.title))
        image_width = 180
        x = (pdf.w - image_width) / 2
        pdf.image(str(panel.image_path), x=x, w=image_width)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=12)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _pdf_text(panel.narration))

    destination.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destination))
    return destination


def timestamped_pdf_path(directory: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directory / f"comiccraft-{timestamp}.pdf"
