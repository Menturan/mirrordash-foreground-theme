"""The shapes, one SVG file each in shapes/ (where they come from: shapes/CREDITS.md). A shape is drawn in a 2x2
box around 0,0, a dot's size at size 1; SIZES says how much larger each is drawn and which never turn."""

import re
from functools import cache
from pathlib import Path

SHAPES_DIR = Path(__file__).parent / "shapes"
# name -> (how many dots wide, upright: drawn as it stands, never turned)
SIZES = {
    "dot": (1.0, False), "simple-flake": (4.0, False), "simple-heart": (4.4, False), "sparkle": (3.2, False),
    "twinkle": (2.8, False), "petal": (3.6, False), "blossom": (4.4, False), "birch-leaf": (3.6, False),
    "daisy": (4.4, False), "grass": (4.8, False), "confetti": (3.6, False), "streamer": (4.8, False),
    "rain": (6.0, True), "drizzle": (3.2, True),
    "pumpkin": (4.3, True), "lantern": (4.3, True), "ghost": (4.3, True), "ghost-flying": (4.3, True), "bat": (4.3, True),
    "maple-leaf": (4.3, False), "oak-leaf": (4.3, False), "leaf": (4.3, False), "acorn": (4.3, True),
    "snowflake": (4.3, False), "crystal": (4.3, False), "heart": (3.6, False), "flower": (4.3, False),
    "tulip": (4.3, True), "butterfly": (4.3, False), "feather": (4.3, False), "egg": (4.3, False),
    "star": (3.6, False), "balloon": (4.3, True), "drop": (3.6, True),
}


@cache
def symbol(name: str, symbol_id: str) -> str:
    """The shape as a <symbol> filling the 2x2 box, for <use href="#id"> in a tile."""
    svg = (SHAPES_DIR / f"{name}.svg").read_text()
    box = re.search(r'viewBox="([^"]+)"', svg).group(1)
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.DOTALL).group(1).strip()
    return f'<symbol id="{symbol_id}" viewBox="{box}">{inner}</symbol>'
