# Handoff: where minitype stands, and how to carry on

Read this first when picking the project up (you or an AI coding agent).
Then `docs/art-notes.md` for anything about the corner art.

## Pick up here (left off 2026-10-15)
The last long session ran on the owner's work laptop. Its chat and the
agent's memory don't travel, so this section is the memory.

**Do next, in order:**
1. **Finish the upscaled build.** Only 6 of 40 pictures are in truecolour:
   grid, island, keyboard, moon, pines and sunset. The other 34 still show
   their revamp picture in that style, which works but doesn't look
   upscaled. Run `python tools/make_art_upscaled.py -j<cores>` (pure
   Python, CPU-bound; it skips finished pictures and writes after each
   one, so it can be stopped and resumed). Then `python tests/run_all.py`,
   commit `minitype/terminal/art_upscaled.py` and push. It takes about 2
   hours on 4 cores. The owner meant to run it on their workstation.
2. **Settings menu: cascading pages (done 2026-10-16).** The owner wanted
   it like Serious Sam Fusion / BFE's options (menus inside menus), keeping
   the side tabs, and easy to extend. `minitype/ui/tree_menu.py` (Page,
   TreeMenu: a Menu over pages; each top page remembers how deep you are;
   rows ending in › open a page; esc / left go up) and
   `minitype/ui/settings_tree.py` (TREE: the whole grouping in one table;
   unplaced rows land in an "other" tab). Tabs: gameplay, words, typing
   screen, theme, effects, art, interface, results, progress, ui (all look
   switches, last). Sidebar with tabs on the left is the default layout
   (`Settings.ui_style` / `sidebar_tabs`); tests that check another layout
   set it themselves. Rows are still built in
   `settings_menu.raw_items`. The owner may want the grouping tuned -
   that's an edit to TREE only. `tests/tree_menu_check.py` covers it.
3. Optional soft spots, listed in `docs/ART-TODO.md`.

**What the owner wants, and how they work:**
- They judge art by eye. Send a preview PNG at every notable step
  (`tools/preview/`, see its README) and be honest about weak spots.
- They hand-design the art. They rejected an automatic braille "upscaled"
  encoder as "slop". Pictures are hand-composed scene functions in
  `tools/art_wow*.py`; improve the scenes, not an encoder.
- They love dense, colourful pictures built from shades, eighths,
  quadrants and braille. The deep sea jellyfish and the vaporwave sky are
  favourites.
- They're short and direct ("status report", "push it"). Give a status
  without being asked when work runs long.
- Commit locally without asking. Push when asked: "push" usually means
  the current branch, "merge it" means into `main`. Author is
  `1vogada <112830070+1vogada@users.noreply.github.com>`, never a
  Co-Authored-By trailer.
- For big batches of art, the working pattern was parallel agents, one
  git worktree each and one file each (`art_wow2/3/4.py`), with every
  result reviewed by rendering it in its own theme before merging. Tell
  agents to `git merge --ff-only <branch>` first: worktrees can start
  from an older `main`.

**Traps found the hard way:**
- **Disk:** the work laptop's C: drive was full (0 GB free). Tests then
  fail with odd errors (`OSError 28`, book, save and smoke checks) and a
  build can die mid-write.
- **Temp folders:** every test run leaves an empty `tmp*` folder in the
  temp dir (`MINITYPE_DIR`). Thousands piled up.
- **Python on Windows:** `python` can be the Microsoft Store alias;
  `python3.13` worked.
- **Scenes off the picture:** scenes are now also drawn above and to the
  left of the picture (`tools/art_extend.py`), so a field must work for
  y < 0 and far-left x. Clamp before fractional powers. nord once crashed
  on `(y/h) ** 1.3` with y < 0.
- **Blank cells:** `Picture.row` trims blanks off the end of a row. A cell
  that shows only a background colour must be a full block in that
  colour, not a blank.

## Repo and workflow
- GitHub: `1vogada/minitype`. Work happens on `main` (the old `art-blocks`
  branch was merged in and is kept level with it).
