# Optimization notes

Branch: `optimization`. Goal: remove lag without changing how the app looks
or behaves. Every change below reuses work or shortens a wait; none changes
what is drawn, the key bindings, the redraw rate or the animations.

## How it was found

Read the draw / input path (`app.styles()`, `console.present()`,
`runner._run`, `keys.read_key`) and profiled with cProfile (terminal mocked,
160x45, the owner's `settings.json`: theme summit, art off). Measured
before the fixes:

| thing | cost |
|---|---|
| `App.styles()` | ~6 ms a call (~14 ms under the profiler) |
| `console.present()` of a 30-line frame | ~3 ms, ~95% of it in `clip()` |

Art-on drawing was **read, not measured** (art is off in that profile).

## Findings

1. **`App.styles()` rebuilt everything every call.** It rebuilds `Styles`,
   the shaded art palette (10 tones x 7 colours, foreground and background)
   and `_extremes`, and re-paints the art. It is called by `paint()`, by
   `keyboard_lines` and, worst, on **every pass of the typing loop** (every
   ~10 ms while idle), so the game burned CPU even when nothing happened.
2. **`console.clip()` ran a regex match per character** - about 72,000
   matches per 30 frames - and every row of every frame goes through it.
3. **Every key press does a full repaint** (`dirty = True` in `_run`), so
   items 1 and 2 were paid per key.
4. **Art behind text / text panel** (`art_behind`, `art_panel`): `_layer`
   blends the text with the art cell by cell for the whole screen every
   frame, even though most rows do not change between frames.
5. **Input latency.** Menus waited for keys with `time.sleep(0.05)` (up to
   50 ms before a key was noticed) and the typing loop slept 10 ms per pass.
6. Repaints happen every 0.1 s (0.05 s with an animated theme) even if the
   frame is unchanged. **Left alone on purpose**: changing it could change
   how animations feel.

## What was done

| change | file | effect |
|---|---|---|
| `styles()` build cached, keyed on every setting that feeds it (theme, effects, art style / colours / picture / remix colours, speed, lighten...). Fade, border, help and `set_decor` still run each call. Draft themes / draft art skip the cache. | `minitype/context.py` | ~6 ms -> a tuple build per call |
| `clip()` rewritten to slice between escape codes instead of per character | `minitype/terminal/console.py` | same output, ~3x faster on coloured rows (more on plain ones) |
| Art-over-text row blend (`_layer`) memoised by `_layered` (LRU 2048). The key holds everything `_layer` reads: row, picture, row index, offsets, card, dim, see-through, text effects, background. | `minitype/terminal/console.py` | unchanged rows cost a dict lookup |
| Menu key wait polls every 2 ms (`keys.POLL`); the terminal-size check keeps its old 50 ms cadence (`keys.SIZE_POLL`) | `minitype/terminal/keys.py` | key noticed in ~2 ms, not up to 50 |
| Typing loop idle sleep 10 ms -> 2 ms | `minitype/engine/runner.py` | up to 8 ms less input lag |

## Checks

- `tests/clip_check.py`: new `clip` against the old one on 20,000 random
  strings (identical) plus a timing.
- `tests/layer_cache_check.py`: draws frames with and without the row cache
  for four themes, with and without the text panel, and compares the output
  (identical).
- `python3.13 tests/run_all.py` for the whole suite.

## Not done / ideas

- Idle repaints (item 6): only repaint when the frame actually changed.
  Needs care for animated themes.
- The non-behind art path (`pic.row` per frame) and `_text_ends` / `_cells`
  parse escapes per character; they could be cached the same way.
- Art-on performance was never profiled in a real terminal.
