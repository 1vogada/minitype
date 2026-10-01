from ..config import (BACKSPACE_MODES, CARETS, DIFFICULTIES, FUNBOXES, GOALS,
                      KEYBOARD_MODES, LAYOUTS, LOWKEY_MODES, MEMORY_SECS,
                      MIN_ACCS, MIN_WPMS, PACES, PCTS, QUOTE_SOURCES,
                      STOP_MODES, THEME_NAMES, UI_STYLES)
from ..terminal import console
from ..terminal.style import RESET
from ..util import cycle
from .key_editor import key_editor
from .menu import Item, Menu, title_lines
from .screen import menu_loop

HINTS = "arrows move   left/right change   [ ] tabs   esc back"


class Builder:
    """Shorthands for the three kinds of settings row."""

    def __init__(self, s):
        self.s = s
        self.section = ""

    def flag(self, key, label, name, help=""):
        s = self.s

        def flip():
            setattr(s, name, not getattr(s, name))
        return Item(key, label, flip, lambda: "on" if getattr(s, name) else "off",
                    back=flip, help=help, section=self.section)

    def choice(self, key, label, name, seq, value=None, help=""):
        s = self.s

        def step(d):
            return lambda: setattr(s, name, cycle(seq, getattr(s, name), step=d))
        return Item(key, label, step(1), value or (lambda: str(getattr(s, name))),
                    back=step(-1), help=help, section=self.section)


def _off_or(v, fmt):
    return lambda: fmt.format(v()) if v() else "off"


