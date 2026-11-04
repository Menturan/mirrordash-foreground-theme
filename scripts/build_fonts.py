"""Builds fonts/<name>.json: each character of the birthday greeting's fonts as an SVG outline, so the card
draws the greeting as a path and loads no font. (A font declared in the card's shadow root works in WebKit, the
mirror, but Chromium ignores it, and the admin page's preview runs in the owner's browser.)

    uv run --with fonttools python scripts/build_fonts.py

Fetches the fonts (all SIL Open Font License) from github.com/google/fonts and writes their license next to them.
"""
import json
import tempfile
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONTS_DIR = Path(__file__).parents[1] / "mirrordash_foreground_theme" / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
# name -> the font file in google/fonts, and where a variable font's axes are pinned
FONTS = {
    "inter": ("inter/Inter[opsz,wght].ttf", {"wght": 100, "opsz": 32}),
    "sacramento": ("sacramento/Sacramento-Regular.ttf", {}),
    "great_vibes": ("greatvibes/GreatVibes-Regular.ttf", {}),
    "dancing_script": ("dancingscript/DancingScript[wght].ttf", {"wght": 400}),
    "pacifico": ("pacifico/Pacifico-Regular.ttf", {}),
    "caveat": ("caveat/Caveat[wght].ttf", {"wght": 400}),
    "amatic_sc": ("amaticsc/AmaticSC-Regular.ttf", {}),
    "fredoka": ("fredoka/Fredoka[wdth,wght].ttf", {"wght": 300, "wdth": 100}),
    "lobster": ("lobster/Lobster-Regular.ttf", {}),
}
# What a name in a greeting may hold: Latin letters with the accents of names around the mirror
CHARACTERS = "".join(chr(c) for c in range(32, 127)) + "ÅÄÖåäöÆØæøÉéÈèÊêËëÜüÖößÑñÇçÁáÍíÓóÚúÀàÂâÎîÔôÛûŁłŚśŹźŻżĆćŃńĘęĄąŠšŽžČčŘřĚěÝý"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as answer:
        return answer.read()


def outlines(font: TTFont) -> dict:
    glyph_set, cmap = font.getGlyphSet(), font.getBestCmap()
    glyphs = {}
    for char in CHARACTERS:
        if (name := cmap.get(ord(char))) is None:
            continue
        pen = SVGPathPen(glyph_set, ntos=lambda n: str(round(n)))
        glyph_set[name].draw(pen)
        glyphs[char] = [glyph_set[name].width, pen.getCommands()]
    hhea = font["hhea"]
    return {"units": font["head"].unitsPerEm, "ascent": hhea.ascent, "descent": hhea.descent, "glyphs": glyphs}


def main():
    FONTS_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        for name, (path, axes) in FONTS.items():
            file = Path(scratch) / f"{name}.ttf"
            file.write_bytes(fetch(BASE + path.replace("[", "%5B").replace("]", "%5D").replace(",", "%2C")))
            font = TTFont(file)
            if axes:
                font = instantiateVariableFont(font, axes)
            data = outlines(font)
            (FONTS_DIR / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            (FONTS_DIR / f"OFL-{name}.txt").write_bytes(fetch(BASE + path.split("/")[0] + "/OFL.txt"))
            print(f"{name}: {len(data['glyphs'])} characters")


if __name__ == "__main__":
    main()
