"""The hacker funbox: any key finishes the word you're on, and a hacker
run isn't kept as a best or in the stats."""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from minitype.config import FUNBOXES                             # noqa: E402
from minitype.context import App                                 # noqa: E402
from minitype.engine.runner import TypingTest, ZenTest           # noqa: E402
from minitype.engine.spec import TestSpec                        # noqa: E402
from minitype.terminal import keys                               # noqa: E402
from minitype.ui import results                                  # noqa: E402

assert "hacker" in FUNBOXES
app = App()
app.settings.funbox = "hacker"
spec = TestSpec("w", "words", 3, "custom", words=("alpha", "beta", "gamma"))
t = TypingTest(app, spec)
assert t.words == ["alpha", "beta", "gamma"], "the words themselves don't change"
t.handle("x", time.time())
assert t.wi == 1 and t.typed[0] == "alpha", "one key, one word"
t.handle(" ", time.time())
assert t.wi == 2 and t.typed[1] == "beta", "space too"
assert t.keys == 11 and t.bad_keys == 0 and t.combo == 11, (t.keys, t.combo)
assert "hacker" in t.status(time.time())[0], "the header says so"
t.handle("q", time.time())
assert t.finished(time.time()) and t.typed[2] == "gamma"
runs, pbs = len(app.history.runs), dict(app.history.pbs)
r = t.result()
assert r.acc == 100 and not r.counted and r.wpm > 0
assert len(app.history.runs) == runs and app.history.pbs == pbs, "not kept"
assert "not kept" in " ".join(results.pb_lines(app, app.styles(), r))
# half a word typed: the key finishes the rest of it
t2 = TypingTest(app, TestSpec("w", "words", 2, "custom", words=("hello", "you")))
app.settings.funbox = "off"
t2.handle("h", time.time())
t2.handle("e", time.time())
app.settings.funbox = "hacker"
t2.handle("z", time.time())
assert t2.typed[0] == "hello" and t2.wi == 1
# a time test keeps going; zen isn't touched
tt = TypingTest(app, TestSpec("t", "time", 15, "words"))
for _ in range(30):
    tt.handle("k", time.time())
    tt.top_up()
assert tt.wi == 30 and all(tt.typed[i] == tt.words[i] for i in range(30))
z = ZenTest(app, TestSpec("zen", "zen", 0, "zen"))
z.handle("a", time.time())
assert z.words == ["a"], z.words
# off again: normal typing, and a run counts
app.settings.funbox = "off"
t3 = TypingTest(app, TestSpec("w", "words", 1, "custom", words=("ok",)))
for ch in "ok":
    t3.handle(ch, time.time())
assert t3.result().counted and len(app.history.runs) == runs + 1
assert keys.is_char("x")
print("ALL OK")