- Commit author: `1vogada <112830070+1vogada@users.noreply.github.com>`;
  **no** "Co-Authored-By: Claude" trailers; never rewrite the first 3 commits.
- Agent habit the owner likes: commit locally without asking, push only
  when asked ("push it"); when asked to do several things, push after each.
- Run the app: `python -m minitype` (Python 3.10+, no dependencies).
- Tests: `python tests/run_all.py` (or `python tests/run_all.py decor`).
  Each `*_check.py` prints `ALL OK`; 30 checks with smoke4. They run against
  the real modules with the terminal mocked. `tests/menu_look.py` prints a
  menu frame as text (`python tests/menu_look.py 120 34 ember sidebar left`)
  and `tests/shows_check.py` reports which art the app actually draws at
  each window size.
- Lint: `python -m pyflakes minitype tools` should be clean.
- Gotchas when editing with an agent: shell heredocs mangle `\\` and
  quotes in art/strings - write edit scripts to files; in a raw string a
  line ending in `\\` before `"""` breaks; files have CRLF line endings.

## Map of the code
- `minitype/app.py` main loop (menu -> test -> results); registers ctrl-o.
- `minitype/context.py` `App`: settings, stats, `styles()` (applies theme,
  background, border, art incl. remix picture/colours, panel, behind).
- `minitype/settings.py` every setting (dataclass) + `CHOICES` validation.
- `minitype/config.py` choice lists (ART_STYLES, ART_SCOPES, ...).
- `minitype/terminal/console.py` drawing: `present()` (scroll, art,
  border, panel, dialog overlay), `overlay_art()` (placement, behind mode,
  `_layer` letters on art), `_panel()`, `set_overlay()` dialogs.
- `minitype/terminal/keys.py` key reading; ctrl-q panic; ctrl-o hook.
- `minitype/terminal/art.py` art data loading (`revamp`, `blocks`,
  `detailed`, `combined`, og), `resolve()`, `Picture` (painting, `row()`,
  `wider()` growth on wide screens).
