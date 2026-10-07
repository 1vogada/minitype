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
where = {it.label: it.section for it in items}
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
print("ALL OK")
