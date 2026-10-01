"""Book mode: pick a book from the books folder and choose where to read.

Each book is a row. Left/right turn one page, pgup/pgdn ten, g asks for a
page number, and enter types the page you're on. The page's opening words
show under the row so you can see where you are. Bulgarian books can be
typed in Cyrillic or in шльокавица (the options under the books).
"""

import os
import string

from ..config import BOOK_SCRIPTS
from ..terminal import keys
from ..terminal.style import RESET
from ..util import cycle
from ..words import books
from ..words.shlokavitsa import STYLE_NAMES
from .menu import Item, Menu, title_lines
from .prompt import prompt
from .screen import menu_loop

HINTS = ("enter read   left/right page   pgup/pgdn 10 pages   g go to page   "
         "o open folder   r refresh   esc back")
JUMP = 10
LIBRARY = "library"     # section holding the book rows


def _turn(app, title, step):
    books.set_page(app, title, books.page_of(app, title) + step)


def _page_label(app, title):
    total = books.page_count(len(books.words(app, title)), app.settings.book_page)
    script = books.script_label(app, title)
    return f"page {books.page_of(app, title) + 1}/{total}" + \
        (f"   {script}" if script else "")


def _cycle(app, name, seq, step):
    s = app.settings
    setattr(s, name, cycle(seq, getattr(s, name), step=step))


def filter_label(spec):
    chars = books.filter_chars(spec)
    if not chars:
        return "none"
    return "all punctuation" if chars == string.punctuation else chars


def edit_book_filter(app):
    """Ask for the characters to remove from books. Esc keeps the old ones."""
    s = app.settings
    v = prompt("symbols to remove from books (punct = all punctuation, "
               "empty = none):", s.book_filter)
    if v is not None:
        s.book_filter = v


def _open_folder(app):
    try:
        os.startfile(books.folder())
    except OSError:
        app.notice = f"couldn't open {books.folder()}"


def build_items(app, refresh):
    items = []
    for title in books.titles():
        try:
            if not books.source_words(title):
                continue                     # nothing typeable in it
        except OSError:
            continue
        items.append(Item(
            "", title,
            action=lambda t=title: _turn(app, t, 1),
            back=lambda t=title: _turn(app, t, -1),
            value=lambda t=title: _page_label(app, t),
            enter=lambda t=title: books.page_spec(app, t),
            help=lambda t=title: books.preview(app, t),
            section=LIBRARY))
    s = app.settings
    items += [
        Item("", "filter", lambda: edit_book_filter(app),
             lambda: filter_label(s.book_filter),
             help="symbols to remove from every book, e.g. ,.;:!?\"' - enter "
                  "to edit, type punct for all punctuation, leave it empty "
                  "for none",
             section="options"),
        Item("", "bulgarian books",
             lambda: _cycle(app, "book_script", BOOK_SCRIPTS, 1),
             lambda: s.book_script,
             back=lambda: _cycle(app, "book_script", BOOK_SCRIPTS, -1),
             help="cyrillic: type Bulgarian books as written. shlokavitsa: "
                  "type them in Latin letters; the converted book is saved "
                  f"in {os.path.join(books.folder(), books.CONVERTED)}. Your "
                  "page is the same in both",
             section="options"),
        Item("", "shlokavitsa style",
             lambda: _cycle(app, "shlokavitsa_style", STYLE_NAMES, 1),
             lambda: s.shlokavitsa_style,
             back=lambda: _cycle(app, "shlokavitsa_style", STYLE_NAMES, -1),
             help="classic: ч 4, ш 6, щ 6t, я q, ж j. letters: ч ch, ш sh, "
                  "щ sht, я ya, ж zh. official: the 2009 transliteration, "
                  "ц ts, ъ a",
             section="options"),
    ]
    items += [
        Item("o", "open books folder", lambda: _open_folder(app),
             help=f"drop .txt files in {books.folder()}", section="folder"),
        Item("r", "refresh", refresh,
             help="look for new or changed books", section="folder"),
    ]
    return items


def go_to_page(app, item):
    title = item.label
    total = books.page_count(len(books.words(app, title)), app.settings.book_page)
    v = prompt(f"go to page (1-{total}) of {title}:")
    if v and v.isdigit():
        books.set_page(app, title, int(v) - 1)


def draw(app, st, menu):
    lines = title_lines(app, st, "books")
    if not any(it.section == LIBRARY for it in menu.items):
        lines += [f"  {st.dim}no books yet. drop .txt files in{RESET}",
                  f"  {books.folder()}",
                  f"  {st.dim}then press r to refresh{RESET}", ""]
    body, focus = menu.render(st, label_width=24)
    focus += len(lines)
    lines += body
    if app.notice:
        lines += ["", f"  {st.title}{app.notice}{RESET}"]
        app.notice = ""
    return lines, focus


def book_menu(app):
    """Returns a page to type, or None to go back."""
    menu = Menu([], app.cursors, "books")

    def refresh():
        menu.set_items(build_items(app, refresh))

    refresh()

    def extra(key):
        item = menu.selected
        is_book = item.section == LIBRARY
        if is_book and key in (keys.PGDN, keys.PGUP):
            _turn(app, item.label, JUMP if key == keys.PGDN else -JUMP)
            return True, None
        if is_book and key == "g":
            go_to_page(app, item)
            return True, None
        return False, None

    return menu_loop(app, menu, lambda st, m: draw(app, st, m), HINTS,
                     extra=extra)
