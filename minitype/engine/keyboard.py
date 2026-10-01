"""On-screen keyboard shown under the words, keybr style."""

from ..config import LAYOUTS
from ..terminal.style import INV, RESET, UND

SPACE_BAR = "space".center(17)


def render(st, layout, next_char, colors=None, underline=()):
    """Lines of a staggered keyboard. next_char is highlighted; colors maps
    keys to a style (others are dim); keys in underline are underlined."""
    colors = colors or {}
    nxt = next_char.lower() if next_char else None
    lines = []
    for r, row in enumerate(LAYOUTS.get(layout, LAYOUTS["qwerty"])):
        cells = []
        for c in row:
            s = colors.get(c, st.dim)
            if c in underline:
                s += UND
            if c == nxt:
                s += INV
            cells.append(f"{s}{c}{RESET}")
        lines.append("  " + " " * r + " ".join(cells))
    bar = (st.title + INV) if nxt == " " else st.dim + UND
    lines.append("  " + " " * 7 + bar + SPACE_BAR + RESET)
    return lines
