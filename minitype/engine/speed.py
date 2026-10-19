"""Active WPM: words a minute over the time you were actually typing.

Classic WPM (scoring.score) divides the correct letters by the whole clock,
so a long stop - reading ahead, a phone call, waiting for the singer in a
lyrics test - drags it down as if you'd been typing slowly all along.

Active WPM counts the same correct letters over a different clock. Each
gap between two key presses counts as it is, up to a cap: four of your own
typical gaps (the median of this test's), but at least IDLE_MIN and at most
IDLE_MAX seconds - a pause to think still costs a little, a walk away
doesn't cost the whole test. In a lyrics test, time spent ahead of the
singer (the karaoke caret hasn't reached the letter you're on) is waiting,
not typing, so a gap counts at most one typical gap of it.
"""

import statistics

IDLE_MIN = 1.0          # seconds: a gap below this always counts in full
IDLE_MAX = 3.0          # ...and no gap counts for more than this
IDLE_MULT = 4.0         # the cap, in your own typical gaps
TYPICAL = 0.25          # a typical gap before there are any to go by


def gaps(times, end):
    """The gaps after each press: to the next press, the last one to `end`."""
    out = [b - a for a, b in zip(times, times[1:])]
    if times:
        out.append(max(0.0, end - times[-1]))
    return out


def typical(between):
    """Your typical gap between presses: the median of the positive ones."""
    seen = [g for g in between if g > 0]
    return max(statistics.median(seen), 0.05) if seen else TYPICAL


def cap(typ):
    return min(max(IDLE_MULT * typ, IDLE_MIN), IDLE_MAX)


def active_seconds(times, end, waits=()):
    """Seconds of typing in a test whose presses came at `times` (seconds,
    from the first) up to `end`; waits[i] is how much of the gap after
    press i was spent waiting for the singer."""
    if not times:
        return 0.0
    g = gaps(times, end)
    # your pace from the gaps you were typing in, not the ones spent waiting
    w = list(waits) + [0.0] * (len(g) - len(waits))
    typ = typical([x for x, wx in zip(g[:-1], w) if wx < x / 2])
    top = cap(typ)
    total = 0.0
    for i, gap in enumerate(g):
        w = min(waits[i], gap) if i < len(waits) else 0.0
        total += min(w, typ) + min(gap - w, top)
    return total


def wpm(chars, keys, secs):
    """(wpm, raw) for correct letters and all presses over secs."""
    mins = secs / 60
    return ((chars / 5) / mins if mins else 0.0, (keys / 5) / mins if mins else 0.0)
