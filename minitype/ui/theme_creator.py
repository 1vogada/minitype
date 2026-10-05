"""The theme creator: build a theme from scratch or from any existing one,
with every colour, effect and fun modifier, and save it to themes.json.

The draft is a theme spec (the same form as themes.json) kept on the app,
so leaving and coming back carries on where you were. A preview line at
the top draws the draft through the real typing renderer, and the screen
takes the draft's background while you're here.

Colours: left/right step through the 256-colour palette, enter types an
exact one (0-255 or #rrggbb). Colours you don't set come from the base.
"""

import re

from ..terminal.art import ART_NAMES
from ..terminal.style import (BOUNCES, CARET_FX, PARTS, RESET, art_of_spec,
                              build, builtin_themes, custom_specs,
                              delete_custom_theme, fg, parse_colour,
                              rgb_to_256, save_custom_theme, theme_names,
                              theme_spec)
from ..util import cycle
from .menu import Item, Menu, title_lines
from .preview import theme_sample
from .prompt import prompt
from .screen import menu_loop

HINTS = "enter edit   esc back"
FLOWS = [0, 0.5, 1, 2, 4, 8, 12]
FROM_BASE = "from base"
SWATCH = "███"
CODE_256 = re.compile(r"\x1b\[38;5;(\d+)m")
CODE_RGB = re.compile(r"\x1b\[38;2;(\d+);(\d+);(\d+)m")
BASIC = {"\x1b[90m": 244, "\x1b[97m": 231, "\x1b[31m": 160, "\x1b[32m": 34,
         "\x1b[33m": 178, "\x1b[38;5;88m": 88}


class Draft:
    def __init__(self, name, spec, source="default"):
        self.name = name
        self.spec = spec
        self.source = source    # the theme it was started from

    @classmethod
    def from_theme(cls, theme):
        """Start from a theme: edit it if it's yours, else a copy of it."""
        spec = theme_spec(theme)
        name = theme if theme in custom_specs() else f"my {theme}"
        return cls(name, spec, theme)

    def set(self, key, value, default=None):
        """Set a key, dropping it when it's back at the default so the saved
        theme only lists what's different."""
        if value == default or value in ((), []):
            self.spec.pop(key, None)
        else:
            self.spec[key] = value

    def built(self):
        """(palette, effects) for the preview, or the error that stops it."""
        try:
            return build(self.spec, builtin_themes()), ""
        except KeyError as e:
            return None, f"missing {e.args[0]}"
        except (TypeError, ValueError) as e:
            return None, str(e)


def code_to_256(code):
    """The 256-colour index of a text colour escape code."""
    m = CODE_256.fullmatch(code)
    if m:
        return int(m.group(1))
    m = CODE_RGB.fullmatch(code)
    if m:
        return rgb_to_256(*(int(g) for g in m.groups()))
    return BASIC.get(code, 250)


def colour_index(value):
    c = parse_colour(value)
    return c if isinstance(c, int) else rgb_to_256(*c)


def parse_list(text):
    """Space or comma separated colours: numbers and #rrggbb."""
    out = []
    for tok in re.split(r"[\s,]+", text.strip()):
        if not tok:
            continue
        v = int(tok) if tok.isdigit() else tok if tok.startswith("#") else "#" + tok
        parse_colour(v)
        out.append(v)
    return out


def swatch(value):
    try:
        return fg(value) + SWATCH + RESET + f" {value}"
    except ValueError:
        return f"? {value}"


