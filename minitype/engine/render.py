"""Drawing the test screen.

Every word becomes a list of cells (style, char, offset). The block layout
wraps those cells into lines; tape mode lays them on one line that scrolls
with the caret. Offsets are global character positions, which is what the
ghost and pace carets are measured in.
"""

from ..config import VIEW_LINES
from ..terminal import console
from ..terminal.style import INV, RESET, UND

SPACE_DOT = "·"
HIDDEN = "_"


def wrap(display, width):
    """Greedily group word indices into lines. display holds what each word
    currently renders as, so extra chars push words onto the next line."""
    lines = []
    start = 0
    cur = 0
    for i, s in enumerate(display):
        add = len(s) if cur == 0 else len(s) + 1
        if cur + add > width and i > start:
            lines.append((start, i))
            start = i
            cur = len(s)
        else:
            cur += add
    lines.append((start, len(display)))
    return lines


class Painter:
    """Turns words and what's been typed into styled cells."""

    def __init__(self, st, settings, words, typed, wi, marks, wrong, hidden,
                 errors=()):
        self.st, self.words, self.typed, self.wi = st, words, typed, wi
        self.marks, self.hidden = marks, hidden
        self.errors = errors
        self.blind = settings.blind
        self.mirror = settings.funbox == "mirror"
        self.caret = INV if settings.caret == "block" else UND + (st.ok or "")
        if wrong and not self.blind:
            self.caret = st.bad + INV
        self.gap_char = SPACE_DOT if settings.show_spaces else " "
        self.display = [w + typed[i][len(w):] for i, w in enumerate(words)]
        self.offs = []
        g = 0
        for s in self.display:
            self.offs.append(g)
            g += len(s) + 1

    def word(self, i):
        st, w, t, wi = self.st, self.words[i], self.typed[i], self.wi
        cells = []
        for j in range(max(len(w), len(t))):
            wc = w[j] if j < len(w) else None
            tc = t[j] if j < len(t) else None
            c = wc if wc is not None else tc
            off = self.offs[i] + j
            if i == wi and j == len(t):
                cells.append((self.caret, HIDDEN if self.hidden else c, off))
                continue
            if tc is None:
                s = st.bad if (i < wi and not self.blind) else st.dim
                if self.hidden and i >= wi:
                    c = HIDDEN
            elif self.blind:
                s = st.ok
            elif wc is None:
                s = st.extra
            elif tc == wc:
                s = st.bad if (i, j) in self.errors else st.ok
            else:
                s = st.bad
            if off in self.marks:
                s = st.dim + UND
            cells.append((s, c, off))
        if self.mirror:
            cells.reverse()
        return cells

    def gap(self, i):
        """The space after word i."""
        off = self.offs[i] + len(self.display[i])
        if i == self.wi and len(self.typed[i]) >= len(self.display[i]):
            return (self.caret, " ", off)
        if off in self.marks:
            return (self.st.dim + UND, " ", off)
        dot = self.gap_char != " "
        return (self.st.dim if dot else "", self.gap_char, off)

    def span(self, a, b):
        """Cells for words a..b-1 with the spaces between them; a trailing
        caret cell if the caret sits after the very last word."""
        cells = []
        for i in range(a, b):
            if i > a:
                cells.append(self.gap(i - 1))
            cells += self.word(i)
        last = b - 1
        if last == self.wi == len(self.words) - 1 \
                and len(self.typed[last]) >= len(self.display[last]):
            cells.append(self.gap(last))
        return cells


def join(cells):
    return "".join(s + c + RESET if s else c for s, c, _ in cells)


def block_lines(p, width):
    lines = wrap(p.display, width)
    li = next((n for n, (a, b) in enumerate(lines) if a <= p.wi < b),
              len(lines) - 1)
    top = max(0, min(li - 1, len(lines) - VIEW_LINES))
    view = [join(p.span(a, b)) for a, b in lines[top:top + VIEW_LINES]]
    return view + [""] * (VIEW_LINES - len(view))


def tape_line(p, width):
    """One line that scrolls so the caret stays a third of the way in."""
    a = max(0, p.wi - 40)
    b = min(len(p.words), p.wi + 40)
    cells = p.span(a, b)
    caret_at = next((k for k, cell in enumerate(cells) if cell[0] == p.caret),
                    len(cells))
    start = max(0, caret_at - width // 3)
    return join(cells[start:start + width])


def draw(st, settings, header, words, typed, wi, width, footer, marks=(),
         wrong=False, below=(), hidden=False, errors=()):
    """Redraw the test screen in place.

    marks:  global char offsets to underline (ghost and pace carets)
    wrong:  turns the caret red after a rejected key
    below:  extra lines under the words (the on-screen keyboard)
    hidden: memory mode, untyped characters are blanked out
    errors: (word, letter) positions to keep red even once typed right
    """
    p = Painter(st, settings, words, typed, wi, marks, wrong, hidden, errors)
    out = []
    if header:
        out += [st.dim + header + RESET, ""]
    focus = len(out)
    if settings.tape:
        out += [tape_line(p, width), ""]
    else:
        out += block_lines(p, width)
    if below:
        out += [""] + list(below)
    pinned = ["", st.dim + footer + RESET] if footer else ()
    console.present(["  " + line if line else "" for line in out], focus, pinned)
