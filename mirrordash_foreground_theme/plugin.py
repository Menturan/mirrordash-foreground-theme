"""Seasonal decoration in front of the other modules: snow at Christmas, sparkles at New Year, hearts, spring
petals, autumn leaves, Halloween embers. Made for MirrorDash's Foreground position, which lies over the whole
screen and takes no clicks. "By date" picks the theme of the day from THEMES; outside every season the card
is empty and costs nothing.

Motion that never stops makes a Raspberry Pi redraw the screen all day (MirrorDash ARCHITECTURE #37: warm,
and a video beside it stutters), so the owner chooses: showers (the default: when someone comes to the
mirror, and now and then), moving all the time, or still. It's plain CSS, so the mirror pauses it while a
video plays. Only light shows on a mirror (black is glass), so every theme is drawn in light colours."""

import asyncio
import random
import time
from datetime import date, datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

MODES = ("showers", "falling", "still")
AMOUNTS = {"light": 1, "normal": 2, "heavy": 3}  # layers of shapes
# Each layer is one square tile of shapes repeated over the screen, sliding one tile and over again. Per
# layer: its tile (px; no two share a multiple, so the repeats don't line up), shapes in a 400 px square of
# it, their size range, how bright, and the seconds one tile takes to pass (the farther layer smaller,
# dimmer and slower). steps(tile): one whole pixel per step, so the Pi draws only when a shape has moved
# (#37: about a quarter of a smooth animation's cost).
LAYERS = [(400, 14, (1.5, 2.5), 0.45, 40), (520, 9, (2.5, 3.5), 0.65, 26), (640, 6, (3.5, 5.0), 0.8, 17)]
SHOWER_SECONDS = 30

# The shapes, drawn around 0,0 at size 1 (a dot's radius), and how much larger than a dot each is drawn
SHAPES = {
    "dot": ('<circle r="1"/>', 1.0),
    "sparkle": ('<path d="M0-1.6L.3-.3 1.6 0 .3.3 0 1.6-.3.3-1.6 0-.3-.3Z"/>', 1.6),
    "heart": ('<path d="M0 1.2C-2 -.2-1.2-1.8 0-.8 1.2-1.8 2-.2 0 1.2Z"/>', 2.2),
    "petal": ('<ellipse rx="1.4" ry=".75"/>', 1.8),
    "leaf": ('<path d="M-1.8 0Q0-1.3 1.8 0 0 1.3-1.8 0Z"/>', 2.4),
}
# name -> the shapes, their colours, the direction (1 falls, -1 rises), its days (MM-DD to MM-DD, earlier
# entries win where they overlap), and whether a snowdrift lies along the bottom edge
THEMES = {
    "newyear": {"shapes": ["sparkle", "dot"], "colors": ["#ffe08a", "#ffffff", "#ffb3c7", "#a8d8ff"], "direction": 1,
                "days": ("12-31", "01-01"), "drift": False},
    "snow": {"shapes": ["dot"], "colors": ["#ffffff"], "direction": 1, "days": ("12-01", "01-06"), "drift": True},
    "hearts": {"shapes": ["heart"], "colors": ["#ff8fb1", "#ffc2d4", "#ff6f91"], "direction": 1,
               "days": ("02-10", "02-14"), "drift": False},
    "petals": {"shapes": ["petal"], "colors": ["#ffd6e5", "#fff0f5", "#f9b8cf"], "direction": 1,
               "days": ("04-01", "05-31"), "drift": False},
    "halloween": {"shapes": ["dot"], "colors": ["#ff9a3c", "#c79bff", "#ffc36b"], "direction": -1,
                  "days": ("10-25", "10-31"), "drift": False},
    "leaves": {"shapes": ["leaf"], "colors": ["#ff9a3c", "#ffcf5a", "#ff6b4a", "#e8b04a"], "direction": 1,
               "days": ("09-20", "11-15"), "drift": False},
}


def in_period(day: date, start: str, end: str) -> bool:
    """Whether day is within start..end, given as MM-DD, also across New Year (12-01..01-06)."""
    first, last = (tuple(int(part) for part in text.split("-")) for text in (start, end))
    today = (day.month, day.day)
    return first <= today <= last if first <= last else today >= first or today <= last


def theme_of(day: date) -> str | None:
    """The theme whose days hold day, the first in THEMES where two do; None outside every season."""
    return next((name for name, theme in THEMES.items() if in_period(day, *theme["days"])), None)


def layer_image(theme: str, layer: int) -> str:
    """One layer of a theme as a CSS url() of an SVG tile, the same every time (a fixed seed), so the card's
    HTML only changes when something should: the mirror doesn't redraw what didn't change."""
    tile, per_400, (smallest, largest), alpha, _ = LAYERS[layer]
    spec, rng = THEMES[theme], random.Random(f"{theme}{layer}")
    shapes = []
    for _ in range(round(per_400 * (tile / 400) ** 2)):  # as dense whatever the tile's size
        path, factor = SHAPES[rng.choice(spec["shapes"])]
        x, y, size = rng.uniform(0, tile), rng.uniform(0, tile), rng.uniform(smallest, largest) * factor
        shapes.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({rng.uniform(0, 360):.0f}) scale({size:.1f})" '
                      f'fill="{rng.choice(spec["colors"])}" fill-opacity="{alpha}">{path}</g>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{tile}" height="{tile}">{"".join(shapes)}</svg>'
    return f"url('data:image/svg+xml,{quote(svg, safe='')}')"


class ForegroundThemeModule:
    def __init__(self, config):
        self.config = config
        self.name = "mirrordash_foreground_theme"
        self.theme = config.get("theme") if config.get("theme") in THEMES else "auto"
        self.mode = config.get("mode") if config.get("mode") in MODES else "showers"
        self.layers = AMOUNTS.get(config.get("amount"), 2)
        self.drift = bool(config.get("drift", True))
        self.every = max(int(config.get("shower_every") or 15), 1) * 60  # seconds between showers
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

    def on_motion(self, data: dict):
        """Someone came to the mirror: a shower to greet them (the screen wakes for them too)."""
        if self.mode == "showers" and self.on_arrival and isinstance(data, dict) and data.get("motion"):
            self.start_shower()

    def start_shower(self):
        now = time.monotonic()
        self.shower_until, self.next_shower = now + SHOWER_SECONDS, now + self.every
        self.changed.set()

    def moving(self) -> bool:
        """Whether the shapes move right now."""
        if self.mode != "showers":
            return self.mode == "falling"
        if time.monotonic() >= self.next_shower:
            self.start_shower()
        return time.monotonic() < self.shower_until

    def today(self) -> date:
        try:
            return datetime.now(ZoneInfo(self.timezone)).date()
        except (KeyError, ValueError):
            return date.today()

    def current_theme(self) -> str | None:
        if self.theme != "auto":
            return self.theme
        return theme_of(self.today()) or ("snow" if self.preview else None)

    async def render(self) -> str:
        theme = self.current_theme()
        if theme is None:
            return ""  # out of every season: nothing on the screen, nothing to draw
        spec = THEMES[theme]
        layers = [{"image": layer_image(theme, i), "tile": LAYERS[i][0], "seconds": LAYERS[i][4]} for i in range(self.layers)]
        return self.render_template("widget.html", layers=layers, moving=self.moving(),
                                    rising=spec["direction"] < 0, drift=self.drift and spec["drift"])
