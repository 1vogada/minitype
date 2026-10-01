# minitype

A minimal CLI typing test inspired by [keybr](https://www.keybr.com/) and
[Monkeytype](https://monkeytype.com/). Pure Python, no dependencies.

> Windows only for now: input uses `msvcrt`.

## Run

```
python -m minitype
```

or install it and use the `minitype` command:

```
pip install -e .
minitype
```

## Controls

- **menus**: arrow keys move, enter selects or starts, left/right change a
  value, tab / shift-tab (or `[` `]`, PgUp / PgDn) jump between sections,
  esc goes back. Rows with a hotkey show it beside the label.
- **settings**: just start typing to filter; only settings whose name
  contains what you typed stay. Start a word with `#` to search tags and
  sections instead (`#colour`, `#mistakes`, `#look`). The search bar shows
  whenever you're searching. Backspace clears a plain search in one go;
  once it has a `#`, backspace deletes one character. `[` `]` aren't typed
  into the search, they switch sections. Esc clears the search, then leaves.
- **during a test**: esc menu, tab restart, ctrl-backspace deletes a word;
  in zen mode enter finishes
- **anywhere**: ctrl-q wipes the screen and exits
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
- **numbers**, and **custom text** from a paste or a file
- **learn**: keybr-style lessons that unlock letters as each one reaches a
  target speed, with optional capitals and punctuation
- **slow words**: a drill built from the words you type slowest

## Rules and challenges

- difficulty: *expert* (a wrong word ends the test), *master* (a wrong key does)
- stop on error: *letter* (a wrong key doesn't move the cursor) or *word*
  (you can't leave a wrong word)
- backspace: *off* (confidence mode) or *freedom* (back into correct words)
- minimum speed and minimum accuracy: fall below and the test fails
- funbox: reversed words, CAPS, rAnDoM case, mirrored text
- memory: the words disappear a few seconds in
- punctuation, numbers, blind mode
- drills for your weak keys and words you got wrong

## Look and feel

- three menu styles: **list**, **sidebar** (details beside the menu) and
  **tabs** (one section at a time). The sidebar can also show a tab bar on
  top, or the sections as buttons down the left (settings → look → sidebar
  tabs)
- themes: default, ocean, forest, sunset, mono
- lowkey: *minimal* shows only the words during a test; *disguised* drops all
  colour and looks like a plain command prompt
- tape mode (one scrolling line), block or underline caret, visible spaces
- on-screen keyboard highlighting the next key, in qwerty, colemak, dvorak,
  qwertz or azerty; in learn mode keys are coloured by speed
- ghost caret (your last run), pace caret (fixed wpm), error beep
- every part of the test header and results screen can be switched on or off

## Results and progress

- speed chart across the test with errors marked
- keyboard heatmap coloured by how often each key was missed
- personal bests per mode, with a banner when you beat one
- **profile**: totals, top and average speed, a speed chart, all your PBs
- daily goal in minutes, shown on the menu and results

## Your files

Both live in the app folder, next to this README, and git ignores them:

- `settings.json`: every setting and your pinned or muted keys. Always kept
  up to date, saved as you change things.
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
  terminal/        frame drawing and clipping, key decoding, themes
  words/           word lists, quotes, code snippets, funbox, generation
  engine/          test spec, typing rules, scoring, rendering, keyboard
  learn/           learn-mode progress and lesson words
  ui/              menus and screens; menus are lists of Items
```

To add a test mode, add a `TestSpec` source in `engine/runner.py` and an
`Item` in `ui/main_menu.py`. To add a setting, add a field to `Settings` and
a row in `ui/settings_menu.py`.
