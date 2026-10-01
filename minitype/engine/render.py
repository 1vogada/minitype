from ..config import VIEW_LINES
from ..terminal import console
from ..terminal.style import INV, RESET, UND


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


SPACE_DOT = "·"


def draw(st, settings, header, words, typed, wi, width, footer, marks=(),
         wrong=False, below=()):
    """Redraw the test screen in place. marks are global char offsets to
    underline (ghost and pace carets). wrong turns the caret red after a
    rejected key. below are extra lines drawn under the words."""
    dim, ok, bad, extra = st.dim, st.ok, st.bad, st.extra
    blind = settings.blind
    caret = INV if settings.caret == "block" else UND + ok
    if wrong and not blind:
        caret = bad + INV
    gap = dim + SPACE_DOT + RESET if settings.show_spaces else " "
    display = [w + typed[i][len(w):] for i, w in enumerate(words)]
    lines = wrap(display, width)

    offs = []
    g = 0
    for s in display:
        offs.append(g)
        g += len(s) + 1

    li = next(n for n, (a, b) in enumerate(lines) if a <= wi < b)
    top = max(0, min(li - 1, len(lines) - VIEW_LINES))
    view = lines[top:top + VIEW_LINES]

    out = ["\x1b[H", dim, header, RESET, "\x1b[K\n\x1b[K\n"]
    for a, b in view:
        buf = []
        for i in range(a, b):
            if i > a:
                sp = offs[i] - 1
                if i - 1 == wi and len(typed[wi]) >= len(display[wi]):
                    buf.append(caret + " " + RESET)
                elif sp in marks:
                    buf.append(dim + UND + " " + RESET)
                else:
                    buf.append(gap)
            w, t = words[i], typed[i]
            for j in range(max(len(w), len(t))):
                wc = w[j] if j < len(w) else None
                tc = t[j] if j < len(t) else None
                c = wc if wc is not None else tc
                if i == wi and j == len(t):
                    buf.append(caret + c + RESET)
                    continue
                if tc is None:
                    s = bad if (i < wi and not blind) else dim
                elif blind:
                    s = ok
                elif wc is None:
                    s = extra
                elif tc == wc:
                    s = ok
                else:
                    s = bad
                if offs[i] + j in marks:
                    buf.append(dim + UND + c + RESET)
                else:
                    buf.append(s + c)
        out.append("".join(buf) + RESET + "\x1b[K\n")
    for _ in range(VIEW_LINES - len(view)):
        out.append("\x1b[K\n")
    if below:
        out.append("\x1b[K\n")
        out.extend(line + "\x1b[K\n" for line in below)
    out.append("\x1b[K\n" + dim + footer + RESET + "\x1b[K\n\x1b[J")
    console.write("".join(out))
    console.flush()
