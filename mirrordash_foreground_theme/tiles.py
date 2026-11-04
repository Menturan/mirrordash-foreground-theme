"""How a theme is drawn: layers of shapes, each an SVG tile repeated down the screen and sliding one tile, and
for the one-by-one motions a few shapes as elements of their own. Seeded: the same settings draw the same
shapes every time, so the card's HTML only changes when something should and the mirror redraws nothing else.

GPU memory is what a Raspberry Pi 3 runs out of first: each moving layer is a texture as large as the screen plus
one tile of travel, and with the mirror's other modules only ~40 MB of its 256 MB is free (a 2026-11-04 stress
test crashed WebKit's renderer at three 1920x2160 layers). So plan() draws one layer with a screen-high tile
(nothing repeats) or two with half-screen tiles (the pattern comes twice down the screen), whichever holds
GPU_BUDGET_MB; the amount fills the layers more densely instead, which costs no GPU memory."""

import base64
import math
import random

from .shapes import SIZES, symbol
from .themes import THEMES

SCREEN_W, SCREEN_H = 1920, 1080  # ponytail: sized for a 1080p mirror; another screen sees the tile repeat more or less
TILE_W = 1920
GPU_BUDGET_MB = 25
# Per layer, far to near: shapes in a 400 px square at amount 5, their size, how bright, and speed (px/s at 100%)
LAYERS = [(14, (1.5, 2.5), 0.45, 18), (9, (2.5, 3.5), 0.65, 37), (6, (3.5, 5.0), 0.8, 71)]
SWAY_SECONDS = (5.5, 7, 4.3)  # each layer its own beat, so they don't swing together
SWAY_PX = 32  # how far a layer swings each way (it's that much wider on each side)
WIND_DEGREES = 15  # the slant of wind: the layer is skewed, and wider by what the skew uncovers
TICK = 36  # every layer steps on this beat (or every 2nd, 3rd ... of it): the screen redraws 36 times a second, not ~60
EACH_LIMIT, TWINKLE_LIMIT = 60, 30  # elements of their own cost the Pi: never more than this


def side(settings, tile: int) -> int:
    """How much wider than the screen a layer is on each side: sway swings it that far, wind's skew uncovers it."""
    if settings.motion == "sway":
        return SWAY_PX
    if settings.motion == "wind":
        return math.ceil((SCREEN_H + tile) / 2 * math.tan(math.radians(WIND_DEGREES)))
    return 0


def layer_mb(settings, tile: int) -> float:
    """The GPU texture one moving layer takes, in MB: the screen (and a side) plus one tile of travel."""
    return (SCREEN_W + 2 * side(settings, tile)) * (SCREEN_H + tile) * 4 / 2 ** 20


