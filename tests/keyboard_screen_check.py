"""The keyboard screen (main menu k): press a key, see what the keyboard
app learnt about it. Key matching (upper case, shifted symbols, space),
each key's lines from a sample status answer, "app not running", the
menu item only with keyboard learn on, and the screen itself: keys pick,
arrows move, esc leaves, status calls only (in the background, refreshed),
nothing sent as typing. The HTTP is faked: nothing reaches the real app."""
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
from minitype.ui import keyboard_screen as ks               # noqa: E402
from minitype.ui import main_menu as mm                     # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.term_size = lambda: (110, 40)
console._last_size = (110, 40)
STATE = {"on": True, "percent": 70, "floorMm": 0.3, "minPresses": 20, "tunedKeys": 1,
         "learningKeys": 1, "lastApply": None, "lastError": None,
         "keys": [{"key": "8", "slot": 9, "presses": 140, "actuationMm": 1.2, "learntMm": 1.05},
                  {"key": "W", "slot": 14, "presses": 12, "actuationMm": 1.5, "learntMm": None},
                  {"key": "Space", "slot": 70, "presses": 300, "actuationMm": 1.0, "learntMm": 0.9}],
         "patterns": {"keys": [{"key": "8", "hits": 120, "misses": 3, "ghosts": 1, "doubles": 0,
                                "typos": 4}],
                      "pairs": [{"expected": "8", "typed": "9", "count": 4},
                                {"expected": "7", "typed": "8", "count": 2},
                                {"expected": "e", "typed": "r", "count": 3}],
                      "fastErrorShare": 0.62,
                      "adjusted": [{"key": "8", "why": "misses", "changeMm": -0.1},
                                   {"key": "8", "why": "doubles", "suggested": True},
                                   {"key": "w", "why": "ghosts", "changeMm": 0.05}]}}


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


# ---------------------------------------------------------------- matching
assert ks.key_id("a") == "A" and ks.key_id("W") == "W" and ks.key_id("!") == "1"
assert ks.key_id("*") == "8" and ks.key_id("?") == "/" and ks.key_id("{") == "["
assert ks.key_id(" ") == ks.key_id("Space") == ks.key_id("space") == "SPACE"
assert ks.key_id("") is None and ks.key_id(None) is None
assert ks.label(" ") == "Space" and ks.label("q") == "Q"

# ---------------------------------------------------------------- a key's lines
A = ka.Answer(state=STATE)
assert ks.detail(A, "8") == [
    "8",
    "actuation   1.20 mm now",
    "learnt      1.05 mm",
    "presses     140",
    "hits 120 · misses 3 (pressed too light) · ghosts 1 (typed by brushing it) · doubles 0"
    " · typos 4 (wrong key)",
    "you typed 9 for 8: 4x",
    "you typed 8 for 7: 2x",
    "changed: types earlier by 0.1 mm (misses)",
    "changed: suggested for the bounce guard",
], ks.detail(A, "8")
assert ks.detail(A, "W") == ["W", "actuation   1.50 mm now", "learning    12 / 20 presses",
                             "presses     12", "changed: types later by 0.05 mm (ghosts)"]
assert ks.detail(A, ks.key_id(" "))[:3] == ["Space", "actuation   1.00 mm now", "learnt      0.90 mm"]
assert ks.detail(A, "Q") == ["Q", "nothing learnt about it yet"]
assert ks.detail(A, "E")[1:] == ["you typed R for E: 3x"]
# no patterns (an older app): just the keys
no_pat = ka.Answer(state={k: v for k, v in STATE.items() if k != "patterns"})
assert ks.detail(no_pat, "8") == ["8", "actuation   1.20 mm now", "learnt      1.05 mm",
                                  "presses     140"]
assert ks.detail(ka.Answer(error=ka.NOT_RUNNING), "8") == ["8", "keyboard learn: app not running"]
assert ks.detail(None, "8")[1] == "asking the keyboard app..."
odd = ka.Answer(state={"on": True, "keys": [None, {"key": 5}], "patterns": {"keys": "x", "pairs": [1],
                                                                          "adjusted": [{"key": "8"}]}})
