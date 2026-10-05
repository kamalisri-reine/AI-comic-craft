from pathlib import Path

from PIL import Image, ImageDraw

from comiccraft.schemas import ComicRequest

_STORY_BEATS = {
    "adventurous": (
        ("The First Clue", "set off to explore", "a trail of glowing footprints"),
        ("A Hidden Passage", "followed the trail", "a secret passage appeared"),
        ("The Big Challenge", "bravely faced the test", "the whole place began to rumble"),
        ("A New Beginning", "found a clever way through", "a wonderful new adventure began"),
    ),
    "dramatic": (
        ("The Ominous Sign", "ventured out alone", "a strange warning appeared"),
        ("The Door Opens", "stepped into the silence", "a long-buried secret came to light"),
        ("The Turning Point", "stood their ground", "the fate of the place hung in the balance"),
        ("After the Storm", "made a difficult choice", "a fragile new hope emerged"),
    ),
    "funny": (
        ("A Very Odd Start", "set off with great confidence", "a suspiciously wobbly sign pointed the way"),
        ("The Unexpected Guest", "followed the sign", "a very serious squirrel demanded directions"),
        ("Oops, Again!", "tried their cleverest plan", "the plan worked, but not quite as intended"),
        ("The Happy Ending", "laughed and tried again", "everyone celebrated with a slightly lopsided cake"),
    ),
    "heartwarming": (
        ("A Kind Beginning", "set off with a little hope", "a small act of kindness lit the way"),
        ("A New Friend", "followed the gentle glow", "a lonely friend was waiting nearby"),
        ("Together Is Better", "shared what they had", "the neighbors came together to help"),
        ("A Place to Belong", "found courage in their friends", "the whole place felt like home"),
    ),
    "mysterious": (
        ("The Strange Clue", "noticed something unusual", "a silver mark appeared without a sound"),
        ("The Whispering Path", "followed the faint clue", "a hidden doorway opened in the shadows"),
        ("The Secret Revealed", "reached for the door", "a surprising secret waited on the other side"),
        ("The Lasting Mystery", "chose to keep exploring", "one final clue promised another mystery"),
    ),
}

_STYLE_COLORS = {
    "anime": ((174, 218, 242), (238, 167, 130), (60, 104, 96)),
    "comic book": ((253, 220, 126), (238, 112, 71), (49, 83, 115)),
    "watercolor": ((191, 220, 205), (214, 177, 149), (98, 137, 126)),
    "pixel art": ((148, 193, 177), (221, 147, 87), (75, 108, 97)),
    "storybook": ((190, 216, 244), (233, 177, 126), (90, 120, 87)),
}


def _story_title(character_name: str, setting: str) -> str:
    location = setting.strip().split()[0].strip(".,!?;:")
    return f"{character_name.strip()}'s {location.title()} Adventure"


def generate_demo_story(request: ComicRequest) -> dict:
    beats = _STORY_BEATS[request.tone]
    idea = request.prompt.strip().rstrip(".!?")[:180]
    panels = []
    for index in range(request.panel_count):
        title, action, event = beats[min(index, len(beats) - 1)]
        narration = (
            f"{request.character_name} {action} through {request.setting}. "
            f'Inspired by "{idea}," the journey took an unexpected turn when {event}.'
        )
        if request.tone == "funny" and index == 0:
            narration += " Even the map seemed to be upside down."
        panels.append(
            {
                "title": title if index < len(beats) else f"{title}: Chapter {index + 1}",
                "narration": narration,
                "image_prompt": (
                    f"Locally drawn demo illustration, scene {index + 1} of {request.panel_count}; "
                    f"{request.character_name} in {request.setting}, {request.art_style} palette."
                ),
            }
        )
    return {"title": _story_title(request.character_name, request.setting), "panels": panels}


def generate_demo_illustration(destination: Path, art_style: str, panel_number: int) -> None:
    """Draw a small, clearly non-AI placeholder scene for offline demo comics."""
    sky, accent, landscape = _STYLE_COLORS[art_style]
    image = Image.new("RGB", (768, 512), sky)
    draw = ImageDraw.Draw(image)

    sun_x = 630 - (panel_number % 3) * 75
    draw.ellipse((sun_x - 38, 52, sun_x + 38, 128), fill=(255, 244, 195))
    draw.polygon(
        [(0, 352), (140, 244), (285, 350), (445, 224), (640, 360), (768, 292), (768, 512), (0, 512)],
        fill=landscape,
    )
    draw.polygon(
        [(0, 414), (180, 331), (340, 420), (520, 332), (700, 428), (768, 386), (768, 512), (0, 512)],
        fill=tuple(max(0, channel - 18) for channel in landscape),
    )

    center_x = 215 + (panel_number % 3) * 98
    draw.ellipse((center_x - 37, 315, center_x + 37, 390), fill=accent, outline=(45, 43, 48), width=5)
    draw.polygon(
        [(center_x - 34, 337), (center_x - 42, 277), (center_x - 4, 317)],
        fill=accent,
        outline=(45, 43, 48),
    )
    draw.polygon(
        [(center_x + 4, 317), (center_x + 42, 277), (center_x + 34, 337)],
        fill=accent,
        outline=(45, 43, 48),
    )
    draw.ellipse((center_x - 12, 340, center_x - 5, 348), fill=(35, 35, 38))
    draw.ellipse((center_x + 5, 340, center_x + 12, 348), fill=(35, 35, 38))
    draw.rounded_rectangle(
        (center_x - 47, 379, center_x + 47, 472),
        radius=30,
        fill=accent,
        outline=(45, 43, 48),
        width=5,
    )

    door_x = 570
    draw.rounded_rectangle(
        (door_x - 56, 274, door_x + 56, 448),
        radius=54,
        fill=(252, 218, 135),
        outline=(58, 52, 66),
        width=9,
    )
    draw.rounded_rectangle(
        (door_x - 39, 297, door_x + 39, 448),
        radius=38,
        fill=(132, 111, 180),
    )
    draw.ellipse((door_x + 19, 365, door_x + 29, 375), fill=(255, 239, 172))

    image.save(destination, format="PNG")
