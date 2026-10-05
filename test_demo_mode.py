import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

import comiccraft.main as main
from comiccraft.demo import generate_demo_illustration, generate_demo_story
from comiccraft.schemas import ComicRequest


class ComicDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_demo_story_uses_character_setting_tone_and_panel_count(self):
        request = ComicRequest(
            prompt="A fox discovers a hidden door",
            character_name="Felix",
            setting="enchanted forest",
            tone="funny",
            art_style="comic book",
            panel_count=5,
        )

        story = generate_demo_story(request)

        self.assertEqual(len(story["panels"]), 5)
        self.assertIn("Felix", story["title"])
        self.assertIn("Felix", story["panels"][0]["narration"])
        self.assertIn("enchanted forest", story["panels"][0]["narration"])
        self.assertIn("squirrel", story["panels"][1]["narration"])

    def test_demo_illustration_is_a_valid_png(self):
        with TemporaryDirectory() as directory:
            image_path = Path(directory) / "panel.png"

            generate_demo_illustration(image_path, "anime", 1)

            with Image.open(image_path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (768, 512))

    def test_api_creates_demo_comic_and_pdf_without_ai_key(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            payload = {
                "prompt": "A fox discovers a hidden door",
                "character_name": "Felix",
                "setting": "enchanted forest",
                "tone": "funny",
                "art_style": "comic book",
                "panel_count": 2,
            }
            with patch.dict(os.environ, {"COMICCRAFT_DEMO_MODE": "true"}):
                os.environ.pop("GEMINI_API_KEY", None)
                with (
                    patch.object(main, "DATA_DIR", root),
                    patch.object(main, "COMICS_DIR", root / "comics"),
                ):
                    response = self.client.post("/api/comics", json=payload)

                    self.assertEqual(response.status_code, 201, response.text)
                    comic = response.json()
                    self.assertEqual(comic["generation_mode"], "demo")
                    self.assertEqual(len(comic["panels"]), 2)
                    self.assertNotIn("image_path", comic["panels"][0])
                    image_response = self.client.get(
                        f"/api/comics/{comic['id']}/images/1"
                    )
                    self.assertEqual(image_response.status_code, 200)
                    pdf_response = self.client.get(f"/api/comics/{comic['id']}/pdf")
                    self.assertEqual(pdf_response.status_code, 200)
                    self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_demo_uses_blank_whitespace_api_key_as_missing(self):
        with patch.dict(os.environ, {"COMICCRAFT_DEMO_MODE": "true", "GEMINI_API_KEY": "   "}):
            response = self.client.post(
                "/api/comics",
                json={
                    "prompt": "A fox discovers a hidden door",
                    "character_name": "Felix",
                    "setting": "enchanted forest",
                    "panel_count": 2,
                },
            )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["generation_mode"], "demo")

    def test_demo_can_be_disabled_without_api_key(self):
        with patch.dict(os.environ, {"COMICCRAFT_DEMO_MODE": "false"}):
            os.environ.pop("GEMINI_API_KEY", None)
            response = self.client.post(
                "/api/comics",
                json={
                    "prompt": "A fox discovers a hidden door",
                    "character_name": "Felix",
                    "setting": "enchanted forest",
                    "panel_count": 2,
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])

