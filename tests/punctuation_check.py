"""The punctuation setting (off / on / forgive) and the 'apostrophes' switch
that replaced the two old apostrophe toggles."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.settings import Settings
from minitype.ui import settings_menu as sm


def run(words, typed, mode):
    app = App()
    app.settings.punctuation = mode
    t = TypingTest(app, TestSpec("c", "words", len(words), "custom", tuple(words)))
    for ch in typed:
        t.handle(ch, 0.1)
    return t


# forgive: every kind of punctuation can be left out
t = run(["hello,", "world"], "hello world", "forgive")
assert t.typed[0] == "hello," and t.bad_keys == 0, (t.typed, t.bad_keys)
t = run(['"hi"', "there"], "hi there", "forgive")
assert t.typed[0] == '"hi"' and t.bad_keys == 0, (t.typed, t.bad_keys)
t = run(["e.g.", "x"], "eg x", "forgive")
assert t.typed[0] == "e.g." and t.bad_keys == 0, (t.typed, t.bad_keys)
t = run(["can't", "x"], "cant x", "forgive")
assert t.typed[0] == "can't" and t.bad_keys == 0
# the last word of the test finishes without its trailing mark
t = run(["one", "end."], "one end", "forgive")
assert t.done and t.typed[1] == "end." and t.bad_keys == 0, (t.done, t.typed, t.bad_keys)
# typing the marks still works
t = run(["hello,", "world"], "hello, world", "forgive")
assert t.typed[0] == "hello," and t.bad_keys == 0
# a real mistake still counts
t = run(["hello,", "world"], "hellx world", "forgive")
assert t.bad_keys == 1, t.bad_keys
# on: marks are typed exactly, leaving one out is a mistake
t = run(["hello,", "world"], "hello world", "on")
assert t.bad_keys >= 1
t = run(["hello,", "world"], "hello, world", "on")
assert t.bad_keys == 0
# off: not forgiven either (custom text is left as it is)
t = run(["hello,", "world"], "hello world", "off")
assert t.bad_keys >= 1

# old saved settings become the new ones
s = Settings(); s.apply({"punctuation": True}); assert s.punctuation == "on"
s = Settings(); s.apply({"punctuation": False}); assert s.punctuation == "off"
s = Settings(); s.apply({"punctuation": False, "forgive_apostrophe": True}); assert s.punctuation == "forgive"
s = Settings(); s.apply({"punctuation": True, "forgive_apostrophe": True}); assert s.punctuation == "forgive"
s = Settings(); s.apply({"remove_apostrophe": True}); assert s.apostrophes is False
s = Settings(); s.apply({}); assert s.punctuation == "off" and s.apostrophes is True
s = Settings(); s.apply({"punctuation": "forgive", "apostrophes": False})
assert (s.punctuation, s.apostrophes) == ("forgive", False)
s = Settings(); s.apply({"punctuation": "nonsense"}); assert s.punctuation == "off"

# the settings rows: one punctuation row, one apostrophes row, no old ones
app = App()
labels = [it.label for it in sm.build_items(app)]
assert "punctuation" in labels and "apostrophes visible" in labels, labels
assert "forgive '" not in labels and "remove '" not in labels
row = next(it for it in sm.build_items(app) if it.label == "punctuation")
seen = [row.value()]
for _ in range(3):
    row.action(); seen.append(row.value())
assert seen == ["off", "on", "forgive", "off"], seen
print("ALL OK")
