# minitype

A minimal CLI typing test inspired by [keybr](https://www.keybr.com/) and
[Monkeytype](https://monkeytype.com/). Pure Python, no dependencies.

Runs on Windows, Linux and macOS (Python 3.8+), and on Android in
[Termux](https://termux.dev/).

## Run

```
python -m minitype
```

(`python3` on Linux and macOS.)

### Linux, macOS and Termux

In Termux, install Python first (`pkg install python git`), clone the repo
and run `python -m minitype` in it.

minitype switches the terminal into raw mode while it runs and puts it
back on exit. If it ever doesn't (a crash in the middle of something), type
`reset` and press enter to get your terminal back.

A few keys depend on the terminal:

- **shift+enter**: most terminals send the same thing for enter and
  shift+enter. It works in terminals that report modified keys: kitty,
  wezterm, foot, iTerm2 with "report modifiers" on, or xterm with
  `modifyOtherKeys`. Elsewhere use left on the row instead.
- **ctrl+backspace** deletes a word where the terminal sends it as `^H`;
  option+backspace (macOS) or alt+backspace does the same everywhere.
- **ctrl+q** (hide) works because flow control is switched off while
  minitype runs.

or install it and use the `minitype` command:

```
pip install -e .
minitype
```

## Controls

- **menus**: arrow keys move, enter selects or starts, left/right change a
  value, tab / shift-tab (or `[` `]`, PgUp / PgDn) jump between sections,
  esc goes back. Rows with a hotkey show it beside the label. Shift+enter
  steps a value backwards. The row you're on has a `>` and is highlighted;
  the section (tab) you're in is marked `>>`. `` ` `` switches to the next
  theme from any menu and `~` (shift-`` ` ``) to the one before (not while
  you're typing, e.g. in the settings search)
- **sidebar with section buttons on the left**: you start on the buttons.
  Up / down pick a section, enter or right steps into its rows, esc steps
  back out (and esc on the buttons leaves). In the rows left / right only
  change values. While you pick a section it has the `>` and highlight;
  in its rows it's marked `>>` and the row you're on is lit instead.
  **gallery**, **settings**, **profile** and **quit** are buttons of
  their own: enter on one opens it (or quits).
- **settings**: just start typing to filter; only settings whose name
  contains what you typed stay. Start a word with `#` to search tags and
  sections instead (`#colour`, `#mistakes`, `#look`). The search bar shows
  whenever you're searching. Backspace clears a plain search in one go;
  once it has a `#`, backspace deletes one character. `[` `]` aren't typed
  into the search, they switch sections. Esc clears the search, then leaves.
- **during a test**: esc menu, tab restart, ctrl-backspace deletes a word;
  in zen mode enter finishes
- **settings** are in sections: rules, challenges, text, drills, theme,
  art, effects, typing screen, interface, results, progress. Old section
  names still work as search tags (#look, #fun, #header, #words)
- **anywhere**: ctrl-q wipes the screen and exits; ctrl-o opens the
  settings. In the middle of a test it's paused (the clock stops), and
  coming back a box asks "Resume?": yes carries on where you were, no
  leaves the test
- key hints can be switched off; pressing any key that does nothing brings
  them back

The screen redraws when the console is resized and fits terminals as small
as 20×5: long menus scroll to keep the selection visible and lines are
clipped to the width.

## Modes

- **time** (15 / 30 / 60 / 120 s) and **words** (10 / 25 / 50 / 100), or any
  custom length
- **quote**: short, medium or long quotes, from a built-in public-domain set
  or Monkeytype's online collection
- **zen**: no target text, type whatever you like
- **code**: Python or JavaScript snippets
- **book**: type through your own books, a page at a time (see below)
- **numbers**, and **custom text** from a paste or a file
- **learn**: keybr-style lessons that unlock letters as each one reaches a
  target speed, with optional capitals and punctuation
- **slow words**: a drill built from the words you type slowest

## Book mode

Drop `.txt` files into the `books` folder in the app folder (main menu →
book → open books folder opens it; git ignores it). On import the text is
cleaned down to plain keyboard characters: curly quotes, dashes and
accented letters become their ASCII forms, markdown-style formatting and
divider lines are dropped, line breaks become spaces, and a Project
Gutenberg licence header and footer are cut off.

To strip more out, set a **filter** (in the book list, or settings → text
→ book filter): the symbols you type there are removed from every book,
for example `,.;:!?"'`. Type `punct` for all punctuation. Quotes and
dashes are already plain `"` `'` `-` by then, so filtering those catches
the curly ones too.

Bulgarian books work too: Cyrillic is kept as it is, and older files saved
in Windows-1251 are read correctly. Under the book list, "bulgarian books"
picks how they're typed:

- **cyrillic**: as written
- **shlokavitsa** (шльокавица): converted to Latin letters. The converted
  book is saved as its own `.txt` in `books/shlokavitsa/` and reused until
  the original changes. Three styles: *classic* (ч 4, ш 6, щ 6t, я q,
  ж j), *letters* (ч ch, ш sh, щ sht, я ya, ж zh) and *official* (the 2009
  transliteration: ц ts, ъ a)

Converting doesn't change the number of words, so your page is the same in
both modes.

Each book is split into pages (50 words by default; settings → text →
book page). Finishing a page moves your bookmark on, and bookmarks are
kept in `settings.json`.

Skipping pages:
- in the book list: left / right one page, PgUp / PgDn ten, `g` to type a
  page number, enter to read
- while typing: PgDn next page, PgUp previous page
- on the results screen: `n` next page

## Rules and challenges

- difficulty: *expert* (a wrong word ends the test), *master* (a wrong key does)
- stop on error: *letter* (a wrong key doesn't move the cursor) or *word*
  (you can't leave a wrong word)
- backspace: *off* (confidence mode) or *freedom* (back into correct words)
- corrected letters: how a letter looks once you fix a mistake on it.
  *marked* (default) uses the theme's warning colour (italic in mono), so a
  live mistake (red) and a fixed one never look the same; *normal* looks
  like any typed letter; *red* stays red
- indicate typos (like Monkeytype's): show the key you actually pressed,
  *below* the letter, in its place (*replace*), or *both* (in its place,
  with the right letter underneath). With stop on error: letter, the
  turned-away key shows under the caret until you press the right one
- with stop on error: word, backspace always works inside a wrong word, so
  you can't get stuck on it (even with backspace off or on expert)
- minimum speed and minimum accuracy: fall below and the test fails
- funbox: reversed words, CAPS, rAnDoM case, mirrored text
- memory: the words disappear a few seconds in
- punctuation, numbers, blind mode, all lowercase (every word in lower
  case, whatever the source)
- drills for your weak keys and words you got wrong

## Look and feel

- three menu styles: **list**, **sidebar** (details beside the menu) and
  **tabs** (one section at a time). The sidebar can also show a tab bar on
  top, or the sections as buttons down the left (settings → interface → sidebar
  tabs)
- 45 themes (settings → theme → theme; a sample line under the row shows
  each one as you flip through):
  - plain: default, ocean, forest, sunset, dracula, nord, gruvbox,
    solarized, monokai, catppuccin, rose pine, matrix, amber, paper (for
    light terminals), mono
  - nature: moss, pine, autumn, desert, meadow, jungle, cherry blossom,
    lavender, tundra, coral reef, volcanic, bamboo
  - high contrast in yellow, cyan, magenta, green, orange and light
  - with effects: **rainbow** (a flowing rainbow across your letters),
    **aurora** and **deep sea** (slow gradients word by word, on a dark
    background), **synthwave** (bold neon gradient), **ember** (your text
    heats up from grey to white hot as your combo grows, and cools on a
    mistake), **phosphor** (green CRT), **vaporwave** (italic pastel neon),
    **candy** (flowing pastels), **midnight** (a dark background theme),
    **summit** (black and white: a snowy peak made of light and code)
  - fun: **party** (fast rainbow, bouncing letters, pop, rainbow caret),
    **glitch** (cyberpunk gradient, glitching letters, shake, pulsing
    caret), **bubbly** (pastels that bounce wildly)
- "accent letters" makes the letters you type take the theme's accent colour
- **border**: a frame around the screen in the theme's accent colour:
  off, ascii (`+ - |` only), line, rounded (default), double, heavy,
  block (solid `█`) or thick (solid, with double-width sides so every
  edge looks equally heavy)
- **show art** (settings → art): a picture that fits the theme in
  the bottom-right corner (a palm island at sunset for ocean, a bat over
  a castle under the moon for dracula, a campfire for ember, a neon grid
  for synthwave, ...), painted in shades of the theme's colours: off,
  menus (default, not on the typing screen) or everywhere. Every one runs
  across the whole bottom of the screen (the sea, a forest, a mountain
  range, the grid, a city, a desk) while the picture itself stays in the
  corner. Each comes in four sizes, 10 to 26 rows tall, and the biggest
  that fits is drawn. It
  never covers text: the background steps around it, and if the picture
  itself doesn't fit, a smaller one is used. The help under the selected
  menu row is the exception: it goes in a box drawn over the art, so the
  art keeps its size as you move. Lowkey disguised hides it along with
  the border. On a screen wider than a picture was drawn for, its
  scenery (sea, hills, grid...) grows on to the left to fill it, from
  runs of its own columns joined where they line up, so it doesn't look
  like one strip repeated
- **art fade** (settings → art, `d` in the gallery): the art dissolves into
  the screen instead of stopping on a straight line - dithered, its colour
  thinning through ▓ ▒ ░. *edges* (default) fades the top and left side
  (**fade top** rows, **fade side** columns); *corner* keeps a round patch
  from the bottom right corner (**fade round**, % of the picture); *off*
- **text panel** (settings → art, off by default, `p` in the gallery):
  the art full size over the whole screen and the text in a panel of its
  own on top, bordered like the screen with a shaded drop shadow; the key
  hints get a panel of their own along the bottom
- **art behind text** (settings → art, off by default): the art always
  shows at full size, behind everything. Text is drawn over it letter by
  letter and the art shows between the letters (each letter keeps the
  art's colour behind it, so it's printed on the picture, not cut out of
  it); highlights stay solid,
  and only the help box under the selected row gets a solid card
- every effect can be switched off on its own, for any theme: theme
  background, gradients, gradient flow, heat, and bold / italic (all on
  by default; the sample line shows the change as you toggle)
- **theme background**: *theme* (themes with a background of their own
  paint it), *always* (every theme gets one: a very dark tint of its
  accent, or a pale one for light themes; use this in a light-mode
  terminal so dark themes still look right) or *off* (your terminal's own)
- **effects** (settings → effects), purely visual, never changes what you type:
  - **bounce**: letters bob up and down, *gentle* near the caret or *wild*
  - **shake**: the text jolts sideways after a wrong key
  - **pop**: the last few letters you typed flash bright
  - **fade**: typed letters dim as they fall behind
  - **caret effect**: *pulse* (blinks) or *rainbow* (cycles colour)
  - **glitch**: letters further ahead flicker into symbols now and then
  - **effect speed** (0.25x-4x) and **flow direction** for gradients
  - **art style** (settings → art): *revamp* (default: hand-drawn ASCII line art, one
    picture per theme, over scenery that runs across the bottom of the
    screen - sea, city, grass, snow, a code wall - in shape-matched ASCII:
    each character picked by where its ink sits in the cell, measured from
    the terminal font), *blocks* (pixel art in half and quadrant blocks,
    with braille dots for fine lines and textures), *detailed* (shaded
    ASCII), *og*, the original, simpler pictures, or *combined*: every
    technique at once, each cell drawn with whichever fits it best -
    shades (░▒▓) for smooth gradients, eighth blocks for crisp horizons
    and stripes, quadrants for edges, braille for fine lines and text for
    stars and shine. So far vaporwave has one (a striped sun over a neon
    grid, with palms); other themes show their blocks picture. If blocks
    show as boxes or question marks, your terminal's font lacks them:
    pick detailed
  - **art shading** (settings → art): *shaded* (softer shades and hues of the theme's
    colours: darker and cooler in shadow, lighter and warmer in the
    light) or *flat* (the theme's colours as they are)
  Each follows the theme by default ("theme") or can be forced on or off.
  The party, glitch and bubbly themes come with modifiers switched on
- **theme creator** (settings → theme): build a theme from scratch or from
  any theme, with every colour, the background, gradient, flow, heat,
  bold / italic and the fun modifiers, and a live preview. Save it to
  `themes.json` or save and switch to it straight away

### Your own themes

Copy `themes.example.json` to `themes.json` next to the app and edit it.
Each theme has seven colours (dim, text, error, extra, accent, good, warn),
or `"base": "<built-in theme>"` plus just the ones you want to change.
Colours are 256-colour numbers (0-255) or `"#rrggbb"`. Effects:

| key | what it does |
| --- | --- |
| `background` | paints the whole screen in a colour |
| `gradient` | list of colours your typed letters shade through |
| `by` | `"letter"` or `"word"`: how the gradient steps |
| `flow` | how many steps a second the gradient moves (0 = still) |
| `heat` | list of colours, coolest first: typed text changes colour every 5 keys of combo |
| `bold`, `italic` | `true` to draw typed letters that way |
| `bounce` | `"gentle"` or `"wild"`: letters bob |
| `shake`, `pop`, `fade`, `glitch` | `true` to switch that modifier on |
| `caret` | `"pulse"` or `"rainbow"` |
| `art` | a built-in picture's name (see `minitype/terminal/art.py`; it brings its large coloured version too), `"none"`, or a list of your own lines (up to 40 wide, 12 tall); without it, the base theme's picture |

`#rrggbb` is sent as true colour where the terminal supports it (Windows,
Termux, iTerm2, kitty, ...) and rounded to the nearest of 256 colours
elsewhere (macOS Terminal). New themes show up the next time you open
settings; if one has a mistake, the theme row's help says what's wrong.
- lowkey: *minimal* shows only the words during a test; *disguised* drops all
  colour and looks like a plain command prompt
- tape mode (one scrolling line); underline caret (the letter to type is
  underlined and keeps its colour) or block caret (drawn inverted); word
  gap: blank, dots or an underline between words
- on-screen keyboard highlighting the next key, in qwerty, colemak, dvorak,
  qwertz or azerty; in learn mode keys are coloured by speed
- ghost caret (your last run), pace caret (fixed wpm), error beep
- every part of the test header and results screen can be switched on or off
  (settings → typing screen: show timer, progress, live wpm, combo;
  settings → results)

## Results and progress

- speed chart across the test with errors marked
- keyboard heatmap coloured by how often each key was missed
- personal bests per mode, with a banner when you beat one
- **gallery** (a main menu tab, `g`; `/` searches the themes by name): every theme full screen, exactly as it
  looks - colours, background, art and a typing sample. Up / down (or
  `` ` `` / `~`) flip through the themes, left / right through the art styles
  (revamp, blocks, detailed, og, combined), `[` `]` the picture and `c`
  its colours (a remix, see below), `v` where the art shows (off, menus,
  everywhere) and `b` art behind text; enter uses what's on screen, esc
  keeps yours
- **remix** (settings → art → picture): any theme can wear any other
  theme's picture - candy with the keyboard, say - drawn in this theme's
  colours, or (picture colours: own) in the colours of the theme it comes
  from
- **profile**: totals, top and average speed, a speed chart, all your PBs
- daily goal in minutes, shown on the menu and results

## Your files

Both live in the app folder, next to this README, and git ignores them
(and the `books` folder and your `themes.json`):

- `settings.json`: every setting, your pinned or muted keys and your place
  in each book. Always kept up to date, saved as you change things.
- `save.json`: history, personal bests, word timings and learn progress.
  Only written once you switch on settings → progress → save to disk;
  switching it off deletes the file.

Set `MINITYPE_DIR` to keep them somewhere else. If the app folder isn't
writable they go to `%LOCALAPPDATA%\minitype`. A save from an older version
in `%LOCALAPPDATA%\minitype` is moved into the app folder automatically.

## Word lists

built-in, Monkeytype's English 200 / 1k / 5k / 10k / 25k / 450k, double
letters, commonly misspelled, and offline themed lists: programming,
left hand, right hand, home row.

The one-hand and home-row lists follow your keyboard layout (settings →
look → layout). On qwerty there are about 770 left-hand and 135 right-hand
words. Some layouts have almost none: dvorak puts every vowel on the left,
so its right hand falls back to the built-in list (the menu says so) until
you switch back.

The detailed pictures in `minitype/terminal/art_detailed.py` are made by
`python tools/make_art.py` from the scenes in `tools/art_scenes.py`:
shapes, lines and text drawn by a small rasteriser (`tools/artgen.py`)
that picks each character by how its cell is covered and shaded, and
records how light each one is for the shaded colours. Edit a
scene and run `python tools/make_art.py <name>` to rebuild just that one,
or `--show <name>` to print it.

The revamp pictures in `minitype/terminal/art_revamp.py` are made by
`python tools/make_revamp.py` from the hand-drawn subjects in
`tools/revamp_art.py`, each laid over its scenery: the background of its
scene (or ones it gives, or a hand-drawn strip repeated across the
screen) rendered by `tools/artgen_ascii.py`. That renderer picks every
character by shape, not just darkness, against the ink of each character
measured from the terminal font (`tools/glyphs.py` reads Cascadia Mono or
Consolas into `tools/glyph_shapes.json`): inside a shape the material's
own texture, on its edge the character covering the same part of the
cell, and lines by the way they run, at the right height in the cell
(`_ - ¯`, `/ | \`). `--show <name>` prints a picture; `tools/sketch.py`
drafts line art to finish by hand.

The one-hand words come from `minitype/words/hand_words.py`, generated by
`python tools/make_hand_words.py`: common words from Monkeytype's 10k and
25k lists that are also in the public-domain
[dwyl/english-words](https://github.com/dwyl/english-words) dictionary and
in [Peter Norvig's word counts](https://norvig.com/ngrams/), minus a
reviewed blocklist of names, places and crude words.

## Layout

```
minitype/
  app.py           entry point and screen loop
  context.py       App: shared state handed to every screen
  nav.py           navigation values screens return (MENU, QUIT)
  config.py        fixed tuning values and option lists
  settings.py      user settings
  stats.py         per-session errors, bad words, word timings
  history.py       every finished test and personal bests
  storage.py       settings.json and the opt-in save.json
  terminal/        frame drawing and clipping, key decoding (_windows.py
                   with msvcrt, _posix.py with termios), themes
  words/           word lists, quotes, code snippets, funbox, generation
  engine/          test spec, typing rules, scoring, rendering, keyboard
  learn/           learn-mode progress and lesson words
  ui/              menus and screens; menus are lists of Items
tools/
  make_hand_words.py   rebuilds the one-hand word lists
  make_art.py          rebuilds the detailed corner art (art_scenes.py,
                       artgen.py)
  make_revamp.py       rebuilds the revamp corner art (revamp_art.py,
                       artgen_ascii.py, glyphs.py)
```

Tests: `python tests/run_all.py` runs every check (each prints ALL OK).
See `docs/HANDOFF.md` for the state of the project and how to carry on.

To add a test mode, add a `TestSpec` source in `engine/runner.py` and an
`Item` in `ui/main_menu.py`. To add a setting, add a field to `Settings` and
a row in `ui/settings_menu.py`.
