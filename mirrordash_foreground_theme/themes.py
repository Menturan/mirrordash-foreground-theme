"""The themes, as data: a new theme is one entry here (and its shapes in shapes/). Only light shows on a mirror
(black is glass), so every palette is light. The order of THEMES is who wins where two themes' days overlap."""

from dataclasses import dataclass, field

# Motions: their titles in the admin page say which ones cost the Raspberry Pi more while they move
MOTIONS = {
    "straight": "Straight down",
    "wind": "Slanting, as in wind",
    "sway": "Swaying (the whole layer; uses more while it moves)",
    "sway_each": "Swaying one by one (heavy for the Pi)",
    "spin_each": "Spinning one by one (heavy for the Pi)",
    "twinkle": "Twinkling (uses more while it moves)",
}
STANDARD_MOTIONS = ("straight", "wind", "sway", "sway_each", "spin_each")
MODES = {"showers": "Now and then", "falling": "All the time", "still": "Still"}


@dataclass(frozen=True)
class Theme:
    title: str
    variants: dict[str, tuple[str, tuple[str, ...]]]  # key -> (title, the shapes it draws)
    palettes: dict[str, tuple[str, tuple[str, ...]]]  # key -> (title, its colours)
    days: tuple[str, str] | str | None  # (MM-DD, MM-DD) the owner may change, "easter", "midsummer", "birthdays" or None
    defaults: dict = field(default_factory=dict)  # what differs from DEFAULTS
    motions: tuple[str, ...] = STANDARD_MOTIONS
    rising: tuple[str, ...] = ()  # the variants that rise instead of falling
    fast: bool = False  # rain: six times the speed
    drift: bool = False  # snow: a snowdrift along the bottom edge


DEFAULTS = {"mode": "showers", "motion": "straight", "amount": 4, "size": 100, "brightness": 80, "speed": 100}

