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
# every theme's heatmap colours tell apart (a grey theme gets green, amber, red)
from minitype.terminal import style as _style                  # noqa: E402
for _t in _style.theme_names():
    _rgbs = [_style.rgb_of_code(c) for c in rs.heat_colours(_style.Styles(_t))]
    assert all(sum((a - b) ** 2 for a, b in zip(x, y)) ** 0.5 >= rs.HEAT_APART
               for i, x in enumerate(_rgbs) for y in _rgbs[i + 1:]), (_t, _rgbs)

# ---------------------------------------------------------------- a new install
from minitype.settings import SETUPS, Settings                  # noqa: E402
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()               # nothing saved yet
fresh = App()
fresh.load()
assert fresh.first_run, "nothing saved: the welcome screen comes up"
for _k, _v in SETUPS["clean"].items():   # until it does, the first setup
    assert getattr(fresh.settings, _k) == _v, (_k, getattr(fresh.settings, _k), _v)
os.environ["MINITYPE_FACTORY"] = "1"                          # the baseline instead
base = App()
base.load()
assert base.settings.theme == Settings().theme and base.settings.art == Settings().art
assert not base.first_run, "no welcome screen for the factory baseline"
del os.environ["MINITYPE_FACTORY"]
print("ALL OK")
