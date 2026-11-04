"""The owner's settings, checked: each theme's block merged with the theme's defaults (themes.py). Whatever is
missing, unknown or out of range falls back to the default, so a hand-edited config can't break the card."""

import re
from dataclasses import dataclass
from datetime import date

from .greeting import FONTS, POSITIONS
from .themes import MODES, THEMES, Theme, default

# Sliders: (smallest, largest)
RANGES = {"amount": (1, 10), "size": (50, 200), "brightness": (10, 100), "speed": (25, 300)}
MONTH_DAY = re.compile(r"^(\d{4}-)?(\d{2})-(\d{2})$")


@dataclass(frozen=True)
class ThemeSettings:
    by_date: bool
    start: str
    end: str
    mode: str
    variant: str
    palette: str
    motion: str
    amount: int
    size: int
    brightness: int
    speed: int
    drift: bool = False
    people: tuple = ()  # birthday: ({"name", "date"}, ...)
    greeting_at: str = "quarter"  # not "position": the core owns that name (where a module sits)
    font: str = "inter"


def month_day(text) -> str | None:
    """MM-DD (from MM-DD or YYYY-MM-DD) if it's a real day of the year, else None."""
    match = MONTH_DAY.match(str(text or "").strip())
    if not match:
        return None
    try:
        date(2000, int(match[2]), int(match[3]))  # a leap year: 02-29 is a day
    except ValueError:
        return None
    return f"{match[2]}-{match[3]}"


def _choice(raw: dict, key: str, allowed, fallback):
    return raw.get(key) if raw.get(key) in allowed else fallback


def _number(raw: dict, key: str, fallback: int) -> int:
    smallest, largest = RANGES[key]
    try:
        return min(max(int(float(raw.get(key))), smallest), largest)
    except (TypeError, ValueError):
        return fallback


def theme_settings(key: str, raw) -> ThemeSettings:
    theme: Theme = THEMES[key]
    raw = raw if isinstance(raw, dict) else {}
    start, end = theme.days if isinstance(theme.days, tuple) else ("", "")
    people = tuple({"name": str(person.get("name") or "").strip()[:40], "date": month_day(person.get("date"))}
                   for person in raw.get("people") or [] if isinstance(person, dict) and month_day(person.get("date")))
    return ThemeSettings(
        by_date=bool(raw.get("by_date", True)),  # a theme without days of its own (stars, rain) has empty ones: never
        start=month_day(raw["start"]) if "start" in raw else start,
        end=month_day(raw["end"]) if "end" in raw else end,
        mode=_choice(raw, "mode", MODES, default(theme, "mode")),
        variant=_choice(raw, "variant", theme.variants, default(theme, "variant")),
        palette=_choice(raw, "palette", theme.palettes, default(theme, "palette")),
        motion=_choice(raw, "motion", theme.motions, default(theme, "motion")),
        **{name: _number(raw, name, default(theme, name)) for name in RANGES},
        drift=theme.drift and bool(raw.get("drift", True)),
        people=people,
        greeting_at=_choice(raw, "greeting_at", POSITIONS, "quarter"),
        font=_choice(raw, "font", FONTS, "inter"),
    )


def all_theme_settings(config: dict) -> dict[str, ThemeSettings]:
    return {key: theme_settings(key, config.get(key)) for key in THEMES}
