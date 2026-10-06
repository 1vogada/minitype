"""Ctrl-o: the settings from anywhere. In the middle of a test the test
is paused (its clock stops) and, coming back, a box asks whether to
resume it or leave it."""

import time

from ..terminal import console, keys
from ..terminal.style import INV, RESET


def open_settings(app):
    """Show the settings menu over wherever you are; then, if a test was
    under way, ask whether to carry on with it."""
    from .settings_menu import settings_menu       # it imports screens that import this
    running = app.current_test
    paused = time.time()
    settings_menu(app)
    app.save_settings()
    if not running:
        return
    test, redraw = running
    if test.start is None:
        return                       # nothing typed yet: nothing to lose
    if resume_dialog(app, redraw):
        test.resume_after(time.time() - paused)
    else:
        test.abandoned = True


def resume_dialog(app, redraw):
    """Yes / No over the screen behind: True to resume. Left / right (or
    tab) pick, enter confirms, y and n answer at once, esc resumes."""
    choice = 0
    try:
        while True:
            console.set_overlay(_box(app.styles(), choice))
            redraw()
            key = keys.read_key()
            if key in (keys.LEFT, keys.RIGHT, keys.TAB, keys.SHIFT_TAB):
                choice = 1 - choice
            elif key in ("y", "Y"):
                return True
            elif key in ("n", "N"):
                return False
            elif key == keys.ENTER:
                return choice == 0
            elif key == keys.ESC:
                return True
    finally:
        console.set_overlay(None)


def _box(st, choice):
    """The dialog: a double-lined box with the question and the two
    answers, the chosen one marked and highlighted."""
    inner = 26
    title = "Resume?"

    def option(label, on):
        return (f"{st.title}>{INV} {label} {RESET}" if on
                else f"{st.dim}  {label} {RESET}")
    answers = option("Yes", choice == 0) + "      " + option("No", choice == 1)
    pad_l = (inner - console.visible_len(answers)) // 2
    line = st.title + "║" + RESET
    centre = lambda text, n: " " * ((inner - n) // 2) + text + " " * (inner - n - (inner - n) // 2)
    return [f"{st.title}╔{'═' * inner}╗{RESET}",
            line + " " * inner + line,
            line + centre(f"{st.title}{title}{RESET}", len(title)) + line,
            line + " " * inner + line,
            line + " " * pad_l + answers + " " * (inner - pad_l - console.visible_len(answers)) + line,
            line + " " * inner + line,
            f"{st.title}╚{'═' * inner}╝{RESET}"]
