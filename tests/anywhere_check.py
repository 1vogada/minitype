"""ctrl-o (settings from anywhere, pausing a test and asking to resume),
~ for the theme before, the all-lowercase rule."""
import os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys, style
from minitype.context import App
from minitype.engine.runner import run_test, TypingTest
from minitype.engine.spec import TestSpec
from minitype.nav import MENU
from minitype.ui import main_menu as mm, settings_menu as sm
from minitype.ui.anywhere import open_settings

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
SIZE = [100, 30]
console.term_size = lambda: tuple(SIZE)
words = tuple("alpha beta gamma delta epsilon zeta eta theta".split())


def play(app, presses, clock):
    """Run a test with these key presses fed through the real read_key (so
    ctrl-o goes through its hook), the clock jumping as given; return the
    result and every frame written."""
    out = []
    seq = iter(presses)
    pending = []

    def read():
        k = next(seq)
        if isinstance(k, float):          # a pause: time passes
            clock[0] += k
            k = next(seq)
        return k
    with mock.patch.object(keys.backend, "read", read), \
            mock.patch.object(keys.backend, "ready", lambda: True), \
            mock.patch.object(keys, "key_ready", lambda: True), \
            mock.patch.object(time, "time", lambda: clock[0]), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        res = run_test(app, TestSpec("c", "words", len(words), "custom", words))
    return res, out


app = App()
keys.on_settings_key(lambda: open_settings(app))
clock = [1000.0]
# type "alpha ", then ctrl-o: the settings open (esc leaves), 60 seconds go by,
# the box asks; enter resumes (Yes is chosen first)
presses = list("alpha ") + [keys.CTRL_O, 60.0, keys.ESC, keys.ENTER] + list("beta gamma delta epsilon zeta eta theta")
res, out = play(app, presses, clock)
frames = [strip(f) for f in out if f.startswith("\x1b[H")]
assert any("Resume?" in f for f in frames), "the box was shown"
box = next(f for f in frames if "Resume?" in f)
assert "Yes" in box and "No" in box and "╔" in box and "alpha" in box, "over the test"
assert not any("Resume?" in f for f in frames[frames.index(box) + 3:]), "and gone after"
assert res is not None and not isinstance(res, str)
assert res.elapsed < 30, ("the minute in the settings didn't count", res.elapsed)

# No: the test is left, back to the menu
clock = [2000.0]
presses = list("alpha ") + [keys.CTRL_O, keys.ESC, keys.RIGHT, keys.ENTER]
res, out = play(app, presses, clock)
assert res == MENU, res

# "n" answers at once; nothing typed yet means no question at all
clock = [3000.0]
res, out = play(app, list("al") + [keys.CTRL_O, keys.ESC, "n"], clock)
assert res == MENU
clock = [4000.0]
presses = [keys.CTRL_O, keys.ESC] + list(" ".join(words))
res, out = play(app, presses, clock)
assert not any("Resume?" in strip(f) for f in out)
assert res is not None and res != MENU

# from a menu it opens the settings too, and comes back to that menu
a = App()
keys.on_settings_key(lambda: open_settings(a))
seen = []
seq = iter([keys.CTRL_O, "t", "h", "e", "m", "e", keys.CTRL_C, keys.ESC, keys.ESC, keys.ESC])
with mock.patch.object(keys.backend, "read", lambda: next(seq)), \
        mock.patch.object(keys.backend, "ready", lambda: True), \
        mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **k: seen.append(lines)):
    mm.main_menu(a)
texts = ["\n".join(strip(l) for l in f) for f in seen]
assert any("search  theme" in t for t in texts), "the settings were open"
assert "minitype" in texts[-1], "back on the main menu"
# ctrl-o inside the settings doesn't open them twice
assert keys._settings["busy"] is False

