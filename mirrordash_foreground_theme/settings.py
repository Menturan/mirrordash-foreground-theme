"""The owner's settings, checked: each row of the Themes list merged with the theme's defaults (themes.py). Whatever
is missing, unknown or out of range falls back to the default, so a hand-edited config can't break the card."""

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
    enabled: bool  # a row of the list that's switched on
    all_year: bool  # shown whatever the date
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


def parse_people(raw) -> tuple:
    """The birthdays that are a name and a real day."""
    return tuple({"name": str(person.get("name") or "").strip()[:40], "date": month_day(person.get("date"))}
                 for person in raw or [] if isinstance(person, dict) and month_day(person.get("date")))


def theme_settings(key: str, raw, enabled: bool = True, people=()) -> ThemeSettings:
    """One theme's settings from its row's `settings` (None: all defaults); people are the top-level birthdays."""
    theme: Theme = THEMES[key]
    raw = raw if isinstance(raw, dict) else {}
    start, end = theme.days if isinstance(theme.days, tuple) else ("", "")
    return ThemeSettings(
        enabled=enabled,
        all_year=bool(raw.get("all_year", False)),  # a theme without days of its own (stars, rain) has empty ones: never
        start=month_day(raw["start"]) if "start" in raw else start,
        end=month_day(raw["end"]) if "end" in raw else end,
        mode=_choice(raw, "mode", MODES, default(theme, "mode")),
        variant=_choice(raw, "variant", theme.variants, default(theme, "variant")),
        palette=_choice(raw, "palette", theme.palettes, default(theme, "palette")),
        motion=_choice(raw, "motion", theme.motions, default(theme, "motion")),
        **{name: _number(raw, name, default(theme, name)) for name in RANGES},
        drift=theme.drift and bool(raw.get("drift", True)),
        people=parse_people(people) if key == "birthday" else (),
        greeting_at=_choice(raw, "greeting_at", POSITIONS, "quarter"),
        font=_choice(raw, "font", FONTS, "inter"),
    )


def all_theme_settings(config: dict) -> dict[str, ThemeSettings]:
    """Every theme's settings, the listed ones first in the list's order (that order decides where days overlap),
    a theme twice in the list taking its first row. A theme with no row is off (but still has its defaults)."""
    rows = [row for row in config.get("themes") or [] if isinstance(row, dict) and row.get("theme") in THEMES]
    people = config.get("people")
    found = {}
    for row in rows:
        found.setdefault(row["theme"], theme_settings(row["theme"], row.get("settings"), bool(row.get("enabled", True)), people))
    return found | {key: theme_settings(key, None, False, people) for key in THEMES if key not in found}
