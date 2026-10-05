"""Drawing the test screen.

Every word becomes a list of cells (style, char, offset). The block layout
wraps those cells into lines; tape mode lays them on one line that scrolls
with the caret. Offsets are global character positions, which is what the
ghost and pace carets are measured in.

Letters that had a wrong key and were fixed look as the corrected letters
setting says (marked in the warn colour, normal, or red), and indicate
typos shows the wrong key pressed: in place of the letter (replace), on a
row underneath (below), or both.

The theme's fun modifiers are applied here too, and only here, so they
never change what you have to type:
    pop      the last few typed letters are bright and bold
    fade     typed letters far behind the caret go dim
    glitch   untyped letters well ahead flicker to symbols now and then
    caret    pulse blinks it, rainbow cycles its colour
    shake    the text jolts sideways for a moment after a wrong key
    bounce   each line becomes two rows and letters hop between them
"""

import math

from ..config import VIEW_LINES
from ..terminal import console
from ..terminal.style import BOLD, INV, ITALIC, RESET, UND

SPACE_DOT = "·"
HIDDEN = "_"

POP_LEN = 3            # typed letters behind the caret that pop
FADE_FROM = 12         # typed letters further back than this fade
GLITCH_SAFE = 3        # letters right after the caret never glitch
GLITCH_ODDS = 45       # about one letter in this many flickers at a time
GLITCH_GLYPHS = "#%&@$*?!<>/\\=+"
SHAKE_TIME = 0.3       # seconds the text shakes after a wrong key
SHAKE_STEPS = (1, -1, 1, -1, 0)
BOB_RATE = 5.0         # how fast letters bob
BOB_RANGE = 8          # gentle bounce: letters this close to the caret bob
PULSE_RATE = 2.0       # caret blinks a second


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
                 errors=(), combo=0, now=0.0, typo_keys=None):
        self.st, self.words, self.typed, self.wi = st, words, typed, wi
        self.marks, self.hidden = marks, hidden
        self.errors = errors                   # letters that ever had a wrong key
        self.typo_keys = typo_keys or {}       # ...and the wrong key pressed there
        self.combo, self.now = combo, now      # for theme heat and flow
        self.blind = settings.blind
        self.corrected = settings.corrected
        self.typos = "off" if self.blind else settings.typos
        self.typo_row = self.typos in ("below", "both")
        self.below = {}                        # offset -> (style, char) for that row
        self.rejected = wrong                  # a wrong key was just turned away
        self.mirror = settings.funbox == "mirror"
        self.fx = st.effects
        self.speed = abs(getattr(st, "speed", 1.0)) or 1.0
        wrong = wrong and not self.blind
        rainbow = self.fx.caret_fx == "rainbow" and not wrong
        if settings.caret == "block":
            # the letter to type drawn inverted; red after a wrong key
            colour = st.caret_colour(now) if rainbow else st.bad if wrong else ""
            self.caret = self.caret_gap = colour + INV
        else:
            # underline only: the letter keeps the untyped colour, the
            # underline turns red after a wrong key. On a space the
            # underline is bright, so it stands out from an underlined gap
            colour = st.caret_colour(now) if rainbow else None
            self.caret = (colour or (st.bad if wrong else st.dim)) + UND
            self.caret_gap = (colour or (st.bad if wrong else st.title)) + UND
        if self.fx.caret_fx == "pulse" and int(now * PULSE_RATE * self.speed) % 2:
            self.caret, self.caret_gap = st.dim, ""        # the blink's off half
        self.gap_style = settings.word_gap
        self.display = [w + typed[i][len(w):] for i, w in enumerate(words)]
        self.offs = []
        g = 0
        for s in self.display:
            self.offs.append(g)
            g += len(s) + 1
        self.caret_off = (self.offs[wi] + len(typed[wi])) if wi < len(words) else -1

    def _corrected(self, typed_style):
        """Style for a letter that had a wrong key and was then fixed:
        marked in the theme's warn colour (italic without colour), red, or
        like any other typed letter. Returns (style, still counts as a
        clean typed letter for pop and fade)."""
        if self.blind or self.corrected == "normal":
            return typed_style, True
        if self.corrected == "red":
            return self.st.bad, False
        return (self.st.warn or ITALIC), False

    def _typo(self, off, wanted, pressed):
        """Fill in the row under the text for a wrong letter."""
        if self.typos == "below":
            self.below[off] = (self.st.bad, pressed)
        elif self.typos == "both":
            self.below[off] = (self.st.dim, wanted)    # the right one under it

    def _glitched(self, off):
        """Whether an untyped letter flickers this moment (the same answer
        all through one flicker, so it doesn't change every frame)."""
        moment = int(self.now * 8 * self.speed)
        return (off * 7919 + moment * 104729) % GLITCH_ODDS == 0

    def _flourish(self, s, c, off, typed_ok, untyped):
        """Apply pop, fade and glitch to one letter."""
        fx, d = self.fx, self.caret_off - off
        if typed_ok and fx.pop and 0 < d <= POP_LEN:
            s = BOLD + self.st.title
        elif typed_ok and fx.fade and d > FADE_FROM:
            s = self.st.dim
        elif untyped and fx.glitch and -d > GLITCH_SAFE and self._glitched(off):
            c = GLITCH_GLYPHS[(off + int(self.now * 8)) % len(GLITCH_GLYPHS)]
        return s, c

    def is_up(self, off):
        """Bounce: whether this letter is on the upper row right now."""
        fx = self.fx
        if fx.bounce == "off":
            return False
        if fx.bounce == "gentle" and abs(off - self.caret_off) > BOB_RANGE:
            return False
        return math.sin(self.now * BOB_RATE * self.speed + off * 0.7) > 0.35

    def shake(self, last_error):
        """Columns to nudge the text sideways after a wrong key."""
        t = self.now - last_error
        if not self.fx.shake or not 0 <= t < SHAKE_TIME:
            return 0
        return SHAKE_STEPS[int(t / SHAKE_TIME * len(SHAKE_STEPS))]

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
                if self.rejected and self.typo_row and (i, j) in self.typo_keys:
                    # stop on error: the turned-away key, under the caret
                    self.below[off] = (st.bad, self.typo_keys[(i, j)])
                continue
            typed_ok = False
            if tc is None:
                s = st.bad if (i < wi and not self.blind) else st.dim
                if self.hidden and i >= wi:
                    c = HIDDEN
            elif self.blind:
                s = st.ok
            elif wc is None:
                s = st.extra
            elif tc == wc:
                typed_ok = True
                s = st.typed(off, i, self.combo, self.now)
                if (i, j) in self.errors:
                    s, typed_ok = self._corrected(s)
            else:
                s = st.bad
                self._typo(off, wc, tc)
                if self.typos in ("replace", "both"):
                    c = tc                     # show what was actually pressed
            s, c = self._flourish(s, c, off, typed_ok,
                                  tc is None and i >= wi and not self.hidden)
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
            return (self.caret_gap, " ", off)
        if off in self.marks:
            return (self.st.dim + UND, " ", off)
        if self.gap_style == "dots":
            return (self.st.dim, SPACE_DOT, off)
        if self.gap_style == "underline":
            return (self.st.dim + UND, " ", off)
        return ("", " ", off)

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


