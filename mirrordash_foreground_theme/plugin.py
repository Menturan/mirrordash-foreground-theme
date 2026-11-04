"""Seasonal decoration in front of the other modules, made for MirrorDash's Foreground position (it lies over
the whole screen and takes no clicks). Each theme has its own settings (settings.py); "By date" picks the
theme of the day (dates.py), and outside every season the card is empty and costs nothing.

Motion that never stops makes a Raspberry Pi redraw the screen all day (MirrorDash ARCHITECTURE #37: warm,
and a video beside it stutters), so each theme has a mode: showers (when someone comes to the mirror, and now
and then), all the time, or still. It's plain CSS, so the mirror pauses it while a video plays.

The parts: themes.py (the data), shapes.py and shapes/ (the shapes), tiles.py (how they're drawn),
greeting.py and fonts/ (the birthday text), schema.py (writes config_schema.json from themes.py)."""

import asyncio
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

from . import tiles
from .dates import birthday_names, theme_of
from .greeting import POSITIONS, outline
from .settings import all_theme_settings
from .themes import THEMES

SHOWER_SECONDS = 30
ONE_BY_ONE = ("sway_each", "spin_each")


class ForegroundThemeModule:
    def __init__(self, config):
        self.config = config
        self.name = "mirrordash_foreground_theme"
        self.theme = config.get("theme") if config.get("theme") in THEMES else "auto"
        self.settings = all_theme_settings(config)
        try:
            self.every = max(int(config.get("shower_every") or 15), 1) * 60  # seconds between showers
        except (TypeError, ValueError):
            self.every = 15 * 60
        self.on_arrival = bool(config.get("shower_on_arrival", True))
        self.preview = bool(config.get("preview"))  # the admin page's preview: a theme whatever the date
        self.timezone = config.get("globals", {}).get("timezone", "Europe/Stockholm")
        # A shower's end is checked this often; the mirror sends the card only when its HTML changed
        self.interval = 5
        self.changed = asyncio.Event()
        self.shower_until = 0.0
        self.next_shower = time.monotonic() + self.every
        event_bus = config.get("event_bus")  # not there in a test
        if event_bus:
            event_bus.subscribe("hardware.motion", self.on_motion)

    def today(self) -> date:
        try:
            return datetime.now(ZoneInfo(self.timezone)).date()
        except (KeyError, ValueError):
            return date.today()

    def current_theme(self) -> str | None:
        if self.theme != "auto":
            return self.theme
        return theme_of(self.today(), self.settings) or ("snow" if self.preview else None)

    def on_motion(self, data: dict):
        """Someone came to the mirror: a shower to greet them (the screen wakes for them too)."""
        theme = self.current_theme()
        if theme and self.settings[theme].mode == "showers" and self.on_arrival and isinstance(data, dict) and data.get("motion"):
            self.start_shower()

    def start_shower(self):
        now = time.monotonic()
        self.shower_until, self.next_shower = now + SHOWER_SECONDS, now + self.every
        self.changed.set()

    def moving(self, mode: str) -> bool:
        """Whether the shapes move right now."""
        if mode != "showers":
            return mode == "falling"
        if time.monotonic() >= self.next_shower:
            self.start_shower()
        return time.monotonic() < self.shower_until

    def text(self, key: str, default: str) -> str:
        """A translation: the mirror gives the module translate() (not there in a test)."""
        return self.translate(key, default) if hasattr(self, "translate") else default

    def greeting(self, theme: str) -> dict | None:
        """The birthday text for whoever has their birthday today (the preview: a sample name), in its font."""
        settings = self.settings[theme]
        names = birthday_names(self.today(), settings.people) or (["Anna"] if self.preview else [])
        if theme != "birthday" or not names or settings.greeting_at == "none":
            return None
        joined = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} {self.text('and', 'and')} {names[-1]}"
        return {**outline(self.text("birthday", "Happy birthday, {names}!").replace("{names}", joined), settings.font),
                "top": POSITIONS[settings.greeting_at][1]}

    async def render(self) -> str:
        theme = self.current_theme()
        if theme is None:
            return ""  # out of every season: nothing on the screen, nothing to draw
        settings, spec = self.settings[theme], THEMES[theme]
        single = settings.motion in ONE_BY_ONE or settings.motion == "twinkle"
        return self.render_template(
            "widget.html", settings=settings, moving=self.moving(settings.mode),
            layers=[] if settings.motion in ONE_BY_ONE else [tiles.layer(theme, settings, i) for i in tiles.layers_for(settings.amount)],
            singles=tiles.singles(theme, settings) if single else [], symbols=tiles.symbols(theme, settings) if single else "",
            rising=settings.variant in spec.rising, drift=settings.drift, greeting=self.greeting(theme))
