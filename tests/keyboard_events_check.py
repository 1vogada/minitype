"""Keyboard learn, part two: every keystroke of a test goes to the keyboard
app so it can match mistakes to key depth. The recording (what the text
wanted, what was typed, backspace, zen and past the end with nothing
wanted), nothing kept or sent with keyboard learn off, the calls (one
events call, split at MAX_EVENTS, in the background, flushed on quit) and
the line the results show from the app's "patterns". The HTTP is faked:
nothing here reaches the real keyboard app."""
import json
import os
import re
import tempfile
import threading
import time

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"
from unittest import mock                                   # noqa: E402
from minitype import keyboard_app as ka                     # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.engine import runner                          # noqa: E402
from minitype.engine.runner import TypingTest, ZenTest      # noqa: E402
from minitype.engine.spec import TestSpec                   # noqa: E402
from minitype.terminal import keys                          # noqa: E402
from minitype.ui import keyboard_learn as kl                # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
SPEC = TestSpec("c", "words", 2, "custom", ("cat", "dog"))
STATE = {"on": True, "percent": 70, "floorMm": 0.3, "minPresses": 20, "tunedKeys": 42,
         "learningKeys": 3, "lastApply": None, "lastError": None, "keys": []}
PATTERNS = {"keys": [{"key": "8", "hits": 120, "misses": 3, "ghosts": 1, "doubles": 0, "typos": 4},
                     {"key": "j", "hits": 80, "misses": 0, "ghosts": 2, "doubles": 0, "typos": 0}],
            "pairs": [{"expected": "8", "typed": "9", "count": 4},
                      {"expected": "e", "typed": "r", "count": 2}],
            "fastErrorShare": 0.62,
            "adjusted": [{"key": "8", "why": "misses", "changeMm": -0.1}]}


class Fake:
    """urlopen stand-in: records each body, answers `reply` (a dict or an exception)."""

    def __init__(self, reply):
        self.reply, self.sent, self.urls = reply, [], []

    def __call__(self, req, timeout=None):
        self.sent.append(json.loads(req.data))
        self.urls.append(req.full_url)
        if isinstance(self.reply, Exception):
            raise self.reply
        body = json.dumps(self.reply).encode()
        return mock.MagicMock(__enter__=lambda s: mock.MagicMock(read=lambda: body),
                              __exit__=lambda *a: False)


def fake(reply):
    f = Fake(reply)
    return f, mock.patch("urllib.request.urlopen", f)


def new(spec=SPEC, cls=TypingTest, **settings):
    app = App()
    app.settings.keyboard_learn = True
    for k, v in settings.items():
        setattr(app.settings, k, v)
    return app, cls(app, spec)


def typ(t, s, now=1000.0):
    for i, ch in enumerate(s):
        t.handle(keys.BACKSPACE if ch == "<" else ch, now + i / 10)


def pairs(t):
    return [(e["expected"], e["typed"]) for e in t.keystrokes]


# ---------------------------------------------------------------- recording
app, t = new()
typ(t, "cxt<<at dog")
assert pairs(t) == [("c", "c"), ("a", "x"), ("t", "t"), (" ", "\b"), ("t", "\b"),
                    ("a", "a"), ("t", "t"), (" ", " "), ("d", "d"), ("o", "o"), ("g", "g")], pairs(t)
assert [e["t"] for e in t.keystrokes][:3] == [1000000, 1000100, 1000200], "epoch ms, ints"
assert all(type(e["t"]) is int for e in t.keystrokes)
assert all(set(e) == {"t", "expected", "typed"} for e in t.keystrokes)
assert t.done and t.typed == ["cat", "dog"]
# the same position logic as the marks: a wrong letter is what the test compared
app, t = new()
typ(t, "dat")
assert pairs(t) == [("c", "d"), ("a", "a"), ("t", "t")] and (0, 0) in t.err_marks
# extra letters past a word: the text wanted the space; past the text's end: nothing
app, t = new()
typ(t, "catt ")
assert pairs(t)[3:] == [(" ", "t"), (" ", " ")]
app, t = new(TestSpec("c", "words", 1, "custom", ("cat",)), stop_on_error="word")
typ(t, "cax")                                   # the last word stays open: fix it to finish
typ(t, "z")
assert pairs(t)[-1] == (None, "z"), pairs(t)
# stop on letter: the wrong key never lands, but it is a keystroke
app, t = new(stop_on_error="letter")
typ(t, "cxa")
assert pairs(t) == [("c", "c"), ("a", "x"), ("a", "a")] and t.typed[0] == "ca"
# other control keys are skipped; ctrl-backspace too; esc leaves
app, t = new()
typ(t, "c")
for k in (keys.LEFT, keys.CTRL_BACKSPACE, keys.RESIZE, keys.ENTER):
    t.handle(k, 1001.0)
