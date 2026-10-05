"""Menus as data, navigated with arrow keys or hotkeys.

A screen describes its options as Items grouped into sections and hands them
to a Menu, which draws them in the chosen ui style and turns key presses
into actions:

    up / down        move (left / right too, in a horizontal menu)
    home / end       jump to the first / last item
    enter            activate the selected item (start, for a mode row)
    right / left     step an item's value forward / back; on a row with no
                     value, switch section when one section shows at a time
    shift-enter      step the value back, in every style
    two columns      (sidebar with section buttons on the left) you start on
                     the buttons: up / down pick a section, enter or right
                     steps into its rows, esc steps back out. In the rows
                     left / right only change values
    tab / shift-tab  next / previous section, in every style
    [ ] pgup pgdn    the same
    hotkey           jump to that item and activate it

Styles:
    list     every item in one column under section headings
    sidebar  items on the left, details of the selected one on the right;
             with sidebar tabs "top" a tab bar shows one section at a time,
             with "left" the sections are buttons down the left side
             (narrow terminals fall back to list, or tabs with sidebar tabs)
    tabs     one section at a time, with a tab bar to switch between them
"""

import os
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

from ..terminal import console, keys
from ..terminal.style import INV, RESET

SIDEBAR_MIN_WIDTH = 60
HELP_INDENT = 6           # lines help text up with the labels: " >k  label"
                          # without hotkeys labels start at 3 (" > label");
                          # help goes 2 further in so it doesn't look like a row
TAB_PREV = (keys.SHIFT_TAB, keys.PGUP, "[")
TAB_NEXT = (keys.TAB, keys.PGDN, "]")


@dataclass
class Item:
    key: str                                    # hotkey ("" for none); shown beside the label
    label: str
    action: Callable[[], Any]                   # non-None return leaves the menu with that value
    value: Optional[Callable[[], str]] = None   # current setting, shown beside the label
    back: Optional[Callable[[], Any]] = None    # left arrow: step the value backwards
    help: Any = ""                              # shown while selected; a str, or a
                                                # function returning one
    section: str = ""
    enter: Optional[Callable[[], Any]] = None   # enter / hotkey, when it differs from action
    tags: Tuple[str, ...] = ()                  # extra words a #tag search finds it by

    def activate(self):
        return (self.enter or self.action)()

    def help_text(self):
        return self.help() if callable(self.help) else self.help

    def matches(self, query):
        """Every word of the query must be in the label; words starting
        with # must instead be in one of the tags or the section name."""
        for word in query.lower().split():
            if word.startswith("#"):
                tag = word[1:]
                if tag and not any(tag in t for t in (self.section,) + self.tags):
                    return False
            elif word not in self.label.lower():
                return False
        return True


