from ..config import DIFFICULTIES, PACES, PCTS
from ..terminal import console, keys
from ..terminal.style import RESET
from ..util import cycle
from ..words.bank import SOURCES
from .key_editor import key_editor
from .menu import Item, Menu


def _on_off(s, name):
    return lambda: "on" if getattr(s, name) else "off"


def _toggle(s, name):
    return lambda: setattr(s, name, not getattr(s, name))


def _cycler(s, name, seq, missing=-1, step=1):
    return lambda: setattr(s, name, cycle(seq, getattr(s, name), missing, step))


def _bool_item(key, label, s, name, help=""):
    flip = _toggle(s, name)
    return Item(key, label, flip, _on_off(s, name), back=flip, help=help)


def _cycle_item(key, label, s, name, seq, value, missing=-1, help=""):
    return Item(key, label, _cycler(s, name, seq, missing), value,
                back=_cycler(s, name, seq, missing, step=-1), help=help)


def build_items(app):
    s = app.settings

    def load_list(step):
        nxt = app.bank.next_source(step)
        console.clear()
        print(f"\n  {app.styles().dim}loading {SOURCES[nxt][0]}...{RESET}")
        console.flush()
        app.bank.load(nxt)

    return [
        _cycle_item("d", "difficulty", s, "difficulty", DIFFICULTIES,
                    lambda: s.difficulty,
                    help="expert: a wrong word ends the test   "
                         "master: a wrong key ends it"),
        _bool_item("p", "punctuation", s, "punctuation",
                   help="capitals, commas, full stops and quotes"),
        _bool_item("n", "numbers", s, "numbers",
                   help="sprinkle numbers into word tests"),
        _bool_item("b", "blind", s, "blind",
                   help="no feedback until the results"),
        _bool_item("w", "bad keys", s, "weak",
                   help="bias words toward the keys you keep missing"),
        _cycle_item("r", "bad key %", s, "weak_pct", PCTS,
                    lambda: f"{s.weak_pct}%", missing=1,
                    help="that % of words will contain a bad key"),
        Item("k", "edit keys", lambda: key_editor(app),
             lambda: " ".join(app.stats.bad_keys()) or "none yet",
             help="pin or mute keys in the bad-key pool"),
        _bool_item("m", "bad words", s, "bad_words",
                   help="replay words you got wrong"),
        _cycle_item("v", "bad word %", s, "bad_words_pct", PCTS,
                    lambda: f"{s.bad_words_pct}%", missing=1,
                    help="that % of words are replays of ones you got wrong"),
        Item("l", "word list", lambda: load_list(1),
             lambda: app.bank.source_name, back=lambda: load_list(-1),
             help="built-in, or monkeytype's english lists (needs internet)"),
        _bool_item("g", "ghost", s, "ghost",
                   help="replays your last run as a dim caret"),
        _cycle_item("c", "pace caret", s, "pace", PACES,
                    lambda: f"{s.pace} wpm" if s.pace else "off",
                    help="a dim caret moving at a fixed speed"),
        _bool_item("q", "quiet", s, "quiet", help="no colour, no banner"),
        Item("x", "reset", app.stats.reset_errors,
             lambda: f"{len(app.stats.missed)} bad words remembered",
             help="forget all key errors and bad words", group=1),
    ]


def draw(app, menu):
    st = app.styles()
    console.clear()
    print(f"\n  {st.title}settings{RESET}\n")
    menu.render(st, label_width=14)
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
            return None
        menu.handle(key)
