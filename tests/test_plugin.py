import re
import time
from datetime import date
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

import pytest

from mirrordash_foreground_theme import plugin
from mirrordash_foreground_theme.plugin import ForegroundThemeModule


def make_module(today=date(2026, 12, 20), **settings):
    """The module as the mirror sets it up, its date fixed, with the template replaced by what it gets."""
    module = ForegroundThemeModule(settings)
    module.render_template = MagicMock(side_effect=lambda name, **context: context)
    module.today = lambda: today
    return module


@pytest.mark.parametrize("day,theme", [
    (date(2026, 12, 1), "snow"), (date(2027, 1, 6), "snow"), (date(2026, 12, 31), "newyear"),
    (date(2027, 1, 1), "newyear"), (date(2027, 2, 14), "hearts"), (date(2027, 4, 20), "petals"),
    (date(2026, 10, 28), "halloween"), (date(2026, 10, 1), "leaves"), (date(2026, 11, 15), "leaves"),
    (date(2027, 1, 7), None), (date(2026, 7, 1), None),
])
def test_by_date_the_theme_of_the_season_and_nothing_between(day, theme):
    assert plugin.theme_of(day) == theme


@pytest.mark.asyncio
async def test_out_of_season_the_card_is_empty_but_a_chosen_theme_shows_all_year():
    assert await make_module(today=date(2026, 7, 1)).render() == ""
    assert (await make_module(today=date(2026, 7, 1), theme="leaves").render())["layers"]
    assert (await make_module(today=date(2026, 7, 1), preview=True).render())["layers"]  # the admin page's preview


@pytest.mark.asyncio
async def test_each_theme_draws_its_own_shapes_and_colours_in_light_tones():
    for theme, spec in plugin.THEMES.items():
        shown = await make_module(theme=theme, amount="heavy").render()
        assert len(shown["layers"]) == 3
        svg = unquote(shown["layers"][0]["image"])
        assert all(color in spec["colors"] for color in re.findall(r'fill="(#[0-9a-f]{6})"', svg))
        assert shown["rising"] == (spec["direction"] < 0)
    assert (await make_module(theme="snow").render())["drift"] is True
    assert (await make_module(theme="leaves").render())["drift"] is False  # a drift is snow's


@pytest.mark.asyncio
async def test_the_html_stays_the_same_until_something_changes():
    """The mirror redraws only changed HTML: the same shapes every round, so a still screen draws nothing."""
    first, second = await make_module(mode="still").render(), await make_module(mode="still").render()
    assert first["layers"] == second["layers"] and first["moving"] is False


@pytest.mark.asyncio
async def test_a_little_normal_or_a_lot():
    assert [len((await make_module(amount=amount).render())["layers"]) for amount in ("light", "normal", "heavy")] == [1, 2, 3]


@pytest.mark.asyncio
async def test_showers_come_when_someone_arrives_and_now_and_then_and_stop():
    module = make_module(shower_every=15)
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


@pytest.mark.asyncio
async def test_all_the_time_or_still():
    assert (await make_module(mode="falling").render())["moving"] is True
    still = make_module(mode="still")
    still.on_motion({"motion": True})
    assert (await still.render())["moving"] is False


def test_it_listens_for_the_motion_sensor():
    bus = MagicMock()
    module = ForegroundThemeModule({"event_bus": bus})
    bus.subscribe.assert_called_once_with("hardware.motion", module.on_motion)
