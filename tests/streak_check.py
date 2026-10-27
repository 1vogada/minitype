"""Day streaks and the days-typed calendar on the profile."""
import os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from datetime import date, datetime, timedelta
from minitype.context import App
from minitype.terminal import console
from minitype.ui import profile

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
TODAY = date(2026, 10, 27)                       # a tuesday


def app_with(days):
    """An app with a run of `secs` on each of {days back: secs}."""
    a = App()
    noon = datetime(TODAY.year, TODAY.month, TODAY.day, 12).timestamp()
    a.history.runs = [{"t": noon - d * 86400, "mode": "30 seconds", "wpm": 80, "acc": 97,
                       "secs": s, "failed": False} for d, s in days.items()]
    return a


h = app_with({}).history
assert h.streak(TODAY) == (0, 0)
# today and the two days before, a gap, then a longer run further back
h = app_with({0: 60, 1: 60, 2: 60, 4: 60, 10: 60, 11: 60, 12: 60, 13: 60, 14: 60}).history
assert h.streak(TODAY) == (3, 5), h.streak(TODAY)
# nothing yet today: yesterday's streak is still alive
h = app_with({1: 60, 2: 60}).history
assert h.streak(TODAY) == (2, 2)
# two days ago it's broken
h = app_with({2: 60, 3: 60}).history
assert h.streak(TODAY) == (0, 2)
# two runs on one day are one day, and their time adds up
a = app_with({0: 60, 1: 30})
a.history.runs.append(dict(a.history.runs[0]))
assert a.history.streak(TODAY) == (2, 2)
assert a.history.day_seconds()[TODAY] == 120

# the calendar: a column a week, monday on top, darker for longer
console.term_size = lambda: (80, 40)
a = app_with({0: 700, 1: 200, 2: 400})
a.settings.daily_goal = 10
rows = [strip(l) for l in profile.calendar_lines(a, a.styles(), 80, TODAY)]
assert len(rows) == 9, rows                       # months, seven days, the key
mon, tue, sun = rows[1].split(), rows[2].split(), rows[7].split()
assert mon[-1] == "▪", mon                        # yesterday: a little
assert tue[-1] == "█", tue                        # today: the whole goal
assert sun[-1] == "■", sun                        # sunday: over half the goal
assert len(rows[3].rstrip()) < len(rows[2].rstrip()), "days after today stay blank"
assert rows[0].split()[0] in ("may", "apr", "jun"), rows[0]
assert "less" in rows[-1] and "more" in rows[-1]
# narrow: fewer weeks, never wider than the screen
rows = [strip(l) for l in profile.calendar_lines(a, a.styles(), 40, TODAY)]
assert max(map(len, rows)) <= 40 and len(rows[1].split()) - 1 >= 4, rows

# the profile shows the streak and the calendar; the goal line the streak
a.history.runs = app_with({0: 700, 1: 200, 2: 400}).history.runs
text = "\n".join(strip(l) for l in profile.draw(a, a.styles()))
assert "days typed" in text and "less" in text, text
assert profile.streak_text(a) in ("3 days", ""), profile.streak_text(a)   # relative to the real today
print("ALL OK")
