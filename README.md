# ComicCraft

ComicCraft turns a short story brief into a panel-by-panel comic using Gemini for the script and Stable Diffusion (Diffusers) for panel illustrations. The browser app previews the panels and exports them with their narration as a PDF. Without a Gemini key, the app uses a clearly labeled local demo mode with template-based stories and simple placeholder artwork, so you can try the complete workflow without AI credentials.

## Run locally

1. Use Python 3.10 or newer and install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   Install a PyTorch build that matches your machine, then install the full app dependencies:

   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/<cpu-or-cuda-index>
   pip install -r requirements-ai.txt
   ```

   Choose the PyTorch command for your host using the [PyTorch install selector](https://pytorch.org/get-started/locally/). For API and PDF-only use, `pip install -r requirements.txt` omits the large image-generation dependencies.
2. Set the Gemini key:

   ```bash
   export GEMINI_API_KEY="your-key"
   ```

   `GEMINI_MODEL` defaults to `gemini-1.5-pro`; set it to another model available to your API key if needed. Stable Diffusion defaults to `stable-diffusion-v1-5/stable-diffusion-v1-5`; override it with `STABLE_DIFFUSION_MODEL`. `STABLE_DIFFUSION_DEVICE` may be set to `cpu`, `cuda`, or another supported PyTorch device.
3. Start the server:

   ```bash
   uvicorn comiccraft.main:app --reload
   ```
4. Visit <http://127.0.0.1:8000>. Generated images and timestamped PDF exports are stored under `.comiccraft/`. Set `COMICCRAFT_DATA_DIR` to change the storage directory.

The first image generation downloads the configured model and may take several minutes; GPU acceleration is recommended. Provider setup or generation failures are returned with actionable API errors and shown in the interface. Set `COMICCRAFT_DEMO_MODE=false` to disable the no-key demo and require AI provider configuration.

## API

- `POST /api/comics` — create a comic from `prompt`, `character_name`, `setting`, and optional `tone`, `art_style`, and `panel_count` (2–8).
- `GET /api/comics/{comic_id}` — retrieve the generated comic.
- `GET /api/comics/{comic_id}/images/{panel_number}` — retrieve a panel illustration.
- `GET /api/comics/{comic_id}/pdf` — export and download the comic as a PDF.

Interactive API docs are available at `/docs`.

## Tests

```bash
python -m pytest
```
