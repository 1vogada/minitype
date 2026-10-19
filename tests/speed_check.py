"""Active WPM: long stops capped, waiting for the singer left out, and
both systems kept so switching between them works on old runs too."""

import os
import sys
import tempfile
import time
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from minitype.context import App                                 # noqa: E402
from minitype.engine import speed                                # noqa: E402
from minitype.engine.runner import TypingTest                    # noqa: E402
from minitype.engine.spec import TestSpec                        # noqa: E402
from minitype.ui import lyrics_mode, results                     # noqa: E402
from minitype.words import lyrics                                # noqa: E402

# ---------------------------------------------------------------- the clock
steady = [0.2 * k for k in range(50)]
assert abs(speed.active_seconds(steady, steady[-1]) - steady[-1]) < 1e-9, "no stops: the clock"
paused = steady[:25] + [t + 60 for t in steady[25:]]
got = speed.active_seconds(paused, paused[-1])
assert abs(got - (steady[-1] - 0.2 + speed.IDLE_MIN)) < 1e-9, got   # the minute: 1s at most
slow = [1.0 * k for k in range(20)] + [19 + 30.0]
assert abs(speed.active_seconds(slow, slow[-1]) - (19 + speed.IDLE_MAX)) < 1e-9, \
    "a slow typist's cap is bigger, up to IDLE_MAX"
tail = speed.active_seconds(steady, steady[-1] + 100)
assert abs(tail - (steady[-1] + speed.IDLE_MIN)) < 1e-9, "walked away at the end: capped too"
waited = speed.active_seconds([0, 0.2, 10.2], 10.2, waits=[0, 10.0, 0])
assert abs(waited - (0.2 + 0.2)) < 1e-9, waited          # 10s waiting: one typical gap of it
assert speed.active_seconds([], 5) == 0

# ---------------------------------------------------------------- a test, both ways
app = App()
app.settings.stop_on_error = "off"
spec = TestSpec("w", "words", 4, "custom", words=("aaaa", "bbbb", "cccc", "dddd"))
clock = [1000.0]


def typ(t, text, step=0.2):
    for ch in text:
        clock[0] += step
        with mock.patch.object(time, "time", lambda: clock[0]):
            t.handle(ch, clock[0])


t = TypingTest(app, spec)
typ(t, "aaaa bbbb ")
clock[0] += 120                                    # two minutes away
typ(t, "cccc dddd")
el = clock[0] - t.start
classic, active = t.classic(el)[0], t.active(el)[0]
assert classic < 10 and active > 50, (classic, active)
app.settings.wpm_system = "classic"
assert t.score(el)[0] == classic
app.settings.wpm_system = "active"
assert t.score(el)[0] == active and t.score(el)[2] == t.classic(el)[2], "same accuracy"
with mock.patch.object(time, "time", lambda: clock[0]):
    r = t.result()
assert r.system == "active" and r.wpm == active and r.classic == classic and r.active == active
assert r.active_secs < 5 < r.elapsed
head = " ".join(results.headline(app, app.styles(), r))
assert f"{classic:.1f} classic" in head and "s typing)" in head, head

# ---------------------------------------------------------------- history keeps both
h = app.history
run = h.runs[-1]
assert run["wpm"] == round(classic, 1) and run["awpm"] == round(active, 1)
mode = h.mode(r)
assert h.pbs[mode]["wpm"] == round(classic, 1) and h.pbs[mode]["awpm"] == round(active, 1)
app.settings.wpm_system = "classic"
assert h.pb(r) == round(classic, 1) and h.best_by_mode()[mode] == round(classic, 1)
app.settings.wpm_system = "active"
assert h.pb(r) == round(active, 1)
# a run from before active wpm counts with its classic one
h.runs.append({"t": 0, "mode": "old", "wpm": 42.0, "acc": 99.0, "secs": 30, "failed": False})
h.pbs["old"] = {"wpm": 42.0, "acc": 99.0, "t": 0}
assert h.speed(h.runs[-1]) == 42.0 and h.best_by_mode()["old"] == 42.0
# a classic-mode run that beats only the active best still counts as a best there
r2 = type(r)(**dict(r.__dict__))
r2.classic, r2.active, r2.wpm, r2.system = classic - 1, active + 5, active + 5, "active"
assert h.add(r2) and h.pbs[mode]["awpm"] == round(active + 5, 1)
assert h.pbs[mode]["wpm"] == round(classic, 1), "the classic best stays"

# ---------------------------------------------------------------- waiting for the singer
song = lyrics.Song("s", "a", lines=((0.0, "go"), (30.0, "now")))
lt = TypingTest(app, lyrics_mode.spec_for(song))
clock[0] = 5000.0
typ(lt, "go ")                                     # sung at 0s: you're done by 0.6s
clock[0] += 29.4                                   # the singer gets to "now" at 30s
typ(lt, "now")
el = clock[0] - lt.start
waits = lt._waits(el)
assert waits[2] > 25, waits                        # after "go ": waiting, not idle
assert lt.active_seconds(el) < 2, lt.active_seconds(el)
assert lt.active(el)[0] > 5 * lt.classic(el)[0], (lt.active(el), lt.classic(el))
# behind the singer it's not waiting: just a stop
lt2 = TypingTest(app, lyrics_mode.spec_for(lyrics.Song("s", "a", lines=((0.0, "go now"),))))
clock[0] = 9000.0
typ(lt2, "g")
clock[0] += 20
typ(lt2, "o now")
assert max(lt2._waits(clock[0] - lt2.start)) < 0.5, "a stop behind the singer is no wait"
print("ALL OK")
