import json, os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.settings import Settings
from minitype.engine.runner import TypingTest
from minitype.engine.render import Painter, rows
from minitype.engine.spec import TestSpec
from minitype.terminal import style
from minitype.ui import settings_menu as sm

strip = lambda s: re.sub(r"\x1b\[[0-9;]*m", "", s)
SPEC = TestSpec("c", "words", 2, "custom", ("cat", "dog"))


def run(keys_, **settings):
    app = App()
    for k, v in settings.items():
        setattr(app.settings, k, v)
    t = TypingTest(app, SPEC)
    for ch in keys_:
        t.handle(ch, time.time())
    return app, t


def screen(app, t):
    st = app.styles()
    p = Painter(st, app.settings, t.words, t.typed, t.wi, (), t.wrong, False,
                t.error_marks(), t.combo, time.time(), t.typo_keys)
    return p, rows(p, p.span(0, len(t.words))), st


# ---------------------------------------------------------------- corrected letters
# a fixed letter is NOT the same red as a live mistake (the default)
app, t = run("cx\x08a" .replace("\x08", ""))         # stop off: x lands
from minitype.terminal import keys
app, t = run("cx")
t.handle(keys.BACKSPACE, 0)
for ch in "at d":
    t.handle(ch, time.time())
p, r, st = screen(app, t)
cells = p.word(0)
assert app.settings.corrected == "marked"
assert cells[1][0] == st.warn != st.bad, "fixed: warn colour, not red"
# a live mistake next to it stays red
t.handle("x", time.time())
p, r, st = screen(app, t)
assert p.word(1)[1][0] == st.bad
# normal / red
for mode, want in (("normal", lambda st: st.typed(1, 0)), ("red", lambda st: st.bad)):
    app.settings.corrected = mode
    p, r, st = screen(app, t)
    assert p.word(0)[1][0] == want(st), mode
# mono has no colour: marked fixed letters are italic instead
app.settings.corrected, app.settings.theme = "marked", "mono"
p, r, st = screen(app, t)
assert p.word(0)[1][0] == style.ITALIC and st.bad != style.ITALIC
app.settings.theme = "default"
# blind mode gives no feedback at all
app.settings.blind = True
p, r, st = screen(app, t)
assert p.word(0)[1][0] == st.ok and len(r) == 1
app.settings.blind = False

# ---------------------------------------------------------------- indicate typos
app, t = run("cx")                 # the "a" of cat is wrong, "x" was pressed
for mode, line, under in (("off", "cat dog", None),
                          ("below", "cat dog", " x     "),
                          ("replace", "cxt dog", None),
                          ("both", "cxt dog", " a     ")):
    app.settings.typos = mode
    p, r, st = screen(app, t)
    assert strip(r[0]) == line, (mode, strip(r[0]))
    if under is None:
        assert len(r) == 1, mode
    else:
        assert strip(r[1]) == under, (mode, strip(r[1]))
        colour = st.bad if mode == "below" else st.dim
        assert colour + ("x" if mode == "below" else "a") in r[1]
# stop on error letter: the turned-away key shows under the caret until fixed
app, t = run("cx", stop_on_error="letter", typos="below")
p, r, st = screen(app, t)
assert strip(r[0]) == "cat dog" and strip(r[1]) == " x     "
t.handle("a", time.time())
p, r, st = screen(app, t)
assert strip(r[1]).strip() == "", "gone once the right key comes"
# a wrong space in letter mode shows as _
app, t = run("c ", stop_on_error="letter", typos="below")
p, r, st = screen(app, t)
assert strip(r[1]) == " _     "
# typos row and bounce together: three rows, nothing lost
app, t = run("cx", typos="below", fun_bounce="wild")
p, r, st = screen(app, t)
assert len(r) == 3 and strip(r[2]) == " x     "
# the block layout reserves the extra row for every line
from minitype.engine.render import block_lines, rows_per_line
assert rows_per_line(p) == 3 and len(block_lines(p, 60)) == 9

# ---------------------------------------------------------------- settings
s = Settings(); s.apply({"keep_errors": True}); assert s.corrected == "marked"
s = Settings(); s.apply({"keep_errors": True, "corrected": "red"}); assert s.corrected == "red"
s = Settings(); s.apply({"typos": "sideways"}); assert s.typos == "off"
rows_ = {it.label: it for it in sm.build_items(App())}
assert rows_["corrected letters"].section == "rules" and rows_["corrected letters"].preview
assert rows_["indicate typos"].value() == "off" and rows_["indicate typos"].preview
# the preview shows a fixed and a live mistake
app = App()
app.settings.typos = "below"
r = sm.theme_sample(app)
assert strip(r[0]) == "the quick brown fox jumps" and strip(r[1]).strip() == "i"
# your settings.json (read only) comes over as marked
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
with open(SETTINGS_FILE if os.path.exists(SETTINGS_FILE) else os.devnull, encoding="utf-8") as f:
    mine = json.load(f) if os.path.exists(SETTINGS_FILE) else {}
s = Settings(); s.apply(mine)
print("your corrected letters ->", s.corrected, "| indicate typos ->", s.typos)
print("ALL OK")
