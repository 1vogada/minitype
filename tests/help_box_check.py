"""Help text over the corner art (boxed, art keeps its size) and the
selection markers: >> on the section you're in, > plus highlight on the
row you're on."""
import os, re, sys, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unittest import mock
from minitype.terminal import console, keys
from minitype.terminal.style import INV
from minitype.context import App
from minitype.ui.menu import Menu
from menu_look import look

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
BOX = set("┌┐└┘│─")


def present(lines, w=96, h=24):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    out = []
    with mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        console.present(lines, None)
    return out[-1]


app = App()
app.settings.theme = "summit"
app.styles()
assert console.art_shown() and not console.art_shown("test")

# ---------------------------------------------------------------- console: floating text
base = strip(present(["  x"] * 3)).split("\n")
art_rows = [i for i, r in enumerate(base) if r.strip(" │").strip() and i > 3]
assert art_rows, "art drawn"
top = art_rows[0]
long = "  x" + " " * 30 + "y" * 40          # plain text where the art is
float_line = "  x" + " " * 30 + console.FLOAT + "y" * 40
lines = ["  x"] * 3 + [""] * (top - 4)       # one row above the art...
solid = strip(present(lines + [long, long])).split("\n")
floating = present(lines + [float_line, float_line])
assert console.FLOAT not in floating and "minitype-float" not in floating, "marker taken out"
floating = strip(floating).split("\n")
# plain text pushes the art smaller (or off); floating text doesn't
assert solid[-3:] != base[-3:] or solid[top:top + 3] != base[top:top + 3]
for i in range(len(base)):
    if i in (top - 1 + 1, top + 1):        # the rows with the floating text
        assert "y" * 40 in floating[i], floating[i]
        tail = floating[i].split("y" * 40)[1]
        # the art goes on a cell after the floating text
        assert base[i].endswith(tail.lstrip(" ")) or not tail.strip(" │"), (i, base[i], floating[i])
    elif i > top + 1:
        assert floating[i] == base[i], (i, base[i], floating[i])
# floating text a menu draws past the art's end: the art just isn't drawn there
over = "  x" + console.FLOAT + "y" * 200
r = strip(present(["  x"] * 3 + [""] * (top - 4) + [over])).split("\n")
assert r[top].count("y") >= 80 and r[-3:] == base[-3:]

# ---------------------------------------------------------------- the main menu
def rows(frame):
    return strip(frame).split("\n")


def line(frame, word):
    return next(l for l in frame.split("\n") if word in strip(l))


# in the rows, on "zen": its help is boxed, the art is the size it is on "time"
time_f = look(96, 24, presses=[keys.ENTER], raw=True)
zen_f = look(96, 24, presses=[keys.ENTER, keys.DOWN, keys.DOWN, keys.DOWN], raw=True)
t, z = rows(time_f), rows(zen_f)
help_i = next(i for i, r in enumerate(z) if "type whatever you like" in r)
assert "┌" in z[help_i - 1] and "└" in z[help_i + 1], z[help_i - 1:help_i + 2]
assert z[help_i].split("|", 1)[1].lstrip().startswith("│ no target text"), z[help_i]
# art rows below the box are the same as with the short help; on the box's
# rows the art carries on after the box
assert t[help_i + 2:] == z[help_i + 2:]
for k in (help_i - 1, help_i, help_i + 1):
    after = z[k].rstrip(" │").split("┐" if k < help_i else "┘" if k > help_i else "│ ")[-1]
    assert t[k].rstrip(" │").endswith(after.strip()), (t[k], z[k])
assert any(c not in " │" for c in z[help_i].rsplit("│", 2)[-2]), "art beside the box"
assert "minitype-float" not in zen_f

# markers: in the rows, the section is >> (not lit) and the row is > and lit
assert strip(line(zen_f, "gamemode")).lstrip("│ ").startswith(">> gamemode")
assert INV not in line(zen_f, "gamemode").split("|")[0]
assert INV in line(zen_f, " zen") and ">4" in strip(line(zen_f, " zen"))
assert INV not in line(zen_f, " time") and INV not in line(zen_f, " words")
# on the section buttons: the section is > and lit, the row isn't lit
on = look(96, 24, presses=[keys.DOWN, keys.UP], raw=True)
assert "> " in strip(line(on, "gamemode")) and ">>" not in strip(line(on, "gamemode"))
left, right = line(on, "gamemode").split("|", 1)     # both on one line
assert INV in left and " time" in strip(right) and INV not in right

# art off: plain help lines, no box
a = App(); a.settings.art = "off"; a.styles()
assert not console.art_shown()
m = Menu([__import__("minitype.ui.menu", fromlist=["Item"]).Item("", "alpha", lambda: None, help="some help")], {}, "x")
r = [strip(l) for l in m.render(a.styles())[0]]
assert r[1].strip() == "some help" and not BOX & set("".join(r)), r
a.settings.art = "menus"; a.styles()
r = [strip(l) for l in m.render(a.styles())[0]]
assert "┌" in r[1] and "│ some help │" in r[2] and "└" in r[3], r
# the row itself: pointer, and the label lit with a space either side
row = m.render(a.styles())[0][0]
assert INV + " alpha " in row and strip(row).startswith(" > alpha "), repr(row)