def build_items(app, d):
    s = d.spec
    known = builtin_themes()

    def base_palette():
        base = s.get("base", "default")
        return known.get(base, known["default"])[0] or known["default"][0]

    # ---- theme
    def rename():
        v = prompt("theme name:", d.name)
        if v:
            d.name = v.strip()

    names = [t for t in theme_names() if t != "mono"]

    def start_from(step):
        def go():
            fresh = Draft.from_theme(cycle(names, d.source, step=step))
            d.spec.clear()
            d.spec.update(fresh.spec)
            d.name, d.source = fresh.name, fresh.source
        return go

    def base_step(step):
        def go():
            plain = [t for t in names if t in known]
            d.spec["base"] = cycle(plain, s.get("base", "default"), step=step)
        return go

    items = [
        Item("", "name", rename, lambda: d.name, section="theme",
             help="what it's called in the theme list; enter to change"),
        Item("", "start from", start_from(1), lambda: d.source,
             back=start_from(-1), section="theme",
             help="replace the draft with a copy of a theme (yours are edited "
                  "in place). left/right go through them"),
        Item("", "base", base_step(1), lambda: s.get("base", "default"),
             back=base_step(-1), section="theme",
             help="the theme every colour you don't set comes from"),
    ]

    # ---- colours
    def colour_row(part, i):
        def value():
            if part in s:
                return swatch(s[part])
            code = base_palette()[i]
            return code + SWATCH + RESET + " from base"

        def step(dn):
            def go():
                cur = colour_index(s[part]) if part in s \
                    else code_to_256(base_palette()[i])
                s[part] = (cur + dn) % 256
            return go

        def edit():
            v = prompt(f"{part} colour (0-255 or #rrggbb, empty = from base):",
                       str(s.get(part, "")))
            if v is None:
                return
            if not v.strip():
                s.pop(part, None)
                return
            try:
                s[part] = parse_list(v)[0]
            except (ValueError, IndexError):
                app.notice = f"{v!r} isn't a colour"
        return Item("", part, step(1), value, back=step(-1), enter=edit,
                    section="colours",
                    help=f"left/right step through the 256 colours, enter types "
                         f"one. {COLOUR_HELP[part]}")

    items += [colour_row(p, i) for i, p in enumerate(PARTS)]

    # ---- background
    def bg_step(dn):
        def go():
            cur = colour_index(s["background"]) if "background" in s else 233 - dn
            s["background"] = (cur + dn) % 256
        return go

    def bg_edit():
        v = prompt("background (0-255 or #rrggbb, empty = none):",
                   str(s.get("background", "")))
        if v is None:
            return
        if not v.strip():
            s.pop("background", None)
            return
        try:
            s["background"] = parse_list(v)[0]
        except (ValueError, IndexError):
            app.notice = f"{v!r} isn't a colour"

    items.append(Item("", "background", bg_step(1),
                      lambda: swatch(s["background"]) if "background" in s else "none",
                      back=bg_step(-1), enter=bg_edit, section="background",
                      help="paints the whole screen; enter to type one, empty "
                           "for none"))

    # ---- gradient and heat
    def list_edit(key, label):
        def go():
            v = prompt(f"{label}, space separated (e.g. #ff5f5f 214 #5fafff; "
                       "empty = none):", " ".join(str(c) for c in s.get(key, [])))
            if v is None:
                return
            try:
                d.set(key, parse_list(v))
            except ValueError:
                app.notice = f"couldn't read {v!r} as colours"
        return go

    def list_value(key):
        cols = s.get(key, [])
        return " ".join(fg(c) + "█" + RESET for c in cols) if cols else "none"

    def by_flip():
        d.set("by", "word" if s.get("by", "letter") == "letter" else "letter",
              "letter")

    def flow_step(dn):
        return lambda: d.set("flow", cycle(FLOWS, s.get("flow", 0), step=dn), 0)

    items += [
        Item("", "gradient", list_edit("gradient", "gradient colours"),
             lambda: list_value("gradient"), section="gradient",
             help="colours your typed letters shade through; at least two"),
        Item("", "gradient by", by_flip, lambda: s.get("by", "letter"),
             back=by_flip, section="gradient",
             help="letter: each letter steps along the gradient. word: each word"),
        Item("", "flow", flow_step(1), lambda: f"{s.get('flow', 0):g}",
             back=flow_step(-1), section="gradient",
             help="steps a second the gradient moves; 0 holds it still"),
        Item("", "heat", list_edit("heat", "heat colours, coolest first"),
             lambda: list_value("heat"), section="gradient",
             help="typed text changes colour every 5 keys of combo, coolest "
                  "first; used instead of the gradient"),
    ]

    # ---- style and fun
    def flag(key, label, section, help):
        def flip():
            d.set(key, not s.get(key, False), False)
        return Item("", label, flip, lambda: "on" if s.get(key) else "off",
                    back=flip, section=section, help=help)

    def choice(key, label, options, section, help):
        def step(dn):
            return lambda: d.set(key, cycle(list(options), s.get(key, "off"),
                                            step=dn), "off")
        return Item("", label, step(1), lambda: s.get(key, "off"), back=step(-1),
                    section=section, help=help)

    items += [
        flag("bold", "bold", "style", "typed letters in bold"),
        flag("italic", "italic", "style", "typed letters in italics"),
        choice("bounce", "bounce", BOUNCES, "fun",
               "letters bob: gentle near the caret, wild everywhere"),
        flag("shake", "shake", "fun", "the text jolts sideways after a wrong key"),
        flag("pop", "pop", "fun", "the last few typed letters flash bright"),
        flag("fade", "fade", "fun", "typed letters dim as they fall behind"),
        choice("caret", "caret effect", CARET_FX, "fun",
               "pulse blinks the caret, rainbow cycles its colour"),
        flag("glitch", "glitch", "fun", "letters further ahead flicker to symbols"),
    ]

    # ---- art
    art_choices = [FROM_BASE, "none"] + ART_NAMES

    def art_value():
        art = s.get("art")
        if art is None:
            return FROM_BASE
        return art if isinstance(art, str) else f"your own ({len(art)} lines)"

    def art_step(dn):
        def go():
            cur = art_value() if art_value() in art_choices else FROM_BASE
            nxt = cycle(art_choices, cur, step=dn)
            if nxt == FROM_BASE:
                s.pop("art", None)
            else:
                s["art"] = nxt
        return go

    items.append(Item("", "art", art_step(1), art_value, back=art_step(-1),
                      section="art",
                      help="the ASCII picture in the screen's corner, shown "
                           "here as you pick. from base uses the base theme's; "
                           "your own lines can go in themes.json as a list"))

    # ---- save
    def save(use):
        def go():
            err = save_custom_theme(d.name, d.spec)
            if err:
                app.notice = f"not saved: {err}"
                return None
            if use:
                app.settings.theme = d.name.strip()
            app.notice = f"saved {d.name!r}" + (" and switched to it" if use else "")
            return None
        return go

    def delete():
        if d.name not in custom_specs():
            app.notice = f"{d.name!r} isn't saved, nothing to delete"
            return
        v = prompt(f"delete {d.name!r} from themes.json? type yes:")
        if v and v.lower() == "yes":
            err = delete_custom_theme(d.name)
            app.notice = f"couldn't delete: {err}" if err else f"deleted {d.name!r}"
            if not err and app.settings.theme == d.name:
                app.settings.theme = "default"

    items += [
        Item("", "save", save(False), section="save",
             help="add it to themes.json (replaces a theme of yours with the "
                  "same name)"),
        Item("", "save and use", save(True), section="save",
             help="save it and switch to it"),
        Item("", "delete", delete, section="save",
             help="remove this theme from themes.json"),
    ]
    return items


