"""The settings screen.

There are no hotkeys here: typing filters the list instead. Plain words
must appear in a setting's name; words starting with # match its tags or
its section ("#colour", "#look"). The search bar shows whenever there's a
search. Backspace clears a plain search in one go; once it has a # in it,
backspace deletes a character at a time. [ and ] aren't typed into the
search: they switch sections, like tab and shift-tab.
"""

from ..words.shlokavitsa import STYLE_NAMES as SHLOKAVITSA_STYLES
from ..config import (BACKSPACE_MODES, BOOK_PAGES, BOOK_SCRIPTS, CARETS, DIFFICULTIES, FUNBOXES, GOALS,
                      KEYBOARD_MODES, LAYOUTS, LOWKEY_MODES, MEMORY_SECS,
                      MIN_ACCS, MIN_WPMS, PACES, PCTS, QUOTE_SOURCES,
                      SIDEBAR_TABS, STOP_MODES, THEME_NAMES, UI_STYLES)
from .. import storage
from ..terminal import console, keys
from ..terminal.style import INV, RESET
from ..util import cycle
from .book_menu import edit_book_filter, filter_label
from .key_editor import key_editor
from .menu import Item, Menu, title_lines
from .screen import menu_loop

HINTS = "type to search   #tag   tab / [ ] section   esc back"
BACK = object()     # returned from the key handler to leave the menu
NOT_SEARCHABLE = ("[", "]")   # these switch sections instead


class Builder:
    """Shorthands for the three kinds of settings row."""

    def __init__(self, s):
        self.s = s
        self.section = ""

    def flag(self, label, name, help="", tags=()):
        s = self.s

        def flip():
            setattr(s, name, not getattr(s, name))
        return Item("", label, flip, lambda: "on" if getattr(s, name) else "off",
                    back=flip, help=help, section=self.section, tags=tags)

    def choice(self, label, name, seq, value=None, help="", tags=()):
        s = self.s

        def step(d):
            return lambda: setattr(s, name, cycle(seq, getattr(s, name), step=d))
        return Item("", label, step(1), value or (lambda: str(getattr(s, name))),
                    back=step(-1), help=help, section=self.section, tags=tags)

    def item(self, label, action, value=None, back=None, help="", tags=()):
        return Item("", label, action, value, back=back, help=help,
                    section=self.section, tags=tags)


def _off_or(v, fmt):
    return lambda: fmt.format(v()) if v() else "off"


