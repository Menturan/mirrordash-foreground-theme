from mirrordash_foreground_theme.settings import month_day, theme_settings


def test_each_theme_has_its_own_defaults():
    leaves, snow = theme_settings("leaves", None), theme_settings("snow", {})
    assert (leaves.amount, leaves.size, leaves.motion, leaves.variant) == (2, 160, "sway", "mixed")  # few and large
    assert (snow.amount, snow.size, snow.drift) == (5, 100, True)
    stars = theme_settings("stars", {})
    assert stars.by_date and not stars.start  # no days of its own: never by date until the owner gives some


def test_whatever_is_unknown_or_out_of_range_falls_back():
    odd = theme_settings("leaves", {"variant": "palm", "motion": "twinkle", "amount": "99", "size": -5, "speed": "fast",
                                    "start": "13-40", "mode": "<b>"})
    assert (odd.variant, odd.motion, odd.amount, odd.size, odd.speed, odd.mode) == ("mixed", "sway", 10, 50, 100, "showers")
    assert odd.start is None  # a day that isn't one: the period is off, not wrong
    assert theme_settings("rain", {"motion": "sway_each"}).motion == "straight"  # rain only falls straight or slanting


def test_birthdays_keep_only_real_days():
    people = theme_settings("birthday", {"people": [{"name": "Anna", "date": "03-14"}, {"name": "X", "date": "02-30"},
                                                    {"name": "Leo", "date": "2016-02-29"}, "junk"]}).people
    assert people == ({"name": "Anna", "date": "03-14"}, {"name": "Leo", "date": "02-29"})
    assert month_day(" 12-01 ") == "12-01" and month_day("1-1") is None
