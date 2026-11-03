"""Wrong-finger presses (the keyboard app's "slips": a finger on the key
next to the one meant) and the mixed-up keys drill. The slips suggestion's
box and answer, slips / fingers on the results lines and the keyboard
screen, the drill's pairs (fingers first, else pairs; kept for when the
app isn't there) and words (both keys close together, runs for digits),
the menu item, and the drill as a normal test (keystrokes recorded). The
HTTP is faked: nothing reaches the real keyboard app."""
import json
import os
import random
import re
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"
from unittest import mock                                   # noqa: E402
from minitype import keyboard_app as ka, storage            # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.engine.runner import TypingTest               # noqa: E402
from minitype.terminal import console, keys                 # noqa: E402
from minitype.ui import keyboard_learn as kl                # noqa: E402
from minitype.ui import keyboard_screen as ks               # noqa: E402
from minitype.ui import keyboard_suggest as sg              # noqa: E402
from minitype.ui import main_menu as mm                     # noqa: E402
from minitype.words import pair_drill as pd                 # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.term_size = lambda: (110, 40)
console._last_size = (110, 40)
SLIP = {"key": "L", "slot": 57, "why": "slips", "count": 9, "actuationMm": 2.2,
        "slipMm": 1.6, "normalMm": 3.3}
PATTERNS = {"keys": [{"key": "L", "hits": 200, "misses": 0, "ghosts": 0, "doubles": 0, "typos": 1,
                      "slips": 9}],
            "pairs": [{"expected": "8", "typed": "9", "count": 4}],
            "fingers": [{"meant": "K", "typed": "L", "count": 9}, {"meant": "L", "typed": "K", "count": 2},
                        {"meant": "D", "typed": "F", "count": 3}],
            "suggestions": [SLIP],
            "adjusted": [{"key": "L", "why": "slips", "suggested": True}]}
STATE = {"on": True, "tunedKeys": 1, "learningKeys": 0, "minPresses": 20,
         "keys": [{"key": "L", "presses": 210, "actuationMm": 1.4, "learntMm": 1.3}],
         "patterns": PATTERNS}


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
    app.keyboard_app = ka.Answer(state=state) if state else None
    return app


# ---------------------------------------------------------------- A: the slips suggestion
q = sg.question(SLIP)
assert q[0] == ("9 wrong-finger presses on L stop at ~1.6 mm, real ones go to 3.3 mm.\n"
                "Set L's actuation to 2.2 mm so they don't type?"), q[0]
assert q[1] == ("yes", "no") and q[2] == 0 and q[3] == ("y", "n")
assert sg.question({"key": "L", "why": "slips"})[0] == \
    "Wrong-finger presses on L stop short of real ones.\nSet L's actuation deeper so they don't type?"
for presses, want in ((["y"], {"action": "accept", "key": "L"}),
                      ([keys.ENTER], {"action": "accept", "key": "L"}),
                      ([keys.RIGHT, keys.ENTER], {"action": "dismiss", "key": "L"}),
                      (["n"], {"action": "dismiss", "key": "L"})):
    app = new()
    f, seq, boxes = Fake(STATE), iter(presses), []
    with mock.patch("urllib.request.urlopen", f), \
            mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "set_overlay",
                              lambda o: boxes.append(strip("\n".join(o))) if o else None):
        sg.ask(app, lambda: None)
        ka.flush()
    assert f.sent == [want], (presses, f.sent)
    assert "9 wrong-finger presses on L stop at ~1.6 mm, real ones go to 3.3 mm." in boxes[0]
    assert "> yes" in boxes[0]
# esc: later
app = new()
with mock.patch("urllib.request.urlopen", Fake(STATE)) as f, \
        mock.patch.object(keys, "read_key", lambda *a, **k: keys.ESC), \
        mock.patch.object(console, "set_overlay", lambda o: None):
    assert sg.ask(app, lambda: None) == []
assert [x["key"] for x in sg.pending(app)] == ["L"]

# ---------------------------------------------------------------- A: the lines
lines = kl.pattern_text(PATTERNS)
assert lines[0].startswith("keyboard: L pressed by the wrong finger · K→L wrong finger 9x"), lines
assert lines[1] == "keyboard: L: suggested deeper against wrong-finger presses", lines
assert kl.guard_text({"why": "slips", "accepted": True}) == \
    "set deeper against wrong-finger presses (you said yes)"
assert kl.guard_text({"why": "slips", "dismissed": True}) == "wrong-finger fix dismissed (you said no)"
assert kl.guard_text({"why": "doubles", "accepted": True}) == "put in the bounce guard (you said yes)"
A = ka.Answer(state=STATE)
d = ks.detail(A, "L")
assert "hits 200 · misses 0 · ghosts 0 · doubles 0 · typos 1 (wrong key) · slips 9 (wrong finger)" in d, d
assert d[d.index("wrong finger: meant K, pressed L: 9x"):] == [
    "wrong finger: meant K, pressed L: 9x", "wrong finger: meant L, pressed K: 2x",
    "waiting for your answer: actuation to 2.20 mm against wrong-finger presses?",
    "changed: suggested deeper against wrong-finger presses"], d
assert "wrong finger: meant D, pressed F: 3x" in ks.detail(A, "F")
assert not any("wrong finger" in x for x in ks.detail(A, "J"))

