import json, os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import style, console, keys
from minitype.context import App
from minitype.engine.render import Painter, rows, draw, POP_LEN, FADE_FROM, GLITCH_GLYPHS
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.ui import settings_menu as sm, theme_creator as tc
from minitype.ui.preview import SAMPLE

strip = lambda s: re.sub(r"\x1b\[[0-9;]*m", "", s)


def painter(app, words, typed, wi, now=0.0, combo=0):
    return Painter(app.styles(), app.settings, words, typed, wi, (), False, False,
                   (), combo, now)


app = App()
s = app.settings
words = ("abcdefghijklmnopqrstuvwxyz", "next", "word", "here", "and", "more", "text")
typed = ["abcdefghijklmnopqrst"] + [""] * 6       # caret on "u" (offset 20)

# ---------------------------------------------------------------- pop & fade
s.fun_pop = "on"
p = painter(app, words, typed, 0)
cells = p.word(0)
st = app.styles()
for k in range(20 - POP_LEN, 20):
    assert cells[k][0] == style.BOLD + st.title, k
assert cells[20 - POP_LEN - 1][0] == st.typed(0, 0)
s.fun_pop, s.fun_fade = "off", "on"
cells = painter(app, words, typed, 0).word(0)
assert cells[0][0] == st.dim and cells[20 - FADE_FROM][0] != st.dim, "far behind fades"
s.fun_fade = "off"

# ---------------------------------------------------------------- glitch
s.fun_glitch = "on"
seen = set()
for t in range(200):
    p = painter(app, words, typed, 0, now=t / 8)
    span = p.span(0, len(words))
    for st_, c, off in span:
        if c in GLITCH_GLYPHS:
            seen.add(off)
    assert all(c == w for (_, c, _), w in zip(span[20:23], "uvw")), "next letters never glitch"
assert seen and min(seen) > 20 + 2, seen
assert all(strip("".join(c for _, c, _ in painter(app, words, typed, 0, now=1).span(0, 1)))[k] == "abcdefghijklmnopqrstuvwxyz"[k] for k in range(23))
s.fun_glitch = "off"

# ---------------------------------------------------------------- caret
s.fun_caret = "pulse"
on = painter(app, words, typed, 0, now=0.0).word(0)[20][0]
off = painter(app, words, typed, 0, now=0.6).word(0)[20][0]
assert on != off and style.UND not in off, "pulse blinks the caret"
s.fun_caret = "rainbow"
colours = {painter(app, words, typed, 0, now=t / 6).word(0)[20][0] for t in range(7)}
assert len(colours) == 7 and all(style.UND in c for c in colours)
s.fun_caret = "theme"

# ---------------------------------------------------------------- bounce
s.fun_bounce = "wild"
p = painter(app, words, typed, 0, now=0.3)
r = rows(p, p.span(0, 3))
assert len(r) == 2
top, low = strip(r[0]), strip(r[1])
assert len(top) == len(low) and all((a == " ") != (b == " ") or a == b == " "
                                    for a, b in zip(top, low))
merged = "".join(a if a != " " else b for a, b in zip(top, low))
assert merged == "abcdefghijklmnopqrstuvwxyz next word", "nothing lost, just moved"
moved = {strip(rows(painter(app, words, typed, 0, now=t / 10), painter(app, words, typed, 0, now=t / 10).span(0, 1))[0]) for t in range(10)}
assert len(moved) > 3, "letters move over time"
s.fun_bounce = "gentle"
p = painter(app, words, typed, 0, now=0.3)
assert not any(p.is_up(o) for o in range(0, 20 - 8)), "gentle: only near the caret"
s.fun_bounce = "off"
assert len(rows(painter(app, words, typed, 0), painter(app, words, typed, 0).span(0, 2))) == 1

# ---------------------------------------------------------------- shake
s.fun_shake = "on"
frames = []
with mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **kw: frames.append(lines)), \
        mock.patch.object(console, "size", lambda: (80, 30)):
    for dt in (0.0, 0.07, 0.5):
        draw(app.styles(), s, "h", list(words), typed, 0, 70, "", now=10 + dt, last_error=10)
indents = [len(f[2]) - len(f[2].lstrip(" ")) for f in frames]
assert indents[0] != 2 and indents[1] != indents[0] and indents[2] == 2, indents
s.fun_shake = "theme"

# ---------------------------------------------------------------- the test records mistakes for shake
t = TypingTest(app, TestSpec("c", "words", 2, "custom", ("ab", "cd")))
t.handle("x", time.time())
assert time.time() - t.last_error < 1

# ---------------------------------------------------------------- speed and direction
s.theme = "rainbow"
grad = app.styles().effects.gradient
a = app.styles().typed(0, 0, now=0.5)
s.effect_speed = 4.0
b = app.styles().typed(0, 0, now=0.5)
assert a == grad[4] and b == grad[16], "4x speed: four times as far along"
s.effect_speed = 1.0
s.flow_direction = "backward"
st = app.styles()
assert st.typed(0, 0, now=1.0) == st.effects.gradient[int(-8.0) % len(st.effects.gradient)]
s.flow_direction = "forward"
assert app.styles().animated and not App().styles().animated

# themes bring their own modifiers, settings override them
for f in ("fun_bounce", "fun_shake", "fun_pop", "fun_fade", "fun_caret", "fun_glitch"):
    setattr(s, f, "theme")
