"""Menus as data, navigated with arrow keys or hotkeys.

A screen describes its options as a list of Items and hands them to a Menu,
which draws them with the selected row highlighted and turns key presses
into actions:

    up / down      move (left / right too, in a horizontal menu)
    home / end     jump to the first / last item
    enter          activate the selected item
    right / left   step an item's value forward / back (vertical menus)
    hotkey         jump to that item and activate it
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..terminal import keys
from ..terminal.style import RESET


@dataclass
class Item:
    key: str                                    # hotkey; also what's shown beside the label
    label: str
    action: Callable[[], Any]                   # non-None return leaves the menu with that value
    value: Optional[Callable[[], str]] = None   # current setting, shown beside the label
    back: Optional[Callable[[], Any]] = None    # left arrow: step the value backwards
    help: str = ""                              # shown while the item is selected
    group: int = 0                              # a blank line separates groups


class Menu:
    def __init__(self, items, memory=None, name=None, horizontal=False):
        self.items = items
        self.memory = memory if memory is not None else {}   # remembers the cursor between visits
        self.name = name
        self.horizontal = horizontal
        self.cursor = min(self.memory.get(name, 0), len(items) - 1)

    @property
    def selected(self):
        return self.items[self.cursor]

    def _move_to(self, i):
        self.cursor = i % len(self.items)
        self.memory[self.name] = self.cursor

    def handle(self, key):
        """Apply a key. Returns (handled, result): handled is False if the key
        means nothing to this menu, result is whatever the action returned."""
        prev = (keys.UP, keys.LEFT) if self.horizontal else (keys.UP,)
        nxt = (keys.DOWN, keys.RIGHT) if self.horizontal else (keys.DOWN,)
        item = self.selected
        if key in prev:
            self._move_to(self.cursor - 1)
        elif key in nxt:
            self._move_to(self.cursor + 1)
        elif key == keys.HOME:
            self._move_to(0)
        elif key == keys.END:
            self._move_to(len(self.items) - 1)
        elif key == keys.ENTER:
            return True, item.action()
        elif key == keys.RIGHT and item.value is not None:
            return True, item.action()
        elif key == keys.LEFT and item.back is not None:
            return True, item.back()
        else:
            for i, it in enumerate(self.items):
                if it.key == key:
                    self._move_to(i)
                    return True, it.action()
            return False, None
        return True, None

    # ---------------------------------------------------------------- drawing

    def render(self, st, label_width=0):
        """One row per item, the selected one pointed at and brightened."""
        group = self.items[0].group if self.items else 0
        for i, item in enumerate(self.items):
            if item.group != group:
                print()
                group = item.group
            sel = i == self.cursor
            pointer = f"{st.title}>{RESET}" if sel else " "
            lab = st.title if sel else st.dim
            line = f" {pointer}{st.title}{item.key}{RESET}  {lab}"
            if item.value is None:
                line += f"{item.label}{RESET}"
            else:
                width = max(label_width, len(item.label) + 2)
                line += f"{item.label:<{width}}{RESET}{item.value()}"
            print(line)

    def render_inline(self, st):
        """All items on one line, for short choice rows."""
        cells = []
        for i, item in enumerate(self.items):
            if i == self.cursor:
                cells.append(f"{st.title}>{item.key} {item.label}{RESET}")
            else:
                cells.append(f"{st.dim} {item.key} {item.label}{RESET}")
        print("  " + "  ".join(cells))

    def render_help(self, st):
        if self.selected.help:
            print(f"\n  {st.dim}{self.selected.help}{RESET}")
