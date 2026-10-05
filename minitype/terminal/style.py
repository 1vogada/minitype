"""Colours and themes.

A theme is seven colours (PARTS) and, optionally, effects:

    background   the whole screen is painted this colour
    gradient     typed letters shade through these colours, per letter or
                 per word ("by"), and with "flow" the gradient moves along
                 that many steps a second
    heat         typed letters change colour with your combo, coolest
                 first: every HEAT_STEP correct keys in a row moves one on
    bold, italic how typed letters are drawn
    bounce       letters bob up and down: "gentle" near the caret, "wild"
    shake        the text jolts sideways after a wrong key
    pop          the last few typed letters flash bright
    fade         typed letters dim the further behind they fall
    caret        "pulse" (blinks) or "rainbow" (cycles colour)
    glitch       letters further ahead flicker to symbols
    art          the picture in the screen's corner: a name from art.py,
                 "none", or a list of lines of your own

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
from dataclasses import dataclass, replace

from .. import storage
from .art import THEME_ART
from .art import resolve as resolve_art

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
EFFECT_KEYS = ("background", "gradient", "by", "flow", "heat", "bold", "italic",
               "bounce", "shake", "pop", "fade", "caret", "glitch", "art")
ART_MAX_COLS, ART_MAX_ROWS = 40, 12     # a themes.json picture's limits


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
        "by": "letter", "flow": 8, "caret": "rainbow",
    },
    # fun ones: movement and flourishes
    "party": {
        "base": "default", "background": "#12001f", "accent": "#ff5fd7",
        "gradient": ["#ff005f", "#ffaf00", "#d7ff00", "#00ffaf", "#00afff",
                     "#af5fff"],
        "by": "letter", "flow": 12, "bold": True,
        "bounce": "gentle", "pop": True, "caret": "rainbow",
    },
    "glitch": {
        "base": "matrix", "background": "#000000", "text": "#e0e0e0",
        "accent": "#ff0055", "error": "#ff0055",
        "gradient": ["#00ff9f", "#00b8ff", "#001eff", "#bd00ff", "#d600ff"],
        "by": "word", "flow": 2,
        "glitch": True, "shake": True, "caret": "pulse",
    },
    "bubbly": {
        "base": "candy", "background": "#2b1b2e",
        "gradient": ["#ffb3ba", "#ffdfba", "#ffffba", "#baffc9", "#bae1ff",
                     "#e0bbff"],
        "by": "word", "flow": 1, "bounce": "wild", "pop": True,
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
    # fun modifiers: movement and flourishes, see engine/render.py
    bounce: str = "off"     # letters bob: off, gentle (near the caret), wild
    shake: bool = False     # the text jolts sideways after a wrong key
    pop: bool = False       # the last few typed letters flash bright
    fade: bool = False      # typed letters dim the further behind they fall
    caret_fx: str = "off"   # off, pulse (blinks) or rainbow (cycles colour)
    glitch: bool = False    # letters further ahead flicker to symbols


NO_EFFECTS = Effects()

# fun modifiers, as named in themes.json and settings, and their values
BOUNCES = ("off", "gentle", "wild")
CARET_FX = ("off", "pulse", "rainbow")
MODIFIERS = {          # themes.json key -> Effects field
    "bounce": "bounce", "shake": "shake", "pop": "pop", "fade": "fade",
    "caret": "caret_fx", "glitch": "glitch",
}
RAINBOW = tuple(c256(n) for n in (196, 208, 226, 46, 51, 21, 201))


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
    bounce = spec.get("bounce", "off")
    if bounce not in BOUNCES:
        raise ValueError(f"bounce should be one of {', '.join(BOUNCES)}")
    caret = spec.get("caret", "off")
    if caret not in CARET_FX:
        raise ValueError(f"caret should be one of {', '.join(CARET_FX)}")
    art = spec.get("art")
    if art is not None and art != "none" and resolve_art(art) is None:
        raise ValueError("art should be a picture name, \"none\", or a list "
                         "of lines")
    if isinstance(art, list) and (len(art) > ART_MAX_ROWS
                                  or max(map(len, art)) > ART_MAX_COLS):
        raise ValueError(f"art can be at most {ART_MAX_COLS} wide and "
                         f"{ART_MAX_ROWS} tall")
    effects = Effects(
        background=bg(spec["background"]) if "background" in spec else "",
        gradient=tuple(_code(c, 38) for c in blend([parse_colour(c) for c in gradient]))
        if gradient else (),
        by=by, flow=float(flow),
        heat=tuple(fg(c) for c in heat),
        bold=spec.get("bold") is True, italic=spec.get("italic") is True,
        bounce=bounce, caret_fx=caret,
        shake=spec.get("shake") is True, pop=spec.get("pop") is True,
        fade=spec.get("fade") is True, glitch=spec.get("glitch") is True,
    )
    return tuple(palette), effects


def _builtin():
    """Plain themes first, then the complex ones; a complex theme can use
    any theme built before it (plain or complex) as its base."""
    out = {name: (p, NO_EFFECTS) for name, p in THEMES.items()}
    pending = dict(COMPLEX)
    while pending:
        ready = {n: s for n, s in pending.items() if s.get("base", "default") in out}
        if not ready:
            raise ValueError(f"unknown base in {', '.join(pending)}")
        for name, spec in ready.items():
            out[name] = build(spec, out)
            del pending[name]
    return out


_cache = {"truecolor": None, "builtin": None}
_custom = {"key": None, "themes": {}, "specs": {}, "error": ""}


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
        _custom.update(key=None, themes={}, specs={}, error="")
        return {}
    key = (path, mtime, truecolor())
    if key == _custom["key"]:
        return _custom["themes"]
    known = builtin_themes()
    themes, specs, errors = {}, {}, []
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
                specs[name] = spec
            except KeyError as e:
                errors.append(f"{name}: missing {e.args[0]}")
            except (TypeError, ValueError) as e:
                errors.append(f"{name}: {e}")
    except (OSError, ValueError) as e:
        errors.append(str(e))
    _custom.update(key=key, themes=themes, specs=specs, error="; ".join(errors))
    return themes


def custom_specs():
    """The themes from themes.json as written there, for editing."""
    custom_themes()
    return _custom.get("specs", {})


def theme_spec(name):
    """A theme as a spec the creator can start from: a themes.json or
    complex theme as written, a plain built-in one as {"base": name}."""
    if name in custom_specs():
        return json.loads(json.dumps(custom_specs()[name]))
    if name in COMPLEX:
        return json.loads(json.dumps(COMPLEX[name]))
    if THEMES.get(name) is not None:
        return {"base": name}
    return {"base": "default"}


def _read_custom_file():
    """themes.json as a dict, {} if there's none. ValueError if it isn't
    valid, so a broken file is never overwritten."""
    path = storage.path(CUSTOM_FILE)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("themes.json isn't an object of themes")
    return data


def _write_custom_file(data):
    path = storage.path(CUSTOM_FILE)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    _custom["key"] = None                  # read it again next time


def save_custom_theme(name, spec):
    """Add or replace a theme in themes.json. Returns "" or what's wrong;
    a theme that doesn't build, or a broken themes.json, isn't written."""
    name = name.strip()
    if not name:
        return "the theme needs a name"
    if name in builtin_themes():
        return f"{name!r} is a built-in theme, pick another name"
    try:
        build(spec, builtin_themes())
        data = _read_custom_file()
    except KeyError as e:
        return f"missing {e.args[0]}"
    except (OSError, TypeError, ValueError) as e:
        return str(e)
    data[name] = spec
    try:
        _write_custom_file(data)
    except OSError as e:
        return str(e)
    return ""


def delete_custom_theme(name):
    try:
        data = _read_custom_file()
        if name in data:
            del data[name]
            _write_custom_file(data)
    except (OSError, ValueError) as e:
        return str(e)
    return ""


def custom_error():
    custom_themes()
    return _custom["error"]


def theme_names():
    names = list(THEMES) + list(COMPLEX)
    names.remove("mono")
    return names + ["mono"] + list(custom_themes())


def art_of_spec(spec, art_style="detailed", seen=()):
    """The corner art a theme spec asks for: its own "art", or its base
    theme's when it doesn't say. A list of art pieces, biggest first; []
    for none. art_style "og" leaves the detailed pictures out."""
    art = spec.get("art")
    if art == "none":
        return []
    if art is not None:
        return resolve_art(art, art_style) or []
    return theme_art(spec.get("base", "default"), art_style, seen)


def theme_art(name, art_style="detailed", seen=()):
    """A theme's corner art as pieces, biggest first; [] for none."""
    if name in seen:
        return []                      # a base loop in themes.json
    if name in custom_specs():
        return art_of_spec(custom_specs()[name], art_style, seen + (name,))
    return resolve_art(THEME_ART.get(name), art_style) or []


