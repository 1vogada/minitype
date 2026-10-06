from ..terminal import console, keys, style
from .menu import Hints

HINT_GAP = "   "
THEME_KEY = "`"              # on any menu: the next theme, no trip to settings


def next_theme(app, step=1):
    """Switch to the next theme (built-in, then your own) and say which."""
    names = style.theme_names()
    cur = names.index(app.settings.theme) if app.settings.theme in names else -1
    app.settings.theme = names[(cur + step) % len(names)]
    app.notice = f"theme  {app.settings.theme}   (` for the next)"
    return True


def screen_hints(menu, text):
    """A screen's own hints, minus the ones the two-column layout changes
    (the menu's own hint covers those): on the section buttons enter opens
    a section rather than "enter start", and in the rows esc goes back to
    the sections rather than "esc back" / "esc quit"."""
    if menu.columns:
        drop = "enter " if menu.on_sections else "esc "
        text = HINT_GAP.join(h for h in text.split(HINT_GAP)
                             if not h.startswith(drop))
    return text


def menu_loop(app, menu, draw, hint_text, extra=None, on_back=None,
              back_keys=(keys.ESC, keys.CTRL_C)):
    """Run a menu screen until an action returns something or you go back.

    draw(st, menu)  returns (lines, focus) for the body of the screen
    extra(key)      optional; sees each key first and returns (handled, result)
    on_back()       what going back returns (None by default)

    The ui style is re-read every frame, so changing it in settings takes
    effect immediately, and a resize simply redraws at the new size.
    Settings are written to disk after every key that did something.
    In the two-column layout, esc in the rows goes back to the sections
    before it leaves the screen. ` switches to the next theme, unless the
    screen takes the key itself (a search box you're typing in).
    """
    hints = Hints(app)
    while True:
        st = app.styles()
        menu.style = app.settings.ui_style
        menu.sidebar_tabs = app.settings.sidebar_tabs
        lines, focus = draw(st, menu)
        console.present(lines, focus,
                        hints.lines(st, f"{menu.nav_hint()}   "
                                        f"{screen_hints(menu, hint_text)}"))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        if key == keys.ESC and key in back_keys and menu.back_out():
            continue                   # out of the rows, onto the sections
        if key in back_keys:
            return on_back() if on_back else None
        handled, result = extra(key) if extra else (False, None)
        if not handled and key == THEME_KEY:
            handled, result = next_theme(app), None
        if not handled:
            handled, result = menu.handle(key)
        hints.note(key, handled)
        if handled:
            app.save_settings()
        if result is not None:
            return result
