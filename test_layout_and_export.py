from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from comiccraft.exporters import export_comic_pdf
from comiccraft.layout_builder import build_panel_layout
from comiccraft.schemas import Comic, ComicPanel


def make_comic(image_path: Path) -> Comic:
    return Comic(
        id="test-comic",
        title="The Little Adventure",
        prompt="A fox finds a new path",
        character_name="Felix",
        setting="the woods",
        tone="funny",
        art_style="comic book",
        panels=[
            ComicPanel(
                title="A New Path",
                narration="Felix found a curious trail.",
                image_prompt="A fox in a forest",
                image_path=str(image_path),
            )
        ],
    )


class ComicExportTests(unittest.TestCase):
    def test_layout_binds_image_title_and_narration(self):
        image = Path("/tmp/panel.png")

        layout = build_panel_layout(make_comic(image))

        self.assertEqual(len(layout), 1)
        self.assertEqual(layout[0].title, "A New Path")
        self.assertEqual(layout[0].narration, "Felix found a curious trail.")
        self.assertEqual(layout[0].image_path, image)

    def test_comic_response_does_not_expose_server_image_path(self):
        response = make_comic(Path("/private/comiccraft/panel.png")).model_dump()

        self.assertNotIn("image_path", response["panels"][0])

    def test_export_rejects_missing_panel_image(self):
        with self.assertRaisesRegex(FileNotFoundError, "Panel illustration is missing"):
            export_comic_pdf(make_comic(Path("/tmp/not-a-real-panel.png")), Path("/tmp/comic.pdf"))

    def test_export_supports_smart_punctuation(self):
        from PIL import Image

        with TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "panel.png"
            Image.new("RGB", (320, 200), color="white").save(image_path)
            comic = make_comic(image_path)
            comic.panels[0].narration = "Felix’s curious trail… led to a ‘new’ path."

            pdf_path = export_comic_pdf(comic, root / "comic.pdf")

            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))

    def test_export_writes_comic_pages(self):
        from PIL import Image

        with TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "panel.png"
            Image.new("RGB", (320, 200), color="white").save(image_path)
            pdf_path = export_comic_pdf(make_comic(image_path), root / "comic.pdf")

            self.assertTrue(pdf_path.is_file())
            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))
