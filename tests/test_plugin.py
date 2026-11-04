import base64
import re
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from mirrordash_foreground_theme import plugin, tiles
from mirrordash_foreground_theme.plugin import ForegroundThemeModule
from mirrordash_foreground_theme.themes import THEMES


def make_module(today=date(2026, 12, 20), **settings):
    """The module as the mirror sets it up, its date fixed, with the template replaced by what it gets."""
    module = ForegroundThemeModule(settings)
    module.render_template = MagicMock(side_effect=lambda name, **context: context)
    module.today = lambda: today
    return module


def tile_svg(layer: dict) -> str:
    return base64.b64decode(re.search(r"base64,([^']+)'", layer["image"])[1]).decode()


@pytest.mark.asyncio
async def test_out_of_season_the_card_is_empty_but_a_chosen_theme_shows_all_year():
    assert await make_module(today=date(2026, 7, 1)).render() == ""
    assert (await make_module(today=date(2026, 7, 1), theme="leaves").render())["layers"]
    assert (await make_module(today=date(2026, 7, 1), preview=True).render())["layers"]  # the admin page's preview


@pytest.mark.asyncio
async def test_each_theme_and_variant_draws_its_shapes_in_its_colours():
    for key, theme in THEMES.items():
        for variant, (_, shapes) in theme.variants.items():
            for palette, (_, colors) in theme.palettes.items():
                shown = await make_module(theme=key, **{key: {"variant": variant, "palette": palette, "motion": theme.motions[0], "amount": 7}}).render()
                if not shown["layers"]:
                    continue  # twinkle draws its layers dimmer, but still draws them; one by one has none
                svg = tile_svg(shown["layers"][0])
                assert set(re.findall(r'fill="(#[0-9a-f]{6})"', svg)) <= set(colors)
                assert svg.count("<symbol") == len(shapes)
    assert (await make_module(theme="halloween", halloween={"variant": "ghosts"}).render())["rising"] is True
    assert (await make_module(theme="snow").render())["drift"] is True
    assert (await make_module(theme="leaves").render())["drift"] is False  # a drift is snow's


@pytest.mark.asyncio
async def test_how_many_how_large_and_how_fast():
    def count(amount):
        return sum(tile_svg(layer).count("<use") for layer in tiles_of(amount))

    def tiles_of(amount):
        return [tiles.layer("leaves", make_module(leaves={"amount": amount}).settings["leaves"], i) for i in tiles.layers_for(amount)]

    assert [len(tiles.layers_for(a)) for a in (1, 3, 4, 6, 7, 10)] == [1, 1, 2, 2, 3, 3]
    assert count(1) < count(2) < count(5) < count(10)
    slow, fast = (make_module(leaves={"speed": speed}).settings["leaves"] for speed in (50, 200))
    assert tiles.layer("leaves", slow, 1)["seconds"] == 4 * tiles.layer("leaves", fast, 1)["seconds"]
    def largest(size):
        settings = make_module(leaves={"size": size}).settings["leaves"]
        return max(float(scale) for scale in re.findall(r"scale\(([\d.]+)\)", tile_svg(tiles.layer("leaves", settings, 1))))

    assert largest(200) == pytest.approx(4 * largest(50), rel=0.05)


@pytest.mark.asyncio
async def test_one_by_one_draws_a_few_shapes_of_their_own_and_no_layers():
    shown = await make_module(theme="leaves", leaves={"motion": "spin_each", "amount": 10}).render()
    assert shown["layers"] == [] and len(shown["singles"]) == tiles.EACH_LIMIT  # never more, whatever the amount
    assert 'id="fg-0"' in shown["symbols"]
    stars = await make_module(theme="stars").render()
    assert stars["layers"] and 0 < len(stars["singles"]) <= tiles.TWINKLE_LIMIT


@pytest.mark.asyncio
async def test_the_html_stays_the_same_until_something_changes():
    """The mirror redraws only changed HTML: the same shapes every round, so a still screen draws nothing."""
    first, second = [await make_module(snow={"mode": "still"}).render() for _ in range(2)]
    assert first["layers"] == second["layers"] and first["moving"] is False


@pytest.mark.asyncio
async def test_showers_follow_the_theme_of_the_day():
    module = make_module(shower_every=15)  # snow, now and then
    assert (await module.render())["moving"] is False
    module.on_motion({"motion": True, "sensor": "pir"})
    assert module.changed.is_set() and (await module.render())["moving"] is True
    with patch.object(plugin.time, "monotonic", return_value=time.monotonic() + plugin.SHOWER_SECONDS + 1):
        assert (await module.render())["moving"] is False
    with patch.object(plugin.time, "monotonic", return_value=time.monotonic() + 15 * 60 + 1):
        assert (await module.render())["moving"] is True  # by itself, every 15 minutes
    quiet = make_module(shower_on_arrival=False)
    quiet.on_motion({"motion": True})
    assert (await quiet.render())["moving"] is False
    assert (await make_module(snow={"mode": "falling"}).render())["moving"] is True
    still = make_module(snow={"mode": "still"})
    still.on_motion({"motion": True})
    assert (await still.render())["moving"] is False


@pytest.mark.asyncio
async def test_the_birthday_greeting_names_whoever_has_their_birthday():
    people = [{"name": "Anna", "date": "12-20"}, {"name": "Åsa", "date": "12-20"}, {"name": "Leo", "date": "01-02"}]
    module = make_module(birthday={"people": people, "font": "pacifico", "greeting_at": "golden"})
    module.translate = lambda key, default: {"birthday": "Grattis {names}!", "and": "och"}[key]
    shown = await module.render()
    assert 'aria-label="Grattis Anna och Åsa!"' in shown["greeting"]["svg"] and shown["greeting"]["top"] == 38.2
    assert shown["greeting"]["svg"].count("<path") == len("GrattisAnnaochÅsa!")  # a path per letter, no font to load
    hidden = make_module(birthday={"people": people, "greeting_at": "none"})
    assert (await hidden.render())["greeting"] is None
    bottom = make_module(birthday={"people": people, "greeting_at": "bottom"})
    assert (await bottom.render())["greeting"]["top"] is None
    assert (await make_module().render())["greeting"] is None  # snow: no text


def test_a_letter_the_font_lacks_is_drawn_without_its_accent():
    from mirrordash_foreground_theme.greeting import glyph
    glyphs = {"a": [500, "M0 0Z"], "?": [400, "M1 1Z"]}
    assert glyph(glyphs, "á") == glyphs["a"] and glyph(glyphs, "☃") == glyphs["?"]


def test_it_listens_for_the_motion_sensor():
    bus = MagicMock()
    module = ForegroundThemeModule({"event_bus": bus})
    bus.subscribe.assert_called_once_with("hardware.motion", module.on_motion)