def rows_per_line(p):
    return 1 + (p.fx.bounce != "off") + p.typo_row


def rows(p, cells):
    """A line of cells as screen rows: one row, or with bounce two, where
    each letter sits on the upper or lower row as it bobs. With indicate
    typos below (or both), one more row under it holds the wrong keys."""
    if p.fx.bounce == "off":
        out = [join(cells)]
    else:
        up = [p.is_up(off) for _, _, off in cells]
        out = [join((s, c, o) if u else ("", " ", o) for (s, c, o), u in zip(cells, up)),
               join(("", " ", o) if u else (s, c, o) for (s, c, o), u in zip(cells, up))]
    if p.typo_row:
        out.append(join((*p.below[o], o) if o in p.below else ("", " ", o)
                        for _, _, o in cells))
    return out


def block_lines(p, width):
    lines = wrap(p.display, width)
    li = next((n for n, (a, b) in enumerate(lines) if a <= p.wi < b),
              len(lines) - 1)
    top = max(0, min(li - 1, len(lines) - VIEW_LINES))
    per_line = rows_per_line(p)
    view = [r for a, b in lines[top:top + VIEW_LINES] for r in rows(p, p.span(a, b))]
    return view + [""] * (VIEW_LINES * per_line - len(view))


def tape_line(p, width):
    """One line that scrolls so the caret stays a third of the way in."""
    a = max(0, p.wi - 40)
    b = min(len(p.words), p.wi + 40)
    cells = p.span(a, b)
    # found by position, not colour: an underline caret can share its
    # colour with the ghost caret or an underlined gap
    caret_off = p.offs[p.wi] + len(p.typed[p.wi]) if p.wi < len(p.words) else -1
    caret_at = next((k for k, cell in enumerate(cells) if cell[2] == caret_off),
                    len(cells))
    start = max(0, caret_at - width // 3)
    return rows(p, cells[start:start + width])


def draw(st, settings, header, words, typed, wi, width, footer, marks=(),
         wrong=False, below=(), hidden=False, errors=(), combo=0, now=0.0,
         last_error=-1.0, typo_keys=None):
    """Redraw the test screen in place.

    marks:  global char offsets to underline (ghost and pace carets)
    wrong:  turns the caret red after a rejected key
    below:  extra lines under the words (the on-screen keyboard)
    hidden: memory mode, untyped characters are blanked out
    errors: (word, letter) positions that had a wrong key; once fixed they
            look as the corrected letters setting says
    combo, now:  for theme heat, flow and the animated modifiers
    last_error:  when the last wrong key was, for shake
    typo_keys:   the wrong key pressed at each of those, for indicate typos
    """
    p = Painter(st, settings, words, typed, wi, marks, wrong, hidden, errors,
                combo, now, typo_keys)
    out = []
    if header:
        out += ["  " + st.dim + header + RESET, ""]
    focus = len(out)
    text = tape_line(p, width) + [""] if settings.tape else block_lines(p, width)
    shifted = " " * (2 + p.shake(last_error))       # shake nudges just the words
    out += [shifted + line if line else "" for line in text]
    if below:
        out += [""] + ["  " + line for line in below]
    pinned = ["", st.dim + footer + RESET] if footer else ()
    console.present(out, focus, pinned)
