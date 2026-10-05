from typing import Literal

from pydantic import BaseModel, Field


class ComicRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    character_name: str = Field(min_length=1, max_length=80)
    setting: str = Field(min_length=1, max_length=160)
    tone: Literal["adventurous", "dramatic", "funny", "heartwarming", "mysterious"] = "adventurous"
    art_style: Literal["anime", "comic book", "watercolor", "pixel art", "storybook"] = "comic book"
    panel_count: int = Field(default=4, ge=2, le=8)


class ComicPanel(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    narration: str = Field(min_length=1, max_length=1200)
    image_prompt: str = Field(min_length=1, max_length=1000)
    image_path: str = Field(exclude=True)


class Comic(BaseModel):
    id: str
    title: str
    prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str
    generation_mode: Literal["ai", "demo"] = "ai"
    panels: list[ComicPanel]
