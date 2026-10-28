"""Cascading menus: pages inside pages, as deep as they need to go.

A Page holds rows - settings (menu Items) and other pages - so related
settings can sit together however many there are: "art" holds the
picture rows and an "art and text" page and a "fade" page, and "fade"
holds a "top edge" page of its own. The top pages are the menu's
sections (the tabs down the side in the two-column layout).

TreeMenu is a Menu over such pages. Every top page remembers how deep you
went into it (its trail of open pages), and the rows shown for it are its
innermost open page's. A row that opens a page reads "name ›" with how
many settings are in it, and sits after the page's settings, a blank line
down. It has no value: the arrows never change anything on it. Enter or
right opens it; esc (or left, on a row with no value to step) goes back up one level -
then out to the tabs, then out of the screen, as before. A search looks
through every setting at every depth.

With the mouse on, a row in a page you came through (a column to the
left) can be clicked: it goes back up to that page with the row selected.
A click on a row in the dim column of what's in the page under the cursor
opens that page with the row selected.

Building one: TreeMenu([Page("typing", [row, row, Page("drills", [...])]),
...]). To add a setting, make its row and put it in a page; to regroup,
move it - nothing else knows where a row lives.
"""

from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Item, Menu

SUB_MARK = "›"
ROWS_ROOM = 44      # the page you're on needs this much; columns before it give way


class Page:
    """A page of rows: Items, and Pages of their own. `help` shows on the
    row that opens it."""

    def __init__(self, name, children=(), help=""):
        self.name, self.children, self.help = name, list(children), help

    def leaves(self):
        """Every setting under this page, at any depth, in order."""
        for child in self.children:
            if isinstance(child, Page):
                yield from child.leaves()
            else:
                yield child

    def count(self):
        return sum(1 for _ in self.leaves())


