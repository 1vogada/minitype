"""Learn as you type on a magnetic keyboard (see keyboard_app): the
question at start-up, switching it from settings, and the status line.

At start, with "ask at start" on, a box asks whether to learn; the answer
becomes the keyboard learn setting and goes to the keyboard app. With it
off, the setting goes to the app as it is, unasked. Changing the setting
sends it straight away. Nothing else is ever asked: the app applies what it
learns by itself.
"""

from .. import keyboard_app
from ..terminal import console
from ..terminal.style import RESET
from .anywhere import ask_dialog

QUESTION = "Learn your keyboard's actuation while you type?"


def send(app):
    """Tell the keyboard app what the setting says; keep its answer."""
    s = app.settings
    app.keyboard_app = keyboard_app.switch(s.keyboard_learn, s.keyboard_server)
    return app.keyboard_app


def refresh(app):
    """One status call (the results screen); only when learning is meant to
    be on, so someone without the keyboard never waits on it."""
    s = app.settings
    if s.keyboard_learn:
        app.keyboard_app = keyboard_app.status(s.keyboard_server)
    return app.keyboard_app


def status_line(app, st):
    """The dim status line, or None while keyboard learn is off."""
    if not app.settings.keyboard_learn or app.keyboard_app is None:
        return None
    return f"{st.dim}{app.keyboard_app.line()}{RESET}"


def at_start(app):
    """The start-up question (if asked for), then the setting to the app."""
    s = app.settings
    if s.keyboard_ask:
        h = console.size()[1]
        st = app.styles()
        behind = ["", f"  {st.title}minitype{RESET}"] + [""] * max(0, h - 2)
        answer = ask_dialog(app, lambda: console.present(behind), QUESTION,
                            ("on", "off"), choice=0 if s.keyboard_learn else 1, esc=None)
        if answer is not None and answer != s.keyboard_learn:
            s.keyboard_learn = answer
            app.save_settings()
    return send(app)