class Menu:
    def __init__(self, items, memory=None, name=None, horizontal=False,
                 style="list"):
        self.items = items
        self.memory = memory if memory is not None else {}   # remembers the cursor between visits
        self.name = name
        self.horizontal = horizontal
        self.style = style
        self.sidebar_tabs = "off"
        self.query = ""          # only items matching it are shown
        self.on_sections = True   # two-column layout: focus on the section buttons,
                                  # where you start
        self.set_items(items)

    def set_items(self, items):
        """Replace the items (a refreshed list), keeping the cursor in range."""
        self.items = items
        self.show_keys = any(it.key for it in items)
        self.cursor = max(0, min(self.memory.get(self.name, 0), len(items) - 1))

    def set_query(self, query):
        """Filter the items. If the selection is filtered out, select the
        first one left."""
        self.query = query
        vis = self.visible()
        if vis and self.cursor not in vis:
            self._move_to(vis[0])

    def visible(self):
        """Indices of the items that match the current query."""
        return [i for i, it in enumerate(self.items) if it.matches(self.query)]

    @property
    def paged(self):
        """Whether one section is shown at a time, so up/down stay in it."""
        if self.horizontal:
            return False
        return self.style == "tabs" or (self.style == "sidebar"
                                        and self.sidebar_tabs != "off")

    @property
    def columns(self):
        """Section buttons in one column and the rows in another (sidebar
        style with sidebar tabs on the left, when the terminal is wide
        enough to draw it). Left and right then move between the columns."""
        return (not self.horizontal and self.style == "sidebar"
                and self.sidebar_tabs == "left"
                and console.size()[0] >= SIDEBAR_MIN_WIDTH)

    def nav_hint(self):
        """The movement keys, for the hint line; they depend on the layout."""
        if self.columns:
            if self.on_sections:
                return "up/down section   enter/right open"
            return ("arrows move   left/right change   shift-enter step back   "
                    "esc sections")
        return "arrows move   left/right change   shift-enter step back"

    @property
    def selected(self):
        return self.items[self.cursor]

    def sections(self):
        return list(dict.fromkeys(self.items[i].section for i in self.visible()))

    def _in_section(self, section):
        return [i for i in self.visible() if self.items[i].section == section]

    def _move_to(self, i):
        self.cursor = i % len(self.items)
        self.memory[self.name] = self.cursor

    def _step(self, d):
        """Move up or down through the visible items; when paged, only
        within the current section."""
        idx = self._in_section(self.selected.section) if self.paged \
            else self.visible()
        pos = idx.index(self.cursor) if self.cursor in idx else -d
        self._move_to(idx[(pos + d) % len(idx)])

    def _switch_tab(self, d):
        secs = self.sections()
        cur = secs.index(self.selected.section) if self.selected.section in secs else 0
        self._move_to(self._in_section(secs[(cur + d) % len(secs)])[0])

    def handle(self, key):
        """Apply a key. Returns (handled, result): handled is False if the key
        means nothing to this menu, result is whatever the action returned."""
        prev = (keys.UP, keys.LEFT) if self.horizontal else (keys.UP,)
        nxt = (keys.DOWN, keys.RIGHT) if self.horizontal else (keys.DOWN,)
        vis = self.visible()
        if not vis:
            return False, None              # everything is filtered out
        item = self.selected
        sections = not self.horizontal and len(self.sections()) > 1
        if self.columns:
            done = self._handle_columns(key, item, sections)
            if done is not None:
                return done
        if key in prev:
            self._step(-1)
        elif key in nxt:
            self._step(1)
        elif key == keys.HOME:
            self._move_to(vis[0])
        elif key == keys.END:
            self._move_to(vis[-1])
        elif key == keys.ENTER:
            return True, item.activate()
        elif key == keys.SHIFT_ENTER:
            return True, (item.back() if item.back is not None else None)
        elif key == keys.RIGHT and item.value is not None:
            return True, item.action()
        elif key == keys.LEFT and item.back is not None:
            return True, item.back()
        elif sections and (key in TAB_NEXT or (self.paged and key == keys.RIGHT)):
            self._switch_tab(1)
        elif sections and (key in TAB_PREV or (self.paged and key == keys.LEFT)):
            self._switch_tab(-1)
        else:
            for i in vis:
                if self.items[i].key and self.items[i].key == key:
                    self._move_to(i)
                    self.on_sections = False
                    return True, self.items[i].activate()
            return False, None
        return True, None

    def _handle_columns(self, key, item, sections):
        """Keys that mean something different in the two-column layout.
        Returns None for keys that work the same as anywhere else.

        On the section buttons, up/down pick a section and enter or right
        steps into its rows (esc steps back out, see back_out). On the
        rows, left/right only change the value, and do nothing on rows
        that have none."""
        if self.on_sections:
            if key in (keys.UP, keys.DOWN):
                if sections:
                    self._switch_tab(-1 if key == keys.UP else 1)
                return True, None
            if key in (keys.ENTER, keys.SHIFT_ENTER, keys.RIGHT):
                self.on_sections = False
                return True, None
            if key == keys.LEFT:
                return True, None
            return None
        if key == keys.RIGHT:
            return True, (item.action() if item.value is not None else None)
        if key == keys.LEFT:
            return True, (item.back() if item.back is not None else None)
        return None

    def back_out(self):
        """Esc in the rows of the two-column layout steps back to the
        section buttons. Returns True if it did, False if esc should do
        what it does anywhere else (leave the menu)."""
        if self.columns and not self.on_sections:
            self.on_sections = True
            return True
        return False

    # ---------------------------------------------------------------- drawing

    def _row(self, st, item, sel, label_width, with_value=True, active=True):
        """One row. `active` is False when focus is in the other column:
        the selection still shows, but dimmed."""
        lit = st.title if active else st.dim
        pointer = f"{lit}>{RESET}" if sel else " "
        lab = lit if sel else st.dim
        if self.show_keys:
            key = f"{item.key:<1}" if len(item.key) <= 1 else item.key
            line = f" {pointer}{st.title}{key}{RESET}  {lab}"
        else:
            line = f" {pointer} {lab}"
        if item.value is None or not with_value:
            return line + f"{item.label}{RESET}"
        w = max(label_width, len(item.label) + 2)
        return line + f"{item.label:<{w}}{RESET}{item.value()}"

    def render(self, st, label_width=0):
        """Lines for the menu and the index of the selected one."""
        width = console.size()[0]
        label_width = min(label_width, max(8, width // 3))
        if not self.visible():
            return [f"  {st.dim}nothing matches{RESET}"], 0
        if self.style == "sidebar" and width >= SIDEBAR_MIN_WIDTH:
            if self.sidebar_tabs == "top":
                return self._render_sidebar_top(st, width, label_width)
            if self.sidebar_tabs == "left":
                return self._render_sidebar_left(st, width, label_width)
            return self._render_sidebar(st, width, label_width)
        if self.paged:
            return self._render_tabs(st, label_width)
        return self._rows(st, self.visible(), label_width)

    # -- pieces

    def _help_under(self, st, item, width):
        """The item's help, wrapped and indented to sit under its label, so
        it stays next to the selection however far the menu has scrolled."""
        text = item.help_text()
        if not text:
            return []
        indent = HELP_INDENT if self.show_keys else HELP_INDENT - 1
        return [" " * indent + f"{st.dim}{ln}{RESET}"
                for ln in textwrap.wrap(text, max(10, width - indent - 2))]

    def _rows(self, st, indices, label_width, with_value=True, inline_help=True,
              width=None, headings=True, active=True):
        """Rows for the given items, with a heading wherever the section
        changes (if the menu has sections at all). Returns (lines, index of
        the selected row)."""
        width = width or console.size()[0]
        lines, focus, section = [], 0, None
        headings = headings and len({it.section for it in self.items}) > 1
        for i in indices:
            item = self.items[i]
            if headings and item.section != section:
                if section is not None:
                    lines.append("")
                section = item.section
                if section:
                    lines.append(f"  {st.dim}{section}{RESET}")
            sel = i == self.cursor
            if sel:
                focus = len(lines)
            lines.append(self._row(st, item, sel, label_width, with_value, active))
            if sel and inline_help:
                lines += self._help_under(st, item, width)
        return lines, focus

    def _tab_bar(self, st):
        cur = self.selected.section
        tabs = []
        for sec in self.sections():
            name = sec or "-"
            tabs.append(f"{st.title}{INV} {name} {RESET}" if sec == cur
                        else f"{st.dim} {name} {RESET}")
        return "  " + "".join(tabs)

    def _panel(self, st, item, width):
        """Details of the selected item, for the sidebar."""
        lines = [f"{st.title}{item.label}{RESET}"]
        if item.value is not None:
            lines.append(f"{st.dim}value  {RESET}{item.value()}")
            if item.back is not None:
                lines.append(f"{st.dim}left/right to change{RESET}")
        text = item.help_text()
        if text:
            lines.append("")
            lines += [f"{st.dim}{ln}{RESET}"
                      for ln in textwrap.wrap(text, max(10, width))]
        return lines

    @staticmethod
    def _beside(st, left, right, lw):
        """Two columns, the left one padded to lw, split by a bar."""
        return [console.pad(left[k] if k < len(left) else "", lw)
                + f" {st.dim}|{RESET} " + (right[k] if k < len(right) else "")
                for k in range(max(len(left), len(right)))]

    # -- layouts

    def _render_tabs(self, st, label_width):
        rows, focus = self._rows(st, self._in_section(self.selected.section),
                                 label_width, headings=False)
        return [self._tab_bar(st), ""] + rows, focus + 2

    def _sidebar(self, st, width, label_width, indices, headings=True):
        lw = min(40, max(18, width // 2 - 2))
        left, focus = self._rows(st, indices, min(label_width, lw - 15),
                                 inline_help=False, headings=headings)
        # the panel starts level with the selected row, so it scrolls with it
        right = [""] * focus + self._panel(st, self.selected, width - lw - 5)
        return self._beside(st, left, right, lw), focus

    def _render_sidebar(self, st, width, label_width):
        return self._sidebar(st, width, label_width, self.visible())

    def _render_sidebar_top(self, st, width, label_width):
        lines, focus = self._sidebar(st, width, label_width,
                                     self._in_section(self.selected.section),
                                     headings=False)
        return [self._tab_bar(st), ""] + lines, focus + 2

    def _render_sidebar_left(self, st, width, label_width):
        """Section buttons down the left; the chosen section's rows, with
        the selected row's help under it, on the right."""
        cur = self.selected.section
        secs = self.sections()
        lw = max(len(s or "-") for s in secs) + 5
        on = self.on_sections
        left = []
        for s in secs:
            name = s or "-"
            if s != cur:
                left.append(f"   {st.dim}{name}{RESET}")
            elif on:                          # focus here: pointer and bright
                left.append(f" {st.title}>{INV} {name} {RESET}")
            else:
                left.append(f"  {st.title}{INV} {name} {RESET}")
        right, focus = self._rows(st, self._in_section(cur), label_width,
                                  width=width - lw - 3, headings=False,
                                  active=not on)
        if on:
            focus = secs.index(cur)
        return self._beside(st, left, right, lw), focus

    def render_inline(self, st):
        """All items on one line, for short choice rows."""
        cells = []
        for i, item in enumerate(self.items):
            if i == self.cursor:
                cells.append(f"{st.title}>{item.key} {item.label}{RESET}")
            else:
                cells.append(f"{st.dim} {item.key} {item.label}{RESET}")
        return "  " + "  ".join(cells)


class Hints:
    """Key hints at the bottom of a screen. They can be switched off, but
    pressing a key that does nothing brings them back until the next key
    that does something."""

    def __init__(self, app):
        self.app = app
        self.popped = False

    def note(self, key, handled):
        if key != keys.RESIZE:
            self.popped = not handled

    def lines(self, st, text):
        if not (self.app.settings.hints or self.popped):
            return []
        width = console.size()[0]
        return [""] + [f"  {st.dim}{ln}{RESET}"
                       for ln in textwrap.wrap(text, max(10, width - 4))]


def title_lines(app, st, name):
    """A screen's heading; a bare prompt line when disguised."""
    if app.settings.lowkey == "disguised":
        return [f"{os.getcwd()}>minitype {name}", ""]
    return ["", f"  {st.title}{name}{RESET}", ""]
