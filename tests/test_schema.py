import json

from mirrordash_foreground_theme import schema
from mirrordash_foreground_theme.fields import theme_fields as fields_of
from mirrordash_foreground_theme.shapes import SHAPES_DIR, SIZES
from mirrordash_foreground_theme.themes import THEMES


def test_config_schema_json_is_written_from_themes_py():
    """The mirror reads the file, not the code: run `uv run python -m mirrordash_foreground_theme.schema`."""
    assert schema.SCHEMA_FILE.read_text() == schema.text()


def test_one_list_of_themes_with_boxes_a_row_gets_from_the_module():
    properties = json.loads(schema.text())["properties"]
    row = properties["themes"]["items"]
    assert properties["themes"]["type"] == "array" and row["title"] == "Theme"
    assert row["properties"]["theme"]["enum"] == list(THEMES) and row["properties"]["settings"]["format"] == "fields"
    assert [r["theme"] for r in properties["themes"]["default"]] == [key for key, theme in THEMES.items() if theme.days]
    assert properties["people"]["type"] == "array" and properties["shower_every"]["unit"] == "min"
    assert not any(key in properties for key in ("theme", *THEMES))  # no per-theme blocks any more
    for key, theme in THEMES.items():
        fields = fields_of(key)
        assert fields["variant"]["enum"] == list(theme.variants) and fields["motion"]["enum"] == list(theme.motions)
        assert fields["amount"]["minimum"] == 1 and fields["amount"]["maximum"] == 10  # a slider
        assert all(fields[name]["unit"] == "%" and "(%)" not in fields[name]["title"] for name in ("size", "brightness", "speed"))
    assert "heavy" in fields_of("leaves")["motion"]["enum_titles"][3]  # the warning shows


def test_every_shape_a_theme_uses_has_a_file_and_a_size():
    used = {shape for theme in THEMES.values() for _, shapes in theme.variants.values() for shape in shapes}
    assert used <= set(SIZES)
    assert all((SHAPES_DIR / f"{name}.svg").exists() for name in SIZES)
