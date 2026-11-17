"""Tab restarts (a finished test: new words at 90%+ accuracy, else the same): with "tab: same words" on (the default), tab after typing something
gives the same words again, tab with nothing typed gives new ones; off, always new."""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"

from minitype.context import App                                 # noqa: E402
from minitype.engine.runner import TypingTest                    # noqa: E402
from minitype.engine.spec import TestSpec                        # noqa: E402
from minitype.terminal import keys                               # noqa: E402

app = App()
assert app.settings.tab_same is True, "on by default"
spec = TestSpec("25 words", "words", 25)


def press(t, text):
    now = time.time()
    for ch in text:
        now += 0.05
        t.handle(ch, now)


t = TypingTest(app, spec)
first = list(t.words)
nxt = t.handle(keys.TAB, time.time())
assert isinstance(nxt, TestSpec) and not nxt.replay, "nothing typed: new words"
press(t, first[0][:2])
again = t.handle(keys.TAB, time.time())
assert again.replay == tuple(first), "typed something: the same words"
t2 = TypingTest(app, again)
assert t2.words == first and t2.spec.label == spec.label
# and once more from the replay: still the same
press(t2, first[0])
assert TypingTest(app, t2.handle(keys.TAB, time.time())).words == first
# finished test: the results' tab spec carries the words
t3 = TypingTest(app, TestSpec("2 words", "words", 2, "custom", words=("ok", "go")))
press(t3, "ok go")
assert t3.result().spec.replay == (), "90%+ accuracy: new words next"
t5 = TypingTest(app, TestSpec("2 words", "words", 2, "custom", words=("ok", "go")))
press(t5, "oxk go")
assert t5.result().acc < 90 and t5.result().spec.replay == ("ok", "go"), "under 90%: the same again"
# off: always new
app.settings.tab_same = False
t4 = TypingTest(app, spec)
press(t4, t4.words[0][:2])
assert not t4.handle(keys.TAB, time.time()).replay
print("ALL OK")
