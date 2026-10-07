# Art to-do (the owner's notes, 2026-10-07)

Read this together with `docs/art-notes.md` (how the art is made) and
`docs/HANDOFF.md`. Every theme has a "wow" picture for the revamp style,
built from a scene in `tools/art_wow.py` (the first six),
`tools/art_wow2.py`, `tools/art_wow3.py` or `tools/art_wow4.py`. These
are the owner's notes on them, to work through in this order.

## How to work on a picture
1. Edit its scene function (search the WOW / MORE dicts for the picture
   name; `minitype/terminal/art.py` THEME_ART maps theme -> picture).
2. Preview it as a PNG with exact block shapes: `wow_png.py` (kept in the
   Claude scratchpad; it is easy to rewrite: render with
   `art_combined.render(scene, 28, pal)` and paint each cell's
   fg/bg with the glyph's coverage). Browser HTML previews smear because
   block characters fall back to other fonts.
3. Build it into the app: `python tools/make_revamp.py <picture> [...]`
   (rewrites `minitype/terminal/art_revamp.py`; about 10 s a picture).
4. `python tests/run_all.py` - `revamp_check.py` fails if a picture marks
   too much as its subject (focus): only the subject may be focus, never
   a full-height or full-width band, and some row must have no focus.

## 1. Redesigns (the owner didn't like these)
- **amber** (picture `monitor`): an actual piece of amber with a small
  T-rex trapped inside, on a dark background, light shining through the
  amber from behind - "like the movies".
- **solarized** (`sun`): needs a full redesign.
- **monokai** (`code`): not an editor window. Code-themed in monokai's
  colours, closer to matrix-style falling code.
- **rose pine** (`rose`): an actual, realistic rose (layered petals).
- **party** (`party`): balloons in the sky instead of the disco ball,
  and a pinker palette - like the Party Girl / party centre in Terraria.
  (The palette lives in the theme, `minitype/terminal/style.py` / the
  theme list; change it there.)
- **phosphor** (`terminal`): an actual terminal, with sharper lines.

## 2. Polish
- **moss** (`stones`): more detail on the rocks themselves; vines on
  every other tree; brush / grass coming up around the tree trunks.
- **pine** (`pine`): the rocky island under the pines cuts off too
  sharply - soften its edges.
- **autumn** (`leaf`): make the leaf's stem more visible.
- **jungle** (`jungle`): more trees and vines; keep the leaves as they are.
- **cherry blossom** (`blossom`): a more detailed tree, and the blossom
  far more scattered - it reads as one solid colour now.
- **lavender** (`lavender`): a more complex, realistic tree (leaves
  scattered, branches showing).
- **coral reef** (`reef`): add a clownfish and a jellyfish.
- **aurora** (`aurora`): a bit more fidelity.
- **deep sea** (`jellyfish`): more colourful jellyfish.
- **nord** (`mountains`): the foot of the mountain cuts off too sharply.
- **gruvbox** (`coffee`): remove the window, keep just the mug.
- **rainbow** (`rainbow`): too dead - livelier.
- **bubbly** (`bubbles`): remove the green.
- **synthwave** (`grid`): the car needs more fidelity.

## Leave as they are (the owner likes them)
sunset, desert (cactus), meadow (flowers), tundra (snowpeaks), bamboo,
summit, dracula (bat), catppuccin (cat), matrix (rain), paper (plane),
glitch, vaporwave (palm - the combined sunset reused) and the first six
(island, moon, pines, fire, keyboard, lollipop).

## The owner's taste, in short
Loves the vaporwave combined sky and the deep sea picture. Wants
pictures that make people go "wow": dense, detailed, colourful, built
from shades (░▒▓), eighths, quadrants and braille - not thin outlines.