# ---------------------------------------------------------------- ~ goes back a theme
names = style.theme_names()
b = App()
seq = iter(["~", "~", "`", keys.ESC, keys.ESC, keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
        mock.patch.object(console, "present", lambda *x, **k: None):
    mm.main_menu(b)
assert b.settings.theme == names[-1], b.settings.theme      # default, back twice, on once

# ---------------------------------------------------------------- all lowercase
c = App()
items = {it.label: it for it in sm.build_items(c)}
row = items["all lowercase"]
assert row.section == "text" and row.value() == "off"
row.action(); assert c.settings.lowercase and "lower" in c.settings.flags()
t = TypingTest(c, TestSpec("c", "words", 3, "custom", ("Hello", "WORLD", "MiXeD")))
assert t.words == ["hello", "world", "mixed"], t.words
c.settings.lowercase = False
t = TypingTest(c, TestSpec("c", "words", 3, "custom", ("Hello", "WORLD", "MiXeD")))
assert t.words == ["Hello", "WORLD", "MiXeD"]
c.settings.lowercase, c.settings.punctuation = True, True
t = TypingTest(c, TestSpec("w", "words", 40, "english"))
assert all(w == w.lower() for w in t.words), t.words
# ---------------------------------------------------------------- gallery
from minitype.ui.gallery import gallery
g = App()
names = style.theme_names()
frames = []
seq = iter([keys.DOWN, keys.DOWN, keys.UP, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **k: frames.append(lines)):
    gallery(g)
assert g.settings.theme == names[1], g.settings.theme
first = [strip(l) for l in frames[0]]
assert any("gallery" in l for l in first) and any("default" in l and "1 of" in l for l in first)
assert any("the quick brown fox" in l.replace("_", " ") for l in first), "a typing sample"
assert any("ocean" in strip(l) for l in frames[1]), "flipped on"
assert "theme  ocean" in g.notice
# esc puts yours back
g.settings.theme = "nord"
seq = iter(["`", "`", "~", "`", keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "present", lambda *x, **k: None):
    gallery(g)
assert g.settings.theme == "nord"
# it's on the main menu, under app, with the theme beside it
item = next(it for it in mm.build_items(App()) if it.label == "gallery")
assert item.section == "gallery" and item.tab and item.key == "g" and item.value() == "default"
assert not any(it.section == "app" for it in mm.build_items(App())), "no app tab"
assert {it.section for it in mm.build_items(App()) if it.tab} == {"gallery", "settings", "profile", "quit"}
# the art is drawn while browsing (menus get the corner art)
g.settings.theme = "default"
out = []
seq = iter([keys.ESC])
console.term_size = lambda: (120, 34)
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    gallery(g)
frame = strip([o for o in out if o.startswith("[H")][-1])
assert "Q" in frame and "W" in frame and "E" in frame, "the keyboard picture shows"
# up / down switch the art style, shown live; enter keeps both, esc puts both back
from minitype.config import ART_STYLES
h = App()
frames = []
seq = iter([keys.RIGHT, keys.RIGHT, keys.LEFT, keys.DOWN, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **k: frames.append(lines)):
    gallery(h)
assert h.settings.art_style == ART_STYLES[1] and h.settings.theme == names[1]
assert "art  " + ART_STYLES[1] in h.notice
assert any("art style" in strip(l) and ART_STYLES[0] in strip(l) for l in frames[0])
assert any(style.INV + " " + ART_STYLES[2] in l for l in frames[2]), "the chosen style lit"
h.settings.art_style, h.settings.theme = "og", "nord"
seq = iter([keys.RIGHT, keys.DOWN, keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "present", lambda *x, **k: None):
    gallery(h)
assert (h.settings.art_style, h.settings.theme) == ("og", "nord")
# the picture on screen follows the style
h.settings.theme = "default"
out = []
seq = iter([keys.RIGHT, keys.ESC])
console.term_size = lambda: (120, 34)
h.settings.art_style = "revamp"
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)),         mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    gallery(h)
shots = [strip(o) for o in out if o.startswith("[H")]
assert "Q" in shots[0] and shots[1] != shots[0], "blocks art drawn instead"
# v and b: where the art shows, and art behind text, from the gallery
k = App()
k.settings.art, k.settings.art_behind = "menus", False
frames = []
seq = iter(["v", "b", keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)),         mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **kw: frames.append(lines)):
    gallery(k)
assert k.settings.art == "everywhere" and k.settings.art_behind is True
first = [strip(l) for l in frames[0]]
assert any(l.strip().startswith("show art") and "everywhere" in l for l in first)
assert any(l.strip().startswith("art behind text") for l in first)
k.settings.art, k.settings.art_behind = "menus", False
seq = iter(["v", "v", "b", keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)),         mock.patch.object(console, "present", lambda *x, **kw: None):
    gallery(k)
assert (k.settings.art, k.settings.art_behind) == ("menus", False), "esc puts them back"
# ---------------------------------------------------------------- remix
from minitype.terminal.art import ART_NAMES, revamp
from minitype.terminal.style import Styles
r = App()
r.settings.theme = "candy"
r.styles()
assert console._decor["art"][0].lines == revamp("lollipop")[0].lines, "the theme's own"
r.settings.art_picture = "fire"
r.styles()
assert console._decor["art"][0].lines == revamp("fire")[0].lines, "another theme's picture"
own = console._decor["art"][0]._codes
r.settings.art_recolour = "own"
r.styles()
mixed = console._decor["art"][0]._codes
assert mixed != own, "own colours differ from candy's"
r.settings.theme = "ember"; r.settings.art_picture = "fire"; r.styles()
assert console._decor["art"][0]._codes == mixed, "own = the fire's home theme's colours"
from minitype.settings import Settings
z = Settings(); z.apply({"art_picture": "moon", "art_recolour": "own"}); assert (z.art_picture, z.art_recolour) == ("moon", "own")
z = Settings(); z.apply({"art_picture": "nope", "art_recolour": "x"}); assert (z.art_picture, z.art_recolour) == ("theme", "theme")
items = {it.label: it for it in sm.build_items(App())}
assert items["picture"].section == items["picture colours"].section == "art"
# in the gallery: ] [ step the picture, c its colours; enter keeps, esc not
q = App(); q.settings.theme = "candy"
seq = iter(["]", "]", "[", "c", keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)),         mock.patch.object(console, "present", lambda *x, **kw: None):
    gallery(q)
assert q.settings.art_picture == ART_NAMES[0] and q.settings.art_recolour == "own"
assert "picture  " + ART_NAMES[0] in q.notice
seq = iter(["]", "c", keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)),         mock.patch.object(console, "present", lambda *x, **kw: None):
    gallery(q)
assert q.settings.art_picture == ART_NAMES[0] and q.settings.art_recolour == "own"
# ---------------------------------------------------------------- gallery search
gs = App()
gs.settings.art, gs.settings.art_behind, gs.settings.art_panel = "menus", False, False
frames = []
# / then "vapor": letters go into the search, not to v / p; enter goes back to
# browsing on the match; enter again keeps it
seq = iter(["/", "v", "a", "p", "o", "r", keys.ENTER, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)), \
        mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **kw: frames.append(lines)):
    gallery(gs)
assert gs.settings.theme == "vaporwave", gs.settings.theme
assert (gs.settings.art, gs.settings.art_panel) == ("menus", False), "typed letters didn't toggle anything"
assert any("search  vapor_" in strip(l) and "1 match" in strip(l) for l in frames[6])
# up / down move through the matches only; esc clears the search, then esc leaves
gs.settings.theme = "default"
frames = []
seq = iter(["/", "h", "i", "g", "h", keys.DOWN, keys.DOWN, keys.ESC, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)), \
        mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **kw: frames.append(lines)):
    gallery(gs)
highs = [n for n in style.theme_names() if "high" in n]
assert gs.settings.theme == highs[2], gs.settings.theme
assert not any("search" in strip(l) for l in frames[-1]), "cleared"
# nothing matching: says so, keeps showing a theme; backspace widens it again
frames = []
seq = iter(["/", "z", "z", "z", keys.BACKSPACE, keys.BACKSPACE, keys.BACKSPACE, "n", "o", "r", "d", keys.ENTER, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)), \
        mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **kw: frames.append(lines)):
    gallery(gs)
assert any("nothing matches" in strip(l) for l in frames[3])
assert gs.settings.theme == "nord"
print("ALL OK")

