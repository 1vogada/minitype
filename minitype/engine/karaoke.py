"""Where the karaoke caret is: a song's lyrics laid out as the words you
type, with the moments they're sung at.

LRC lyrics time the start of each line. Between two starts the singer
doesn't take the whole gap - a line is sung, then there's a breath, a
pause or an instrumental - so each line also gets an end: how long its
letters take at this song's own pace (the median over its lines, as
letters a second), but never past the next line's start. The caret runs
through a line from its start to its end, then waits for the next one.

Enhanced LRC times each word too ("<00:12.50>word"); those times are used
as they are, and the tags never reach the words.
"""

import re
import statistics

_WORD_TAG = re.compile(r"<(\d+):(\d+(?:\.\d+)?)>")
RATE = 12.0             # letters a second, for a song too short to tell
RATE_RANGE = (4.0, 30.0)
LEAD = 0.3              # seconds a line takes beyond its letters (the first word's attack)


def _pieces(text):
    """(seconds or None, word) for each word of a line, its word tags read."""
    out, t = [], None
    for k, part in enumerate(_WORD_TAG.split(text)):
        if k % 3 == 1:
            t = int(part) * 60
        elif k % 3 == 2:
            t += float(part)
        else:
            for w in part.replace("—", " ").replace("--", " ").split():
                out.append((t, w))
                t = None
    return out


def plain(text):
    """A line's text without word tags."""
    return " ".join(w for _, w in _pieces(text))


def layout(lines, tidy_word=None):
    """The words of (seconds or None, text) lines, the word indices where a
    line starts (after the first), the line starts as (seconds, char
    offset), and the caret's points (seconds, char offset). tidy_word
    changes each word (punctuation off), "" drops it."""
    words, breaks, starts, rows = [], set(), [], []
    at = 0
    for t, text in lines:
        line = []
        for wt, w in _pieces(text):
            w = tidy_word(w) if tidy_word else w
            if w:
                line.append((wt, w, at + sum(len(x) + 1 for _, x, _ in line)))
        if not line:
            if t is not None and words:
                rows.append((t, at, at, ()))         # a break: nothing sung
            continue
        if words:
            breaks.add(len(words))
        if t is not None:
            starts.append((t, at))
        n = sum(len(w) + 1 for _, w, _ in line)
        rows.append((t, at, at + n - 1, tuple((wt, c) for wt, _, c in line if wt is not None)))
        words += [w for _, w, _ in line]
        at += n
    return words, breaks, starts, _points(rows, at)


def _rate(rows):
    """This song's pace in letters a second: the median of its lines' letters
    over the time to the next line (lines with a gap after them count too:
    the median shrugs them off)."""
    timed = [r for r in rows if r[0] is not None]
    seen = []
    for (t0, a, b, _), (t1, *_rest) in zip(timed, timed[1:]):
        if b > a and t1 > t0:
            seen.append((b - a) / (t1 - t0))
    rate = statistics.median(seen) if seen else RATE
    return min(max(rate, RATE_RANGE[0]), RATE_RANGE[1])


def _points(rows, end):
    rate = _rate(rows)
    timed = [r for r in rows if r[0] is not None]
    pts = []
    for k, (t, a, b, tags) in enumerate(timed):
        nxt = timed[k + 1][0] if k + 1 < len(timed) else None
        pts.append((t, a))
        for wt, c in tags:
            pts.append((wt, c))
        if b > a:
            # the line ends once its letters are sung (from its last word
            # time, if words are timed), not later than the next line starts
            last_t, last_c = (tags[-1] if tags else (t, a))
            done = last_t + (b - last_c) / rate + (0 if tags else LEAD)
            pts.append((min(done, nxt) if nxt is not None else done, b))
    # times only go forward, and so does the caret
    out = []
    for t, c in sorted(pts, key=lambda p: p[0]):
        c = max(c, out[-1][1]) if out else c
        out.append((t, c))
    if out and out[-1][1] < end:
        out.append((out[-1][0] + 0.5, end))
    return out


def position(points, t):
    """The caret's char offset at t seconds into the song."""
    if not points:
        return None
    if t <= points[0][0]:
        return points[0][1]
    for (t0, c0), (t1, c1) in zip(points, points[1:]):
        if t < t1:
            return int(c0 + (c1 - c0) * (t - t0) / max(t1 - t0, 1e-6))
    return points[-1][1]