def _then(item, after):
    """Run `after` whenever the item's value changes, in either direction."""
    action, back = item.action, item.back

    def forward():
        action()
        after()

    def backward():
        back()
        after()
    item.action, item.back = forward, backward
    return item


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
        b.choice("difficulty", "difficulty", DIFFICULTIES,
                 help="expert: a wrong word ends the test. "
                      "master: a wrong key ends it",
                 tags=("hard", "fail", "expert", "master", "mistakes")),
        b.choice("stop on error", "stop_on_error", STOP_MODES,
                 help="letter: a wrong key doesn't move the cursor. "
                      "word: you can't leave a wrong word",
                 tags=("mistakes", "errors", "cursor", "letter", "word")),
        b.choice("backspace", "backspace", BACKSPACE_MODES,
                 help="off: no corrections at all (confidence mode). "
                      "freedom: you can go back into correct words too",
                 tags=("confidence", "freedom", "corrections", "delete", "mistakes")),
        b.flag("keep errors", "keep_errors",
               "letters you mistyped stay red even after you type them right, "
               "and backspace does nothing. Best with stop on error: letter",
               tags=("mistakes", "errors", "red", "backspace", "strict", "delete")),
        b.flag("punctuation", "punctuation",
               "capitals, commas, full stops and quotes",
               tags=("text", "symbols", "capitals")),
        b.flag("numbers", "numbers", "sprinkle numbers into word tests",
               tags=("text", "digits")),
        b.flag("blind", "blind", "no feedback until the results",
               tags=("feedback", "hide", "mistakes")),
    ]
    b.section = "challenges"
    items += [
        b.choice("min speed", "min_wpm", MIN_WPMS,
                 _off_or(lambda: s.min_wpm, "{} wpm"),
                 help="the test fails if your speed drops below this "
                      "(checked after the first few seconds)",
                 tags=("fail", "wpm", "speed", "rules")),
        b.choice("min accuracy", "min_acc", MIN_ACCS,
                 _off_or(lambda: s.min_acc, "{}%"),
                 help="the test fails if your accuracy drops below this",
                 tags=("fail", "accuracy", "mistakes", "rules")),
        b.choice("funbox", "funbox", FUNBOXES,
                 help="reversed: type words backwards. caps / random case: "
                      "change the letters. mirror: words are drawn flipped",
                 tags=("fun", "modifiers", "reversed", "caps", "mirror", "text")),
        b.choice("memory", "memory", MEMORY_SECS,
                 _off_or(lambda: s.memory, "{}s"),
                 help="the words disappear this many seconds into the test",
                 tags=("hide", "fun", "remember")),
    ]
    b.section = "drills"
    items += [
        b.flag("bad keys", "weak", "bias words toward the keys you keep missing",
               tags=("weak", "practice", "keys", "mistakes")),
        b.choice("bad key %", "weak_pct", PCTS, lambda: f"{s.weak_pct}%",
                 help="that % of words will contain a bad key",
                 tags=("weak", "practice", "keys", "percent")),
        b.item("edit keys", lambda: key_editor(app),
               lambda: " ".join(app.stats.bad_keys()) or "none yet",
               help="pin or mute keys in the bad-key pool",
               tags=("weak", "practice", "keys", "pin", "mute")),
        b.flag("bad words", "bad_words", "replay words you got wrong",
               tags=("practice", "words", "mistakes", "replay")),
        b.choice("bad word %", "bad_words_pct", PCTS, lambda: f"{s.bad_words_pct}%",
                 help="that % of words are replays of ones you got wrong",
                 tags=("practice", "words", "mistakes", "percent")),
    ]
    b.section = "words"
    items += [
        b.item("word list", lambda: load_list(1), lambda: app.bank.source,
               back=lambda: load_list(-1),
               help="built-in and themed lists work offline; the online "
                    "ones come from monkeytype. left hand, right hand and "
                    "home row follow your keyboard layout",
               tags=("source", "language", "english", "online", "vocabulary",
                     "text", "hand", "one hand", "left", "right")),
        b.choice("quotes from", "quote_source", QUOTE_SOURCES,
                 help="built-in: a small public-domain set. online: "
                      "monkeytype's collection (needs internet)",
                 tags=("quote", "source", "online", "text")),
        b.choice("book page", "book_page", BOOK_PAGES,
                 lambda: f"{s.book_page} words",
                 help="words per page in book mode; your place in each book "
                      "is kept when you change it",
                 tags=("book", "page", "length", "text")),
        b.item("book filter", lambda: edit_book_filter(app),
               lambda: filter_label(s.book_filter),
               help="symbols to remove from every book, e.g. ,.;:!?\"' - "
                    "enter to edit, type punct for all punctuation, leave "
                    "it empty for none",
               tags=("book", "filter", "punctuation", "symbols", "remove", "text")),
        b.choice("bulgarian books", "book_script", BOOK_SCRIPTS,
                 help="cyrillic: type Bulgarian books as written. "
                      "shlokavitsa: type them in Latin letters (the converted "
                      "book is saved next to the original)",
                 tags=("book", "bulgarian", "cyrillic", "shlokavitsa",
                       "latin", "language")),
        b.choice("shlokavitsa style", "shlokavitsa_style", SHLOKAVITSA_STYLES,
                 help="classic: ч 4, ш 6, щ 6t, я q, ж j. letters: ч ch, ш sh, "
                      "щ sht, я ya, ж zh. official: the 2009 transliteration, "
                      "ц ts, ъ a",
                 tags=("book", "bulgarian", "shlokavitsa", "latin", "language")),
    ]
    b.section = "look"
    items += [
        b.choice("theme", "theme", THEME_NAMES, help="colour theme",
                 tags=("colour", "color", "appearance", "dark", "mono")),
        b.choice("ui style", "ui_style", UI_STYLES,
                 help="list: one column. sidebar: details beside the menu. "
                      "tabs: one section at a time",
                 tags=("layout", "menu", "sidebar", "tabs", "appearance")),
        b.choice("sidebar tabs", "sidebar_tabs", SIDEBAR_TABS,
                 help="sidebar style only. top: a tab bar above it, one "
                      "section at a time. left: section buttons down the "
                      "left, that section's settings on the right",
                 tags=("layout", "menu", "sidebar", "tabs", "appearance")),
        b.choice("lowkey", "lowkey", LOWKEY_MODES,
                 help="minimal: only the words during a test. disguised: "
                      "no colour, looks like a plain command prompt",
                 tags=("hide", "stealth", "boss", "work", "minimal", "disguise")),
        b.flag("tape", "tape", "the words scroll along a single line",
               tags=("layout", "line", "scroll", "appearance")),
        b.choice("caret", "caret", CARETS, help="how the cursor is drawn",
                 tags=("cursor", "appearance")),
        b.flag("show spaces", "show_spaces", "draw the spaces between words as dots",
               tags=("whitespace", "dots", "appearance")),
        b.choice("keyboard", "keyboard", KEYBOARD_MODES,
                 help="on-screen keyboard highlighting the next key",
                 tags=("keys", "keyboard", "learn", "appearance")),
        _then(b.choice("layout", "layout", list(LAYOUTS),
                       help="your keyboard layout: the on-screen keyboard, and "
                            "which keys the left hand, right hand and home "
                            "row word lists use",
                       tags=("keyboard", "qwerty", "colemak", "dvorak", "azerty",
                             "qwertz", "hand")),
              app.layout_changed),
        b.flag("ghost", "ghost", "replays your last run as a dim caret",
               tags=("caret", "race", "replay")),
        b.choice("pace caret", "pace", PACES, _off_or(lambda: s.pace, "{} wpm"),
                 help="a dim caret moving at a fixed speed",
                 tags=("caret", "race", "speed", "wpm")),
        b.flag("sound", "sound", "beep on a wrong key",
               tags=("audio", "beep", "mistakes")),
        b.flag("key hints", "hints",
               "the key list at the bottom of each screen; press any unused "
               "key to see it while it's off",
               tags=("help", "keys", "footer")),
    ]
    b.section = "header"
    items += [
        b.flag("timer", "show_timer", "elapsed and remaining time",
               tags=("time", "live", "hud", "stats")),
        b.flag("progress", "show_progress", "words done out of the total",
               tags=("live", "hud", "stats")),
        b.flag("live wpm", "show_wpm", "your speed so far",
               tags=("speed", "live", "hud", "stats")),
        b.flag("combo", "show_combo", "correct keys in a row",
               tags=("streak", "live", "hud", "stats")),
    ]
    b.section = "results"
    items += [
        b.flag("speed chart", "res_chart", "speed over the test, errors marked",
               tags=("chart", "graph", "stats", "speed")),
        b.flag("key heatmap", "res_heatmap", "keyboard coloured by error rate",
               tags=("keyboard", "keys", "stats", "mistakes", "colour")),
        b.flag("personal best", "res_pb", "new PB banner and the gap to your PB",
               tags=("pb", "best", "record", "stats")),
        b.flag("worst keys", "res_worst_keys", "keys you missed most this test",
               tags=("keys", "mistakes", "stats")),
        b.flag("session keys", "res_session_keys", "your worst keys this session",
               tags=("keys", "mistakes", "stats")),
        b.flag("bad words", "res_bad_words", "words you got wrong this session",
               tags=("words", "mistakes", "stats")),
        b.flag("session", "res_history", "your last few speeds this session",
               tags=("history", "speed", "stats")),
    ]
    b.section = "progress"
    items += [
        b.choice("daily goal", "daily_goal", GOALS,
                 _off_or(lambda: s.daily_goal, "{} min"),
                 help="minutes of typing to aim for each day",
                 tags=("goal", "time", "practice", "streak")),
        b.item("save to disk", app.toggle_saving,
               lambda: "on" if app.saving() else "off", back=app.toggle_saving,
               help="keep history, personal bests, word timings and learn "
                    f"progress in {storage.path()}. Settings are always "
                    f"saved, in {storage.path(storage.SETTINGS)}",
               tags=("save", "file", "data", "history", "memory")),
        b.item("reset", app.stats.reset_errors,
               lambda: f"{len(app.stats.missed)} bad words remembered",
               help="forget all key errors and bad words",
               tags=("clear", "data", "mistakes", "forget")),
    ]
    return items


