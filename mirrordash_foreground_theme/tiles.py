"""How a theme is drawn: layers of shapes, each one SVG tile the size of a screen (so nothing repeats on it), and
for the one-by-one motions a few shapes as elements of their own. Seeded: the same settings draw the same
shapes every time, so the card's HTML only changes when something should and the mirror redraws nothing else."""

import base64
import random

from .shapes import SIZES, symbol
from .themes import THEMES

TILE_W, TILE_H = 1920, 1080  # ponytail: one 1080p screen; a larger or portrait screen sees the tile repeat once
# Per layer, far to near: shapes in a 400 px square at amount 5, their size, how bright, and speed (px/s at 100%)
LAYERS = [(14, (1.5, 2.5), 0.45, 18), (9, (2.5, 3.5), 0.65, 37), (6, (3.5, 5.0), 0.8, 71)]
SWAY_SECONDS = (5.5, 7, 4.3)  # each layer its own beat, so they don't swing together
EACH_LIMIT, TWINKLE_LIMIT = 60, 30  # elements of their own cost the Pi: never more than this


def layers_for(amount: int) -> list[int]:
    """Which layers an amount draws: few shapes in the middle one, more in two, a lot in all three."""
    return [1] if amount <= 3 else [0, 2] if amount <= 6 else [0, 1, 2]


def _wrapped(at: float, length: int, reach: float) -> list[float]:
    """Where a shape is drawn along one side of the tile: also on the far side when it reaches over an edge, so
    the repeated tiles join without a seam."""
    return [at] + ([at + length] if at < reach else []) + ([at - length] if at > length - reach else [])


def pace(settings) -> float:
    """How much longer than at 100% a motion takes."""
    return 100 / settings.speed


def _seed(key: str, settings, *parts) -> random.Random:
    return random.Random(f"{key}|{settings.variant}|{settings.palette}|{settings.amount}|{settings.size}|{parts}")


def layer(key: str, settings, index: int) -> dict:
    """One layer: its tile as a CSS url(), how long one tile takes to pass, and its sway beat."""
    theme = THEMES[key]
    per_400, (smallest, largest), alpha, speed = LAYERS[index]
    shapes, colors = theme.variants[settings.variant][1], theme.palettes[settings.palette][1]
    rng = _seed(key, settings, index)
    density = settings.amount / 5 * (0.7 if settings.motion == "twinkle" else 1)
    uses = []
    for _ in range(round(per_400 * TILE_W * TILE_H / 400 ** 2 * density)):
        which = rng.randrange(len(shapes))
        factor, upright = SIZES[shapes[which]]
        x, y = rng.uniform(0, TILE_W), rng.uniform(0, TILE_H)
        scale = rng.uniform(smallest, largest) * factor * settings.size / 100
        turn, color = 0 if upright else rng.uniform(0, 360), rng.choice(colors)
        for at_x in _wrapped(x, TILE_W, scale * 1.5):
            for at_y in _wrapped(y, TILE_H, scale * 1.5):
                uses.append(f'<use href="#s{which}" x="-1" y="-1" width="2" height="2" fill="{color}" fill-opacity="{alpha}" '
                            f'transform="translate({at_x:.0f} {at_y:.0f}) rotate({turn:.0f}) scale({scale:.2f})"/>')
    defs = "".join(symbol(name, f"s{i}") for i, name in enumerate(shapes))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{TILE_W}" height="{TILE_H}"><defs>{defs}</defs>{"".join(uses)}</svg>'
    seconds = TILE_H / (speed * settings.speed / 100 * (6 if theme.fast else 1))
    return {"image": f"url('data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}')",
            "seconds": round(seconds, 1), "steps": TILE_H, "sway": round(SWAY_SECONDS[index] * pace(settings), 1)}


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