COLOUR_HELP = {
    "dim": "Untyped letters, hints and labels.",
    "text": "Letters you've typed correctly.",
    "error": "Wrong letters and failed results.",
    "extra": "Extra letters typed past the end of a word.",
    "accent": "Titles, the selected row, the caret on a space.",
    "good": "Keys at target speed and keys you never miss.",
    "warn": "Keys getting there and some misses.",
}


def draw(app, d, menu):
    built, err = d.built()
    # the preview draws in the draft, which also gives the screen its background
    preview = theme_sample(app, built) if built else [f"  can't preview: {err}"]
    # last, so the screen's border colour and corner art are the draft's
    st = app.styles(built, art=art_of_spec(d.spec)) if built else app.styles()
    lines = title_lines(app, st, f"theme creator - {d.name}")
    lines += ["  " + ln for ln in preview]
    strip = "  " + " ".join(f"{code}{SWATCH}{RESET}"
                            for code in (built[0] if built else ()))
    lines += [strip, ""]
    body, focus = menu.render(st, label_width=14)
    focus += len(lines)
    lines += body
    if app.notice:
        lines += ["", f"  {st.title}{app.notice}{RESET}"]
        app.notice = ""
    return lines, focus


def theme_creator(app):
    if getattr(app, "theme_draft", None) is None:
        app.theme_draft = Draft.from_theme(app.settings.theme)
    d = app.theme_draft
    menu = Menu(build_items(app, d), app.cursors, "creator")
    menu_loop(app, menu, lambda st, m: draw(app, d, m), HINTS)
    app.styles()                     # back to the real theme's background
    return None