# ---------------------------------------------------------------- B: the pairs
assert pd.pairs_from(PATTERNS) == [("k", "l", 11), ("d", "f", 3)], "fingers first, both ways counted"
assert pd.pairs_from({"pairs": PATTERNS["pairs"], "fingers": []}) == [("8", "9", 4)]
assert pd.pairs_from({"pairs": [{"expected": "Space", "typed": "n", "count": 3},
                                {"expected": "a", "typed": "a", "count": 2},
                                {"expected": "x", "typed": "c", "count": "2"}]}) == []
assert pd.pairs_from(None) == [] and pd.pairs_from({"fingers": "x"}) == []
many = {"fingers": [{"meant": c, "typed": d, "count": n} for c, d, n in
                    (("a", "s", 1), ("q", "w", 5), ("e", "r", 3), ("t", "y", 4))]}
assert [p[:2] for p in pd.pairs_from(many)] == [("q", "w"), ("t", "y"), ("e", "r")], "the top 3"
assert pd.label([("k", "l", 11), ("8", "9", 4)]) == "k↔l 8↔9"

# ---------------------------------------------------------------- B: the words
assert pd.closeness("milk", "k", "l") == 1 and pd.closeness("lake", "k", "l") == 2
assert pd.closeness("cat", "k", "l") is None
bank = ["milk", "lake", "kill", "black", "luck", "walk", "kelp", "lock", "look", "silk", "cat", "dog"]
p = pd.pool(bank, "k", "l")
assert "cat" not in p and p.count("milk") == 3 and p.count("lake") == 2
rng = random.Random(4)
for _ in range(50):
    r = pd.run("8", "9", rng)
    assert 2 <= len(r) <= 5 and set(r) == {"8", "9"}, r
w = pd.words(bank, [("k", "l", 11), ("8", "9", 4)], 200, random.Random(1))
assert len(w) == 200
assert all(("k" in x and "l" in x) or set(x) <= {"k", "l"} or set(x) == {"8", "9"} for x in w), w
assert sum(set(x) == {"8", "9"} for x in w) > 20, "digits come as runs"
assert sum(x in bank for x in w) > 80, "letters mostly as real words"
assert all(set(x) <= {"q", "z"} for x in pd.words(bank, [("q", "z", 1)], 20)), "no words: runs"
assert pd.words(bank, [], 10) == []

# ---------------------------------------------------------------- B: starting it
app = new(None)
f = Fake(STATE)
with mock.patch("urllib.request.urlopen", f):
    spec = kl.pairs_drill(app)
assert f.sent == [{"action": "status"}], "one status call as it starts"
assert spec.source == "pairs" and spec.kind == "words" and spec.amount == app.settings.word_amount
assert spec.words == (("k", "l", 11), ("d", "f", 3)) and spec.label == "mixed-up keys k↔l d↔f"
assert app.keyboard_pairs == [("k", "l", 11), ("d", "f", 3)]
saved = json.load(open(storage.path(storage.SETTINGS), encoding="utf-8"))
assert saved["keyboard_pairs"] == [["k", "l", 11], ["d", "f", 3]]
# offline: the pairs it saw last, from settings.json
app = App()
app.load()
assert app.keyboard_pairs == [("k", "l", 11), ("d", "f", 3)]
app.settings.keyboard_learn = True
with mock.patch("urllib.request.urlopen", Fake(ConnectionRefusedError())):
    spec = kl.pairs_drill(app)
assert spec.words == (("k", "l", 11), ("d", "f", 3))
# nothing seen yet: a notice, no test
app = new(None)
with mock.patch("urllib.request.urlopen", Fake(ConnectionRefusedError())):
    assert kl.pairs_drill(app) is None
assert app.notice == kl.NOTHING
app = new(None)
with mock.patch("urllib.request.urlopen", Fake(dict(STATE, patterns={}))):
    assert kl.pairs_drill(app) is None and app.notice == kl.NOTHING
# keyboard learn off: no call, the saved pairs
app = App()
app.keyboard_pairs = [("8", "9", 4)]
with mock.patch("urllib.request.urlopen", Fake(STATE)) as f:
    spec = kl.pairs_drill(app)
assert spec.words == (("8", "9", 4),)
# odd saved pairs are dropped
app = App()
with mock.patch.object(storage, "read_settings", lambda: {"keyboard_pairs": [
        ["k", "l", 3], ["kk", "l", 2], ["a", "b", 0], "x", ["a", "b"], [1, 2, 3]]}):
    app.load()
assert app.keyboard_pairs == [("k", "l", 3)]

# ---------------------------------------------------------------- B: the menu, the test
app = App()
assert "mixed-up keys" not in [it.label for it in mm.build_items(app)]
app.keyboard_pairs = [("k", "l", 3)]
item = next(it for it in mm.build_items(app) if it.label == "mixed-up keys")
assert item.key == "m" and item.section == "practice" and item.value() == "k↔l"
app = new(None)
assert "mixed-up keys" in [it.label for it in mm.build_items(app)]

app = new(None)
app.keyboard_pairs = [("k", "l", 11), ("8", "9", 4)]
with mock.patch("urllib.request.urlopen", Fake(ConnectionRefusedError())):
    spec = kl.pairs_drill(app)
t = TypingTest(app, spec)
assert len(t.words) == spec.amount
assert all(("k" in x and "l" in x) or set(x) <= {"k", "l", "8", "9"} for x in t.words), t.words
for i, ch in enumerate(t.words[0][:3]):
    t.handle(ch, 1000 + i)
assert [(e["expected"], e["typed"]) for e in t.keystrokes] == [(c, c) for c in t.words[0][:3]], \
    "a normal test: keystrokes recorded for the app"
print("ALL OK")
