"""Writes config_schema.json from themes.py: one folding block of settings per theme. The mirror reads the file
and never runs the module's code for it (MirrorDash ARCHITECTURE #41), so it is written here and checked in;
tests/test_schema.py fails when it's out of date.

    uv run python -m mirrordash_foreground_theme.schema
"""

import json
from pathlib import Path

from .greeting import FONTS, POSITIONS
from .themes import MODES, MOTIONS, THEMES, Theme, default

SCHEMA_FILE = Path(__file__).parent / "config_schema.json"
DAYS = {"easter": "Palm Sunday to Easter Monday", "midsummer": "Midsummer Eve to Sunday",
        "birthdays": "On the birthdays below"}


def choice(title: str, options: dict, chosen: str, description: str = "") -> dict:
    """An enum field from {key: title} or {key: (title, ...)}."""
    return {"type": "string", "title": title, "description": description, "default": chosen, "enum": list(options),
            "enum_titles": [value[0] if isinstance(value, tuple) else value for value in options.values()]}


def slider(title: str, smallest: int, largest: int, step: int, value: int, description: str) -> dict:
    return {"type": "integer", "title": title, "description": description, "default": value,
            "minimum": smallest, "maximum": largest, "step": step}


def theme_block(key: str, theme: Theme) -> dict:
    when = DAYS[theme.days] if isinstance(theme.days, str) else "On the days below (none: never)"
    fields = {"by_date": {"type": "boolean", "title": "Show By Date", "default": True,
                          "description": f"When Theme is By date. {when}."}}
    if isinstance(theme.days, tuple) or theme.days is None:
        start, end = theme.days or ("", "")
        on_dates = {"by_date": [True]}  # the days matter only while it's shown by date
        fields["start"] = {"type": "string", "title": "From", "default": start, "description": "MM-DD, e.g. 12-01.",
                           "show_if": on_dates}
        fields["end"] = {"type": "string", "title": "To", "default": end, "description": "MM-DD; may be after New Year.",
                         "show_if": on_dates}
    fields |= {
        "mode": choice("Movement", MODES, default(theme, "mode"),
                       "Showers: half a minute that fades in and out, then nothing until the next one; best when the screen is "
                       "on for hours. All the time: moves while the screen is on; best when it only lights up when someone "
                       "comes. Still: never moves."),
        "variant": choice("Shapes", theme.variants, default(theme, "variant")),
        "palette": choice("Colours", theme.palettes, default(theme, "palette")),
        "motion": choice("Motion", {name: MOTIONS[name] for name in theme.motions}, default(theme, "motion"),
                         "How the shapes move. Those marked heavy draw each shape on its own: best with Showers."),
        "amount": slider("How Many", 1, 10, 1, default(theme, "amount"), "Fewer are calmer; above 4 a second layer is drawn (with wind, never: the Pi's GPU memory)."),
        "size": slider("Size (%)", 50, 200, 10, default(theme, "size"), "How large the shapes are."),
        "brightness": slider("Brightness (%)", 10, 100, 5, default(theme, "brightness"), "How bright the shapes are."),
        "speed": slider("Speed (%)", 25, 300, 25, default(theme, "speed"), "Faster makes the Pi draw more often while it moves."),
    }
    if theme.drift:
        fields["drift"] = {"type": "boolean", "title": "Snowdrift", "default": True, "description": "A low drift along the bottom edge. It never moves."}
    if theme.days == "birthdays":
        fields["people"] = {"type": "array", "title": "Birthdays", "description": "Whose birthdays: confetti and their name on the day.",
                            "items": {"type": "object", "title": "Birthday", "properties": {
                                "name": {"type": "string", "title": "Name"},
                                "date": {"type": "string", "title": "Date", "description": "MM-DD (or YYYY-MM-DD)."}}}}
        fields["greeting_at"] = choice("Where the Text Is", POSITIONS, "quarter", "The greeting stays all day.")
        fields["font"] = choice("Font", FONTS, "inter")
    return {"type": "object", "title": theme.title, "description": f"The {theme.title.lower()} theme's settings.", "properties": fields,
            "show_if": {"theme": ["auto", key]}}  # By date may show any theme; one theme all year shows only its own


def build() -> dict:
    by_date = "By date: " + ", ".join(f"{theme.title} ({DAYS[theme.days].lower() if isinstance(theme.days, str) else ' to '.join(theme.days)})"
                                      for theme in THEMES.values() if theme.days) + ". Each theme's own block below changes its days."
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Foreground Theme",
        "description": "Seasonal decoration over the mirror. Put it in Foreground. Each theme has its own settings below. "
                       "Shapes that keep moving keep the Raspberry Pi drawing (warmer, and a video beside it may stutter); "
                       "showers or still shapes cost next to nothing.",
        "type": "object",
        "properties": {
            "theme": choice("Theme", {"auto": "By date"} | {key: theme.title for key, theme in THEMES.items()}, "auto",
                            by_date + " Or one theme all year."),
            "shower_every": {"type": "integer", "default": 1, "title": "Minutes Between",
                             "description": "Showers: how often one comes by itself."},
            "shower_on_arrival": {"type": "boolean", "default": True, "title": "Move When Someone Comes",
                                  "description": "Showers: one when the motion sensor sees someone at the mirror."},
            "shower_on_wake": {"type": "boolean", "default": True, "title": "Move When the Screen Wakes",
                               "description": "Showers: one when the screen turns on, this module's schedule begins or privacy mode ends."},
        } | {key: theme_block(key, theme) for key, theme in THEMES.items()},
    }


def text() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    SCHEMA_FILE.write_text(text())
    print(f"wrote {SCHEMA_FILE}")
