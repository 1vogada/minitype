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
down. It has no value: the arrows never change anything on it. Enter opens
it; esc (or left, on a row with no value to step) goes back up one level -
then out to the tabs, then out of the screen, as before. A search looks
through every setting at every depth.

Building one: TreeMenu([Page("typing", [row, row, Page("drills", [...])]),
...]). To add a setting, make its row and put it in a page; to regroup,
move it - nothing else knows where a row lives.
"""

from ..terminal import keys
from .menu import Item, Menu

SUB_MARK = "›"


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

    def __init__(self, pages, memory=None, name=None, style="list"):
        self.pages = list(pages)
        self.trail = {p.name: [p] for p in self.pages}   # top page -> open pages, outermost first
        self._openers = {}
        self.query = ""
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
            return True, None                 # a page row: only enter opens it
        return super().handle(key)

    def nav_hint(self):
        hint = super().nav_hint()
        if self.items and not self.query and self.depth_of(self.selected.section) > 0:
            hint += "   esc up"
        return hint