assert pairs(t) == [("c", "c")], pairs(t)
# forgive: the left-out punctuation is skipped, as the test does
app, t = new(TestSpec("c", "words", 2, "custom", ("hi,", "you")), punctuation="forgive")
assert t.words[0] == "hi,", t.words
typ(t, "hi y")
assert pairs(t) == [("h", "h"), ("i", "i"), (" ", " "), ("y", "y")], pairs(t)
assert t.wi == 1
# zen: no text, nothing wanted
app, t = new(TestSpec("z", "zen", 0, "zen"), ZenTest)
typ(t, "ab <")
assert pairs(t) == [(None, "a"), (None, "b"), (None, " "), (None, "\b")]
# keyboard learn off: nothing kept
app, t = new(keyboard_learn=False)
typ(t, "cat")
assert t.keystrokes is None


# ---------------------------------------------------------------- the calls
ev = [{"t": i, "expected": "a", "typed": "a"} for i in range(4500)]
assert [len(b) for b in ka.batches(ev)] == [2000, 2000, 500] and ka.MAX_EVENTS == 2000
assert ka.batches([]) == []
assert ka.events_body(ev[:2]) == {"action": "events", "events": ev[:2]}
f, p = fake(dict(STATE, patterns=PATTERNS))
with p:
    a = ka.send_events(ev, "http://127.0.0.1:7000")
assert [len(b["events"]) for b in f.sent] == [2000, 2000, 500]
assert all(b["action"] == "events" for b in f.sent) and f.sent[0]["events"][0] == ev[0]
assert f.urls[0] == "http://127.0.0.1:7000/api/learn/typing"
assert a.ok and a.state["patterns"] == PATTERNS
f, p = fake(ConnectionRefusedError())
with p:
    a = ka.send_events(ev)
assert len(f.sent) == 1 and a.error == ka.NOT_RUNNING, "stops at the first failure"
assert ka.send_events([]) is None and ka.post_events([]) is None

# the test's end: sent in the background, the answer kept; the screen never waits
app, t = new()
typ(t, "cat dog")
gate = threading.Event()
f = Fake(dict(STATE, patterns=PATTERNS))


def slow(req, timeout=None):
    gate.wait(5)
    return f(req, timeout)


with mock.patch("urllib.request.urlopen", slow):
    t0 = time.monotonic()
    th = runner._send_keystrokes(app, t)
    assert time.monotonic() - t0 < 0.1 and th.is_alive(), "nothing waits on it"
    assert t.keystrokes == [] and app.keyboard_patterns is None
    gate.set()
    ka.flush()
assert not th.is_alive() and [len(b["events"]) for b in f.sent] == [7]
assert app.keyboard_patterns == PATTERNS and app.keyboard_app.on
assert runner._send_keystrokes(app, t) is None, "sent once"
# the app not running: nothing kept, nothing raised
app, t = new()
typ(t, "c")
with fake(ConnectionRefusedError())[1]:
    runner._send_keystrokes(app, t)
    ka.flush()
assert app.keyboard_patterns is None and app.keyboard_app is None
# keyboard learn off: no call at all
app, t = new(keyboard_learn=False)
typ(t, "cat")
f, p = fake(STATE)
with p:
    assert runner._send_keystrokes(app, t) is None
    ka.flush()
assert f.sent == []
# flush on quit gives up after its time
gate2 = threading.Event()
with mock.patch("urllib.request.urlopen", lambda *a, **k: gate2.wait(5) or (_ for _ in ()).throw(OSError())):
    th = ka.post_events(ev[:3])
    t0 = time.monotonic()
    ka.flush(0.2)
    assert 0.15 < time.monotonic() - t0 < 1.0 and th.is_alive()
    gate2.set()
    ka.flush()

