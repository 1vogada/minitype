"""Text over the art: the text contrast (nudge / flip) and bold settings,
and the switch that turns the fade off for every picture."""
import os, re, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from unittest import mock
from minitype.config import TEXT_CONTRASTS
from minitype.settings import Settings
from minitype.terminal import console, keys, style
from minitype.terminal.console import _contrast, _readable, READABLE
from minitype.context import App
from minitype.ui import main_menu as mm, settings_menu as sm

DARK, LIGHT = (20, 18, 24), (250, 240, 230)
light_bg = "\x1b[48;2;240;210;150m"
grey_text = "\x1b[38;2;150;140;130m"


def fg_of(codes):
    return tuple(int(v) for v in re.findall(r"\x1b\[38;2;(\d+);(\d+);(\d+)m", codes)[-1])


# ---------------------------------------------------------------- the rule
assert _readable(grey_text, light_bg, ("off", False, DARK, LIGHT)) == grey_text
nudged = fg_of(_readable(grey_text, light_bg, ("nudge", False, DARK, LIGHT)))
assert _contrast(nudged, (240, 210, 150)) >= READABLE, nudged
assert sum(nudged) < sum((150, 140, 130)), "darker on a light background"
ok_text = "\x1b[38;2;30;30;30m"                 # already reads: left alone
assert fg_of(_readable(ok_text, light_bg, ("nudge", False, DARK, LIGHT))) == (30, 30, 30)
assert fg_of(_readable(grey_text, light_bg, ("flip", False, DARK, LIGHT))) == DARK
assert fg_of(_readable(grey_text, "\x1b[48;2;20;10;40m", ("flip", False, DARK, LIGHT))) == LIGHT
assert _readable(grey_text, light_bg, ("off", True, DARK, LIGHT)).endswith("\x1b[1m")
assert _readable(grey_text, "", ("nudge", False, DARK, LIGHT)) == grey_text, "no art colour: as it is"

# ---------------------------------------------------------------- settings
s = Settings()
assert (s.text_contrast, s.text_bold, s.fade_on) == ("off", False, True)
assert TEXT_CONTRASTS == ["off", "nudge", "flip"]
s.apply({"text_contrast": "flip", "text_bold": True, "fade_on": False})
assert (s.text_contrast, s.text_bold, s.fade_on) == ("flip", True, False)
s.apply({"text_contrast": "loud"})
assert s.text_contrast == "flip"
items = sm.arrange(sm.build_items(App()))
where = {it.label: it.section for it in items if it.section != "ui"}
in_ui = {it.label for it in items if it.section == "ui"}
assert {"text contrast", "bold text", "see-through", "fade (all pictures)", "text panel",
        "art behind text", "ui style", "border"} <= in_ui, in_ui
assert where["text contrast"] == "art" and where["bold text"] == "art"
assert where["fade (all pictures)"] == "art fade"

# ---------------------------------------------------------------- on screen
W, H = 120, 30


def frame(**kw):
    console.term_size = lambda: (W, H)
    console._last_size = (W, H)
    a = App()
    a.settings.theme, a.settings.art_behind, a.settings.art_fade = "sunset", True, "off"
    for k, v in kw.items():
        setattr(a.settings, k, v)
    out = []
    seq = iter([keys.ESC] * 3)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        mm.main_menu(a)
    return [o for o in out if o.startswith("\x1b[H")][0], a


def letters_on_art(f):
    """(fg, bg) of every letter printed over an art colour."""
    found = []
    for row in f.split("\n"):
        fg = bg = None
        for m in re.finditer(r"\x1b\[([0-9;]*)m|\x1b\[K|\x1b\][^\x07]*\x07|(.)", row):
            if m.group(1) is not None:
                p = m.group(1)
                if p in ("", "0"):
                    fg = bg = None
                fg = style.rgb_of_code(m.group(0)) or fg
                bg = style.rgb_of_code(m.group(0), 48) or bg
            elif m.group(2) and m.group(2).isalpha() and fg and bg:
                found.append((fg, bg))
    return found


plain, _ = frame()
low = [p for p in letters_on_art(plain) if _contrast(*p) < 3]
assert low, "sunset has letters that get lost (or this test proves nothing)"
nudge, _ = frame(text_contrast="nudge")
assert all(_contrast(*p) >= READABLE - 0.01 for p in letters_on_art(nudge)), "every letter reads"
flip, _ = frame(text_contrast="flip")
assert min(_contrast(*p) for p in letters_on_art(flip)) > min(_contrast(*p) for p in letters_on_art(plain))
bold, _ = frame(text_bold=True)
assert "\x1b[1m" in bold


