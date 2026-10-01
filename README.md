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

- **menus**: arrow keys move, enter selects, left/right change a setting,
  esc goes back. Every row also has a hotkey shown beside it.
- **during a test**: esc menu, tab restart, ctrl-backspace deletes a word
- **anywhere**: ctrl-q wipes the screen and exits

## Features

- word, time, number and custom-text tests
- **learn** mode: keybr-style lessons that unlock letters as each one reaches
  a target speed, with optional capitals and punctuation
- **stop on error**: *letter* (a wrong key doesn't move the cursor) or *word*
  (you can't leave a wrong word)
- difficulties: *expert* (a wrong word ends the test) and *master* (a wrong key ends it)
- on-screen keyboard highlighting the next key, in qwerty, colemak, dvorak,
  qwertz or azerty; in learn mode keys are coloured by speed
- **profile**: totals, top and average speed, a speed chart, best per mode
- daily goal in minutes, shown on the menu and results
- punctuation, numbers, blind mode, block or underline caret, visible spaces,
  error beep
- drills for your weak keys and words you got wrong
- ghost caret (your last run) and pace caret (fixed wpm)
- built-in word list, or Monkeytype's 200 / 1k / 5k English lists online
- opt-in saving of settings, history and learn progress to
  `%LOCALAPPDATA%\minitype\save.json` (settings → save to disk)

## Layout

```
minitype/
  app.py           entry point and screen loop
  context.py       App: shared state handed to every screen
  nav.py           navigation values screens return (MENU, QUIT)
  config.py        fixed tuning values
  settings.py      user settings
  stats.py         per-session error, word and history tracking
  history.py       every finished test, for the profile and daily goal
  storage.py       the opt-in save file
  terminal/        console output, key decoding (arrows included), colours
  words/           word lists, online loading, word generation
  engine/          test spec, typing rules, scoring, rendering, results
  learn/           learn-mode progress, lesson words, save file
  ui/              menus and screens; menus are lists of Items
```

To add a test mode, add a `TestSpec` source in `engine/runner.py` and an
`Item` in `ui/main_menu.py`. To add a setting, add a field to `Settings` and
an `Item` in `ui/settings_menu.py`.
