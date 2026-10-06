"""The combined art style, art that grows on wide screens, and quit as a
section button of its own."""
import os, re, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from unittest import mock
from minitype.config import ART_STYLES
from minitype.terminal import art, console, keys, style
from minitype.terminal.art import THEME_ART, blocks, combined, paint
from minitype.context import App
from minitype.ui import main_menu as mm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)

# ---------------------------------------------------------------- combined
assert "combined" in ART_STYLES and "combined" in art.ART_STYLES
assert ART_STYLES[0] == "revamp", "revamp is the default"
vap = style.theme_art("vaporwave", "combined")
assert THEME_ART["vaporwave"] == "palm" and combined("palm")
assert vap[:len(combined("palm"))] == combined("palm") and vap[-2:] == style.theme_art("vaporwave", "og")
# a picture with no combined version shows in blocks
assert combined("island") == []
assert style.theme_art("ocean", "combined") == style.theme_art("ocean", "blocks")
# biggest first, and every technique is in it
heights = [len(p.lines) for p in combined("palm")]
assert heights == sorted(heights, reverse=True) and heights[0] >= 20, heights
big = combined("palm")[0]
chars = set("".join(big.lines))
assert any(0x2801 <= ord(c) <= 0x28ff for c in chars), "braille"
assert chars & set("▘▝▖▗▚▞▙▛▜▟▌▐"), "quadrants"
assert chars & set("▁▂▃▅▆▇▔"), "eighths"
assert chars & set("░▒▓"), "shades"
assert chars & set("*+.'·"), "text (stars)"
assert chars & set("=-~"), "text (reflection)"
assert big.span and big.back_parts, "spans the bottom, two colours a cell"
assert set("".join(big.parts)) <= set("dtexagw ") and set("".join(big.back_parts)) <= set("dtexagw ")
assert len({len(l) for l in big.lines}) == 1 and any(k < len(big.lines[0]) for k in big.keep)
# it paints, in the theme's shades, foreground and background
st = style.Styles("vaporwave")
pic = paint(big, st.art_palette(True))
row = pic.row(len(big.lines) // 2)
assert "38;2;" in row and "48;2;" in row

# the app draws it
app = App(); app.settings.theme = "vaporwave"; app.settings.art_style = "combined"; app.styles()
assert console._decor["art"] and len(console._decor["art"][0].lines) == heights[0]

# ---------------------------------------------------------------- growing on wide screens
p = paint(blocks("summit")[0], style.Styles("summit").art_palette(True))
assert p.span and p.wider(p.width) is p and p.wider(p.width - 10) is p
w = p.wider(p.width + 150)
assert w.width == p.width + 150 and w.height == p.height
assert all(len(l) == w.width for l in w.lines)
assert all(l.endswith(o) for l, o in zip(w.lines, p.lines)), "the picture itself unchanged"
assert w.keep == tuple(k + 150 for k in p.keep)
assert p.wider(p.width + 150) is w, "kept, not grown again every frame"
again = paint(blocks("summit")[0], style.Styles("summit").art_palette(True))
assert again.wider(again.width + 150).lines == w.lines, "the same every time"
# grown from the scenery only: every new column is one of the picture's own
# columns left of its focus
room = min(p.keep)
cols = {tuple(l[c] for l in p.lines) for c in range(room)}
assert all(tuple(l[c] for l in w.lines) in cols for c in range(150))
# not one strip over and over: lots of different columns, in runs from different places
new = [tuple(l[c] for l in w.lines) for c in range(150)]
assert len(set(new)) > 40, len(set(new))
# a non-spanning picture never grows
small = paint(art._og(art.ART["cat"], {}), {"accent": "\x1b[36m"})
assert small.wider(500) is small
# on screen: a wide terminal is filled right across the bottom
app = App(); app.settings.theme = "summit"; app.styles()
console.term_size = lambda: (260, 30)
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    console.present(["  x"] * 3, None)
rows = strip(out[-1]).split("\n")
filled = [r for r in rows if r[2:6].strip("│ ")]
assert filled, "art runs to the left edge"

# ---------------------------------------------------------------- quit
items = mm.build_items(App())
q = next(it for it in items if it.label == "quit")
assert q.tab and q.section == "quit" and q.key == "q"
assert all(it.section != "app" or it.label != "quit" for it in items)
# the list layout gives it no heading of its own
console.term_size = lambda: (90, 40)
from minitype.ui.menu import Menu
m = Menu(items, {}, "x")
lines = [strip(l) for l in m.render(App().styles())[0]]
assert not any(l.strip() == "quit" for l in lines) and any("quit" in l for l in lines), lines
# ---------------------------------------------------------------- no background bars
# a blank after a cell with a background must not carry that background on
# (it painted solid bars across the block and detailed pictures)
from minitype.terminal.art import detailed
for t, name in list(THEME_ART.items())[::3]:
    pal = style.Styles(t).art_palette(True)
    for piece in (blocks(name)[:1] + detailed(name)[:1]):
        pic = paint(piece, pal)
        for r in range(pic.height):
            for c, (codes, ch) in enumerate(console._cells(pic.row(r))):
                assert not (ch == " " and "\x1b[48;" not in pic._codes[r][c] and "\x1b[48;" in codes), (t, name, r, c)
print("ALL OK")
