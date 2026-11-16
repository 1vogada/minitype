"""Best words: a test from the words you type fastest and cleanest. Needs
enough history (each word typed 5+ times, 90%+ clean, timed 3+ times; 20
best words at least), falls back to the normal word test before that, and
its runs are kept apart: their own mode and profile rows, out of the normal
speed / accuracy figures, the per-key and per-word stats, the session list
and learn as you type."""

import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"

from minitype import storage                                     # noqa: E402
from minitype.context import App                                 # noqa: E402
from minitype.engine.runner import TypingTest                    # noqa: E402
from minitype.engine.spec import TestSpec                        # noqa: E402
from minitype.terminal import console, keys                      # noqa: E402
from minitype.ui import main_menu, profile, results              # noqa: E402
from minitype.words import best_words as bw                      # noqa: E402

console.term_size = lambda: (100, 40)
console._last_size = (100, 40)
WORDS = [f"w{chr(97 + i // 26)}{chr(97 + i % 26)}" for i in range(60)]   # "waa", "wab", ...
WORDS = ["".join(c for c in w if c.isalpha()) for w in WORDS]


def typed(t, text, dt=0.05):
    now = time.time()
    for ch in text:
        now += dt
        t.handle(keys.BACKSPACE if ch == "" else ch, now)


# ---------------------------------------------------------------- the stats it reads
app = App()
st = app.stats
st.word_done("Hello,", True)
st.word_done("hello", False)
st.word_done("a", True)                       # too short: not kept, as word_speed
assert st.word_clean == {"hello": [1, 2]}, st.word_clean

# a normal test records clean / not clean per word
t = TypingTest(app, TestSpec("w", "words", 3, "custom", words=("alpha", "beta", "gamma")))
typed(t, "alpha bxta gamma")
assert st.word_clean["alpha"] == [1, 1] and st.word_clean["beta"] == [0, 1] and st.word_clean["gamma"] == [1, 1]
t = TypingTest(app, TestSpec("w", "words", 1, "custom", words=("alpha",)))
typed(t, "alx\bpha")                          # a wrong key, fixed: right, but not clean
assert st.word_clean["alpha"] == [1, 2], st.word_clean["alpha"]

# ---------------------------------------------------------------- too little history
app = App()
st = app.stats
assert bw.pool(st) == [] and bw.progress(st) == (0, bw.MIN_POOL)
items = {it.key: it for it in main_menu.build_items(app)}
assert items["w"].label == "best words"
spec = items["w"].action()
assert spec.source == "words" and spec.label == f"{app.settings.word_amount} words", spec
assert "needs more history (0/20" in app.notice and "normal word test" in app.notice

# 60 words with history; the fast half clean, a few not clean or too new
rng = random.Random(1)
for i, w in enumerate(WORDS):
    st.word_speed[w] = [100.0 + i * 5, 6]     # waa fastest
    st.word_clean[w] = [6, 6]
st.word_clean[WORDS[0]] = [4, 6]              # fastest, but 67% clean: out
st.word_clean[WORDS[1]] = [4, 4]              # typed only 4 times: out
st.word_speed[WORDS[2]] = [100.0, 2]          # timed only twice: out
pool = bw.pool(st)
assert len(pool) == (len(WORDS) - 3) // 2 == 28, len(pool)
assert pool[0] == WORDS[3] and WORDS[0] not in pool and WORDS[1] not in pool and WORDS[2] not in pool
assert all(st.word_speed[a][0] <= st.word_speed[b][0] for a, b in zip(pool, pool[1:])), "fastest first"
assert WORDS[-1] not in pool, "the slow half isn't"
drawn = bw.words(st, 40, rng)
assert len(drawn) == 40 and set(drawn) <= set(pool)
assert all(a != b for a, b in zip(drawn, drawn[1:])), "no word twice in a row"
# just under the line: falls back
st2 = App().stats
for i, w in enumerate(WORDS[:39]):
    st2.word_speed[w], st2.word_clean[w] = [100.0 + i, 5], [5, 5]
assert bw.pool(st2) == [] and bw.progress(st2) == (19, 20)
st2.word_speed["zz"], st2.word_clean["zz"] = [500.0, 5], [5, 5]
assert len(bw.pool(st2)) == 20

# ---------------------------------------------------------------- a best-words run is kept apart
app.settings.keyboard_learn = True
spec = {it.key: it for it in main_menu.build_items(app)}["w"].action()
assert spec == TestSpec("best words", "words", app.settings.word_amount, "best"), spec
t = TypingTest(app, TestSpec("best words", "words", 3, "best"))
assert set(t.words) <= set(pool), t.words
assert t.keystrokes is None, "nothing for learn as you type"
before = (dict(st.errors), dict(st.missed), {w: list(v) for w, v in st.word_speed.items()},
          {w: list(v) for w, v in st.word_clean.items()}, list(st.history), list(st.ghost))
w0, w1, w2 = t.words
typed(t, w0 + " " + "q" + w1[1:] + " " + w2)          # one wrong key, one wrong word
r = t.result()
assert r.counted and r.errors == 1
after = (st.errors, st.missed, st.word_speed, st.word_clean, st.history, st.ghost)
assert after == before, "no per-key, per-word or session stats from it"
h = app.history
assert h.runs[-1]["mode"] == "best words" and h.runs[-1]["tag"] == "best", h.runs[-1]
assert "best words" in h.pbs, "its own personal best"
assert h.normal() == [], "not in the normal runs"
lines = " ".join(results.pb_lines(app, app.styles(), r))
assert "kept apart from your normal stats" in lines and "personal best" in lines, lines

# a normal run next to it: the profile's normal figures are the normal run's only
t = TypingTest(app, TestSpec("2 words", "words", 2, "custom", words=("ok", "go")))
typed(t, "ok go", dt=0.2)
normal = t.result()
assert len(h.runs) == 2 and h.normal() == [h.runs[-1]]
strip = lambda s: __import__("re").sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
text = strip("\n".join(profile.draw(app, app.styles())))
assert f"{normal.wpm:.0f} wpm (last 10)" in text, text
assert "tests       1" in text, text
assert "best words  1 test, top" in text and f"{h.speed(h.runs[0]):.0f} wpm" in text, text
assert bw.summary(h)[0] == 1
# a run from before tags (or any other) still counts as normal
h.apply([{"t": 1, "mode": "30 seconds", "wpm": 50, "acc": 95, "secs": 30, "failed": False}])
assert len(h.normal()) == 1 and bw.summary(h) is None

# ---------------------------------------------------------------- saved and loaded
storage.toggle(app.to_dict())                     # saving on
app.stats.word_clean["saved"] = [5, 6]
app.save()
back = App()
back.load()
assert back.stats.word_clean["saved"] == [5, 6]
assert back.stats.word_clean == app.stats.word_clean
d = storage.read()
d["word_clean"] = {"bad": [7, 3], "neg": [-1, 2], "odd": "x", "ok": [1, 2]}
storage.write(d)
again = App()
again.load()
assert again.stats.word_clean == {"ok": [1, 2]}, again.stats.word_clean
print("ALL OK")
