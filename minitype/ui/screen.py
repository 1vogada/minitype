from ..terminal import console, keys
from .menu import Hints


def menu_loop(app, menu, draw, hint_text, extra=None, on_back=None,
              back_keys=(keys.ESC, keys.CTRL_C)):
    """Run a menu screen until an action returns something or you go back.

    draw(st, menu)  returns (lines, focus) for the body of the screen
    extra(key)      optional; sees each key first and returns (handled, result)
    on_back()       what going back returns (None by default)

    The ui style is re-read every frame, so changing it in settings takes
    effect immediately, and a resize simply redraws at the new size.
    Settings are written to disk after every key that did something.
    """
    hints = Hints(app)
    while True:
        st = app.styles()
        menu.style = app.settings.ui_style
        menu.sidebar_tabs = app.settings.sidebar_tabs
        lines, focus = draw(st, menu)
        console.present(lines, focus,
                        hints.lines(st, f"{menu.nav_hint()}   {hint_text}"))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        if key in back_keys:
            return on_back() if on_back else None
        handled, result = extra(key) if extra else (False, None)
        if not handled:
            handled, result = menu.handle(key)
        hints.note(key, handled)
        if handled:
            app.save_settings()
        if result is not None:
            return result
