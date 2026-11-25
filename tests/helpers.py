from mirrordash_foreground_theme.themes import THEMES


def config(theme=None, people=None, **per_theme) -> dict:
    """A module's settings with the Themes list built from a theme's settings per keyword, as the old config was:
    `theme="leaves"` shows only that one all year; else the default list (themes with days), in THEMES' order,
    plus the keyword's themes, each with its settings (`people` is the top-level birthdays)."""
    if theme:
        rows = [{"theme": theme, "enabled": True, "settings": {"all_year": True} | per_theme.get(theme, {})}]
    else:
        rows = [{"theme": key, "enabled": True, "settings": per_theme.get(key, {})}
                for key, spec in THEMES.items() if spec.days or key in per_theme]
    return {"themes": rows, "people": people or []}
