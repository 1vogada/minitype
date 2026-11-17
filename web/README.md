# minitype in the browser

The same typing test as the terminal minitype, as a web page: smooth
scrolling lines, a gliding caret, real fonts, 60 fps. Plain JS modules and
Vite, no framework.

```
cd web
npm install
npm run dev        # http://localhost:5178
npm test           # the engine's tests (node --test)
npm run build      # a static site in web/dist
```

## What's here

- `src/core/` - the engine, ported rule for rule from `minitype/` and run by
  the tests in node: the test rules (`test.js` = engine/runner.py), scoring
  and active wpm, the replay, stats, history and personal bests, best words,
  learn mode, the word generator and lists, settings, the keyboard learn
  client, and the save (`app.js`).
- `src/ui/` - the screens: main menu, typing screen, results, replay, profile,
  learn, settings, welcome.
- `src/fx/` - the effects (off by default).
- `src/data/` - the word list, quotes, code, themes and themed lists, written
  from the Python by `python tools/export_web_data.py`.

## Save data

Kept in the browser (localStorage) in the same shape as minitype's
`save.json` and `settings.json`. Settings › data imports either file (a save
is merged into what's here) and exports both, so they go back to the
terminal version too. Settings the browser has no use for (art, books,
lyrics) travel through untouched.

## Keyboard learn

With *keyboard learn* on, each test's keystrokes go to the MAX68HE app
(`POST http://127.0.0.1:6869/api/learn/typing`, `{"action": "events"}`) in
the background. The page tries the app directly, then the dev server's `/kb`
proxy (the app sends no CORS headers). While the app is down they wait in
localStorage and go first the next time it answers. The browser version
never switches the app's learning on or off and never changes the keyboard.