def backgrounds(f):
    """The background colour of every cell on screen, in order."""
    out = []
    for row in f.split("\n"):
        bg = None
        for m in re.finditer(r"\x1b\[([0-9;]*)m|\x1b\[K|\x1b\][^\x07]*\x07|(.)", row):
            if m.group(1) is not None:
                if m.group(1) in ("", "0"):
                    bg = None
                bg = style.rgb_of_code(m.group(0), 48) or bg
            elif m.group(2):
                out.append(bg)
    return out


# the art itself is untouched: every cell keeps its background
assert backgrounds(plain) == backgrounds(nudge) == backgrounds(flip) == backgrounds(bold)

# ---------------------------------------------------------------- fade switch
_, a = frame(fade_on=False, art_fade="edges")
assert console._decor["fade"] is None
assert a.settings.art_fade == "edges", "each picture's own setting kept"
_, a = frame(fade_on=True, art_fade="edges")
assert console._decor["fade"][0] == "edges"
# ---------------------------------------------------------------- see-through
assert Settings().see_through == 40
_, a = frame(see_through=70)
assert console._decor["see_through"] == 0.7
art_cell = ("\x1b[38;2;200;100;50m", "█")
assert console._scrim(art_cell, 0.5) == "\x1b[48;2;100;50;25m"
# a light shade over a dark background looks mostly dark: the box does too
light_dots = ("\x1b[38;2;240;240;240m\x1b[48;2;20;20;20m", "░")
assert console._looks(light_dots) == (75, 75, 75), console._looks(light_dots)
# a help box is the same shade inside a text panel and outside it
row = "  x" + console.FLOAT + "help"
pic = [light_dots] * 10
inside = console._layer(row, pic, (3, 7), (0, 10))
outside = console._layer(row, pic, (3, 7), None)
tint = lambda r: re.findall(r"48;2;(\d+;\d+;\d+)m", r.split("help")[0][-40:])[-1]
assert tint(inside) == tint(outside), (tint(inside), tint(outside))
# a pause box over the art: the art shows through it, as dark as the setting says
box = ["+------+", "| hi   |", "+------+"]
under = ["\x1b[48;2;200;200;200m" + " " * 40] * 9
for st_, want in ((0.0, (0, 0, 0)), (0.5, (100, 100, 100))):
    console._decor["see_through"] = st_
    out = console._over(under, box)
    assert "\x1b[48;2;%d;%d;%dm" % want in out[4], (st_, out[4])
console._decor["see_through"] = 0.4
# ---------------------------------------------------------------- lighter text
from minitype.terminal.style import Styles, rgb_of_code
assert Settings().text_lighten == 0 and Settings().untyped_lighten == 0
# menu text: only the letters' own colour changes, never a background
line = "\x1b[38;2;100;50;0mabc\x1b[48;2;10;20;30m \x1b[38;5;196;48;2;138;2;50mx"
lit = console._lighter(line, 0.5)
assert "38;2;177;152;127" in lit, lit
assert "48;2;10;20;30" in lit and "48;2;138;2;50" in lit, "backgrounds untouched: " + lit
# on screen: menu text lighter, the border, background and art the same
f0, _ = frame(border="line", theme_background="always")
f1, _ = frame(border="line", theme_background="always", text_lighten=60)
assert backgrounds(f0) == backgrounds(f1), "background and art unchanged"
top0, top1 = f0.split("\n")[0], f1.split("\n")[0]
assert top0 == top1, "the border unchanged"
assert f0 != f1, "the text did change"
# neither lighter text nor accent letters changes the art: the same palette
base = Styles("forest")
assert Styles("forest", accent_text=True).art_palette(True) == base.art_palette(True)
assert Styles("forest", accent_text=True).ok == base.title, "the text does take the accent"
# untyped: its own colour on the typing screen, the dim one by default
assert base.untyped == base.dim
a2 = App(); a2.settings.theme = "forest"; a2.settings.untyped_lighten = 50
st2 = a2.styles()
d, u = rgb_of_code(st2.dim), rgb_of_code(st2.untyped)
assert all(abs(uv - (dv + (255 - dv) * 0.5)) <= 2 for dv, uv in zip(d, u)), (d, u)
from minitype.engine.render import Painter
p = Painter(st2, a2.settings, ["ab", "cd"], ["", ""], 0, {}, False, False)
assert any(st2.untyped in c[0] for c in p.word(1)), "untyped words use it"
items2 = sm.build_items(App())
assert {it.section for it in items2 if it.label == "lighter untyped"} == {"theme", "ui"}
print("ALL OK")
