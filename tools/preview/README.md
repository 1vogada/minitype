# Preview tools (judge the art by eye)

PNG previews that draw block, shade and braille glyphs exactly. Browser and
HTML previews smear them through font fallback. Letters show as blobs, so
for text the owner's terminal is the ground truth. These are pure Python,
and they write their PNGs without any image library. Run them from the
repo root with `PYTHONIOENCODING=utf-8`. `SCALE` sets the pixels per glyph
grid cell (1 or 2). `MT_ROOT` sets the checkout to render, and defaults to
this one, so you can use it to render an agent's worktree.

| script | what | example |
|---|---|---|
| `wip.py` | scenes straight from `tools/art_wow*.py`, in their own theme (no rebuild needed) | `python tools/preview/wip.py out.png grid cactus` (env `ROWS=28`) |
| `ext_png.py` | a scene with its drawn extension above and to the left | `PYTHONPATH=".;tools" python tools/preview/ext_png.py out.png grid` |
| `tc_vs.py` | revamp vs truecolour (upscaled), one under the other | `PYTHONPATH=".;tools" LAST=110 python tools/preview/tc_vs.py out.png island` |
| `apppng.py` | pictures as the app stores and paints them | `python tools/preview/apppng.py out.png synthwave:revamp "deep sea:upscaled:2"` |
| `screen_png.py` | the whole main menu screen at a window size, from the app's real output | `PYTHONPATH=. python tools/preview/screen_png.py out.png 120 32 synthwave fade_on=0 art_style=upscaled` |
| `help_look.py` | the settings screen as text, with the help box anywhere | `PYTHONPATH=. python tools/preview/help_look.py 110 26 "top left" rounded panel enter` |

Notes:

- `wip.py` and `ext_png.py` build each scene with its own theme's palette,
  as `make_revamp.build_wow` does: `Palette(make(Palette("default")).theme)`.
- An older `mt_sheet.py` that went round between sessions used the default
  palette unless `THEME` was set, so its colours were wrong.
- `screen_png.py` with a fresh profile has the art fade on. Pass `fade_on=0`
  to see the art itself.
