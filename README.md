# mirrordash-foreground-theme

Seasonal decoration over your [MirrorDash](https://github.com/Menturan/MirrorDash) mirror: snow, New Year,
Easter, Midsummer, Halloween, autumn leaves, birthdays and more, each theme with its own shapes, colours and
motion. Put it in the **Foreground** position (MirrorDash 0.12 or newer): it lies over the whole screen, in
front of the other modules.

![Snow over a photo and the clock](screenshot.png)

## Themes

![The themes](themes.png)

| Theme | By date | Shapes |
| :--- | :--- | :--- |
| Birthday | On the birthdays you add, with *Happy birthday, Anna!* | Confetti, streamers, balloons (they rise) |
| New Year | 31 December – 1 January | Sparkles, stars, confetti |
| Easter | Palm Sunday – Easter Monday (worked out each year) | Feathers, eggs, tulips |
| Midsummer | Midsummer Eve – Sunday (worked out each year) | Flowers, butterflies, a meadow, birch leaves |
| Halloween | 25 – 31 October | Pumpkins, jack-o'-lanterns, ghosts, bats, embers |
| Snow, with a snowdrift | 1 December – 6 January | Fine snow, snowflakes, crystals |
| Hearts | 10 – 14 February | Hearts |
| Spring petals | April and May | Petals, cherry blossom, tulips |
| Autumn leaves | 20 September – 15 November | Maple, oak, birch, leaves and acorns |
| Stars | Your own days | A twinkling starry sky |
| Rain | Your own days | Rain, drops, drizzle |

**Theme: By date** (the default) shows the theme of the day, and nothing on other days: then the module draws
nothing at all. Where two themes' days meet, the one higher in the table wins. Or choose one theme to show
all year.

Only light shows on a two-way mirror (black is glass), so every theme is drawn in light colours.

## Each theme's settings

Each theme has a folding block of its own in the module's settings:

| Setting | |
| :--- | :--- |
| Show By Date, From, To | Whether By date shows it, and on which days (MM-DD; may run over New Year). Easter and Midsummer are worked out each year. |
| Movement | Now and then, All the time or Still (below) |
| Shapes, Colours | The theme's variants and palettes |
| Motion | Straight down, slanting as in wind, swaying, or swaying or spinning one by one |
| How Many, Size, Brightness, Speed | Sliders. Autumn leaves start few and large; snow many and small. |
| Snowdrift (snow) | A low drift along the bottom edge |
| Birthdays, Where the Text Is, Font (birthday) | Names and dates; the greeting a quarter down (the default), at the golden ratio, in the middle, at the bottom or not at all; in one of nine fonts |

## Movement, and what it costs

| Movement | |
| :--- | :--- |
| Now and then (default) | It moves for half a minute when the motion sensor sees someone at the mirror, and by itself every 15 minutes (*Minutes Between*); otherwise it stands still. |
| All the time | Keeps the Raspberry Pi drawing all day: it runs warmer, and a video playing beside it may stutter. |
| Still | Never moves. Costs nothing. |

| Motion | Cost while it moves |
| :--- | :--- |
| Straight down, slanting | Low: a layer moves a whole pixel at a time, so the Pi only draws when a shape has moved (about a quarter of a smooth animation's cost, measured on a Pi 3) |
| Swaying | Medium: the whole layer swings smoothly |
| Twinkling (stars) | Medium: up to 30 stars fade in and out |
| Swaying or spinning one by one | High: each shape (never more than 60) is an element of its own |

A higher **Speed** makes the Pi draw more often while it moves. While a module plays a video, the mirror hides the decoration altogether (MirrorDash after 0.12; older versions pause it).

All layers step at the same moments, 36 times a second, so the screen redraws only then. Each moving layer is a
texture in the GPU's memory, which a Raspberry Pi 3 has little of (about 40 MB free beside the other modules), so
the module never asks for more than 25 MB: one layer as high as the screen for a few shapes, two with half-screen
tiles for more (their pattern comes twice down the screen), and *Slanting* always one, its skewed layer being
wider. **How Many** fills the layers more densely instead.

## Shapes and fonts

The shapes are SVG files in `mirrordash_foreground_theme/shapes/`: silhouettes from
[Phosphor Icons](https://phosphoricons.com) (MIT) and [game-icons.net](https://game-icons.net) (CC BY 3.0, by
Lorc, Delapouite and Skoll), and a few simple shapes drawn for this module. Who made which, and the licenses:
[shapes/CREDITS.md](mirrordash_foreground_theme/shapes/CREDITS.md). Swap a file to change a shape.

The birthday fonts (Inter, Sacramento, Great Vibes, Dancing Script, Pacifico, Caveat, Amatic SC, Fredoka and
Lobster, all SIL Open Font License, their licenses in `fonts/`) are stored as outlines, so the greeting is drawn
as a shape and looks the same on the mirror and in the admin page's preview in any browser.

## Develop

```bash
uv run pytest                                          # the module's tests
uvx mirrordash-sdk validate .                          # checks the module before you push it
uv run python -m mirrordash_foreground_theme.schema    # writes config_schema.json after a change in themes.py
uv run --with fonttools python scripts/build_fonts.py  # rebuilds fonts/ (only when the fonts change)
```

Try it on a local mirror: see the [MirrorDash SDK](https://github.com/Menturan/mirrordash-sdk#quick-start).

| File | What it holds |
| :--- | :--- |
| `themes.py` | The themes as data: a new theme is one entry (its shapes in `shapes/`) |
| `dates.py` | Which theme a day has: periods, Easter, Midsummer, birthdays |
| `settings.py` | The owner's settings, checked and merged with each theme's defaults |
| `tiles.py` | How the shapes are drawn: screen-sized SVG layers, and the one-by-one shapes |
| `shapes.py`, `greeting.py` | The shapes, and the birthday text as an outline |
| `schema.py` | Writes `config_schema.json` from `themes.py` (a test fails when it's out of date) |
| `plugin.py` | The module: showers, the theme of the day, rendering |
