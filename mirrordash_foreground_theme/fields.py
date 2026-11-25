"""The boxes of one row in the Themes list: what the row's theme can be set to (ARCHITECTURE #63). The enums
differ per theme, so the module builds them from themes.py when the owner picks a theme in the row."""

from .greeting import FONTS, POSITIONS
from .themes import MODES, MOTIONS, THEMES, default

DAYS = {"easter": "Palm Sunday to Easter Monday", "midsummer": "Midsummer Eve to Sunday",
        "birthdays": "On the birthdays under Birthdays"}


def choice(title: str, options: dict, chosen: str, description: str = "", help: str = "") -> dict:
    """An enum field from {key: title} or {key: (title, ...)}; `help` is the long text behind the info button."""
    field = {"type": "string", "title": title, "description": description}
    if help:
        field["help"] = help
    return field | {"default": chosen, "enum": list(options),
                    "enum_titles": [value[0] if isinstance(value, tuple) else value for value in options.values()]}


def slider(title: str, smallest: int, largest: int, step: int, value: int, description: str, unit: str = "") -> dict:
    field = {"type": "integer", "format": "slider", "title": title, "description": description, "default": value,
             "minimum": smallest, "maximum": largest, "step": step}
    return field | {"unit": unit} if unit else field


def days_of(key: str) -> str:
    """Where a theme's days come from, for a description."""
    days = THEMES[key].days
    return DAYS[days] if isinstance(days, str) else "On the days below (none: never)"


def theme_fields(key: str) -> dict:
    """The schema properties for one theme's row."""
    theme = THEMES[key]
    fields = {"all_year": {"type": "boolean", "title": "Show all year", "default": False,
                           "description": f"Otherwise by date: {days_of(key).lower()}."}}
    if isinstance(theme.days, tuple) or theme.days is None:
        start, end = theme.days or ("", "")
        by_date = {"all_year": [False]}  # the days matter only while it's not shown all year
        fields["start"] = {"type": "string", "title": "From", "default": start, "description": "MM-DD, e.g. 12-01.",
                           "show_if": by_date}
        fields["end"] = {"type": "string", "title": "To", "default": end, "description": "MM-DD; may be after New Year.",
                         "show_if": by_date}
    fields |= {
        "mode": choice("Movement", MODES, default(theme, "mode"),
                       "How the shapes move: in showers, all the time, or not at all.",
                       "Showers: half a minute that fades in and out, then nothing until the next one; best when the screen is "
                       "on for hours. All the time: moves while the screen is on; best when it only lights up when someone "
                       "comes. Still: never moves."),
        "variant": choice("Shapes", theme.variants, default(theme, "variant")),
        "palette": choice("Colours", theme.palettes, default(theme, "palette")),
        "motion": choice("Motion", {name: MOTIONS[name] for name in theme.motions}, default(theme, "motion"),
                         "How the shapes move. Those marked heavy draw each shape on its own: best with Showers."),
        "amount": slider("How many", 1, 10, 1, default(theme, "amount"),
                         "Fewer are calmer; above 4 a second layer is drawn (with wind, never: the Pi's GPU memory)."),
        "size": slider("Size", 50, 200, 10, default(theme, "size"), "How large the shapes are.", "%"),
        "brightness": slider("Brightness", 10, 100, 5, default(theme, "brightness"), "How bright the shapes are.", "%"),
        "speed": slider("Speed", 25, 300, 25, default(theme, "speed"),
                        "Faster makes the Pi draw more often while it moves.", "%"),
    }
    if theme.drift:
        fields["drift"] = {"type": "boolean", "title": "Snowdrift", "default": True,
                           "description": "A low drift along the bottom edge. It never moves."}
    if theme.days == "birthdays":
        fields["greeting_at"] = choice("Where the text is", POSITIONS, "quarter", "The greeting stays all day.")
        fields["font"] = choice("Font", FONTS, "inter")
    return fields
