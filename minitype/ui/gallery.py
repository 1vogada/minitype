"""The gallery: every theme, one at a time and full screen, exactly as it
looks - its colours, background, border, art and a typing sample. Flip
through the themes and the art styles and pick."""

from ..config import ART_STYLES
from ..terminal import console, keys, style
from ..terminal.art import THEME_ART
from ..terminal.style import INV, RESET
from .menu import Hints, title_lines
from .preview import theme_sample

HINTS = ("left/right (or ` ~) theme   up/down art style   "
         "enter use these   esc keep yours")


def gallery(app):
    """Show the themes; left / right flip through them, up / down through
    the art styles. Enter keeps what's on screen, esc puts back the theme
    and art style you had. Returns None (back to the menu)."""
    names = style.theme_names()
    mine, my_art = app.settings.theme, app.settings.art_style
    i = names.index(mine) if mine in names else 0
    a = ART_STYLES.index(my_art) if my_art in ART_STYLES else 0
    hints = Hints(app)
    while True:
        name = names[i]
        app.settings.theme = name
        app.settings.art_style = ART_STYLES[a]
        st = app.styles()
        art = THEME_ART.get(name) or style.custom_specs().get(name, {}).get("art", "")
        styles = "  ".join(f"{st.title}{INV} {s} {RESET}" if k == a else f"{st.dim} {s} {RESET}"
                           for k, s in enumerate(ART_STYLES))
        lines = title_lines(app, st, "gallery") + [
            f"  {st.title}{name}{RESET}   {st.dim}{i + 1} of {len(names)}"
            f"{'   (yours)' if name == mine else ''}{RESET}",
            "",
            *["  " + row for row in theme_sample(app)],
            "",
            f"  {st.dim}art style{RESET}  {styles}",
            f"  {st.dim}picture: {art if isinstance(art, str) and art else 'its own'}{RESET}",
        ]
        console.present(lines, 0, hints.lines(st, HINTS))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        handled = True
        if key in (keys.RIGHT, keys.TAB, "`", "l"):
            i = (i + 1) % len(names)
        elif key in (keys.LEFT, keys.SHIFT_TAB, "~", "h"):
            i = (i - 1) % len(names)
        elif key in (keys.DOWN, "j"):
            a = (a + 1) % len(ART_STYLES)
        elif key in (keys.UP, "k"):
            a = (a - 1) % len(ART_STYLES)
        elif key == keys.HOME:
            i = 0
        elif key == keys.END:
            i = len(names) - 1
        elif key == keys.ENTER:
            app.notice = f"theme  {name}   art  {ART_STYLES[a]}"
            app.save_settings()
            return None
        elif key in (keys.ESC, keys.CTRL_C):
            app.settings.theme, app.settings.art_style = mine, my_art
            app.styles()
            return None
        else:
            handled = False
        hints.note(key, handled)
