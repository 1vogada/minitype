"""Small things on the typing and results screens: the combo hides while you
race a ghost; the heatmap's key line shows each word in its colour; session
keys read "i - 3; b - 2"."""
import os
import re
import tempfile
import time

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from minitype.context import App                  # noqa: E402
from minitype.engine.runner import TypingTest     # noqa: E402
from minitype.engine.spec import TestSpec         # noqa: E402
from minitype.ui import results as rs             # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)

# ---------------------------------------------------------------- combo and the ghost
app = App()
app.settings.show_combo = True
t = TypingTest(app, TestSpec("10 words", "words", 10, "custom", ("aaaa",) * 10))
t.start, t.combo = time.time() - 2, 12
assert "x12" in t.status(time.time())[0], "the combo shows"
app.settings.ghost = True
assert "x12" in t.status(time.time())[0], "ghost on but nothing to race yet: still shows"
app.stats.ghost[:] = [(0.5, 3), (1.0, 6)]
assert "x12" not in t.status(time.time())[0], "racing a ghost: hidden"
app.settings.ghost = False
assert "x12" in t.status(time.time())[0]

# ---------------------------------------------------------------- the heatmap's key
st = app.styles()


class R:
    presses = {"a": 10, "s": 10, "d": 10}
    misses = {"s": 1 / 2, "d": 5}


lines = rs.heatmap_lines(app, st, R())
legend = lines[1]
assert strip(legend).strip() == "keys: clean, some misses, many misses"
assert (st.good or st.ok) + "clean" in legend and st.warn + "some misses" in legend \
    and st.bad + "many misses" in legend, "each word in the colour it stands for"

# ---------------------------------------------------------------- session keys
app.settings.res_session_keys = True
app.stats.errors.update({"i": 3, "b": 2})
app.stats.key_state.update({"i": "on", "b": "on"})


class R2:
    spec = TestSpec("10 words", "words", 10, "words")
    misses = {}


text = "\n".join(strip(l) for l in rs.detail_lines(app, st, R2()))
assert "session keys: i - 3; b - 2" in text, text
print("ALL OK")