def search_keys(menu, key):
    """Typing goes into the search; returns (handled, result) for menu_loop."""
    q = menu.query
    if key in NOT_SEARCHABLE:
        return False, None                  # left to the menu: switch tabs
    if keys.is_char(key):
        if key != " " or q:                 # a leading space does nothing
            menu.set_query(q + key)
        return True, None
    if key == keys.BACKSPACE and q:
        menu.set_query(q[:-1] if "#" in q else "")
        return True, None
    if key in (keys.CTRL_BACKSPACE, keys.CTRL_W) and q:
        menu.set_query("")
        return True, None
    if key == keys.ESC:
        if q:
            menu.set_query("")
            return True, None
        return True, BACK
    return False, None


def search_bar(st, menu):
    """Shown whenever there's something in the search."""
    if not menu.query:
        return []
    n = len(menu.visible())
    return [f"  {st.dim}search{RESET}  {menu.query}{INV} {RESET}"
            f"   {st.dim}{n} match{'es' if n != 1 else ''}{RESET}", ""]


def draw(app, st, menu):
    lines = title_lines(app, st, "settings") + search_bar(st, menu)
    body, focus = menu.render(st, label_width=15)
    focus += len(lines)
    lines += body
    if app.bank.note:
        lines += ["", f"  {st.dim}{app.bank.note}{RESET}"]
    return lines, focus


def settings_menu(app):
    menu = Menu(build_items(app), app.cursors, "settings")
    menu_loop(app, menu, lambda st, m: draw(app, st, m), HINTS,
              extra=lambda key: search_keys(menu, key),
              back_keys=(keys.CTRL_C,))
    app.save()
    return None