s.theme = "party"
e = app.styles().effects
assert e.bounce == "gentle" and e.pop and e.caret_fx == "rainbow"
s.fun_bounce, s.fun_pop = "off", "off"
e = app.styles().effects
assert e.bounce == "off" and not e.pop and e.caret_fx == "rainbow"
s.fun_bounce, s.fun_pop = "theme", "theme"
# disguised: nothing moves; mono: movement but no colour effects
s.lowkey = "disguised"; assert not app.styles().animated; s.lowkey = "off"
s.theme = "mono"; s.fun_bounce = "wild"; s.fun_caret = "rainbow"
e = app.styles().effects
assert e.bounce == "wild" and e.caret_fx == "off"
s.fun_bounce = s.fun_caret = "theme"

# ---------------------------------------------------------------- settings rows
rows_ = {it.label: it for it in sm.build_items(app)}
for label in ("bounce", "shake", "pop", "fade", "caret effect", "glitch",
              "effect speed", "flow direction"):
    assert rows_[label].section == "effects" and rows_[label].preview, label
assert rows_["effect speed"].value() == "1x"
rows_["effect speed"].action(); assert s.effect_speed == 1.5
assert rows_["theme creator"].section == "theme"
s.theme = "bubbly"
assert len(rows_["theme"].preview()) == 2, "the sample bounces too"
assert strip("".join(a if a != " " else b for a, b in zip(*map(strip, rows_["theme"].preview())))) == SAMPLE

# ---------------------------------------------------------------- the theme creator
app = App()
app.settings.theme = "nord"
d = tc.Draft.from_theme("nord")
assert d.name == "my nord" and d.spec == {"base": "nord"} and d.source == "nord"
items = {it.label: it for it in tc.build_items(app, d)}
# colours: step from the base, type one, clear back to base
items["accent"].action()
assert d.spec["accent"] == (tc.code_to_256(style.Styles("nord").title) + 1) % 256
items["accent"].back(); items["accent"].back()
with mock.patch.object(tc, "prompt", return_value="#123456"):
    items["accent"].activate()
assert d.spec["accent"] == "#123456"
with mock.patch.object(tc, "prompt", return_value="  "):
    items["accent"].activate()
assert "accent" not in d.spec
with mock.patch.object(tc, "prompt", return_value="nope"):
    items["text"].activate()
assert "text" not in d.spec and "isn't a colour" in app.notice
# background
items["background"].action(); assert d.spec["background"] == 233
with mock.patch.object(tc, "prompt", return_value=""):
    items["background"].activate()
assert "background" not in d.spec
# gradient, by, flow, heat
with mock.patch.object(tc, "prompt", return_value="#ff0000, 46  0000ff"):
    items["gradient"].action()
assert d.spec["gradient"] == ["#ff0000", 46, "#0000ff"]
items["gradient by"].action(); assert d.spec["by"] == "word"
items["gradient by"].action(); assert "by" not in d.spec, "back at default: dropped"
items["flow"].action(); items["flow"].action(); assert d.spec["flow"] == 1
with mock.patch.object(tc, "prompt", return_value="240 226 196"):
    items["heat"].action()
assert d.spec["heat"] == [240, 226, 196]
# style and fun
items["bold"].action(); items["bounce"].action(); items["bounce"].action()
items["caret effect"].action(); items["glitch"].action()
assert d.spec["bold"] is True and d.spec["bounce"] == "wild"
assert d.spec["caret"] == "pulse" and d.spec["glitch"] is True
# the preview draws the draft, background included
built, err = d.built()
assert err == "" and built[1].bounce == "wild"
lines, focus = tc.draw(app, d, tc.Menu(tc.build_items(app, d), {}, "c"))
assert "theme creator - my nord" in strip("\n".join(lines))
# a draft that doesn't build says why instead of crashing
d.spec["gradient"] = ["#ff0000"]
lines, _ = tc.draw(app, d, tc.Menu(tc.build_items(app, d), {}, "c"))
assert "can't preview: a gradient needs at least two colours" in strip("\n".join(lines))
d.spec["gradient"] = ["#ff0000", "#00ff00"]

# saving
items["save"].action()
assert app.notice == "saved 'my nord'"
saved = json.load(open(os.path.join(HOME, "themes.json"), encoding="utf-8"))
assert saved["my nord"]["base"] == "nord" and saved["my nord"]["bounce"] == "wild"
assert "my nord" in style.theme_names() and app.settings.theme == "nord"
items["save and use"].action()
assert app.settings.theme == "my nord" and "switched" in app.notice
assert app.styles().effects.glitch
# names that can't be used
d.name = "nord"; items["save"].action(); assert "built-in" in app.notice
d.name = ""; items["save"].action(); assert "needs a name" in app.notice
d.name = "my nord"
# a broken themes.json is never overwritten
path = os.path.join(HOME, "themes.json")
good = open(path, encoding="utf-8").read()
open(path, "w").write("{ broken")
items["save"].action()
assert app.notice.startswith("not saved") and open(path).read() == "{ broken"
open(path, "w", encoding="utf-8").write(good)
# editing your own theme in place, then deleting it
d2 = tc.Draft.from_theme("my nord")
assert d2.name == "my nord" and d2.spec["bounce"] == "wild"
items2 = {it.label: it for it in tc.build_items(app, d2)}
with mock.patch.object(tc, "prompt", return_value="no"):
    items2["delete"].action()
assert "my nord" in style.theme_names()
with mock.patch.object(tc, "prompt", return_value="yes"):
    items2["delete"].action()
assert "my nord" not in style.theme_names() and app.settings.theme == "default"
# start from cycles through themes
items2["start from"].action()
assert d2.source != "my nord" and d2.spec == style.theme_spec(d2.source)
# the draft stays on the app between visits
app.theme_draft = None
seq = iter([keys.ESC, keys.ESC])
with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "present", lambda *a, **k: None):
    tc.theme_creator(app)
    first = app.theme_draft
    tc.theme_creator(app)
assert app.theme_draft is first
print("ALL OK")
