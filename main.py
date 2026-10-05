import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from comiccraft.demo import generate_demo_illustration, generate_demo_story
from comiccraft.exporters import export_comic_pdf, timestamped_pdf_path
from comiccraft.providers import (
    DiffusersImageGenerator,
    GeminiStoryGenerator,
    ProviderConfigurationError,
    ProviderGenerationError,
    safe_image_filename,
)
from comiccraft.schemas import Comic, ComicPanel, ComicRequest

logger = logging.getLogger("comiccraft")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("COMICCRAFT_DATA_DIR", BASE_DIR / ".comiccraft")).resolve()
COMICS_DIR = DATA_DIR / "comics"

app = FastAPI(title="ComicCraft", description="Create personalized illustrated comics.")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
comics: dict[str, Comic] = {}
story_generator = GeminiStoryGenerator()
image_generator = DiffusersImageGenerator()


def demo_mode_enabled() -> bool:
    return os.getenv("COMICCRAFT_DEMO_MODE", "true").strip().lower() in {
        "1", "true", "yes", "on"
    }


def should_use_demo_mode() -> bool:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    return demo_mode_enabled() and not api_key


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"demo_mode": should_use_demo_mode()},
    )


@app.post("/api/comics", response_model=Comic, status_code=201)
async def create_comic(payload: ComicRequest):
    comic_id = str(uuid4())
    comic_dir = COMICS_DIR / comic_id
    use_demo_mode = should_use_demo_mode()
    try:
        story = await run_in_threadpool(
            generate_demo_story if use_demo_mode else story_generator.generate, payload
        )
        comic_dir.mkdir(parents=True, exist_ok=False)
        panels = []
        for index, panel in enumerate(story["panels"], start=1):
            image_path = comic_dir / safe_image_filename(index)
            if use_demo_mode:
                await run_in_threadpool(
                    generate_demo_illustration, image_path, payload.art_style, index
                )
            else:
                await run_in_threadpool(
                    image_generator.generate, panel["image_prompt"], image_path, payload.art_style
                )
            panels.append(
                ComicPanel(
                    title=panel["title"],
                    narration=panel["narration"],
                    image_prompt=panel["image_prompt"],
                    image_path=str(image_path),
                )
            )
        comic = Comic(
            id=comic_id,
            title=story["title"],
            prompt=payload.prompt,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.tone,
            art_style=payload.art_style,
            generation_mode="demo" if use_demo_mode else "ai",
            panels=panels,
        )
        comics[comic_id] = comic
        return comic
    except ProviderConfigurationError as exc:
        logger.warning("Comic generation configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderGenerationError as exc:
        logger.exception("Comic generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected comic generation failure")
        raise HTTPException(status_code=500, detail="Comic generation failed. Check server logs.") from exc


@app.get("/api/comics/{comic_id}", response_model=Comic)
async def get_comic(comic_id: str):
    comic = comics.get(comic_id)
    if comic is None:
        raise HTTPException(status_code=404, detail="Comic not found.")
    return comic


@app.get("/api/comics/{comic_id}/images/{panel_number}")
async def get_panel_image(comic_id: str, panel_number: int):
    comic = comics.get(comic_id)
    if comic is None or panel_number < 1 or panel_number > len(comic.panels):
        raise HTTPException(status_code=404, detail="Comic panel not found.")
    image_path = Path(comic.panels[panel_number - 1].image_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Panel illustration not found.")
    return FileResponse(image_path, media_type="image/png")


@app.get("/api/comics/{comic_id}/pdf")
async def download_comic_pdf(comic_id: str):
    comic = comics.get(comic_id)
    if comic is None:
        raise HTTPException(status_code=404, detail="Comic not found.")
    try:
        pdf_path = await run_in_threadpool(
            export_comic_pdf, comic, timestamped_pdf_path(DATA_DIR / "exports")
        )
    except FileNotFoundError as exc:
        logger.exception("Comic PDF export failed because a panel image is missing")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Comic PDF export failed")
        raise HTTPException(status_code=500, detail="PDF export failed. Check server logs.") from exc
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
        background=None,
    )


@app.get("/export-success/{comic_id}", response_class=HTMLResponse)
async def export_success(request: Request, comic_id: str):
    if comic_id not in comics:
        raise HTTPException(status_code=404, detail="Comic not found.")
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={"comic_id": comic_id, "comic_title": comics[comic_id].title},
    )
