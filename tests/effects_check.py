import json, os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import style, console
from minitype.context import App
from minitype.engine.render import Painter
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.ui import settings_menu as sm

names = style.theme_names()
nature = ("moss", "pine", "autumn", "desert", "meadow", "jungle", "cherry blossom",
          "lavender", "tundra", "coral reef", "volcanic", "bamboo")
complex_ = ("rainbow", "aurora", "synthwave", "ember", "deep sea", "phosphor",
            "vaporwave", "candy", "midnight")
for t in nature + complex_:
    assert t in names, t
    style.Styles(t)
assert names[-1] == "mono" and len(names) == 46

# ---------------------------------------------------------------- colour maths
assert style.rgb_to_256(255, 0, 0) == 196 and style.rgb_to_256(0, 0, 0) == 16
assert style.rgb_to_256(128, 128, 128) in (244, 102, 243)
assert 232 <= style.rgb_to_256(30, 30, 30) <= 255, "greys use the grey ramp"
g = style.blend([(0, 0, 0), (240, 0, 0)], steps=4)
assert g == [(0, 0, 0), (120, 0, 0), (240, 0, 0), (120, 0, 0)], g
# true colour vs 256 fallback
with mock.patch.object(style, "truecolor", lambda: True):
    assert style.fg("#102030") == "\x1b[38;2;16;32;48m"
    assert style.bg("#102030") == "\x1b[48;2;16;32;48m"
with mock.patch.object(style, "truecolor", lambda: False):
    assert style.fg("#ff0000") == "\x1b[38;5;196m"
    assert style.bg(17) == "\x1b[48;5;17m"
    # whole themes rebuild in 256 colours when true colour goes away
    style._cache["builtin"] = None
    aur = style.Styles("aurora")
    assert aur.background.startswith("\x1b[48;5;") and "38;2" not in aur.typed(0, 0)
style._cache["builtin"] = None
with mock.patch.dict(os.environ, {"COLORTERM": "truecolor"}):
    assert style.truecolor()

# ---------------------------------------------------------------- effects
r = style.Styles("rainbow")
first = [r.typed(k, 0) for k in range(5)]
assert len(set(first)) > 3, "rainbow changes colour per letter"
assert r.typed(0, 0, now=0) != r.typed(0, 0, now=1.0), "rainbow flows with time"
assert r.typed(3, 0, now=0) == r.typed(3, 0, now=0), "same moment, same colour"
a = style.Styles("aurora")
assert a.typed(0, 2) == a.typed(9, 2) != a.typed(0, 5), "aurora goes by word"
assert a.background.startswith("\x1b[48;")
sw = style.Styles("synthwave")
assert sw.typed(0, 0, now=0) == sw.typed(0, 0, now=9), "synthwave doesn't flow"
assert sw.typed(0, 0).startswith(style.BOLD)
assert style.Styles("vaporwave").typed(0, 0).startswith(style.ITALIC)
e = style.Styles("ember")
heat = [e.typed(0, 0, combo=c) for c in (0, 5, 10, 15, 20, 25, 60)]
assert len(set(heat[:6])) == 6 and heat[5] == heat[6], "heat climbs, then stays white hot"
assert style.Styles("forest").typed(3, 1) == style.Styles("forest").ok, "plain themes: plain text"
assert style.Styles("forest").background == ""
assert style.Styles("rainbow", "disguised").typed(0, 0) == "", "disguised has no colour"

# ---------------------------------------------------------------- the test screen uses them
app = App()
app.settings.theme = "ember"
t = TypingTest(app, TestSpec("c", "words", 3, "custom", ("aaaaaaaaaaaa", "b", "c")))
for ch in "aaaaaaaaaaaa":
    t.handle(ch, time.time())
st = app.styles()
cells = Painter(st, app.settings, t.words, t.typed, t.wi, (), False, False, (),
                t.combo, time.time()).word(0)