# tab bar: the tab you're in is >>, nothing in it highlighted
from minitype.ui.menu import Item
tm = Menu([Item("", "a", lambda: None, section="one"), Item("", "b", lambda: None, section="two")],
          {}, "t", style="tabs")
bar = tm.render(a.styles())[0][0]
assert strip(bar).split() == [">>", "one", "two"] and INV not in bar, strip(bar)

# ---------------------------------------------------------------- art behind text
from minitype.settings import Settings
assert Settings().art_behind is False
from minitype.ui import settings_menu as sm
assert any(it.label == "art behind text" and it.section == "art" for it in sm.build_items(App()))
b = App(); b.settings.theme = "summit"; b.settings.art_behind = True; b.styles()
W, H = 80, 24
base = strip(present(["  x"] * 3, W, H)).split("\n")
k = max(i for i, r in enumerate(base) if r.startswith("│") and sum(c not in " │" for c in r) > 20)   # a full art row
text = "  hello" + " " * 20 + "world" + " " * 10 + "again"
lines = ["  x"] * 3 + [""] * (k - 4) + [text]
r = strip(present(lines, W, H)).split("\n")
# letters on top at their own columns, the art in every gap, the rest of the art as it was
pos = lambda row, word: row.index(word)
for word in ("hello", "world", "again"):
    assert pos(r[k], word) == pos(" " + text, word), (word, r[k])     # +1 for the frame side
gap = range(pos(r[k], "hello") + 5, pos(r[k], "world"))
assert all(r[k][c] == base[k][c] for c in gap), (r[k], base[k])
assert [x for i, x in enumerate(r) if i != k] == [x for i, x in enumerate(base) if i != k]
# a floating card covers the art whole, spaces and all
card = "  x" + " " * 10 + console.FLOAT + "[" + " " * 20 + "]"
r = strip(present(["  x"] * 3 + [""] * (k - 4) + [card], W, H)).split("\n")
inside = r[k][r[k].index("[") + 1:r[k].index("]")]
assert inside == " " * 20, inside
after = r[k].index("]") + 1
assert r[k][after:].rstrip(" │") == base[k][after:].rstrip(" │")
# highlighted blanks cover it too
hl = "  x" + " " * 10 + INV + "    " + "\x1b[0m"
r = present(["  x"] * 3 + [""] * (k - 4) + [hl], W, H).split("\n")[k]
assert INV + "    " in r, repr(r)
# the menu: the art is the same wherever the cursor is, the help still boxed
f1 = rows(look(W, H, presses=[keys.ENTER], raw=True, behind=True))
f2 = rows(look(W, H, presses=[keys.ENTER] + [keys.DOWN] * 5, raw=True, behind=True))
assert f1[-6:] == f2[-6:] and any("┌" in x for x in f2)
# ---------------------------------------------------------------- text panel
pn = App(); pn.settings.theme = "ember"; pn.settings.border = "double"; pn.settings.art_panel = True
pn.styles()
assert console.panel_shown()
W2, H2 = 110, 34
lines2 = ["", "  minitype", "", "  1  time   30s", "  2  words  25"]
raw = present(lines2 + [], W2, H2)
rows2 = strip(raw).split("\n")
assert rows2[1].startswith("║╔") and "╗" in rows2[1], rows2[1]           # the panel, in the frame's style
panel_right = rows2[1].index("╗")
assert rows2[3][1:].startswith("║  minitype")
assert rows2[2][panel_right + 1] == "░", "a shadow down its right side"
below = rows2[len(lines2) + 2]
assert "░" in below[1:panel_right + 2], "and along its bottom"
assert any(ch in "".join(rows2[10:]) for ch in "▀▄█▌▐"), "the art fills the rest"
# hints in a panel of their own along the bottom, wrapped to fit
console.term_size = lambda: (W2, H2)
from minitype.ui.menu import Hints
hl = Hints(pn).lines(pn.styles(), "word " * 60)
assert all(console.visible_len(l) <= W2 - 6 for l in hl)
pn.settings.art_panel = False; pn.styles()
assert not console.panel_shown()

# ---------------------------------------------------------------- letters over the art keep its colour
bb = App(); bb.settings.theme = "ember"; bb.settings.art_behind = True; bb.styles()
raw = present([""] * 20 + ["  " + "x" * 100], W2, H2)
row = [r for r in raw.split("\n") if "xxxx" in strip(r)][0]
cells = console._cells(row)
on_art = [codes for codes, ch in cells if ch == "x" and "\x1b[48;" in codes]
assert on_art, "letters over the art take its colour behind them"
print("ALL OK")

