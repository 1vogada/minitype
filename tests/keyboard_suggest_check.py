"""The keyboard app's suggestions (a key that doubles: put it in the bounce
guard?): the answer bodies, the box (one per suggestion, group 2 marked
for the big keys, esc = later), the answer sent in the background, a key
answered not asked again while still listed, asked on the results and as
the keyboard screen opens, and the adjusted lines (suggested / yes / no).
The HTTP is faked: nothing reaches the real keyboard app."""
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
from minitype.terminal import console, keys                 # noqa: E402
from minitype.ui import anywhere                            # noqa: E402
from minitype.ui import keyboard_learn as kl                # noqa: E402
from minitype.ui import keyboard_screen as ks               # noqa: E402
from minitype.ui import keyboard_suggest as sg              # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.term_size = lambda: (110, 40)
console._last_size = (110, 40)
SUGS = [{"key": "Space", "slot": 41, "why": "doubles", "count": 3},
        {"key": "J", "slot": 30, "why": "doubles", "count": 2},
        {"key": "X", "why": "something new"}]
STATE = {"on": True, "tunedKeys": 1, "learningKeys": 0, "minPresses": 20, "keys": [],
         "patterns": {"keys": [], "pairs": [], "suggestions": SUGS,
                      "adjusted": [{"key": "Space", "why": "doubles", "suggested": True}]}}


class Fake:
    def __init__(self, reply):
        self.reply, self.sent = reply, []

    def __call__(self, req, timeout=None):
        self.sent.append(json.loads(req.data))
        if isinstance(self.reply, Exception):
            raise self.reply
        body = json.dumps(self.reply).encode()
        return mock.MagicMock(__enter__=lambda s: mock.MagicMock(read=lambda: body),
                              __exit__=lambda *a: False)


def new(state=STATE):
    app = App()
    app.settings.keyboard_learn = True
    app.keyboard_app = ka.Answer(state=state)
    return app


def ask(app, presses, reply=STATE):
    """sg.ask with `presses`; (bodies sent, the boxes shown, its return)."""
    f, seq, boxes = Fake(reply), iter(presses), []
    with mock.patch("urllib.request.urlopen", f), \
            mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "set_overlay",
                              lambda o: boxes.append(strip("\n".join(o))) if o else None):
        got = sg.ask(app, lambda: None)
        ka.flush()
    assert next(seq, None) is None, "every key used"
    return f.sent, boxes, got


# ---------------------------------------------------------------- the bodies
assert ka.suggestion_body("Space", True, 2) == {"action": "accept", "key": "Space", "group": 2}
assert ka.suggestion_body("J", True, 1) == {"action": "accept", "key": "J", "group": 1}
assert ka.suggestion_body("L", True) == {"action": "accept", "key": "L"}
assert ka.suggestion_body("L", True, 7) == {"action": "accept", "key": "L"}
assert ka.suggestion_body("Space", False, 2) == {"action": "dismiss", "key": "Space"}
assert ka.suggestion_body("", True) is None and ka.answer_suggestion(None, True) is None

# ---------------------------------------------------------------- the box
q = sg.question(SUGS[0])
assert q[0] == "Space typed twice from one press 3x (a bounce).\nPut it in the keyboard's bounce guard?"
assert q[1] == ("group 1", "group 2", "no") and q[2] == 1, "group 2 marked for Space"
assert sg.question(SUGS[1])[2] == 0, "group 1 for the rest"
for big in ("LShift", "RShift", "Enter", "Bksp"):
    assert sg.question({"key": big, "why": "doubles"})[2] == 1, big
assert sg.question(SUGS[2]) is None, "an unknown kind isn't asked"

app = new()
sent, boxes, got = ask(app, [keys.ENTER, "n"])     # Space: enter takes group 2; J: no
assert sent == [{"action": "accept", "key": "Space", "group": 2}, {"action": "dismiss", "key": "J"}], sent
assert got == [("Space", True, 2), ("J", False, None)]
assert "Space typed twice from one press 3x (a bounce)." in boxes[0]
assert "Put it in the keyboard's bounce guard?" in boxes[0]
assert "> group 2" in boxes[0] and "group 1" in boxes[0] and " no " in boxes[0]
assert "J typed twice from one press 2x" in boxes[-1] and "> group 1" in boxes[-1]
assert all(len(set(len(x) for x in b.splitlines())) == 1 for b in boxes), "a square box"
# answered: not asked again while the app still lists them
sent, boxes, got = ask(app, [])
assert sent == [] and boxes == [] and got == []
# no longer listed: forgotten, so a new suggestion for them is asked
app.keyboard_app = ka.Answer(state=dict(STATE, patterns={"suggestions": []}))
assert sg.pending(app) == [] and app.keyboard_answered == set()
app.keyboard_app = ka.Answer(state=STATE)
assert [x["key"] for x in sg.pending(app)] == ["Space", "J"]

