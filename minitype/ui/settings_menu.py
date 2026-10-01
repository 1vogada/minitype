from ..config import (CARETS, DIFFICULTIES, GOALS, KEYBOARD_MODES, LAYOUTS,
                      PACES, PCTS, STOP_MODES)
from ..terminal import console, keys
from ..terminal.style import RESET
from ..util import cycle
from ..words.bank import SOURCES
from .key_editor import key_editor
from .menu import Item, Menu

TEST, DRILLS, DISPLAY, DATA = range(4)   # row groups


def _on_off(s, name):
    return lambda: "on" if getattr(s, name) else "off"


def _toggle(s, name):
    return lambda: setattr(s, name, not getattr(s, name))


def _cycler(s, name, seq, missing=-1, step=1):
    return lambda: setattr(s, name, cycle(seq, getattr(s, name), missing, step))


def _bool_item(key, label, s, name, group, help=""):
    flip = _toggle(s, name)
    return Item(key, label, flip, _on_off(s, name), back=flip, help=help,
                group=group)


def _cycle_item(key, label, s, name, seq, value, group, missing=-1, help=""):
    return Item(key, label, _cycler(s, name, seq, missing), value,
                back=_cycler(s, name, seq, missing, step=-1), help=help,
                group=group)


def build_items(app):
    s = app.settings

    def load_list(step):
        nxt = app.bank.next_source(step)
        console.clear()
        print(f"\n  {app.styles().dim}loading {SOURCES[nxt][0]}...{RESET}")
        console.flush()
        app.bank.load(nxt)

    return [
        # the test itself
        _cycle_item("d", "difficulty", s, "difficulty", DIFFICULTIES,
                    lambda: s.difficulty, TEST,
                    help="expert: a wrong word ends the test   "
                         "master: a wrong key ends it"),
        _cycle_item("e", "stop on error", s, "stop_on_error", STOP_MODES,
                    lambda: s.stop_on_error, TEST,
                    help="letter: a wrong key doesn't move the cursor   "
                         "word: you can't leave a wrong word"),
        _bool_item("p", "punctuation", s, "punctuation", TEST,
                   help="capitals, commas, full stops and quotes"),
        _bool_item("n", "numbers", s, "numbers", TEST,
                   help="sprinkle numbers into word tests"),
        _bool_item("b", "blind", s, "blind", TEST,
                   help="no feedback until the results"),
        Item("l", "word list", lambda: load_list(1),
             lambda: app.bank.source_name, back=lambda: load_list(-1),
             help="built-in, or monkeytype's english lists (needs internet)",
             group=TEST),

        # practising weaknesses
        _bool_item("w", "bad keys", s, "weak", DRILLS,
                   help="bias words toward the keys you keep missing"),
        _cycle_item("r", "bad key %", s, "weak_pct", PCTS,
                    lambda: f"{s.weak_pct}%", DRILLS, missing=1,
                    help="that % of words will contain a bad key"),
        Item("k", "edit keys", lambda: key_editor(app),
             lambda: " ".join(app.stats.bad_keys()) or "none yet",
             help="pin or mute keys in the bad-key pool", group=DRILLS),
        _bool_item("m", "bad words", s, "bad_words", DRILLS,
                   help="replay words you got wrong"),
        _cycle_item("v", "bad word %", s, "bad_words_pct", PCTS,
                    lambda: f"{s.bad_words_pct}%", DRILLS, missing=1,
                    help="that % of words are replays of ones you got wrong"),

        # what you see and hear
        _bool_item("g", "ghost", s, "ghost", DISPLAY,
                   help="replays your last run as a dim caret"),
        _cycle_item("c", "pace caret", s, "pace", PACES,
                    lambda: f"{s.pace} wpm" if s.pace else "off", DISPLAY,
                    help="a dim caret moving at a fixed speed"),
        _cycle_item("u", "caret", s, "caret", CARETS, lambda: s.caret, DISPLAY,
                    help="how the cursor is drawn"),
        _bool_item("h", "show spaces", s, "show_spaces", DISPLAY,
                   help="draw the spaces between words as dots"),
        _cycle_item("j", "keyboard", s, "keyboard", KEYBOARD_MODES,
                    lambda: s.keyboard, DISPLAY,
                    help="on-screen keyboard highlighting the next key"),
        _cycle_item("o", "layout", s, "layout", list(LAYOUTS),
                    lambda: s.layout, DISPLAY,
                    help="layout of the on-screen keyboard"),
        _bool_item("z", "sound", s, "sound", DISPLAY,
                   help="beep on a wrong key"),
        _bool_item("q", "quiet", s, "quiet", DISPLAY,
                   help="no colour, no banner"),

        # progress
        _cycle_item("t", "daily goal", s, "daily_goal", GOALS,
                    lambda: f"{s.daily_goal} min" if s.daily_goal else "off", DATA,
                    help="minutes of typing to aim for each day"),
        Item("f", "save to disk", app.toggle_saving,
             lambda: "on" if app.saving() else "off", back=app.toggle_saving,
             help="keep settings, history and learn progress between sessions",
             group=DATA),
        Item("x", "reset", app.stats.reset_errors,
             lambda: f"{len(app.stats.missed)} bad words remembered",
             help="forget all key errors and bad words", group=DATA),
    ]


def draw(app, menu):
    st = app.styles()
    console.clear()
    print(f"\n  {st.title}settings{RESET}\n")
    menu.render(st, label_width=15)
    menu.render_help(st)
    if app.bank.note:
        print(f"  {st.dim}{app.bank.note}{RESET}")
    print(f"\n  {st.dim}arrows move   left/right change   esc back{RESET}")


def settings_menu(app):
    menu = Menu(build_items(app), app.cursors, "settings")
    while True:
        draw(app, menu)
        key = keys.read_key()
        if key in (keys.ESC, keys.CTRL_C):
            app.save()
            return None
        menu.handle(key)