def build_items(app):
    s = app.settings
    b = Builder(s)

    def load_list(step):
        nxt = app.bank.next_source(step)
        console.present(["", f"  {app.styles().dim}loading {nxt}...{RESET}"])
        app.load_words(nxt)

    items = []
    b.section = "test"
    items += [
        b.choice("d", "difficulty", "difficulty", DIFFICULTIES,
                 help="expert: a wrong word ends the test. "
                      "master: a wrong key ends it"),
        b.choice("e", "stop on error", "stop_on_error", STOP_MODES,
                 help="letter: a wrong key doesn't move the cursor. "
                      "word: you can't leave a wrong word"),
        b.choice("a", "backspace", "backspace", BACKSPACE_MODES,
                 help="off: no corrections at all (confidence mode). "
                      "freedom: you can go back into correct words too"),
        b.flag("p", "punctuation", "punctuation",
               "capitals, commas, full stops and quotes"),
        b.flag("n", "numbers", "numbers", "sprinkle numbers into word tests"),
        b.flag("b", "blind", "blind", "no feedback until the results"),
    ]
    b.section = "challenges"
    items += [
        b.choice("s", "min speed", "min_wpm", MIN_WPMS,
                 _off_or(lambda: s.min_wpm, "{} wpm"),
                 help="the test fails if your speed drops below this "
                      "(checked after the first few seconds)"),
        b.choice("y", "min accuracy", "min_acc", MIN_ACCS,
                 _off_or(lambda: s.min_acc, "{}%"),
                 help="the test fails if your accuracy drops below this"),
        b.choice("f", "funbox", "funbox", FUNBOXES,
                 help="reversed: type words backwards. caps / random case: "
                      "change the letters. mirror: words are drawn flipped"),
        b.choice("i", "memory", "memory", MEMORY_SECS,
                 _off_or(lambda: s.memory, "{}s"),
                 help="the words disappear this many seconds into the test"),
    ]
    b.section = "drills"
    items += [
        b.flag("w", "bad keys", "weak",
               "bias words toward the keys you keep missing"),
        b.choice("r", "bad key %", "weak_pct", PCTS, lambda: f"{s.weak_pct}%",
                 help="that % of words will contain a bad key"),
        Item("k", "edit keys", lambda: key_editor(app),
             lambda: " ".join(app.stats.bad_keys()) or "none yet",
             help="pin or mute keys in the bad-key pool", section=b.section),
        b.flag("m", "bad words", "bad_words", "replay words you got wrong"),
        b.choice("v", "bad word %", "bad_words_pct", PCTS,
                 lambda: f"{s.bad_words_pct}%",
                 help="that % of words are replays of ones you got wrong"),
    ]
    b.section = "words"
    items += [
        Item("l", "word list", lambda: load_list(1), lambda: app.bank.source,
             back=lambda: load_list(-1), section=b.section,
             help="built-in and themed lists work offline; the online "
                  "ones come from monkeytype"),
        b.choice("", "quotes from", "quote_source", QUOTE_SOURCES,
                 help="built-in: a small public-domain set. online: "
                      "monkeytype's collection (needs internet)"),
    ]
    b.section = "look"
    items += [
        b.choice("t", "theme", "theme", THEME_NAMES, help="colour theme"),
        b.choice("u", "ui style", "ui_style", UI_STYLES,
                 help="list: one column. sidebar: details beside the menu. "
                      "tabs: one section at a time"),
        b.choice("o", "lowkey", "lowkey", LOWKEY_MODES,
                 help="minimal: only the words during a test. disguised: "
                      "no colour, looks like a plain command prompt"),
        b.flag("", "tape", "tape", "the words scroll along a single line"),
        b.choice("", "caret", "caret", CARETS, help="how the cursor is drawn"),
        b.flag("h", "show spaces", "show_spaces",
               "draw the spaces between words as dots"),
        b.choice("", "keyboard", "keyboard", KEYBOARD_MODES,
                 help="on-screen keyboard highlighting the next key"),
        b.choice("", "layout", "layout", list(LAYOUTS),
                 help="layout of the on-screen keyboard"),
        b.flag("g", "ghost", "ghost", "replays your last run as a dim caret"),
        b.choice("c", "pace caret", "pace", PACES,
                 _off_or(lambda: s.pace, "{} wpm"),
                 help="a dim caret moving at a fixed speed"),
        b.flag("z", "sound", "sound", "beep on a wrong key"),
        b.flag("", "key hints", "hints",
               "the key list at the bottom of each screen; press any unused "
               "key to see it while it's off"),
    ]
    b.section = "header"
    items += [
        b.flag("", "timer", "show_timer", "elapsed and remaining time"),
        b.flag("", "progress", "show_progress", "words done out of the total"),
        b.flag("", "live wpm", "show_wpm", "your speed so far"),
        b.flag("", "combo", "show_combo", "correct keys in a row"),
    ]
    b.section = "results"
    items += [
        b.flag("", "speed chart", "res_chart", "speed over the test, errors marked"),
        b.flag("", "key heatmap", "res_heatmap", "keyboard coloured by error rate"),
        b.flag("", "personal best", "res_pb", "new PB banner and the gap to your PB"),
        b.flag("", "worst keys", "res_worst_keys", "keys you missed most this test"),
        b.flag("", "session keys", "res_session_keys", "your worst keys this session"),
        b.flag("", "bad words", "res_bad_words", "words you got wrong this session"),
        b.flag("", "session", "res_history", "your last few speeds this session"),
    ]
    b.section = "progress"
    items += [
        b.choice("", "daily goal", "daily_goal", GOALS,
                 _off_or(lambda: s.daily_goal, "{} min"),
                 help="minutes of typing to aim for each day"),
        Item("", "save to disk", app.toggle_saving,
             lambda: "on" if app.saving() else "off", back=app.toggle_saving,
             help="keep settings, history, personal bests and learn "
                  "progress between sessions", section=b.section),
        Item("x", "reset", app.stats.reset_errors,
             lambda: f"{len(app.stats.missed)} bad words remembered",
             help="forget all key errors and bad words", section=b.section),
    ]
    return items


def draw(app, st, menu):
    lines = title_lines(app, st, "settings")
    body, focus = menu.render(st, label_width=15)
    focus += len(lines)
    lines += body
    if app.bank.note:
        lines += ["", f"  {st.dim}{app.bank.note}{RESET}"]
    return lines, focus


def settings_menu(app):
    menu = Menu(build_items(app), app.cursors, "settings")
    menu_loop(app, menu, lambda st, m: draw(app, st, m), HINTS)
    app.save()
    return None