assert ks.detail(odd, "8") == ["8", "nothing learnt about it yet"]

# ---------------------------------------------------------------- the main menu item
app = App()
assert "keyboard" not in [it.label for it in mm.build_items(app)], "learn off: no item"
app.settings.keyboard_learn = True
item = next(it for it in mm.build_items(app) if it.label == "keyboard")
assert item.key == "k" and item.section == "practice"


# ---------------------------------------------------------------- the screen
def run(app, presses, reply, every=60, gap=0.0):
    """Drive keyboard_screen with `presses` (a key, or a number: wait that long)."""
    f = Fake(reply)
    frames, queue = [], list(presses)

    def ready():
        while queue and isinstance(queue[0], (int, float)):
            time.sleep(queue.pop(0))
        return bool(queue)

    with mock.patch("urllib.request.urlopen", f), \
            mock.patch.object(keys, "key_ready", ready), \
            mock.patch.object(keys, "read_key", lambda **k: queue.pop(0)), \
            mock.patch.object(console, "present", lambda lines, *a, **k: frames.append(
                "\n".join(strip(x) for x in lines))):
        t0 = time.monotonic()
        assert ks.keyboard_screen(app, every) is None
        took = time.monotonic() - t0
    return f, frames, took


app = App()
app.settings.keyboard_learn = True
with mock.patch.object(ka, "post_events") as posted:
    f, frames, _ = run(app, [0.2, "8", "*", keys.LEFT, keys.ESC], STATE)
assert not posted.called, "keys here aren't typing"
assert f.sent and all(b == {"action": "status"} for b in f.sent), f.sent
last_8 = [fr for fr in frames if "actuation   1.20 mm now" in fr]
assert last_8 and "you typed 9 for 8: 4x" in last_8[-1] and "changed: suggested for the bounce guard" in last_8[-1]
assert "keyboard learn: on · 1 key tuned · 1 learning" in frames[-1]
assert "  7\n  you typed 8 for 7: 2x" in frames[-1], "left of 8: 7"
assert " 8·8 " in frames[-1], "8 mistakes on 8"
assert app.cursors["keyboard"] == ks.place("7")
assert app.keyboard_app.on, "the menu's status line gets the answer too"

# space and a shifted symbol pick their key; arrows wrap; esc leaves
assert ks.place(" ") == (4, 0) and ks.place("!") == ks.place("1")
assert ks.move((0, 0), keys.LEFT) == (0, len(ks.ROWS[0]) - 1)
assert ks.move((1, 12), keys.DOWN) == (2, len(ks.ROWS[2]) - 1)
assert ks.move((4, 0), keys.DOWN) == (0, 0)

# the app not running: said so, input never waits on it
app = App()
app.settings.keyboard_learn = True
f, frames, _ = run(app, [0.2, "8", keys.ESC], ConnectionRefusedError())
assert "keyboard learn: app not running" in frames[-1]

# a slow app: keys are answered straight away, before any reply
gate = threading.Event()
calls = []


def slow(req, timeout=None):
    calls.append(1)
    gate.wait(5)
    raise OSError()


app = App()
app.settings.keyboard_learn = True
with mock.patch("urllib.request.urlopen", slow):
    queue = ["8", "9", keys.ESC]
    shown = []
    with mock.patch.object(keys, "key_ready", lambda: bool(queue)), \
            mock.patch.object(keys, "read_key", lambda **k: queue.pop(0)), \
            mock.patch.object(console, "present", lambda lines, *a, **k: shown.append(
                "\n".join(strip(x) for x in lines))):
        t0 = time.monotonic()
        ks.keyboard_screen(app)
        assert time.monotonic() - t0 < 2.0, "never blocks on the app (it holds 5 s)"
    gate.set()
assert any("asking the keyboard app..." in x for x in shown)

# refreshed while open: a new answer shows without a key
app = App()
app.settings.keyboard_learn = True
f, frames, _ = run(app, [0.35, keys.ESC], STATE, every=0.1)
assert len(f.sent) >= 2, f.sent
print("ALL OK")
