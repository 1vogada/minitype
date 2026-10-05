"""Colours and themes.

A theme is seven colours (PARTS) and, optionally, effects:

    background   the whole screen is painted this colour
    gradient     typed letters shade through these colours, per letter or
                 per word ("by"), and with "flow" the gradient moves along
                 that many steps a second
    heat         typed letters change colour with your combo, coolest
                 first: every HEAT_STEP correct keys in a row moves one on
    bold, italic how typed letters are drawn

Plain themes are listed in THEMES, ones with effects in COMPLEX. You can add
your own in themes.json in the app folder (see themes.example.json), with
the same keys; "base" starts from a built-in theme so you only list what
changes. Colours are 256-colour numbers (0-255) or "#rrggbb".

"#rrggbb" colours are sent as true colour where the terminal supports it
(Windows Terminal, the Windows console, Termux, iTerm2, kitty, ...) and
rounded to the nearest of the 256 colours elsewhere (macOS Terminal).
"""

import json
import os
from dataclasses import dataclass

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
ITALIC = "\x1b[3m"
RESET = "\x1b[0m"

CUSTOM_FILE = "themes.json"
# the parts of a theme, in order, as named in themes.json
PARTS = ("dim", "text", "error", "extra", "accent", "good", "warn")
GRADIENT_STEPS = 24      # colours a gradient is blended into
HEAT_STEP = 5            # correct keys in a row per step of heat
EFFECT_KEYS = ("background", "gradient", "by", "flow", "heat", "bold", "italic")


# ---------------------------------------------------------------- colours

def truecolor():
    """Whether "#rrggbb" can be sent as is."""
    env = os.environ
    return (env.get("COLORTERM", "").lower() in ("truecolor", "24bit")
            or os.name == "nt" or "WT_SESSION" in env or "TERMUX_VERSION" in env
            or env.get("TERM_PROGRAM") in ("iTerm.app", "WezTerm", "vscode"))


def c256(n):
    return f"\x1b[38;5;{n}m"


def _cube(v):
    return 0 if v < 48 else 1 if v < 115 else (v - 35) // 40


def rgb_to_256(r, g, b):
    """Nearest xterm 256-colour index: the 6x6x6 cube or the grey ramp."""
    levels = (0, 95, 135, 175, 215, 255)
    ci = [_cube(v) for v in (r, g, b)]
    cube = tuple(levels[i] for i in ci)
    grey_i = max(0, min(23, round((sum((r, g, b)) / 3 - 8) / 10)))
    grey = 8 + grey_i * 10

    def dist(c):
        return sum((a - b) ** 2 for a, b in zip(c, (r, g, b)))
    if dist((grey,) * 3) < dist(cube):
        return 232 + grey_i
    return 16 + 36 * ci[0] + 6 * ci[1] + ci[2]