# run_test hands the keystrokes over however the test ends (here: esc)
app, t = new()
seq = iter(["c", "a", keys.ESC])
with mock.patch.object(runner, "_send_keystrokes") as sent, \
        mock.patch.object(keys, "key_ready", lambda: True), \
        mock.patch.object(keys, "read_key", lambda **k: next(seq)), \
        mock.patch.object(keys, "key_time", time.time), \
        mock.patch.object(keys, "stamping", mock.MagicMock()), \
        mock.patch.object(runner, "draw", lambda *a, **k: None):
    app.settings.esc_pause = False
    runner.run_test(app, SPEC)
assert sent.call_count == 1 and pairs(sent.call_args[0][1]) == [("c", "c"), ("a", "a")]


# ---------------------------------------------------------------- the results line
lines = kl.pattern_text(PATTERNS)
assert len(lines) == 2, lines
assert lines[0] == "keyboard: 8 often missed (pressed too light) · 8→9 mixed up 4x",     "what doesn't fit is left out, not cut"
assert kl.pattern_text({"pairs": [{"expected": "8", "typed": "9", "count": 4}], "fastErrorShare": 0.7}) ==     ["keyboard: 8→9 mixed up 4x · most when typing fast"]
assert lines[1] == "keyboard: lowered 8 by 0.1 mm"
assert kl.pattern_text(dict(PATTERNS, fastErrorShare=0.2))[0] == \
    "keyboard: 8 often missed (pressed too light) · 8→9 mixed up 4x"
assert kl.pattern_text({"keys": [{"key": "j", "ghosts": 3}], "pairs": [{"expected": " ", "typed": "n",
                                                                        "count": 2}]}) == \
    ["keyboard: j typed by brushing it · space→n mixed up 2x"]
assert kl.pattern_text({"keys": [{"key": "k", "doubles": 2}]}) == ["keyboard: k typed twice (bounce)"]
assert kl.pattern_text({"adjusted": [{"key": "8", "changeMm": 0.05}, {"key": "9", "changeMm": -0.25}]}) == \
    ["keyboard: raised 8 by 0.05 mm · lowered 9 by 0.25 mm"]
# nothing to say: no lines
for empty in (None, {}, [], "x", {"keys": [], "pairs": [], "adjusted": []},
              {"keys": [{"key": "8", "misses": 1}], "pairs": [{"expected": "8", "typed": "9", "count": 1}],
               "fastErrorShare": 0.9},
              {"keys": [{"key": "8", "misses": "3"}, "x", {"misses": 5}], "pairs": "no",
               "adjusted": [{"key": "8", "changeMm": 0}, {"key": "8", "changeMm": True}, None]}):
    assert kl.pattern_text(empty) == [], empty

app = App()
st = app.styles()
app.keyboard_patterns = PATTERNS
assert kl.pattern_lines(app, st) == [], "learn off: nothing"
app.settings.keyboard_learn = True
assert [strip(x) for x in kl.pattern_lines(app, st)] == kl.pattern_text(PATTERNS)
app.keyboard_patterns = None
assert kl.pattern_lines(app, st) == []

# the results wait for the keystrokes' answer (at most WAIT), then skip the status call
app = App()
app.settings.keyboard_learn = True
app, t = new()
typ(t, "cat")
f, p = fake(dict(STATE, patterns=PATTERNS))
with p:
    app.keyboard_sent = (time.time(), ka.post_events(t.keystrokes, done=lambda a: (
        setattr(app, "keyboard_app", a), setattr(app, "keyboard_patterns", a.state.get("patterns")))))
    kl.refresh(app)
assert [b["action"] for b in f.sent] == ["events"], "the answer is the status: no second call"
assert app.keyboard_patterns == PATTERNS
# an answer that's late: the results go on after WAIT and ask the status
gate3 = threading.Event()
calls = []


def late(req, timeout=None):
    calls.append(json.loads(req.data)["action"])
    if calls[-1] == "events":
        gate3.wait(5)
    return Fake(STATE)(req, timeout)


app.keyboard_patterns = None
with mock.patch("urllib.request.urlopen", late):
    app.keyboard_sent = (time.time(), ka.post_events(t.keystrokes))
    t0 = time.monotonic()
    kl.refresh(app)
    took = time.monotonic() - t0
    gate3.set()
    ka.flush()
assert kl.WAIT - 0.05 < took < kl.WAIT + 0.5, took
assert calls == ["events", "status"], calls
print("ALL OK")