def _with_modifiers(effects, settings):
    """Apply the fun-modifier settings on top of a theme's effects."""
    changes = {}
    for field, value in settings.items():
        if value == "theme" or not hasattr(effects, field):
            continue
        if isinstance(getattr(effects, field), bool):
            changes[field] = value == "on"
        else:
            changes[field] = value
    return replace(effects, **changes)


def _theme(name):
    return (builtin_themes().get(name) or custom_themes().get(name)
            or builtin_themes()["default"])


class Styles:
    """Colour codes for the current theme. The mono theme, and the disguised
    lowkey mode, use only dim/underline so nothing on screen is coloured."""

    def __init__(self, theme="default", lowkey="off", accent_text=False,
                 background=True, gradient=True, flow=True, heat=True,
                 text_style=True, modifiers=None, speed=1.0, reverse=False,
                 custom=None):
        """The keyword switches turn a theme's effects off one by one:
        its background, gradient, the gradient's movement, heat, and
        bold / italic letters.

        modifiers   {Effects field: setting} for the fun modifiers, where
                    "theme" keeps what the theme says, "off"/"on" force a
                    switch and anything else is the value (e.g. "wild")
        speed       multiplies how fast everything animated moves
        reverse     gradients flow the other way
        custom      a (palette, effects) pair to use instead of `theme`
                    (the theme creator's draft)"""
        self.lowkey = lowkey
        self.quiet = theme == "mono" or lowkey == "disguised"
        self.speed = speed * (-1 if reverse else 1)
        palette, effects = custom or _theme(theme)
        if self.quiet:
            self.dim, self.ok, self.bad, self.extra = DIM, "", UND, UND + DIM
            self.title = "" if lowkey == "disguised" else WHITE
            self.good = self.warn = ""
            # no colour, but movement still works (not when disguised)
            effects = replace(NO_EFFECTS, bounce=effects.bounce,
                              shake=effects.shake, glitch=effects.glitch)
        else:
            effects = replace(
                effects,
                background=effects.background if background else "",
                gradient=effects.gradient if gradient else (),
                flow=effects.flow if flow else 0.0,
                heat=effects.heat if heat else (),
                bold=effects.bold and text_style,
                italic=effects.italic and text_style)
            (self.dim, self.ok, self.bad, self.extra,
             self.title, self.good, self.warn) = palette
            if accent_text:
                self.ok = self.title     # typed letters in the accent colour
        effects = _with_modifiers(effects, modifiers or {})
        if lowkey == "disguised":
            effects = NO_EFFECTS         # stealth: nothing moves either
        elif self.quiet:
            effects = replace(effects, pop=False, caret_fx="off"
                              if effects.caret_fx == "rainbow" else effects.caret_fx)
        self.effects = effects
        e = self.effects
        self.typed_attr = (BOLD if e.bold else "") + (ITALIC if e.italic else "")

    @property
    def animated(self):
        """Whether anything on the typing screen moves on its own."""
        e = self.effects
        return bool((e.gradient and e.flow) or e.bounce != "off" or e.glitch
                    or e.caret_fx != "off" or e.shake)

    def art_palette(self):
        """The theme's colours by name, for painting corner art. A theme
        without a colour for a part (mono) falls back to the accent."""
        return {"dim": self.dim, "text": self.ok or self.title,
                "error": self.bad if not self.quiet else self.title,
                "extra": self.extra if not self.quiet else self.dim,
                "accent": self.title, "good": self.good or self.title,
                "warn": self.warn or self.title}

    def caret_colour(self, now):
        """The rainbow caret's colour at this moment."""
        return RAINBOW[int(now * 6 * abs(self.speed)) % len(RAINBOW)]

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
            shift = int(now * e.flow * self.speed)
            colour = e.gradient[(k + shift) % len(e.gradient)]
        else:
            colour = self.ok
        return self.typed_attr + colour

    def conf_color(self, v):
        """Good at target, warning getting there, bad far off."""
        if self.quiet:
            return ""
        return self.good if v >= 1 else self.warn if v >= 0.6 else self.bad