# heat: the whole typed line glows with the current combo
hot = st.typed(0, 0, combo=t.combo)
assert t.combo == 12 and all(c[0] == hot for c in cells), "all typed letters at the current heat"
assert hot != st.typed(0, 0, combo=0)
t.handle("x", time.time())                # a mistake: combo back to 0, the line cools
cells = Painter(st, app.settings, t.words, t.typed, t.wi, (), False, False, (),
                t.combo, time.time()).word(0)
assert cells[0][0] == st.typed(0, 0, combo=0)

# ---------------------------------------------------------------- backgrounds paint the frame
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None), \
        mock.patch.object(console, "size", lambda: (40, 6)), \
        mock.patch.object(console, "term_size", lambda: (40, 6)):
    app.settings.border = app.settings.art = "off"     # just the background here
    app.settings.theme = "midnight"
    bgc = app.styles().background
    assert bgc and console._background == bgc
    console.present(["hello \x1b[0mworld", "x"])
    frame = out[-1]
    assert frame.count(bgc) >= 4, "each line starts with it and every reset brings it back"
    assert "\x1b[0mworld" not in frame and "\x1b[0m" + bgc + "world" in frame
    assert frame.endswith("\x1b[J\x1b[0m"), "screen cleared with the bg on, then reset"
    app.settings.theme = "forest"
    app.styles()
    console.present(["plain"])
    assert out[-1] == "\x1b[H" + "plain\x1b[0m" + "\x1b[K\x1b[J", out[-1]
console.set_background("")

# ---------------------------------------------------------------- settings preview
app.settings.theme = "rainbow"
row = next(it for it in sm.build_items(app) if it.label == "theme")
line = row.preview()[0]
assert re.sub(r"\x1b\[[0-9;]*m", "", line) == __import__("minitype.ui.preview", fromlist=["SAMPLE"]).SAMPLE
assert "\x1b[38;2;" in line or "\x1b[38;5;" in line
from minitype.ui.menu import Menu
m = Menu(sm.build_items(app), {}, "s")
m.cursor = next(i for i, it in enumerate(m.items) if it.label == "theme")
lines, focus = m.render(app.styles(), 15)
assert __import__("minitype.ui.preview", fromlist=["SAMPLE"]).SAMPLE in re.sub(r"\x1b\[[0-9;]*m", "", "\n".join(lines[focus:focus + 6]))

# ---------------------------------------------------------------- themes.json with effects
example = os.path.join(os.path.dirname(os.path.dirname(style.__file__)), "..", "themes.example.json")
with open(example, encoding="utf-8") as f:
    ex = json.load(f)
path = os.path.join(HOME, "themes.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(ex, f)
assert style.custom_error() == "", style.custom_error()
assert style.theme_names()[-len(ex):] == list(ex)
n = style.Styles("nord with a gradient")
assert n.background and n.typed(0, 0) != n.typed(0, 1)
assert n.dim == style.Styles("nord").dim, "base fills in what isn't listed"
assert len({style.Styles("on fire").typed(0, 0, combo=c) for c in (0, 5, 10, 15)}) == 4
assert style.Styles("slanted").typed(0, 0).startswith(style.ITALIC)
# mistakes are reported, not crashed on
time.sleep(0.02)
with open(path, "w", encoding="utf-8") as f:
    json.dump({"a": {"base": "nope"}, "b": {"base": "nord", "by": "line"},
               "c": {"base": "nord", "gradient": ["#ffffff"]},
               "d": {"base": "nord", "flow": -1}, "e": {"dim": 1},
               "f": {"base": "mono"}, "ok": {"base": "nord"}}, f)
os.utime(path, (time.time() + 3, time.time() + 3))
assert style.theme_names()[-1] == "ok"
err = style.custom_error()
for k in ("a: unknown base", "b: by should be", "c: a gradient needs", "d: bad flow",
          "e: missing text", "f: unknown base"):
    assert k in err, (k, err)
print("ALL OK")