- `minitype/terminal/style.py` themes, palettes (`art_palette`), Styles.
- `minitype/ui/` screens: `main_menu.py` (tabs: gamemode, practice,
  gallery, settings, profile, quit), `settings_menu.py` (rows built in
  `raw_items`), `settings_tree.py` (TREE: which page each row is on),
  `tree_menu.py` (cascading pages), `gallery.py`,
  `anywhere.py` (ctrl-o settings + Resume? dialog), `menu.py` (Menu, Item,
  Hints; `tab=True` items are section buttons that act), `screen.py`
  (menu_loop, ` and ~ theme keys).
- `minitype/engine/` typing test (`runner.py`: pause/resume, lowercase rule).
- `tools/` art builders (see art-notes): `make_art.py`, `make_revamp.py`,
  `art_scenes.py`, `artgen.py`, `artgen_ascii.py`, `art_combined.py`,
  `art_wow.py`, `revamp_art.py`, `glyphs.py`, `sketch.py`.

## Features added in this stretch (newest last)
- Help text floats over the art in a box; selected row always lit; `>>`
  marks the section you're in.
- Art behind text (text drawn over full-size art; letters keep the art's
  colour behind them). Text panel (art full size, text in a bordered panel
  with a ░ shadow, hints in their own panel).
- Theme background: theme / always / off.
- Combined art style; blocks/detailed/og/revamp styles; art grows on wide
  screens; revamp is the default style.
- Quit, gallery, settings, profile are main menu tabs (no "app" tab).
- ` / ~ next / previous theme on menus; ctrl-o settings from anywhere
  (pauses a test; "Resume?" yes/no after); all-lowercase rule.
- Gallery: up/down theme, left/right art style, [ ] picture (remix), c
  picture colours, v show art, p text panel, b art behind text, / search;
  enter keeps, esc restores.
- Settings sections: rules, challenges, text, drills, theme, art,
  art fade, effects, typing screen, interface, results, progress.
- Background bars fix (blank after a bg cell takes its own code).
- Number settings take a typed number (config `NUMBER_RANGES`, any
  value in range is saved; `settings_menu.number_keys`); a wrong one
  shows `anywhere.warn` - the pause box for 1.5 s. Esc in a test pauses
  it (`runner.pause`, setting `esc_pause`, typing screen → pause on esc).
- Fade settings are per picture: `Settings.fades` (picture -> its
  FADE_FIELDS); `App.picture_fade` swaps them in when the shown picture
  changes (called from `styles()`); gallery esc restores them.
- Text over the art: settings text_contrast (off / nudge / flip) and
  text_bold, applied per letter in `console._readable` (also in the help
  box); fade_on switches the fade off for every picture.
  `style.rgb_of_code` now skips a colour's own numbers and lets the last
  colour win (it used to read `48;2;..;90` as bright black text).
- Text panel is see-through: `console._panel` boxes the text (as wide as
  the text; floating help goes over its edge) and returns the box's
  columns per row; overlay_art(..., dim=) darkens the art there
  (`_dimmed`, PANEL_DIM) and the letters draw over it like art behind text.
- Settings tab "ui": copies of the UI_TAB rows (settings_menu) added
  by arrange(); tests that index rows by label skip section "ui".
  see_through (0-100%) sets how bright the art shows through the help
  box, text panel and dialogs (`console._see_through`, `_over`).
- text_lighten: `console.present` lightens the text colours of menu
  screens (not scene "test") before border/art/background go on
  (`_lighter`, which parses each escape so backgrounds stay).
  untyped_lighten: `Styles.untyped` (the dim colour by default), lightened
  in App.styles(); the typing screen's untyped letters use it. The art
  palette comes from the theme's own colours (`Styles._art`), so accent
  letters never change the art.
- Help box position (setting help_position): inline, or a corner -
  `Menu._help_corner` hands a double-lined box to `console.set_corner`;
  present() draws it for that frame only (`_in_corner`, `_stamp`).
- Taller art: `Picture.taller(n)` puts n filler rows (the sky carried on
  up, `art._filler`) on top; `console._dressed` adds as many as there's
  room for (up to `art.TALLER` = half the height) after the picture is
  placed by its own height, then fades it. `pic.extra` = filler rows.

## First thing in a new session
Ask the user whether to add an **"outline only" option for the text
panel** (just the border, the art showing through inside). Ask every time
the project is picked up with an AI until answered - see CLAUDE.md /
AGENTS.md at the repo root.

## Known issues
- The **art fade settings** have two open points (each amount is a
  strength: 0% = no fade, 100% = no art, in between on an exponential
  curve, subject kept whole - as intended, and steered in a real terminal):
  they only apply to pictures with background colours, and the edge beside
  the menu text still steps. The bleed above the picture's top is **done**
  (`Picture.taller`, `art._filler`, `console._dressed`; up to `art.TALLER`,
  half the picture's own height). Note the owner's own `settings.json` has
  `fade_on: false`, so the fold is off globally there by choice.

## In progress / next (as the owner asked)
The art work left is listed, with the owner's own notes, in
`docs/ART-TODO.md`.

1. Art revamp ("wow" pictures, `tools/art_wow.py`, 28/22/16 rows): done
   for ocean, midnight, forest, ember, default, candy (tilted, all pink,
   "bubblegum pop"). The other 34 themes still use the hand-drawn revamp.
   The owner loves the vaporwave combined background and the deep sea
   picture - use them as the bar.
2. Done: art fade (`Picture.faded`, `art._fade`): ordered dither + ▓▒░
   bleed at the edges of pictures with backgrounds. Settings art_fade
   (edges / corner / off), fade_top, fade_side, fade_round (strengths,
  0-100%), fade_start_top / fade_start (how far in the top / side and
  corner fades reach, % of the picture; for the user to suit their window
  size), fade_angle (side fade tilt, degrees), fade_curve (the
  exponential's sharpness, 0 straight .. 10) - own "art fade" tab; `d` in the
   gallery. Possible next: fade the art where it meets text beside it
   (rows next to the menu), and a bleed above the picture's top.
3. 2026-10-09: seven items from `docs/ART-TODO.md` (amber, party, pine,
   autumn, coral reef, gruvbox, bubbly) - two redesigns and five polish,
   branch `art/owner-todo-polish`. New helpers worth reusing in scenes:
   a return alpha below 1 makes the renderer mix the field with the ground
   (`art_combined.render`), which is how the pine's island now fades into
   its lake; a scene's `inks` must list any letter its field uses or the
   colour is dropped. Note that `pal.path(...)` interpolates between the
   given colours, so a stop in the middle can cross a hue the theme never
   had (g6 gave the amber stone an olive cast) - pick stops that stay on
   the wanted hue. Remaining art items are still listed with the owner's
   notes in `docs/ART-TODO.md`.
4. Same day, on top of 3: the synthwave car (`grid`) - the owner's "needs
   more fidelity". It was two faint dots on the road; it is now a car seen
   from behind, sized as a share of the picture so it reads at 28, 22 and
   16 rows alike: a boot lid catching the light, a dark rear window, wheel
   hints, and two red tail lights. Only the car changed - every other cell
   of the picture is byte-identical. The sizes are unchanged, so the tests
   that pin the big pictures to 28/22/16 rows still hold.
5. Same day: `tests/pictures_check.py` (30 checks now). It closes a trap
   nobody had guarded: `make_revamp.py` builds every name in
   `art_wow.WOW` but `write()` only saves the names listed in
   `revamp_art.PICTURES`, so a new wow picture that is not also registered
   as a picture is built and then silently dropped. The check asserts the
   two sets match, that the stored `REVAMP` data covers exactly those
   pictures, and that every picture a theme points at exists in `ART` and
   `REVAMP` (that last one catches art that was never rebuilt). The check
   was verified by planting a fake unregistered wow picture and watching it
   fail.
6. Same day: a new art style, **upscaled**. Its first version (a braille
   dot encoder, island only) was rejected by the owner as "slop" and
   removed on 2026-10-15; see 9.
7. 2026-10-09/12: every item in docs/ART-TODO.md done (12 pictures by four
   worktree agents, reviewed and merged), then touch-ups started on the
   first-pass eight: **party** on 10-12, and on 10-15 the other seven -
   bubbly (no green anywhere, iridescent rims), synthwave (a clean neon
   grid up to the horizon, a bigger car), amber (a polished wood surface),
   coral reef (a real clownfish, anemone, jellyfish, corals), gruvbox (a
   cosy cafe mug), pine (layered pines, moonlit lake) and autumn (a crisp
   maple leaf in a dense autumn wood).
8. Help box: a **help border** setting, and corner boxes keep clear of the
   text panel and the key hints' panel.
9. 2026-10-15: **the art fills a big window with its own scene.** Every wow
   picture is stored with more of its scene drawn on to the left and above
   it (`tools/art_extend.py`; `art_combined.draw` draws any window of
   cells, so the picture itself is byte for byte unchanged).
   `Picture.wider()` / `taller()` use those real columns and rows first and
   only past them fall back to quilting (`_grow`) and filler (`_filler`).
   Beside menu text the art now comes up to one straight edge two columns
   past the widest text line (it used to stop at the picture's own box,
   leaving a step). The **upscaled** style is now the same hand-drawn
   scenes in **truecolour** (`tools/art_truecolor.py`): every cell its
   exact two colours, the scene sampled with anti-aliasing, so skies are
   smooth instead of banded/grainy - at every revamp size plus 44 and 36
   rows for big windows (`tools/make_art_upscaled.py`, ~40 min with -j4;
   a size is marked truecolour in the data and `art._unpack_tc` reads it,
   colours 3 characters each). A flat truecolour cell is a full block, not
   a blank with a background: `Picture.row` trims blanks off a row's end. Scene fields must be defined everywhere now (negative y above
   the picture, far-left x): the extension guards against a scene that
   fails out there, but clamp before powers (`clamp(y / h) ** k`).
   Builds: `make_revamp.py -j4` / `make_art_upscaled.py -j4` (four at a
   time; ~15 and ~25 minutes for everything).
