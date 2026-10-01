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

Each book is split into pages (50 words by default; settings → words →
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

Both live in the app folder, next to this README, and git ignores them
(and the `books` folder):

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
  terminal/        frame drawing and clipping, key decoding, themes
  words/           word lists, quotes, code snippets, funbox, generation
  engine/          test spec, typing rules, scoring, rendering, keyboard
  learn/           learn-mode progress and lesson words
  ui/              menus and screens; menus are lists of Items
tools/
  make_hand_words.py   rebuilds the one-hand word lists
```

To add a test mode, add a `TestSpec` source in `engine/runner.py` and an
`Item` in `ui/main_menu.py`. To add a setting, add a field to `Settings` and
a row in `ui/settings_menu.py`.
