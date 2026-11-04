"""The birthday greeting drawn as an SVG outline in the font the owner chose. The fonts are outlines in fonts/
(scripts/build_fonts.py makes them), so the card loads no font: Chromium ignores a font declared in a shadow root,
and the admin page's preview runs in the owner's browser."""

import html
import json
import unicodedata
from functools import cache
from pathlib import Path

FONTS_DIR = Path(__file__).parent / "fonts"
# key -> (title, size in px: each about as large to the eye)
FONTS = {
    "inter": ("Inter, thin", 64), "sacramento": ("Sacramento, a thin script", 110),
    "great_vibes": ("Great Vibes, an elegant script", 96), "dancing_script": ("Dancing Script, a cheerful script", 84),
    "pacifico": ("Pacifico, retro", 72), "caveat": ("Caveat, handwritten", 96),
    "amatic_sc": ("Amatic SC, hand-drawn capitals", 96), "fredoka": ("Fredoka, round and playful", 76),
    "lobster": ("Lobster, bold and festive", 80),
}
# key -> (title, how far down the screen the text's middle is, in %; None: at the bottom edge)
POSITIONS = {
    "quarter": ("A quarter down", 25), "golden": ("Golden ratio (38%)", 38.2), "middle": ("The middle", 50),
    "bottom": ("Bottom edge", None), "none": ("No text", None),
}


@cache
def font(key: str) -> dict:
    return json.loads((FONTS_DIR / f"{key}.json").read_text())


def glyph(glyphs: dict, char: str) -> list:
    """The character's outline; one the font lacks is drawn as its letter without the accent, else as ?."""
    base = unicodedata.normalize("NFKD", char)[:1]
    return glyphs.get(char) or glyphs.get(base) or glyphs["?"]


def outline(text: str, key: str) -> dict:
    """text as an <svg> in font key, and its height in px on the mirror."""
    data = font(key)
    x, paths = 0, []
    for char in text:
        advance, commands = glyph(data["glyphs"], char)
        if commands:
            paths.append(f'<path transform="translate({x} 0)" d="{commands}"/>')
        x += advance
    top, height = -data["ascent"], data["ascent"] - data["descent"]
    svg = (f'<svg class="greeting-text" viewBox="0 {top} {x} {height}" role="img" aria-label="{html.escape(text)}">'
           f'<g transform="scale(1 -1)">{"".join(paths)}</g></svg>')
    return {"svg": svg, "height": round(FONTS[key][1] * height / data["units"])}
