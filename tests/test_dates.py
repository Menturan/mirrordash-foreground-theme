from datetime import date

import pytest

from mirrordash_foreground_theme import dates
from mirrordash_foreground_theme.settings import all_theme_settings


@pytest.mark.parametrize("year,sunday", [(2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28)),
                                         (2038, date(2038, 4, 25)), (2008, date(2008, 3, 23))])
def test_easter(year, sunday):
    assert dates.easter(year) == sunday


@pytest.mark.parametrize("year,eve", [(2025, date(2025, 6, 20)), (2026, date(2026, 6, 19)), (2027, date(2027, 6, 25))])
def test_midsummer_eve_is_the_friday_from_19_to_25_june(year, eve):
    assert dates.midsummer_eve(year) == eve


@pytest.mark.parametrize("day,theme", [
    (date(2026, 12, 1), "snow"), (date(2027, 1, 6), "snow"), (date(2026, 12, 31), "newyear"), (date(2027, 1, 1), "newyear"),
    (date(2027, 2, 14), "hearts"), (date(2027, 4, 20), "petals"), (date(2026, 10, 28), "halloween"),
    (date(2026, 10, 1), "leaves"), (date(2026, 11, 15), "leaves"), (date(2026, 3, 29), "easter"), (date(2026, 4, 6), "easter"),
    (date(2026, 6, 21), "midsummer"), (date(2027, 1, 7), None), (date(2026, 7, 1), None),
])
def test_by_date_the_theme_of_the_season_and_nothing_between(day, theme):
    assert dates.theme_of(day, all_theme_settings({})) == theme


def test_the_owner_moves_a_period_or_turns_a_theme_off():
    moved = all_theme_settings({"leaves": {"start": "10-01", "end": "10-20"}})
    assert dates.theme_of(date(2026, 9, 25), moved) is None and dates.theme_of(date(2026, 10, 5), moved) == "leaves"
    off = all_theme_settings({"snow": {"by_date": False}})
    assert dates.theme_of(date(2026, 12, 20), off) is None
    stars = all_theme_settings({"stars": {"start": "07-01", "end": "07-31"}})  # no days of its own: the owner's
    assert dates.theme_of(date(2026, 7, 10), stars) == "stars"


def test_a_birthday_wins_over_the_season_and_29_february_comes_every_year():
    settings = all_theme_settings({"birthday": {"people": [{"name": "Anna", "date": "12-20"}, {"name": "Leo", "date": "2016-02-29"}]}})
    assert dates.theme_of(date(2026, 12, 20), settings) == "birthday"
    assert dates.birthday_names(date(2027, 2, 28), settings["birthday"].people) == ["Leo"]  # not a leap year
    assert dates.birthday_names(date(2028, 2, 28), settings["birthday"].people) == []  # a leap year: the 29th
