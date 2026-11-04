"""Which theme a day has: fixed periods the owner may change, Easter and Midsummer (they move), and birthdays."""

from datetime import date, timedelta

from .themes import THEMES


def in_period(day: date, start: str, end: str) -> bool:
    """Whether day is within start..end, given as MM-DD, also across New Year (12-01..01-06)."""
    first, last = (tuple(int(part) for part in text.split("-")) for text in (start, end))
    today = (day.month, day.day)
    return first <= today <= last if first <= last else today >= first or today <= last


def easter(year: int) -> date:
    """Easter Sunday (the anonymous Gregorian algorithm, Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    weekday = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * weekday) // 451
    month, day = divmod(h + weekday - 7 * m + 114, 31)
    return date(year, month, day + 1)


def midsummer_eve(year: int) -> date:
    """Swedish Midsummer Eve: the Friday from 19 to 25 June."""
    june19 = date(year, 6, 19)
    return june19 + timedelta(days=(4 - june19.weekday()) % 7)


def birthday_today(day: date, birthday: str) -> bool:
    """Whether day is the birthday (MM-DD or YYYY-MM-DD); 29 February is kept on the 28th in other years."""
    month_day = birthday[-5:]
    leap = day.year % 4 == 0 and (day.year % 100 != 0 or day.year % 400 == 0)
    return month_day == day.strftime("%m-%d") or (month_day == "02-29" and not leap and (day.month, day.day) == (2, 28))


def holds(key: str, settings, day: date) -> bool:
    """Whether a theme's days hold day, by its settings (settings.ThemeSettings)."""
    if not settings.by_date:
        return False
    rule = THEMES[key].days
    if rule == "easter":
        sunday = easter(day.year)
        return sunday - timedelta(days=7) <= day <= sunday + timedelta(days=1)  # Palm Sunday to Easter Monday
    if rule == "midsummer":
        eve = midsummer_eve(day.year)
        return eve <= day <= eve + timedelta(days=2)  # the eve to Sunday
    if rule == "birthdays":
        return any(birthday_today(day, person["date"]) for person in settings.people)
    return bool(settings.start and settings.end) and in_period(day, settings.start, settings.end)


def theme_of(day: date, settings: dict) -> str | None:
    """The theme of the day: the first in THEMES whose days hold it, None outside every season."""
    return next((key for key in THEMES if holds(key, settings[key], day)), None)


def birthday_names(day: date, people: list[dict]) -> list[str]:
    return [person["name"] for person in people if person["name"] and birthday_today(day, person["date"])]
