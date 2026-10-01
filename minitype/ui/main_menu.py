import os

from ..config import CODE_LANGS, QUOTE_LENGTHS, TIMES, WORD_COUNTS
from ..engine.runner import MIN_SLOW_WORDS
from ..engine.spec import TestSpec
from ..nav import QUIT
from ..terminal.style import RESET
from ..util import cycle
from .learn_menu import learn_menu
from .menu import Item, Menu, title_lines
from .profile import goal_line, profile_screen
from .prompt import prompt
from .screen import menu_loop
from .settings_menu import settings_menu

HINTS = ("arrows move   left/right change   enter start   [ ] tabs   "
         "esc quit   ctrl-q hide")


def ask_length():
    v = prompt("how long? a number of words, or seconds like 45s:")
    if not v:
        return None
    v = v.lower().strip()
    if v.endswith("s") and v[:-1].isdigit():
        n = max(5, min(3600, int(v[:-1])))
        return TestSpec(f"{n} seconds", "time", n)
    if v.isdigit():
        n = max(1, min(1000, int(v)))
        return TestSpec(f"{n} words", "words", n)
    return None


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


def _mode(key, label, value, seq, attr, start, s, help):
    """A mode row: left/right pick its option, enter starts it."""
    def step(d):
        return lambda: setattr(s, attr, cycle(seq, getattr(s, attr), step=d))
    return Item(key, label, step(1), value, back=step(-1), enter=start,
                help=help, section="test")


def build_items(app):
    s = app.settings

    def slow_drill():
        n = len(app.stats.word_speed)
        if n < MIN_SLOW_WORDS:
            app.notice = (f"type a few tests first: {n}/{MIN_SLOW_WORDS} "
                          "words timed so far")
            return None
        return TestSpec("slow words", "words", s.word_amount, "slow")

    return [
        _mode("1", "time", lambda: f"{s.time_amount}s", TIMES, "time_amount",
              lambda: TestSpec(f"{s.time_amount} seconds", "time", s.time_amount),
              s, "type as many words as you can before the timer runs out"),
        _mode("2", "words", lambda: f"{s.word_amount}", WORD_COUNTS, "word_amount",
              lambda: TestSpec(f"{s.word_amount} words", "words", s.word_amount),
              s, "a fixed number of words, as fast as you can"),
        _mode("3", "quote", lambda: s.quote_length, QUOTE_LENGTHS, "quote_length",
              lambda: TestSpec("quote", "words", 0, "quote"),
              s, "type a real quote; choose built-in or online quotes in settings"),
        Item("4", "zen", lambda: TestSpec("zen", "zen", 0, "zen"),
             help="no target text, type whatever you like; enter finishes",
             section="test"),
        _mode("5", "code", lambda: s.code_lang, CODE_LANGS, "code_lang",
              lambda: TestSpec(f"code {s.code_lang}", "words", 0, "code"),
              s, "type a code snippet: symbols, brackets and keywords"),
        _mode("6", "numbers", lambda: f"{s.word_amount}", WORD_COUNTS, "word_amount",
              lambda: TestSpec(f"{s.word_amount} numbers", "words",
                               s.word_amount, "numbers"),
              s, "numbers only"),
        Item("7", "custom length", ask_length,
             help="any number of words, or any time like 45s", section="test"),
        Item("8", "custom text", ask_text,
             help="paste text or give a file path", section="test"),

        Item("9", "learn", lambda: learn_menu(app),
             help="keybr-style lessons that unlock letters as you get faster",
             section="practice"),
        Item("0", "slow words", slow_drill,
             lambda: f"{len(app.stats.word_speed)} words timed",
             help="a test made of the words you type slowest",
             section="practice"),

        Item("p", "profile", lambda: profile_screen(app),
             help="totals, speed chart and personal bests", section="app"),
        Item("s", "settings", lambda: settings_menu(app),
             value=lambda: " ".join(s.flags()),
             help="rules, challenges, word lists, look and feel", section="app"),
        Item("q", "quit", lambda: QUIT, section="app"),
    ]


def draw(app, st, menu):
    lines = title_lines(app, st, "minitype")
    body, focus = menu.render(st, label_width=15)
    focus += len(lines)
    lines += body
    notes = []
    if app.notice:
        notes.append(f"{st.title}{app.notice}{RESET}")
        app.notice = ""
    if app.bank.note:
        notes.append(f"{st.dim}{app.bank.note}{RESET}")
    best = app.stats.best()
    if best is not None:
        notes.append(f"{st.dim}best {best:.0f} wpm this session{RESET}")
    goal = goal_line(app, st)
    if goal:
        notes.append(goal)
    if notes:
        lines += [""] + ["  " + n for n in notes]
    return lines, focus


def main_menu(app):
    menu = Menu(build_items(app), app.cursors, "main")
    return menu_loop(app, menu, lambda st, m: draw(app, st, m), HINTS,
                     on_back=lambda: QUIT)
