"""Writes config_schema.json from themes.py: one list of themes, each row with its own boxes (fields.py). The mirror
reads the file and never runs the module's code for it (MirrorDash ARCHITECTURE #41), so it is written here and checked in;
tests/test_schema.py fails when it's out of date.

    uv run python -m mirrordash_foreground_theme.schema
"""

import json
from pathlib import Path

from .fields import days_of
from .themes import THEMES

SCHEMA_FILE = Path(__file__).parent / "config_schema.json"


def build() -> dict:
    by_date = ", ".join(f"{theme.title} ({days_of(key).lower() if isinstance(theme.days, str) else ' to '.join(theme.days)})"
                        for key, theme in THEMES.items() if theme.days)
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Foreground Theme",
        "requires_mirrordash": "0.21",
        "description": "Seasonal decoration over the mirror. Put it in Foreground.",
        "help": "Shapes that keep moving keep the Raspberry Pi drawing (warmer, and a video beside it may stutter); "
                "showers or still shapes cost next to nothing.",
        "type": "object",
        "properties": {
            "themes": {
                "type": "array", "title": "Themes",
                "description": "The first theme in the list whose days hold today is shown; move a row up to win where days overlap.",
                "help": "Each row is one theme with its own days, shapes, colours and motion. Out of every theme's days nothing is drawn. "
                        f"Standard days: {by_date}.",
                "default": [{"theme": key, "enabled": True, "settings": {}} for key, theme in THEMES.items() if theme.days],
                "items": {"type": "object", "title": "Theme", "properties": {
                    "theme": {"type": "string", "title": "Theme", "default": next(iter(THEMES)), "enum": list(THEMES),
                              "enum_titles": [theme.title for theme in THEMES.values()]},
                    "enabled": {"type": "boolean", "title": "Show", "default": True,
                                "description": "Off keeps the row's settings but never shows the theme."},
                    "settings": {"type": "object", "format": "fields", "title": "Settings"},
                }, "required": ["theme"]},
            },
            "people": {"type": "array", "title": "Birthdays", "default": [],
                       "description": "Whose birthdays: confetti and their name on the day (the Birthday theme).",
                       "items": {"type": "object", "title": "Birthday", "properties": {
                           "name": {"type": "string", "title": "Name"},
                           "date": {"type": "string", "title": "Date", "description": "MM-DD (or YYYY-MM-DD)."}}}},
            "shower_every": {"type": "integer", "default": 1, "title": "Time between showers", "unit": "min",
                             "description": "Showers: how often one comes by itself."},
            "shower_on_arrival": {"type": "boolean", "default": True, "title": "Move when someone comes",
                                  "description": "Showers: one when the motion sensor sees someone at the mirror."},
            "shower_on_wake": {"type": "boolean", "default": True, "title": "Move when the screen wakes",
                               "description": "Showers: one when the screen turns on, this module's schedule begins or privacy mode ends."},
        },
    }


def text() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    SCHEMA_FILE.write_text(text())
    print(f"wrote {SCHEMA_FILE}")
