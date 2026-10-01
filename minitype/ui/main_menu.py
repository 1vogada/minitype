import os

from ..engine.spec import TestSpec
from ..nav import QUIT
from ..terminal import console, keys
from ..terminal.style import RESET
from .learn_menu import learn_menu
from .menu import Item, Menu
from .prompt import prompt
from .settings_menu import settings_menu


def ask_word_count():
    v = prompt("how many words?")
    if not v or not v.isdigit():
        return None
    n = max(1, min(1000, int(v)))
    return TestSpec(f"{n} words", "words", n)


def ask_seconds():
    v = prompt("how many seconds?")
    if not v or not v.isdigit():
        return None
    n = max(5, min(3600, int(v)))
    return TestSpec(f"{n} seconds", "time", n)


def ask_text():
    v = prompt("file path, or just paste some text:")
    if not v:
        return None
    try:
        if os.path.isfile(v):
            with open(v, encoding="utf-8", errors="ignore") as f:
                v = f.read()
    except OSError:
        pass
    words = v.split()
    if not words:
        return None
    return TestSpec(f"custom {len(words)} words", "words", len(words),
                    "custom", tuple(words))


def _preset(spec):
    return lambda: spec


def build_items(app):
    return [
        Item("1", "15 words", _preset(TestSpec("15 words", "words", 15))),
        Item("2", "30 words", _preset(TestSpec("30 words", "words", 30))),
        Item("3", "60 words", _preset(TestSpec("60 words", "words", 60))),
        Item("4", "30 seconds", _preset(TestSpec("30 seconds", "time", 30))),
        Item("5", "custom words", ask_word_count),
        Item("6", "custom time", ask_seconds),
        Item("7", "numbers", _preset(TestSpec("25 numbers", "words", 25, "numbers"))),
        Item("8", "custom text", ask_text),
        Item("9", "learn", lambda: learn_menu(app)),
        Item("s", "settings", lambda: settings_menu(app),
             value=lambda: " ".join(app.settings.flags()), group=1),
        Item("q", "quit", lambda: QUIT, group=1),
    ]


def draw(app, menu):
    st = app.styles()
    console.clear()
    print(f"\n  {st.title}minitype{RESET}\n" if not app.settings.quiet else "")
    menu.render(st)
    print()
    if app.bank.note:
        print(f"  {st.dim}{app.bank.note}{RESET}")
    best = app.stats.best()
    if best is not None:
        print(f"  {st.dim}best {best:.0f} wpm this session{RESET}")
    print(f"  {st.dim}arrows move   enter select   ctrl-q hide{RESET}")


def main_menu(app):
    menu = Menu(build_items(app), app.cursors, "main")
    while True:
        draw(app, menu)
        key = keys.read_key()
        if key in (keys.ESC, keys.CTRL_C):
            return QUIT
        _, result = menu.handle(key)
        if result is not None:
            return result
