"""The welcome screen: the first run, and after "reset settings".

"welcome to minitype", and a choice of setups (settings.SETUPS) to start
from. Moving between them shows each one live - the screen itself turns
into it, pictures and colours and all - and enter (or esc, or a setup's
number) starts with the one you're on. Everything can be changed later in
settings; the screen says so.
"""

from ..settings import SETUPS
from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Item, Menu

# what each setup is, for its row; a setup without a line here just shows
# its name
DESCRIBE = {
    "clean": "quiet and monochrome: no pictures, no effects, just the words",
    "art": "a picture behind everything, colours that flow and heat up as you type",
}
INTRO = ["a typing game for your terminal.",
         "pick a setup to start with - you can change anything later in settings."]


def _lines(app, st, menu):
    lines = ["", f"  {st.title}welcome to minitype{RESET}", ""]
    lines += [f"  {st.dim}{line}{RESET}" for line in INTRO] + [""]
    body, focus = menu.render(st, label_width=8)
    return lines + body, focus + len(lines)


def welcome(app):
    """Show the welcome screen until a setup is picked; apply and save it.
    Returns the setup's name."""
    names = list(SETUPS)
    items = [Item(str(k + 1), name, (lambda n=name: n),
                  lambda n=name: DESCRIBE.get(n, ""))
             for k, name in enumerate(names)]
    menu = Menu(items, {}, "welcome")
    shown = None
    chosen = None
    while chosen is None:
        if menu.selected.label != shown:         # show the setup you're on, live
            shown = menu.selected.label
            app.use_setup(shown)
        st = app.styles()
        menu.style, menu.sidebar_tabs = "list", "off"
        lines, focus = _lines(app, st, menu)
        # its own hint line, always: a setup may turn the key hints off
        console.present(lines, focus, ["", f"  {st.dim}up/down choose   enter start{RESET}"])
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        if key == keys.ESC:
            chosen = menu.selected.label
            continue
        _, result = menu.handle(key)
        if result is not None:
            chosen = result
    app.use_setup(chosen)
    app.first_run = False
    app.save_settings()
    return chosen
