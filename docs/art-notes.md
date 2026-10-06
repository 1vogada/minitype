# Art notes (how the corner art is made)

## Styles and where they live
| style | made by | data | notes |
|---|---|---|---|
| revamp (default) | `tools/make_revamp.py` from `tools/revamp_art.py` | `minitype/terminal/art_revamp.py` | hand-drawn ASCII subject over scenery |
| blocks | `tools/make_art.py` (`artgen.render_blocks`) from `tools/art_scenes.py` | `art_detailed.py` BLOCKS | quadrant blocks + braille |
| detailed | `tools/make_art.py` (`artgen.render`) | `art_detailed.py` DETAILED | shaded ASCII |
| combined | `tools/make_art.py` via `tools/art_combined.py` | `art_detailed.py` COMBINED | only `palm` (vaporwave) so far; others fall back to blocks |
| og | hand-written | `art_large.py`, `art.py` ART | fallback for every style |

`art.resolve(name, style)` picks the pieces; `Picture.wider()` grows spanning
scenery leftwards on wide screens (column quilting, `art._grow`).

## Combined (vaporwave) - how it was done
File: `tools/art_combined.py`. A scene is a **colour field**, not shapes:
`field(x, y) -> (rgb, alpha, focus, tag)`, plus `lines(rows)` (braille
polylines) and `texts(...)` (stars, reflection streaks). Coordinates: y 0
top .. 1 bottom, x to the aspect; cells are half as wide as tall.

Renderer: each cell sampled 4 across x 8 down in the THEME'S REAL RGB
(`Palette(theme)` reads `Styles(theme).art_palette(True)`: 7 parts x 10
tones + the ground/background). Per cell it picks the closest of:
- solid colour `█` (or blank = ground)
- two colours mixed by a shade `░ ▒ ▓` (25/50/75%) - smooth gradients;
  costs `SHADE_COST` extra so it's only used when clearly better
- an edge: quadrants `▘▝▖▗▚▞▙▛▜▟▀▄▌▐`, eighths `▁▂▃▅▆▇▔`, `▎▊▕`
  (fg = nearest non-ground colour of the covered part, bg = the rest);
  only tried when the cell's samples vary
- braille dots for `lines` (fg = line colour, bg = cell's mean colour)
- text glyphs for `texts`
Floor cells skip shades (they read as grey grit).

KEY TRICK: build every gradient with `pal.path("a0 a1 x1 x2 x3 e3 e4 x5")`
- a ramp running from one palette colour to the next (`"-"` = ground).
Every point then lies between two real theme colours, so the shades draw it
exactly: no blotches. Free RGB gradients came out blotchy (nearest-colour
jumping between hues).

Vaporwave scene choices that worked: indigo->violet->magenta sky fading into
the ground at the box's left/top edge (alpha = smoothstep); stars as text;
sun cream->pink (`pal.path("w9 w7 w6 e7 e6 e5")`) with stripes in its lower
half widening downward (eighths make them crisp); mountains in purples with
a pink braille ridge line; palms as SOLID silhouettes in the ground colour
with a pink rim light on the sun side, fronds as arching curves (rise then
droop) with sawtooth leaflets as shapes - not braille fringes (fg can't be
the ground colour, so dark braille comes out grey); grid floor in braille,
verticals only near the picture and starting where they're >= 8 dots apart;
`~ - =` reflection streaks under the sun.

Build: `python tools/make_art.py --combined palm` (prints), and to store only
the combined data without touching blocks/detailed:
```
python -c "import sys; sys.path.insert(0,'tools'); import make_art as m; d,b,c=m.load(); c['palm']=m.build_combined('palm'); m.write(d,b,c)"
```
(A full `make_art.py palm` rebuild changed one row of the old blocks palm -
avoid unrelated churn.) Preview by rendering cells to HTML in the theme's
RGB and viewing it in a browser.

## Revamp "wow" pictures (tools/art_wow.py) - the new direction
In three sizes (28, 22, 16 rows - the app draws the biggest that fits;
one size alone never showed in a 30-row window), built with the combined renderer
(`tools/art_combined.py`) and stored as revamp art by `make_revamp.py`
(`build_wow`); themes without one still use the hand-drawn picture.
Done so far: island (ocean), moon (midnight), pines (forest), fire (ember),
keyboard (default). Shared helpers: `ridge`, `pine`, `palm`, `sphere_light`,
`stars`. Lessons:
- Only the SUBJECT may be focus (sun, palm, moon, fire, keyboard). Sky,
  sea and ground must be focus=False, or a 28-row picture never fits
  beside the menu and the app falls back to og.
- Gradients along `pal.path(...)` (palette colours) - never free RGB.
- `Scene(inks={tag: "letters"})` limits which palette colours an area may
  use (a dark grey room drifted to dark green / red without it).
- Colour distance is brightness + chroma (`dist`), not weighted RGB.
- Silhouettes: when a cell's covered part is the ground colour, the
  encoder uses the COMPLEMENT glyph (fg = the other part, bg = ground) -
  otherwise thin dark shapes (palm trunks) vanish.
- Gaps between shapes (keycaps) must be wider than a cell or they merge.
- Preview: `wow_preview.py` (scratchpad) renders to HTML; block glyphs
  fall back to wider fonts in the browser, so ragged right edges there
  are a preview artifact, not the art.

User feedback (2026-10-06): loves the vaporwave combined BACKGROUND (the
shaded gradient sky) and the DEEP SEA picture; asked for more ░▒▓
shading (wow scenes now use shade_cost 60 vs 250); candy should be
"bubblegum pop": a bow-tie wrapped sweet, pink all over (done).
Done so far: island, moon, pines, fire, keyboard, lollipop (candy).

## Revamp (hand-drawn) - how it was done
`tools/revamp_art.py`: `picture(name, text, colours=..., tones=..., paint=,
shade=, ground=, tile=, below=, solid=, tile_under=)`. Blanks enclosed by the
drawing are made opaque automatically (flood fill); `§` forces opaque;
`solid=True` fills each row first..last char. `ground` = artgen items for
scenery (default: the scene's non-focus parts), `tile` = hand-drawn strip
repeated across the bottom (shared GRASS / FERNS / SNOW). Scenery is drawn
by `tools/artgen_ascii.py`: shape-matched ASCII using glyph coverage measured
from the font (`tools/glyphs.py` reads Consolas/Cascadia -> `glyph_shapes.json`),
4x8 patches, blur-tolerant matching, lines picked by direction pool then
by height in the cell (`_ - ¯`, `/ | \`). Interiors keep material texture;
edges matched only where coverage < 60%.

User verdict: revamp line art is "not that good" - NEXT: redo with the
"wow" of pixel/braille art (blocks/combined techniques), ~26-30 rows tall.

## Pitfalls
- Writing art through shell heredocs mangles `\` and quotes: write scripts
  to files. In Python raw strings, a line ending in `\` before `"""` breaks.
- Tiles must have even width when glyphs are every other column.
- A blank after a background-coloured cell must get its own code
  (`Picture.row`), or backgrounds run on as bars.
- Test scripts live outside the repo (Claude scratchpad, copied to
  `C:\Claude 2\claude\...\scratchpad`); 24 of them, each prints ALL OK.