def plan(settings) -> tuple[list[int], int]:
    """Which layers to draw and how high their tile is: the far and the near one with half-screen tiles for a
    larger amount, else the middle one with a screen-high tile; the first that holds GPU_BUDGET_MB."""
    options = ([([0, 2], SCREEN_H // 2)] if settings.amount > 4 else []) + [([1], SCREEN_H), ([1], SCREEN_H // 2)]
    return next(((layers, tile) for layers, tile in options if len(layers) * layer_mb(settings, tile) <= GPU_BUDGET_MB),
                options[-1])


def gpu_mb(settings) -> float:
    if settings.motion in ("sway_each", "spin_each"):
        return 0  # no layers: a few small shapes of their own
    layers, tile = plan(settings)
    return len(layers) * layer_mb(settings, tile)


def stepping(speed: float, tile: int) -> tuple[int, float]:
    """Whole pixels per step, and steps a second, on the shared TICK: a fast layer takes larger steps on every
    tick, a slow one a pixel on every 2nd or 3rd, so all layers move at the same moments. The step ends a tile
    exactly and makes its time whole milliseconds: a rounded duration would let the layers drift apart."""
    if speed >= TICK:
        whole = [d for d in range(1, tile + 1) if tile % d == 0 and tile * 1000 % (d * TICK) == 0]
        return min(whole, key=lambda d: abs(d - speed / TICK)), TICK
    return 1, TICK / max(1, round(TICK / speed))


def _wrapped(at: float, length: int, reach: float) -> list[float]:
    """Where a shape is drawn along one side of the tile: also on the far side when it reaches over an edge, so
    the repeated tiles join without a seam."""
    return [at] + ([at + length] if at < reach else []) + ([at - length] if at > length - reach else [])


def pace(settings) -> float:
    """How much longer than at 100% a motion takes."""
    return 100 / settings.speed


def _seed(key: str, settings, *parts) -> random.Random:
    return random.Random(f"{key}|{settings.variant}|{settings.palette}|{settings.amount}|{settings.size}|{parts}")


def layer(key: str, settings, index: int, tile: int) -> dict:
    """One layer: its tile as a CSS url(), how it steps (seconds and steps a tile) and its sway beat."""
    theme = THEMES[key]
    per_400, (smallest, largest), alpha, speed = LAYERS[index]
    shapes, colors = theme.variants[settings.variant][1], theme.palettes[settings.palette][1]
    rng = _seed(key, settings, index, tile)
    density = settings.amount / 5 * (0.7 if settings.motion == "twinkle" else 1)
    uses = []
    for _ in range(round(per_400 * TILE_W * tile / 400 ** 2 * density)):
        which = rng.randrange(len(shapes))
        factor, upright = SIZES[shapes[which]]
        x, y = rng.uniform(0, TILE_W), rng.uniform(0, tile)
        scale = rng.uniform(smallest, largest) * factor * settings.size / 100
        turn, color = 0 if upright else rng.uniform(0, 360), rng.choice(colors)
        for at_x in _wrapped(x, TILE_W, scale * 1.5):
            for at_y in _wrapped(y, tile, scale * 1.5):
                uses.append(f'<use href="#s{which}" x="-1" y="-1" width="2" height="2" fill="{color}" fill-opacity="{alpha}" '
                            f'transform="translate({at_x:.0f} {at_y:.0f}) rotate({turn:.0f}) scale({scale:.2f})"/>')
    defs = "".join(symbol(name, f"s{i}") for i, name in enumerate(shapes))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{TILE_W}" height="{tile}"><defs>{defs}</defs>{"".join(uses)}</svg>'
    px, rate = stepping(speed * settings.speed / 100 * (6 if theme.fast else 1), tile)
    steps = tile // px
    return {"image": f"url('data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}')",
            "seconds": round(steps / rate, 3), "steps": steps, "sway": round(SWAY_SECONDS[index] * pace(settings), 1)}


def singles(key: str, settings) -> list[dict]:
    """The shapes of a one-by-one motion (sway_each, spin_each) or the twinkling stars, each its own element:
    where it is (% of the screen), its size, colour and turn, and its timing."""
    theme, twinkle = THEMES[key], settings.motion == "twinkle"
    shapes, colors = theme.variants[settings.variant][1], theme.palettes[settings.palette][1]
    rng = _seed(key, settings, "single")
    count = min(TWINKLE_LIMIT, 6 * settings.amount) if twinkle else min(EACH_LIMIT, 12 * settings.amount)
    out = []
    for _ in range(count):
        which = rng.randrange(len(shapes))
        factor, upright = SIZES[shapes[which]]
        out.append({
            "shape": which, "px": round(2 * rng.uniform(3, 5.5) * factor * settings.size / 100),
            "color": rng.choice(colors), "alpha": round(rng.uniform(0.6, 0.95), 2), "turn": 0 if upright else round(rng.uniform(0, 360)),
            "x": round(rng.uniform(0, 100), 1), "y": round(rng.uniform(0, 100), 1),
            "fall": round(rng.uniform(8, 15) * pace(settings), 1), "beat": round(rng.uniform(2.5, 5.5) * pace(settings), 1),
            "delay": -round(rng.uniform(0, 20), 1),
        })
    return out


def symbols(key: str, settings) -> str:
    """The theme's shapes as <symbol>s, for the single elements to <use>."""
    shapes = THEMES[key].variants[settings.variant][1]
    return "".join(symbol(name, f"fg-{i}") for i, name in enumerate(shapes))
