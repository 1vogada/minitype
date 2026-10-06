"""The gallery: every theme, one at a time and full screen, exactly as it
looks - its colours, background, border, art and a typing sample. Flip
through them and pick one."""

from ..terminal import console, keys, style
from ..terminal.art import THEME_ART
from ..terminal.style import RESET
from .menu import Hints, title_lines
from .preview import theme_sample

HINTS = "left/right (or ` ~) browse   enter use this one   esc keep yours"


def gallery(app):
    """Show the themes; enter keeps the one on screen, esc goes back to the
    one you had. Returns None (back to the menu)."""
    names = style.theme_names()
    mine = app.settings.theme
    i = names.index(mine) if mine in names else 0
    hints = Hints(app)
    while True:
        name = names[i]
        app.settings.theme = name
        st = app.styles()
        art = THEME_ART.get(name) or style.custom_specs().get(name, {}).get("art", "")
        lines = title_lines(app, st, "gallery") + [
            f"  {st.title}{name}{RESET}   {st.dim}{i + 1} of {len(names)}"
            f"{'   (yours)' if name == mine else ''}{RESET}",
            "",
            *["  " + row for row in theme_sample(app)],
            "",
            f"  {st.dim}picture: {art if isinstance(art, str) and art else 'its own'}"
            f"   art style: {app.settings.art_style}{RESET}",
        ]
        console.present(lines, 0, hints.lines(st, HINTS))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        handled = True
        if key in (keys.RIGHT, keys.DOWN, keys.TAB, "`", "l", "j"):
            i = (i + 1) % len(names)
        elif key in (keys.LEFT, keys.UP, keys.SHIFT_TAB, "~", "h", "k"):
            i = (i - 1) % len(names)
        elif key == keys.HOME:
            i = 0
        elif key == keys.END:
            i = len(names) - 1
        elif key == keys.ENTER:
            app.notice = f"theme  {name}"
            app.save_settings()
            return None
        elif key in (keys.ESC, keys.CTRL_C):
            app.settings.theme = mine
            app.styles()
            return None
        else:
            handled = False
        hints.note(key, handled)
