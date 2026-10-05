import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from comiccraft.schemas import ComicRequest


class ProviderConfigurationError(RuntimeError):
    """Raised when a required AI provider is not configured."""


class ProviderGenerationError(RuntimeError):
    """Raised when an AI provider cannot return a usable result."""


class GeminiStoryGenerator:
    def generate(self, request: ComicRequest) -> dict[str, Any]:
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise ProviderConfigurationError(
                "Story generation is not configured. Set GEMINI_API_KEY and restart ComicCraft."
            )

        try:
            from google import genai
        except ImportError as exc:
            raise ProviderConfigurationError(
                "The Gemini SDK is missing. Install the project dependencies and restart ComicCraft."
            ) from exc

        model = (os.getenv("GEMINI_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro").strip()
        prompt = f"""
Create a cohesive comic story as JSON only. Return exactly this shape:
{{"title":"short title","panels":[{{"title":"panel title","narration":"1-3 sentences","image_prompt":"visual description for an image model"}}]}}
Create exactly {request.panel_count} panels. Keep the same character visually consistent in every image prompt.
Character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}
Story idea: {request.prompt}
Do not include markdown fences or extra keys.
""".strip()
        try:
            response = genai.Client(api_key=api_key).models.generate_content(
                model=model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            payload = json.loads(response.text or "")
            panels = payload.get("panels")
            if (
                not isinstance(payload.get("title"), str)
                or not isinstance(panels, list)
                or len(panels) != request.panel_count
                or any(
                    not isinstance(panel, dict)
                    or not all(isinstance(panel.get(key), str) and panel[key].strip()
                               for key in ("title", "narration", "image_prompt"))
                    for panel in panels
                )
            ):
                raise ValueError("Gemini returned a story with an invalid structure.")
            return {"title": payload["title"].strip(), "panels": panels}
        except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            raise ProviderGenerationError(f"Gemini returned an unusable story: {exc}") from exc
        except Exception as exc:
            raise ProviderGenerationError(f"Gemini story generation failed: {exc}") from exc


@lru_cache(maxsize=1)
def _load_diffusers_pipeline():
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as exc:
        raise ProviderConfigurationError(
            "Image generation dependencies are missing. Install PyTorch and the project dependencies."
        ) from exc

    model_id = (
        os.getenv("STABLE_DIFFUSION_MODEL", "stable-diffusion-v1-5/stable-diffusion-v1-5")
        or "stable-diffusion-v1-5/stable-diffusion-v1-5"
    ).strip()
    device = (
        os.getenv("STABLE_DIFFUSION_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        or ("cuda" if torch.cuda.is_available() else "cpu")
    ).strip()
    try:
        pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        return pipeline.to(device)
    except Exception as exc:
        raise ProviderGenerationError(
            f"Could not load Stable Diffusion model '{model_id}': {exc}"
        ) from exc


class DiffusersImageGenerator:
    def generate(self, prompt: str, destination: Path, art_style: str) -> None:
        styled_prompt = (
            f"{prompt}, {art_style} comic illustration, expressive composition, "
            "clean detailed artwork, no text, no speech bubbles"
        )
        try:
            result = _load_diffusers_pipeline()(prompt=styled_prompt, num_inference_steps=25)
            image = result.images[0]
            image.save(destination, format="PNG")
        except (ProviderConfigurationError, ProviderGenerationError):
            raise
        except Exception as exc:
            raise ProviderGenerationError(f"Stable Diffusion image generation failed: {exc}") from exc


def safe_image_filename(panel_number: int) -> str:
    return f"panel-{panel_number:02d}.png"