# esc: nothing sent, asked again later; left / right / 1 / 2 pick
app = new()
sent, boxes, got = ask(app, [keys.ESC])
assert sent == [] and len(boxes) == 1 and got == []
assert [x["key"] for x in sg.pending(app)] == ["Space", "J"]
sent, _, _ = ask(app, [keys.LEFT, keys.ENTER, "2"])
assert sent == [{"action": "accept", "key": "Space", "group": 1},
                {"action": "accept", "key": "J", "group": 2}], sent
# the reply (the status) is kept
assert app.keyboard_app.ok and app.keyboard_patterns == STATE["patterns"]
# learn off, the app not running, no suggestions: nothing asked
app = new()
app.settings.keyboard_learn = False
assert ask(app, []) == ([], [], [])
app = new()
app.keyboard_app = ka.Answer(error=ka.NOT_RUNNING)
assert ask(app, []) == ([], [], [])
app.keyboard_app = None
assert ask(app, []) == ([], [], [])
app = new(dict(STATE, patterns={"suggestions": "x"}))
assert ask(app, []) == ([], [], [])
app = new({k: v for k, v in STATE.items() if k != "patterns"})
assert ask(app, []) == ([], [], [])

# never blocks the screen: the answer goes in the background
gate = threading.Event()


def slow(req, timeout=None):
    gate.wait(5)
    raise OSError()


app = new()
seq = iter(["1", "n"])
with mock.patch("urllib.request.urlopen", slow), \
        mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "set_overlay", lambda o: None):
    t0 = time.monotonic()
    sg.ask(app, lambda: None)
    assert time.monotonic() - t0 < 2.0, "the answer is held 5 s: nothing waited on it"
    gate.set()
    ka.flush()

# the two-answer box is as it was (the start-up question, resume?)
seq = iter([keys.RIGHT, keys.RIGHT, keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "set_overlay", lambda o: None):
    assert anywhere.ask_dialog(App(), lambda: None, "Resume?") is True, "right twice wraps back"
for key, want in (("y", True), ("N", False), (keys.ESC, "later")):
    with mock.patch.object(keys, "read_key", lambda *a, **k: key), \
            mock.patch.object(console, "set_overlay", lambda o: None):
        assert anywhere.ask_dialog(App(), lambda: None, "Q?", esc="later") == want

# ---------------------------------------------------------------- the adjusted lines
adj = {"adjusted": [{"key": "Space", "why": "doubles", "suggested": True},
                    {"key": "J", "why": "doubles", "accepted": True},
                    {"key": "K", "why": "doubles", "dismissed": True}]}
assert kl.pattern_text(adj) == ["keyboard: Space: suggested for the bounce guard"], kl.pattern_text(adj)
assert kl.pattern_text({"adjusted": adj["adjusted"][1:]}) == [
    "keyboard: J: put in the bounce guard (you said yes)"]
assert kl.guard_text(adj["adjusted"][2]) == "bounce guard dismissed (you said no)"
assert kl.guard_text({"key": "8", "guard": True}) is None, "no guard: true any more"
A = ka.Answer(state=dict(STATE, patterns=adj))
assert ks.detail(A, "J") == ["J", "changed: put in the bounce guard (you said yes)"]
assert ks.detail(A, "SPACE") == ["Space", "changed: suggested for the bounce guard"]

# ---------------------------------------------------------------- where it's asked
# the results: once, after the first draw
from minitype.ui import results                              # noqa: E402
calls = []
app = new()
with mock.patch.object(results.keyboard_suggest, "ask", lambda a, r: calls.append(r) or []), \
        mock.patch.object(results.keyboard_learn, "refresh", lambda a: None), \
        mock.patch.object(results, "draw", lambda *a: (["x"], [])), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "read_key", lambda *a, **k: keys.ESC):
    results.show_results(app, mock.MagicMock(quote="", replay=None))
assert len(calls) == 1
# the keyboard screen: once its first answer is in
app = new()
seq = [0.2, "n", "1", keys.ESC]                 # Space: no; J: group 1; then leave


def ready():
    if seq and isinstance(seq[0], float):        # a pause: no key yet, the answer comes in
        time.sleep(seq.pop(0))
        return False
    return bool(seq)


def next_key():
    while seq and isinstance(seq[0], float):     # the answer may come before the pause
        seq.pop(0)
    return seq.pop(0)


f = Fake(STATE)
boxes = []
with mock.patch("urllib.request.urlopen", f), \
        mock.patch.object(keys, "key_ready", ready), \
        mock.patch.object(keys, "read_key", lambda *a, **k: next_key()), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(console, "set_overlay", lambda o: boxes.append(o) if o else None):
    ks.keyboard_screen(app, 60)
    ka.flush()
assert [b for b in f.sent if b["action"] != "status"] == [
    {"action": "dismiss", "key": "Space"}, {"action": "accept", "key": "J", "group": 1}], f.sent
print("ALL OK")
