"""A mistake is counted once: a wrong key counts when it is pressed, and a
wrong word only adds to the count when it had no wrong key in it."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.terminal import keys


def run(words, typed):
    """typed: a string, or a list where keys.BACKSPACE can appear."""
    app = App()
    t = TypingTest(app, TestSpec("c", "words", len(words), "custom", tuple(words)))
    assert t.stop == "off" and t.diff == "normal", (t.stop, t.diff)
    for ch in typed:
        t.handle(ch, 0.1)
    return t


# one wrong key, never fixed, then space: one mistake (used to be two)
t = run(["hello", "world"], "hellx world")
assert t.bad_keys == 1, t.bad_keys
# the last word of the test ends on its own: still one
t = run(["hello", "world"], "hello worlx")
assert t.bad_keys == 1, t.bad_keys
# a fixed typo is one mistake, as before
t = run(["hello", "world"], ["h", "e", "l", "l", "x", keys.BACKSPACE, "o", " ", "w", "o", "r", "l", "d"])
assert t.bad_keys == 1, t.bad_keys
# two wrong keys in a word are two
t = run(["hello", "world"], "hexxo world")
assert t.bad_keys == 2, t.bad_keys
# letters skipped: no wrong key was pressed, so the wrong word counts once
t = run(["hello", "world"], "hel world")
assert t.bad_keys == 1, t.bad_keys
# a clean run has none
t = run(["hello", "world"], "hello world")
assert t.bad_keys == 0, t.bad_keys
print("ALL OK")
