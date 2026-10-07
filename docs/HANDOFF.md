# Handoff: where minitype stands, and how to carry on

Read this first when picking the project up (you or an AI coding agent).
Then `docs/art-notes.md` for anything about the corner art.

## Repo and workflow
- GitHub: `1vogada/minitype`. Work happens on `main` (the old `art-blocks`
  branch was merged in and is kept level with it).
- Commit author: `1vogada <112830070+1vogada@users.noreply.github.com>`;
  **no** "Co-Authored-By: Claude" trailers; never rewrite the first 3 commits.
- Agent habit the owner likes: commit locally without asking, push only
  when asked ("push it"); when asked to do several things, push after each.
- Run the app: `python -m minitype` (Python 3.10+, no dependencies).
- Tests: `python tests/run_all.py` (or `python tests/run_all.py decor`).
  Each `*_check.py` prints `ALL OK`; 29 checks with smoke4. They run against
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
  gallery, settings, profile, quit), `settings_menu.py` (rows built by
  section, then laid out by `LAYOUT`/`arrange`), `gallery.py`,
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
- The **art fade settings don't fully work** yet (each amount is a
  strength: 0% = no fade, 100% = no art, in between on an exponential
  curve, subject kept whole - that part is as intended): they only apply to
  pictures with background colours; the edge beside the menu text still
  steps; nothing bleeds above the picture's top; the amounts weren't
  checked in a real terminal.

## In progress / next (as the owner asked)
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
