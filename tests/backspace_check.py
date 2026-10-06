import itertools, os, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.engine.render import Painter
from minitype.terminal import keys

SPEC = TestSpec("c", "words", 3, "custom", ("cat", "dog", "owl"))


def test(**settings):
    app = App()
    for k, v in settings.items():
        setattr(app.settings, k, v)
    return app, TypingTest(app, SPEC)


def typ(t, s):
    for ch in s:
        t.handle(ch, time.time())


# every combination: backspace does what the backspace setting says, and
# keep errors never changes it
for bs, keep, stop in itertools.product(("normal", "off", "freedom"), (False, True),
                                        ("off", "letter", "word")):
    app, t = test(backspace=bs, corrected="red" if keep else "normal", stop_on_error=stop)
    typ(t, "ca")
    t.handle(keys.BACKSPACE, 0)
    want = "ca" if bs == "off" else "c"
    assert t.typed[0] == want, (bs, keep, stop, t.typed[0])
    t2 = TypingTest(app, SPEC)
    typ(t2, "ca")
    t2.handle(keys.CTRL_BACKSPACE, 0)
    assert t2.typed[0] == ("ca" if bs == "off" else ""), (bs, keep, stop, "ctrl")
print("matrix ok")

# corrected letters "red": fixing a letter leaves it red
app, t = test(corrected="red")
typ(t, "cx")
t.handle(keys.BACKSPACE, 0)
typ(t, "a")
assert t.typed[0] == "ca"
st = app.styles()
cells = Painter(st, app.settings, t.words, t.typed, t.wi, (), False, False,
                t.error_marks()).word(0)
assert cells[1] == (st.bad, "a", 1), "the fixed letter is still red"
# corrected letters "normal": it goes back to normal
app, t = test(corrected="normal")
typ(t, "cx"); t.handle(keys.BACKSPACE, 0); typ(t, "a")
st = app.styles()
cells = Painter(st, app.settings, t.words, t.typed, t.wi, (), False, False,
                t.error_marks()).word(0)
assert cells[1][0] != st.bad

# stop on error: word never gets you stuck
for bs, diff in (("off", "normal"), ("normal", "expert"), ("freedom", "expert"),
                 ("off", "expert")):
    app, t = test(stop_on_error="word", backspace=bs, difficulty=diff)
    typ(t, "cx ")
    assert t.wi == 0, "can't leave the wrong word"
    t.handle(keys.BACKSPACE, 0)
    assert t.typed[0] == "c", (bs, diff, "backspace works inside the wrong word")
    typ(t, "at ")
    assert t.wi == 1 and not t.failed, (bs, diff)
    # once the word is right again, the normal rules are back
    typ(t, "do")
    t.handle(keys.BACKSPACE, 0)
    assert t.typed[1] == ("do" if bs == "off" or diff != "normal" else "d"), (bs, diff)
# extra letters past the end count as wrong too
app, t = test(stop_on_error="word", backspace="off")
typ(t, "catt ")
assert t.wi == 0
t.handle(keys.BACKSPACE, 0)
assert t.typed[0] == "cat"
typ(t, " ")
assert t.wi == 1
# but the exception never reaches back into the previous word
app, t = test(stop_on_error="word", backspace="off")
typ(t, "cat x")
t.handle(keys.BACKSPACE, 0); t.handle(keys.BACKSPACE, 0)
assert t.wi == 1 and t.typed[0] == "cat" and t.typed[1] == ""
# expert without stop on error: still no backspace (a wrong word just fails)
app, t = test(difficulty="expert")
typ(t, "cx")
t.handle(keys.BACKSPACE, 0)
assert t.typed[0] == "cx"

# the backspace setting's row says what it does
from minitype.ui import settings_menu as sm
rows = {it.label: it for it in sm.build_items(App())}
assert "can't get stuck" in rows["backspace"].help_text()
assert "keep errors" not in rows and "corrected letters" in rows
print("ALL OK")
