import json

from mirrordash_foreground_theme import schema
from mirrordash_foreground_theme.shapes import SHAPES_DIR, SIZES
from mirrordash_foreground_theme.themes import THEMES


def test_config_schema_json_is_written_from_themes_py():
    """The mirror reads the file, not the code: run `uv run python -m mirrordash_foreground_theme.schema`."""
    assert schema.SCHEMA_FILE.read_text() == schema.text()


def test_every_theme_has_a_block_with_its_choices():
    properties = json.loads(schema.text())["properties"]
    for key, theme in THEMES.items():
        block = properties[key]["properties"]
        assert block["variant"]["enum"] == list(theme.variants) and block["motion"]["enum"] == list(theme.motions)
        assert block["amount"]["minimum"] == 1 and block["amount"]["maximum"] == 10  # a slider
    assert "heavy" in properties["leaves"]["properties"]["motion"]["enum_titles"][3]  # the warning shows


def test_every_shape_a_theme_uses_has_a_file_and_a_size():
    used = {shape for theme in THEMES.values() for _, shapes in theme.variants.values() for shape in shapes}
    assert used <= set(SIZES)
    assert all((SHAPES_DIR / f"{name}.svg").exists() for name in SIZES)