def rgb_of_256(n):
    """Approximate RGB of a 256-colour index (for blending gradients)."""
    base = [(0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128),
            (128, 0, 128), (0, 128, 128), (192, 192, 192), (128, 128, 128),
            (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255),
            (255, 0, 255), (0, 255, 255), (255, 255, 255)]
    if n < 16:
        return base[n]
    if n >= 232:
        v = 8 + (n - 232) * 10
        return (v, v, v)
    n -= 16
    levels = (0, 95, 135, 175, 215, 255)
    return (levels[n // 36], levels[n // 6 % 6], levels[n % 6])


def parse_colour(v):
    """A colour from themes.json: (r, g, b) for "#rrggbb", an int for a
    256-colour number. ValueError otherwise."""
    if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 255:
        return v
    if isinstance(v, str) and len(v.lstrip("#")) == 6:
        h = v.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    raise ValueError(f"bad colour {v!r}")


def _code(colour, layer):
    """Escape code for a parsed colour; layer 38 is text, 48 background."""
    if isinstance(colour, int):
        return f"\x1b[{layer};5;{colour}m"
    if truecolor():
        r, g, b = colour
        return f"\x1b[{layer};2;{r};{g};{b}m"
    return f"\x1b[{layer};5;{rgb_to_256(*colour)}m"


def fg(v):
    return _code(parse_colour(v), 38)


def bg(v):
    return _code(parse_colour(v), 48)


def rgb(hex_colour):
    return fg(hex_colour)


def blend(stops, steps=GRADIENT_STEPS):
    """`steps` colours running evenly through the stops and back round to
    the first, so a flowing gradient loops without a seam."""
    pts = [p if isinstance(p, tuple) else rgb_of_256(p) for p in stops]
    pts = pts + pts[:1]
    out = []
    for k in range(steps):
        x = k / steps * (len(pts) - 1)
        i = int(x)
        t = x - i
        a, b = pts[i], pts[min(i + 1, len(pts) - 1)]
        out.append(tuple(round(a[c] + (b[c] - a[c]) * t) for c in range(3)))
    return out


# ---------------------------------------------------------------- themes

def _t(*codes):
    """A plain theme from seven 256-colour numbers, in PARTS order."""
    return tuple(c256(n) for n in codes)


# name -> (dim, text, error, extra, accent, good, warn)
THEMES = {
    "default": (GRAY, WHITE, RED, DARKRED, WHITE, GREEN, YELLOW),
    "ocean": _t(67, 195, 203, 131, 81, 79, 221),
    "forest": _t(65, 194, 167, 95, 114, 77, 179),
    "sunset": _t(96, 224, 197, 125, 215, 150, 222),
    # more from nature, in the spirit of forest
    "moss": _t(58, 187, 167, 94, 107, 113, 178),
    "pine": _t(23, 152, 174, 95, 30, 72, 179),
    "autumn": _t(94, 223, 160, 88, 172, 142, 214),
    "desert": _t(137, 230, 167, 131, 179, 143, 215),
    "meadow": _t(65, 230, 204, 132, 149, 120, 221),
    "jungle": _t(22, 157, 197, 89, 41, 47, 226),
    "cherry blossom": _t(139, 225, 161, 125, 218, 151, 223),
    "lavender": _t(97, 225, 168, 132, 183, 150, 222),
    "tundra": _t(102, 255, 174, 95, 117, 152, 223),
    "coral reef": _t(66, 230, 203, 131, 209, 80, 221),
    "volcanic": _t(94, 230, 196, 88, 202, 142, 214),
    "bamboo": _t(64, 194, 167, 95, 149, 113, 186),
    # well-known editor themes
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

# themes with effects, in the same form as themes.json
COMPLEX = {
    "rainbow": {
        "base": "default", "accent": 213,
        "gradient": ["#ff5f5f", "#ffaf5f", "#ffff5f", "#5fff5f", "#5fffff",
                     "#5f87ff", "#d75fff"],
        "by": "letter", "flow": 8,
    },
    "aurora": {
        "base": "nord", "background": "#0b1021", "accent": "#3ddc97",
        "gradient": ["#3ddc97", "#2bc4c4", "#5b8def", "#a06cd5"],
        "by": "word", "flow": 1,
    },
    "synthwave": {
        "base": "dracula", "background": "#241b2f", "accent": "#ff7edb",
        "dim": "#6d5a8a", "error": "#fe4450",
        "gradient": ["#ff7edb", "#f97e72", "#fede5d", "#72f1b8", "#36f9f6"],
        "by": "letter", "bold": True,
    },
    "ember": {
        "base": "volcanic", "background": "#160b07", "accent": "#ff8c1a",
        "heat": ["#8a8a8a", "#ffd75f", "#ffaf00", "#ff5f00", "#ff1f1f", "#ffffff"],
        "bold": True,
    },
    "deep sea": {
        "base": "ocean", "background": "#001b2e", "accent": "#00d4ff",
        "dim": "#2e5a78",
        "gradient": ["#90e0ef", "#00b4d8", "#0077b6", "#48cae4"],
        "by": "word", "flow": 0.5,
    },
    "phosphor": {
        "base": "matrix", "background": "#030803", "text": "#33ff66",
        "dim": "#145a24", "accent": "#66ff99", "bold": True,
    },
    "vaporwave": {
        "base": "catppuccin", "background": "#1d0f2b", "accent": "#01cdfe",
        "gradient": ["#ff71ce", "#01cdfe", "#05ffa1", "#b967ff", "#fffb96"],
        "by": "word", "italic": True,
    },
    "candy": {
        "base": "default", "accent": "#ffb3ba",
        "gradient": ["#ffb3ba", "#ffdfba", "#ffffba", "#baffc9", "#bae1ff"],
        "by": "letter", "flow": 3,
    },
    "midnight": {
        "base": "catppuccin", "background": "#0d1117", "text": "#e6edf3",
        "dim": "#484f58", "accent": "#58a6ff", "error": "#f85149",
    },
}


@dataclass(frozen=True)
class Effects:
    background: str = ""    # escape code, "" for the terminal's own
    gradient: tuple = ()    # text escape codes
    by: str = "letter"      # "letter" or "word"
    flow: float = 0.0       # gradient steps per second
    heat: tuple = ()        # text escape codes, coolest first
    bold: bool = False
    italic: bool = False


NO_EFFECTS = Effects()


def build(spec, known):
    """A (palette, effects) pair from a theme spec (a COMPLEX entry or a
    themes.json theme). `known` resolves "base". Raises ValueError/KeyError
    on a mistake."""
    if not isinstance(spec, dict):
        raise ValueError("should be an object")
    base = spec.get("base")
    if base is not None:
        if base not in known or known[base][0] is None:
            raise ValueError(f"unknown base {base!r}")
        palette = list(known[base][0])
    else:
        palette = [None] * len(PARTS)
    for i, part in enumerate(PARTS):
        if part in spec:
            palette[i] = fg(spec[part])
        elif palette[i] is None:
            raise KeyError(part)
    by = spec.get("by", "letter")
    if by not in ("letter", "word"):
        raise ValueError(f"by should be letter or word, not {by!r}")
    flow = spec.get("flow", 0)
    if not isinstance(flow, (int, float)) or isinstance(flow, bool) or flow < 0:
        raise ValueError(f"bad flow {flow!r}")
    gradient = spec.get("gradient", [])
    heat = spec.get("heat", [])
    if not isinstance(gradient, list) or not isinstance(heat, list):
        raise ValueError("gradient and heat should be lists of colours")
    if len(gradient) == 1:
        raise ValueError("a gradient needs at least two colours")
    effects = Effects(
        background=bg(spec["background"]) if "background" in spec else "",
        gradient=tuple(_code(c, 38) for c in blend([parse_colour(c) for c in gradient]))
        if gradient else (),
        by=by, flow=float(flow),
        heat=tuple(fg(c) for c in heat),
        bold=spec.get("bold") is True, italic=spec.get("italic") is True,
    )
    return tuple(palette), effects


def _builtin():
    plain = {name: (p, NO_EFFECTS) for name, p in THEMES.items()}
    out = dict(plain)
    for name, spec in COMPLEX.items():
        out[name] = build(spec, plain)
    return out


_cache = {"truecolor": None, "builtin": None}
_custom = {"key": None, "themes": {}, "error": ""}


def builtin_themes():
    """Every built-in theme as (palette, effects), rebuilt if true colour
    support is found to differ."""
    tc = truecolor()
    if _cache["builtin"] is None or _cache["truecolor"] != tc:
        _cache.update(truecolor=tc, builtin=_builtin())
    return _cache["builtin"]


def custom_themes():
    """Themes from themes.json, re-read whenever the file changes. A theme
    with a mistake in it is skipped; custom_error() says why."""
    path = storage.path(CUSTOM_FILE)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        _custom.update(key=None, themes={}, error="")
        return {}
    key = (path, mtime, truecolor())
    if key == _custom["key"]:
        return _custom["themes"]
    known = builtin_themes()
    themes, errors = {}, []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("should be an object of themes")
        for name, spec in data.items():
            try:
                if name in known:
                    raise ValueError("that name is built in")
                themes[name] = build(spec, known)
            except KeyError as e:
                errors.append(f"{name}: missing {e.args[0]}")
            except (TypeError, ValueError) as e:
                errors.append(f"{name}: {e}")
    except (OSError, ValueError) as e:
        errors.append(str(e))
    _custom.update(key=key, themes=themes, error="; ".join(errors))
    return themes


def custom_error():
    custom_themes()
    return _custom["error"]


def theme_names():
    names = list(THEMES) + list(COMPLEX)
    names.remove("mono")
    return names + ["mono"] + list(custom_themes())


def _theme(name):
    return (builtin_themes().get(name) or custom_themes().get(name)
            or builtin_themes()["default"])


class Styles:
    """Colour codes for the current theme. The mono theme, and the disguised
    lowkey mode, use only dim/underline so nothing on screen is coloured."""

    def __init__(self, theme="default", lowkey="off", accent_text=False):
        self.lowkey = lowkey
        self.quiet = theme == "mono" or lowkey == "disguised"
        self.effects = NO_EFFECTS
        if self.quiet:
            self.dim, self.ok, self.bad, self.extra = DIM, "", UND, UND + DIM
            self.title = "" if lowkey == "disguised" else WHITE
            self.good = self.warn = ""
        else:
            palette, self.effects = _theme(theme)
            (self.dim, self.ok, self.bad, self.extra,
             self.title, self.good, self.warn) = palette
            if accent_text:
                self.ok = self.title     # typed letters in the accent colour
        e = self.effects
        self.typed_attr = (BOLD if e.bold else "") + (ITALIC if e.italic else "")

    @property
    def background(self):
        return self.effects.background

    def typed(self, offset, word, combo=0, now=0.0):
        """Colour for a correctly typed letter: heat by combo, a gradient
        by letter or word (moving with time if it flows), or plain text."""
        e = self.effects
        if e.heat:
            colour = e.heat[min(combo // HEAT_STEP, len(e.heat) - 1)]
        elif e.gradient:
            k = offset if e.by == "letter" else word
            colour = e.gradient[(k + int(now * e.flow)) % len(e.gradient)]
        else:
            colour = self.ok
        return self.typed_attr + colour

    def conf_color(self, v):
        """Good at target, warning getting there, bad far off."""
        if self.quiet:
            return ""
        return self.good if v >= 1 else self.warn if v >= 0.6 else self.bad
