"""Menus as data, navigated with arrow keys or hotkeys.

A screen describes its options as Items grouped into sections and hands them
to a Menu, which draws them in the chosen ui style and turns key presses
into actions:

    up / down        move (left / right too, in a horizontal menu)
    home / end       jump to the first / last item
    enter            activate the selected item (start, for a mode row)
    right / left     step an item's value forward / back
    [ ] pgup pgdn    switch section (tabs style)
    hotkey           jump to that item and activate it

Styles:
    list     every item in one column under section headings
    sidebar  items on the left, details of the selected one on the right
             (falls back to list when the terminal is narrow)
    tabs     one section at a time, with a tab bar to switch between them
"""

import os
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..terminal import console, keys
from ..terminal.style import INV, RESET

SIDEBAR_MIN_WIDTH = 60
HELP_INDENT = 6           # lines help text up with the labels: " >k  label"
TAB_PREV = (keys.PGUP, "[")
TAB_NEXT = (keys.PGDN, "]")


@dataclass
class Item:
    key: str                                    # hotkey ("" for none); shown beside the label
    label: str
    action: Callable[[], Any]                   # non-None return leaves the menu with that value
    value: Optional[Callable[[], str]] = None   # current setting, shown beside the label
    back: Optional[Callable[[], Any]] = None    # left arrow: step the value backwards
    help: str = ""                              # shown while the item is selected
    section: str = ""
    enter: Optional[Callable[[], Any]] = None   # enter / hotkey, when it differs from action

    def activate(self):
        return (self.enter or self.action)()


class Menu:
    def __init__(self, items, memory=None, name=None, horizontal=False,
                 style="list"):
        self.items = items
        self.memory = memory if memory is not None else {}   # remembers the cursor between visits
        self.name = name
        self.horizontal = horizontal
        self.style = style
        self.cursor = min(self.memory.get(name, 0), len(items) - 1)

    @property
    def selected(self):
        return self.items[self.cursor]

    def sections(self):
        return list(dict.fromkeys(it.section for it in self.items))

    def _in_section(self, section):
        return [i for i, it in enumerate(self.items) if it.section == section]

    def _move_to(self, i):
        self.cursor = i % len(self.items)
        self.memory[self.name] = self.cursor

    def _step(self, d):
        """Move up or down; in tabs style, only within the current tab."""
        if self.style != "tabs" or self.horizontal:
            self._move_to(self.cursor + d)
            return
        idx = self._in_section(self.selected.section)
        pos = idx.index(self.cursor)
        self._move_to(idx[(pos + d) % len(idx)])

    def _switch_tab(self, d):
        secs = self.sections()
        cur = secs.index(self.selected.section)
        self._move_to(self._in_section(secs[(cur + d) % len(secs)])[0])

    def handle(self, key):
        """Apply a key. Returns (handled, result): handled is False if the key
        means nothing to this menu, result is whatever the action returned."""
        prev = (keys.UP, keys.LEFT) if self.horizontal else (keys.UP,)
        nxt = (keys.DOWN, keys.RIGHT) if self.horizontal else (keys.DOWN,)
        item = self.selected
        tabs = self.style == "tabs" and not self.horizontal
        if key in prev:
            self._step(-1)
        elif key in nxt:
            self._step(1)
        elif key == keys.HOME:
            self._move_to(0)
        elif key == keys.END:
            self._move_to(len(self.items) - 1)
        elif key == keys.ENTER:
            return True, item.activate()
        elif key == keys.RIGHT and item.value is not None:
            return True, item.action()
        elif key == keys.LEFT and item.back is not None:
            return True, item.back()
        elif tabs and (key in TAB_NEXT or key == keys.RIGHT):
            self._switch_tab(1)
        elif tabs and (key in TAB_PREV or key == keys.LEFT):
            self._switch_tab(-1)
        else:
            for i, it in enumerate(self.items):
                if it.key and it.key == key:
                    self._move_to(i)
                    return True, it.activate()
            return False, None
        return True, None

    # ---------------------------------------------------------------- drawing

    def _row(self, st, item, sel, label_width, with_value=True):
        pointer = f"{st.title}>{RESET}" if sel else " "
        lab = st.title if sel else st.dim
        key = f"{item.key:<1}" if len(item.key) <= 1 else item.key
        line = f" {pointer}{st.title}{key}{RESET}  {lab}"
        if item.value is None or not with_value:
            return line + f"{item.label}{RESET}"
        w = max(label_width, len(item.label) + 2)
        return line + f"{item.label:<{w}}{RESET}{item.value()}"

    def render(self, st, label_width=0):
        """Lines for the menu and the index of the selected one."""
        width = console.size()[0]
        label_width = min(label_width, max(8, width // 3))
        if self.style == "tabs" and not self.horizontal:
            return self._render_tabs(st, label_width)
        if self.style == "sidebar" and width >= SIDEBAR_MIN_WIDTH:
            return self._render_sidebar(st, width, label_width)
        return self._render_list(st, label_width)

    def _help_under(self, st, item):
        """The item's help, wrapped and indented to sit under its label, so
        it stays next to the selection however far the menu has scrolled."""
        if not item.help:
            return []
        width = max(10, console.size()[0] - HELP_INDENT - 2)
        return [" " * HELP_INDENT + f"{st.dim}{ln}{RESET}"
                for ln in textwrap.wrap(item.help, width)]

    def _render_list(self, st, label_width, with_value=True, inline_help=True):
        lines, focus, section = [], 0, None
        for i, item in enumerate(self.items):
            if item.section != section:
                if section is not None:
                    lines.append("")
                section = item.section
                if section:
                    lines.append(f"  {st.dim}{section}{RESET}")
            sel = i == self.cursor
            if sel:
                focus = len(lines)
            lines.append(self._row(st, item, sel, label_width, with_value))
            if sel and inline_help:
                lines += self._help_under(st, item)
        return lines, focus

    def _render_tabs(self, st, label_width):
        cur = self.selected.section
        tabs = []
        for sec in self.sections():
            name = sec or "-"
            tabs.append(f"{st.title}{INV} {name} {RESET}" if sec == cur
                        else f"{st.dim} {name} {RESET}")
        lines = ["  " + "".join(tabs), ""]
        focus = 0
        for i in self._in_section(cur):
            sel = i == self.cursor
            if sel:
                focus = len(lines)
            lines.append(self._row(st, self.items[i], sel, label_width))
            if sel:
                lines += self._help_under(st, self.items[i])
        return lines, focus

    def _render_sidebar(self, st, width, label_width):
        lw = min(40, max(18, width // 2 - 2))
        left, focus = self._render_list(st, min(label_width, lw - 15),
                                        inline_help=False)
        item = self.selected
        rw = width - lw - 5
        right = [f"{st.title}{item.label}{RESET}"]
        if item.value is not None:
            right.append(f"{st.dim}value  {RESET}{item.value()}")
            if item.back is not None:
                right.append(f"{st.dim}left/right to change{RESET}")
        if item.help:
            right.append("")
            right += [f"{st.dim}{ln}{RESET}" for ln in textwrap.wrap(item.help, rw)]
        # the panel starts level with the selected row, so it scrolls with it
        right = [""] * focus + right
        lines = []
        for k in range(max(len(left), len(right))):
            a = left[k] if k < len(left) else ""
            b = right[k] if k < len(right) else ""
            lines.append(console.pad(a, lw) + f" {st.dim}|{RESET} " + b)
        return lines, focus

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
