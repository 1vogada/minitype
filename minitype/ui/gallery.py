"""The gallery: every theme, one at a time and full screen, exactly as it
looks - its colours, background, border, art and a typing sample. Flip
through the themes and the art settings and pick."""

from ..config import ART_SCOPES, ART_STYLES
from ..terminal import console, keys, style
from ..terminal.art import ART_NAMES, THEME_ART
from ..terminal.style import INV, RESET
from .menu import Hints, title_lines
from .preview import theme_sample

HINTS = ("up/down (or ` ~) theme   left/right art style   [ ] picture   "
         "c its colours   v show art   b art behind text   enter use these   "
         "esc keep yours")

# the art settings the gallery changes besides the theme: (field, label,
# values, keys that step forward, keys that step back, the key to show)
ROWS = [
    ("art_style", "art style", ART_STYLES, (keys.RIGHT, "l"), (keys.LEFT, "h"), "left/right"),
    ("art", "show art", ART_SCOPES, ("v",), ("V",), "v"),
    ("art_behind", "art behind text", [False, True], ("b",), ("B",), "b"),
    ("art_picture", "picture", ["theme"] + ART_NAMES, ("]",), ("[",), "[ ]"),
    ("art_recolour", "picture colours", ["theme", "own"], ("c",), ("C",), "c"),
]


def _value_row(st, label, values, current, key_hint, theme_art=""):
    """A setting's values in a row, the current one lit; a long list just
    shows the current one and where it is."""
    if len(values) > 6:
        text = f"theme's ({theme_art or 'its own'})" if current == "theme" else current
        k = values.index(current) + 1 if current in values else 1
        return (f"  {st.dim}{label:<16}{RESET}{st.title}{INV} {text} {RESET}"
                f" {st.dim}{k}/{len(values)}   {key_hint}{RESET}")
    cells = []
    for v in values:
        text = ("on" if v else "off") if isinstance(v, bool) else str(v)
        cells.append(f"{st.title}{INV} {text} {RESET}" if v == current else f"{st.dim} {text} {RESET}")
    return f"  {st.dim}{label:<16}{RESET}{' '.join(cells)}   {st.dim}{key_hint}{RESET}"


def gallery(app):
    """Show the themes; up / down flip through them, left / right through
    the art styles, [ and ] through the pictures (any theme's, in this
    theme's colours, or with c in its own), v and b change where the art
    shows. Enter keeps what's on screen, esc puts back everything you had.
    Returns None (back to the menu)."""
    s = app.settings
    names = style.theme_names()
    mine = s.theme
    kept = {row[0]: getattr(s, row[0]) for row in ROWS}
    i = names.index(mine) if mine in names else 0
    hints = Hints(app)
    while True:
        name = names[i]
        s.theme = name
        st = app.styles()
        art = THEME_ART.get(name) or style.custom_specs().get(name, {}).get("art", "")
        lines = title_lines(app, st, "gallery") + [
            f"  {st.title}{name}{RESET}   {st.dim}{i + 1} of {len(names)}"
            f"{'   (yours)' if name == mine else ''}{RESET}",
            "",
            *["  " + row for row in theme_sample(app)],
            "",
            *[_value_row(st, label, values, getattr(s, field), hint,
                         art if isinstance(art, str) else "")
              for field, label, values, _, _, hint in ROWS],
        ]
        console.present(lines, 0, hints.lines(st, HINTS))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        handled = True
        row = next((r for r in ROWS if key in r[3] or key in r[4]), None)
        if row:
            field, _, values, fwd, _, _ = row
            cur = getattr(s, field)
            k = values.index(cur) if cur in values else 0
            setattr(s, field, values[(k + (1 if key in fwd else -1)) % len(values)])
        elif key in (keys.DOWN, keys.TAB, "`", "j"):
            i = (i + 1) % len(names)
        elif key in (keys.UP, keys.SHIFT_TAB, "~", "k"):
            i = (i - 1) % len(names)
        elif key == keys.HOME:
            i = 0
        elif key == keys.END:
            i = len(names) - 1
        elif key == keys.ENTER:
            app.notice = f"theme  {name}   art  {s.art_style}" + (
                f"   picture  {s.art_picture}" if s.art_picture != "theme" else "")
            app.save_settings()
            return None
        elif key in (keys.ESC, keys.CTRL_C):
            s.theme = mine
            for field, value in kept.items():
                setattr(s, field, value)
            app.styles()
            return None
        else:
            handled = False
        hints.note(key, handled)