class TreeMenu(Menu):
    """A Menu over top pages (its sections), each opened as deep as you
    went into it. See the module notes."""

    def __init__(self, pages, memory=None, name=None, style="list", outer=()):
        self.pages = list(pages)
        self.trail = {p.name: [p] for p in self.pages}   # top page -> open pages, outermost first
        self._openers = {}
        self.query = ""
        # the menus this one was opened from, outermost first, each (its
        # rows' names, the one that opened this): drawn left of the tabs
        self.outer = list(outer)
        super().__init__(self._view(), memory, name, style=style)

    # -- where you are

    def depth_of(self, top):
        return len(self.trail.get(top, ())) - 1

    def path(self):
        """The names of the open pages of the selected top page, outermost
        first ([] while searching)."""
        if self.query or not self.items:
            return []
        return [p.name for p in self.trail.get(self.selected.section, ())]

    # -- the rows shown

    def _opener(self, top, page):
        """The row that opens a page."""
        key = (top, id(page))
        if key not in self._openers:
            def open_page():
                self.trail[top].append(page)
                self._refresh(first_of=top)
            n = page.count()
            item = Item("", f"{page.name} {SUB_MARK}", open_page,
                        lambda: f"{n} setting{'' if n == 1 else 's'}",
                        help=page.help, section=top, tags=("page",))
            item.page = page
            self._openers[key] = item
        return self._openers[key]

    def _view(self):
        """Every top page's innermost open page's rows; while searching,
        every setting at every depth instead."""
        items = []
        for top in self.pages:
            if self.query:
                rows = list(top.leaves())
            else:
                children = self.trail[top.name][-1].children
                settings = [c for c in children if not isinstance(c, Page)]
                pages = [self._opener(top.name, c) for c in children if isinstance(c, Page)]
                for i, opener in enumerate(pages):
                    opener.gap = bool(settings) and i == 0   # a blank line between
                rows = settings + pages
            for row in rows:
                row.section = top.name
            items += rows
        return items

    def _refresh(self, first_of=None, select=None):
        """Rebuild the rows after opening or closing a page or searching:
        select `select`, or the first row of top page `first_of`, or keep
        the selected row where it can be kept."""
        keep = select or (self.items[self.cursor] if self.items else None)
        self.items = self._view()
        self.show_keys = any(it.key for it in self.items)
        if first_of is not None:
            keep = next((it for it in self.items if it.section == first_of), keep)
        at = next((i for i, it in enumerate(self.items) if it is keep), 0)
        self._move_to(at) if self.items else None

    @staticmethod
    def _pages_to(page, item):
        """The pages from `page` down to the one holding `item`, or None."""
        for child in page.children:
            if child is item:
                return [page]
            if isinstance(child, Page):
                inner = TreeMenu._pages_to(child, item)
                if inner:
                    return [page] + inner
        return None

    def set_query(self, query):
        searching = bool(query) != bool(self.query)
        picked = self.selected if searching and not query and self.items else None
        self.query = query
        if picked is not None:                # search cleared: open the pages down to it
            top = next((p for p in self.pages if p.name == picked.section), None)
            path = self._pages_to(top, picked) if top else None
            if path:
                self.trail[top.name] = path
        if searching:
            self._refresh()
        super().set_query(query)

    # -- going back up

    def up(self):
        """Close the innermost open page of the selected top page, selecting
        the row that opened it. False if it was already at the top."""
        if self.query or not self.items:
            return False
        trail = self.trail.get(self.selected.section)
        if not trail or len(trail) < 2:
            return False
        page = trail.pop()
        self._refresh(select=self._openers.get((self.selected.section, id(page))))
        return True

    def _click_up(self, page, row):
        """A click on a row of a page you came through: back up to that
        page, the row selected (a page's row, for a page)."""
        top = self.selected.section
        trail = self.trail[top]
        at = next(k for k, p in enumerate(trail) if p is page)
        self.trail[top] = trail[:at + 1]
        self._refresh(select=self._opener(top, row) if isinstance(row, Page) else row)
        self.on_sections = False
        return None

    def _click_into(self, page, row):
        """A click on a row in the preview of the page under the cursor:
        that page opened, the row selected (a page's row, for a page)."""
        top = self.selected.section
        self.trail[top].append(page)
        self._refresh(select=self._opener(top, row) if isinstance(row, Page) else row)
        return None

    def back_out(self):
        """Esc: up a page, then (two columns) out to the tabs, then False
        to leave the screen."""
        if not (self.columns and self.on_sections) and self.up():
            return True
        return super().back_out()

    def handle(self, key):
        on_rows = self.items and not self.query and not (self.columns and self.on_sections)
        if on_rows and key == keys.LEFT and self.selected.back is None:
            if self.up():
                return True, None             # left on a row with nothing to step: up a page
            if self.columns and hasattr(self.selected, "page"):
                self.on_sections = True       # a page row at the top: back to the tabs
                return True, None
        if on_rows and key == keys.RIGHT and hasattr(self.selected, "page"):
            return True, self.selected.activate()   # a page row: right opens it, like enter
        return super().handle(key)

    # -- drawing: the pages you came through stay beside the one you're on

    def _render_sidebar_left(self, st, width, label_width):
        """The menus this was opened from (`outer`), the section buttons,
        then a column for every page you opened on the way (the one you went
        into marked), then the page you're on. When they don't all fit, the
        outermost columns go first, buttons included: the page you're on
        always keeps ROWS_ROOM."""
        if self.query or not self.items:
            return super()._render_sidebar_left(st, width, label_width)
        trail = self.trail.get(self.selected.section, [])
        rows = self._in_section(self.selected.section)
        cols = [self._names_column(st, names, picked) for names, picked in self.outer]
        cols.append(self._section_column(st))
        cols += [self._page_column(st, page, inner) for page, inner in zip(trail, trail[1:])]
        after_buttons = len(trail) - 1                  # the page columns
        # a page row under the cursor shows what's in it, further right
        peek = None
        if not self.on_sections and hasattr(self.selected, "page"):
            peek = self._preview_column(st, self.selected.page)
            own = max(3 + max(label_width, len(self.items[i].label) + 2)
                      + len(self.items[i].value() if self.items[i].value else "") for i in rows) + 2
            own = max(own, ROWS_ROOM)
            room = lambda: width - sum(w + 3 for _, w in cols) - own - 3
            while len(cols) > 1 and room() < peek[1]:
                cols.pop(0)
            if room() < peek[1]:
                peek = None
        while cols and width - sum(w + 3 for _, w in cols) < ROWS_ROOM:
            cols.pop(0)
        on = self.on_sections and len(cols) > after_buttons   # the buttons still show
        lines, focus = self._rows(st, rows, label_width,
                                  width=own if peek else width - sum(w + 3 for _, w in cols),
                                  headings=False, active=not on)
        if on:
            focus = self.sections().index(self.selected.section)
        if peek:
            lines = self._beside(st, lines, peek[0], own)
        for col, w in reversed(cols):
            lines = self._beside(st, col, lines, w)
        return lines, focus

    def _preview_column(self, st, page):
        """What's in the page under the cursor: its settings with their
        values, then its pages, drawn as their own rows are (dim names, the
        values in the plain text colour). Right steps into it. Returns
        (lines, width)."""
        settings = [c for c in page.children if not isinstance(c, Page)]
        pages = [c for c in page.children if isinstance(c, Page)]
        lw = max((len(c.label) for c in settings), default=0) + 2
        into = lambda c: lambda: self._click_into(page, c)
        lines = [console.hit(f"   {st.dim}{c.label.ljust(lw)}{RESET}{c.value() if c.value else ''}",
                             into(c)) for c in settings]
        if settings and pages:
            lines.append("")
        lines += [console.hit(f"   {st.dim}{c.name} {SUB_MARK}{RESET}", into(c)) for c in pages]
        texts = [c.label.ljust(lw) + (c.value() if c.value else "") for c in settings] \
            + [c.name + " " + SUB_MARK for c in pages]
        return lines, max(map(len, texts), default=0) + 4

    @staticmethod
    def _names_column(st, names, picked):
        """A menu this one was opened from: its rows by name, dim, the one
        that opened this marked. Returns (lines, width)."""
        lines = [f" {st.title}>> {n}{RESET}" if n == picked else f"   {st.dim}{n}{RESET}"
                 for n in names]
        return lines, max(map(len, names)) + 5

    def _page_column(self, st, page, inner):
        """A page you came through: its rows by name, dim, and the page you
        went into from it marked. Returns (lines, width)."""
        settings = [c for c in page.children if not isinstance(c, Page)]
        pages = [c for c in page.children if isinstance(c, Page)]
        lines = []
        for c in settings + pages:
            if c is inner:
                line = f" {st.title}>> {c.name} {SUB_MARK}{RESET}"
            elif isinstance(c, Page):
                line = f"   {st.dim}{c.name} {SUB_MARK}{RESET}"
            else:
                line = f"   {st.dim}{c.label}{RESET}"
            lines.append(console.hit(line, lambda c=c: self._click_up(page, c)))
        names = [c.name + " " + SUB_MARK if isinstance(c, Page) else c.label for c in page.children]
        return lines, max(map(len, names)) + 4

    def nav_hint(self):
        hint = super().nav_hint()
        if self.items and not self.query and self.depth_of(self.selected.section) > 0:
            hint += "   esc up"
        return hint