THEMES = {
    "birthday": Theme(
        "Birthday",
        {"confetti": ("Confetti", ("confetti",)), "streamers": ("Confetti and streamers", ("confetti", "streamer")),
         "balloons": ("Balloons", ("balloon",)), "dots": ("Confetti and dots", ("confetti", "dot"))},
        {"party": ("Party", ("#ffe08a", "#ffb3c7", "#a8d8ff", "#c8f5b0", "#ffffff")),
         "gold": ("Gold", ("#ffe08a", "#fff3c4", "#ffffff")), "pastel": ("Pastel", ("#ffccd5", "#cceeff", "#e6ffd9", "#fff3c4"))},
        "birthdays", {"size": 110, "brightness": 85, "motion": "spin_each"}, rising=("balloons",)),
    "newyear": Theme(
        "New Year",
        {"sparkles": ("Sparkles", ("sparkle", "dot")), "stars": ("Stars", ("star", "dot")), "confetti": ("Confetti", ("confetti",))},
        {"festive": ("Festive", ("#ffe08a", "#ffffff", "#ffb3c7", "#a8d8ff")), "gold": ("Gold", ("#ffe08a", "#fff3c4", "#ffffff")),
         "silver": ("Silver", ("#ffffff", "#e0e0e0", "#cceeff"))},
        ("12-31", "01-01"), {"amount": 5}),
    "easter": Theme(
        "Easter",
        {"feathers": ("Feathers", ("feather",)), "eggs": ("Eggs", ("egg",)), "mixed": ("Mixed", ("feather", "egg", "tulip"))},
        {"yellow": ("Yellow", ("#ffe08a", "#fff3c4", "#ffd166")),
         "pastel": ("Pastel", ("#ffe08a", "#cceeff", "#ffccd5", "#d9f5c4")), "white": ("White", ("#ffffff", "#fff8e6"))},
        "easter", {"amount": 3, "size": 130, "motion": "sway"}),
    "midsummer": Theme(
        "Midsummer",
        {"flowers": ("Flowers", ("flower",)), "butterflies": ("Butterflies", ("butterfly",)),
         "meadow": ("Meadow", ("flower", "daisy", "butterfly", "grass")), "birch": ("Birch leaves", ("birch-leaf",))},
        {"meadow": ("Meadow", ("#ffffff", "#ffe08a", "#e0ccff", "#cceeff")), "white": ("White", ("#ffffff", "#fff8e6")),
         "green": ("Green", ("#c8f5b0", "#e6ffd9", "#ffffff"))},
        "midsummer", {"amount": 3, "size": 130, "motion": "sway"}),
    "halloween": Theme(
        "Halloween",
        {"mixed": ("Mixed", ("pumpkin", "ghost", "ghost-flying", "bat")), "pumpkins": ("Pumpkins", ("pumpkin",)),
         "lanterns": ("Jack-o'-lanterns", ("lantern",)), "ghosts": ("Ghosts", ("ghost", "ghost-flying")),
         "bats": ("Bats", ("bat",)), "embers": ("Embers", ("dot",))},
        {"halloween": ("Halloween", ("#ff9a3c", "#ffffff", "#c79bff", "#ffc36b")), "orange": ("Orange", ("#ff9a3c", "#ffc36b")),
         "purple": ("Purple and white", ("#c79bff", "#e0ccff", "#ffffff"))},
        ("10-25", "10-31"), {"amount": 2, "size": 180, "brightness": 85, "motion": "sway"}, rising=("ghosts", "embers")),
    "snow": Theme(
        "Snow",
        {"fine": ("Fine snow", ("dot",)), "flakes": ("Snowflakes", ("snowflake",)), "crystals": ("Crystals", ("crystal", "snowflake")),
         "simple": ("Simple flakes", ("simple-flake",)), "mixed": ("Mixed", ("dot", "snowflake", "crystal"))},
        {"white": ("White", ("#ffffff",)), "ice": ("Ice blue", ("#ffffff", "#cceeff", "#e6f6ff"))},
        ("12-01", "01-06"), {"amount": 5}, drift=True),
    "hearts": Theme(
        "Hearts",
        {"hearts": ("Hearts", ("heart",)), "dots": ("Hearts and dots", ("heart", "dot")), "simple": ("Simple hearts", ("simple-heart",))},
        {"pink": ("Pink", ("#ff8fb1", "#ffc2d4", "#ff6f91")), "red": ("Red", ("#ff6f91", "#ff8f8f", "#ffb3b3")),
         "white": ("White and pink", ("#ffffff", "#ffccd5"))},
        ("02-10", "02-14"), {"amount": 3, "size": 130, "motion": "sway"}),
    "petals": Theme(
        "Spring petals",
        {"petals": ("Petals", ("petal",)), "blossom": ("Cherry blossom", ("blossom",)), "tulips": ("Tulips", ("tulip",)),
         "mixed": ("Mixed", ("petal", "blossom", "flower"))},
        {"cherry": ("Cherry", ("#ffd6e5", "#fff0f5", "#f9b8cf")), "white": ("White", ("#ffffff", "#fff8e6")),
         "apricot": ("Apricot", ("#ffd9b3", "#ffe8cc", "#fff0f5"))},
        ("04-01", "05-31"), {"size": 110, "motion": "sway"}),
    "leaves": Theme(
        "Autumn leaves",
        {"mixed": ("Mixed", ("maple-leaf", "oak-leaf", "leaf", "acorn")), "classic": ("Leaves", ("leaf",)),
         "maple": ("Maple", ("maple-leaf",)), "oak": ("Oak", ("oak-leaf",)), "birch": ("Birch", ("birch-leaf",))},
        {"autumn": ("Autumn", ("#ff9a3c", "#ffcf5a", "#ff6b4a", "#e8b04a")), "gold": ("Gold", ("#ffcf5a", "#ffe08a", "#e8b04a")),
         "red": ("Red", ("#ff6b4a", "#ff8a5c", "#ff9a3c"))},
        ("09-20", "11-15"), {"amount": 2, "size": 160, "brightness": 85, "motion": "sway"}),
    "stars": Theme(
        "Stars",
        {"sky": ("Starry sky", ("twinkle", "dot")), "stars": ("Stars", ("star", "dot")), "dots": ("Just dots", ("dot",))},
        {"white": ("White", ("#ffffff",)), "warm": ("Warm", ("#fff3c4", "#ffffff")), "cold": ("Cold", ("#cceeff", "#ffffff"))},
        None, {"size": 90, "brightness": 70, "motion": "twinkle"}, motions=("twinkle", "straight")),
    "rain": Theme(
        "Rain",
        {"rain": ("Rain", ("rain",)), "drops": ("Drops", ("drop",)), "drizzle": ("Drizzle", ("drizzle",))},
        {"blue": ("Blue grey", ("#cceeff", "#a8c8e0", "#ffffff")), "white": ("White", ("#ffffff",))},
        None, {"brightness": 60}, motions=("straight", "wind"), fast=True),
}


def default(theme: Theme, key: str):
    """A theme's default for one of its settings: its own, else the first variant or palette, else DEFAULTS."""
    if key in theme.defaults:
        return theme.defaults[key]
    if key in ("variant", "palette"):
        return next(iter(theme.variants if key == "variant" else theme.palettes))
    return DEFAULTS[key]
