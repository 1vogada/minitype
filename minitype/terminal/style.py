"""Colours and themes.

Built-in themes use the 256-colour palette, which nearly every terminal
supports. You can add your own in themes.json in the app folder (see
themes.example.json); they appear in the theme list after the built-in
ones. Colours there are 256-colour numbers (0-255) or "#rrggbb" for
terminals with true colour.
"""

import json
import os

from .. import storage

GRAY = "\x1b[90m"
WHITE = "\x1b[97m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
DARKRED = "\x1b[38;5;88m"
INV = "\x1b[7m"
DIM = "\x1b[2m"
UND = "\x1b[4m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"

CUSTOM_FILE = "themes.json"
# the parts of a theme, in order, as named in themes.json
PARTS = ("dim", "text", "error", "extra", "accent", "good", "warn")


def c256(n):
    return f"\x1b[38;5;{n}m"


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"\x1b[38;2;{r};{g};{b}m"


def _t(*codes):
    """A theme from seven 256-colour numbers, in PARTS order."""
    return tuple(c256(n) for n in codes)


# name -> (dim, text, error, extra, accent, good, warn)
THEMES = {
    "default": (GRAY, WHITE, RED, DARKRED, WHITE, GREEN, YELLOW),
    "ocean": _t(67, 195, 203, 131, 81, 79, 221),
    "forest": _t(65, 194, 167, 95, 114, 77, 179),
    "sunset": _t(96, 224, 197, 125, 215, 150, 222),
    "dracula": _t(61, 255, 203, 131, 141, 84, 228),
    "nord": _t(60, 254, 167, 95, 110, 108, 222),
    "gruvbox": _t(243, 223, 167, 88, 208, 142, 214),
    "solarized": _t(240, 109, 160, 125, 33, 64, 136),
    "monokai": _t(242, 231, 197, 125, 81, 148, 186),
    "catppuccin": _t(60, 189, 211, 132, 183, 151, 223),
    "rose pine": _t(60, 189, 204, 132, 152, 152, 222),
    "matrix": _t(22, 46, 196, 88, 82, 46, 190),
    "amber": _t(94, 214, 196, 88, 220, 214, 208),
    "paper": _t(246, 235, 124, 88, 25, 28, 130),      # for light terminals
    "high contrast": _t(250, 231, 196, 160, 226, 46, 226),
    # more high contrast: bright white text, pure red errors, one strong
    # accent each; the light one is black on a light terminal
    "high contrast cyan": _t(250, 231, 196, 160, 51, 46, 226),
    "high contrast magenta": _t(250, 231, 196, 160, 201, 46, 226),
    "high contrast green": _t(250, 231, 196, 160, 46, 51, 226),
    "high contrast orange": _t(250, 231, 196, 160, 208, 46, 226),
    "high contrast light": _t(242, 16, 160, 88, 19, 22, 94),
    "mono": None,
}

_custom = {"mtime": None, "themes": {}, "error": ""}


def _colour(v):
    if isinstance(v, int) and 0 <= v <= 255:
        return c256(v)
    if isinstance(v, str) and len(v.lstrip("#")) == 6:
        int(v.lstrip("#"), 16)               # raises ValueError if it isn't hex
        return rgb(v)
    raise ValueError(f"bad colour {v!r}")


def custom_themes():
    """Themes from themes.json, re-read whenever the file changes. A theme
    with a mistake in it is skipped; custom_error() says why."""
    path = storage.path(CUSTOM_FILE)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        _custom.update(mtime=None, themes={}, error="")
        return {}
    if mtime == _custom["mtime"]:
        return _custom["themes"]
    themes, errors = {}, []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("should be an object of themes")
        for name, parts in data.items():
            try:
                if name in THEMES:
                    raise ValueError("that name is built in")
                themes[name] = tuple(_colour(parts[p]) for p in PARTS)
            except (KeyError, TypeError, ValueError) as e:
                errors.append(f"{name}: {e}")
    except (OSError, ValueError) as e:
        errors.append(str(e))
    _custom.update(mtime=mtime, themes=themes, error="; ".join(errors))
    return themes


def custom_error():
    custom_themes()
    return _custom["error"]


def theme_names():
    return list(THEMES) + list(custom_themes())


def _palette(theme):
    return THEMES.get(theme) or custom_themes().get(theme) or THEMES["default"]


class Styles:
    """Colour codes for the current theme. The mono theme, and the disguised
    lowkey mode, use only dim/underline so nothing on screen is coloured."""

    def __init__(self, theme="default", lowkey="off", accent_text=False):
        self.lowkey = lowkey
        self.quiet = theme == "mono" or lowkey == "disguised"
        if self.quiet:
            self.dim, self.ok, self.bad, self.extra = DIM, "", UND, UND + DIM
            self.title = "" if lowkey == "disguised" else WHITE
            self.good = self.warn = ""
        else:
            (self.dim, self.ok, self.bad, self.extra,
             self.title, self.good, self.warn) = _palette(theme)
            if accent_text:
                self.ok = self.title     # typed letters in the accent colour

    def conf_color(self, v):
        """Good at target, warning getting there, bad far off."""
        if self.quiet:
            return ""
        return self.good if v >= 1 else self.warn if v >= 0.6 else self.bad
