import os, re, sys, tempfile, time, importlib, pkgutil
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
import minitype
for m in pkgutil.walk_packages(minitype.__path__, "minitype."):
    if not m.name.endswith("__main__"):
        importlib.import_module(m.name)
from minitype.terminal import console, keys
from minitype.context import App
from minitype.engine.runner import TypingTest, ZenTest, keyboard_lines
from minitype.engine.spec import TestSpec
from minitype.ui import main_menu as mm, settings_menu as sm, results as rs, learn_menu as lm, profile as pf, key_editor as ke
from minitype.ui.menu import Menu

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07", "", s)
SIZE = [80, 24]
frames = []


def fake_present(lines, focus=None, pinned=(), **kw):
    frames.append((list(lines), focus, list(pinned)))


console.size = lambda: tuple(SIZE)
real_present = console.present
console.present = fake_present


def feed(seq):
    it = iter(seq)
    return mock.patch.object(keys, "read_key", lambda panic=True, resize=True: next(it))


def typ(t, s):
    for ch in s:
        t.handle(ch, time.time())


def last_text():
    l, f, p = frames[-1]
    return strip("\n".join(l + p))


app = App()
app.load_words("built-in")

# ---- present: clipping to tiny terminals, focus scrolling
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    SIZE[:] = [20, 5]
    real_present(["x" * 50, "a", "b", "c", "d", "e", "f", "g"], focus=6)
    rows = strip(out[-1]).split("\n")
    assert len(rows) == 5 and all(len(r) <= 19 for r in rows), rows
    assert "f" in rows, rows
    SIZE[:] = [80, 24]
# ---- read_key reports resizes
with mock.patch.object(keys, "key_ready", lambda: False), \
        mock.patch.object(keys.time, "sleep", lambda x: SIZE.__setitem__(0, 70)):
    assert keys.read_key() == keys.RESIZE
SIZE[:] = [80, 24]

# ---- every mode builds and finishes
for spec in [TestSpec("q", "words", 0, "quote"), TestSpec("c", "words", 0, "code"),
             TestSpec("n", "words", 5, "numbers"), TestSpec("w", "words", 5)]:
    t = TypingTest(app, spec)
    assert t.words, spec
    for w in list(t.words):
        typ(t, w)
        if not t.finished(time.time()):
            typ(t, " ")
    assert t.finished(time.time()), spec
    r = t.result()
    assert r.acc == 100 and not r.failed, (spec, r.acc)
print("quote:", TypingTest(app, TestSpec("q", "words", 0, "quote")).note)
# zen
z = ZenTest(app, TestSpec("zen", "zen", 0, "zen"))
typ(z, "hello wrld")
z.handle(keys.BACKSPACE, 0); z.handle(keys.BACKSPACE, 0); z.handle(keys.BACKSPACE, 0)
typ(z, "orld")
assert z.words == ["hello", "world"] and not z.finished(0), z.words
z.handle(keys.ENTER, 0)
assert z.finished(0)
r = z.result()
assert r.acc == 100 and r.wpm > 0
# slow words drill after timing words
assert app.stats.word_speed, "word timings recorded"
t = TypingTest(app, TestSpec("slow", "words", 10, "slow"))
assert set(t.words) <= set(app.stats.slowest(20))

# ---- backspace modes
app.settings.backspace = "off"
t = TypingTest(app, TestSpec("c", "words", 2, "custom", ("ab", "cd"))); typ(t, "ax")
t.handle(keys.BACKSPACE, 0); assert t.typed[0] == "ax"
app.settings.backspace = "freedom"
t = TypingTest(app, TestSpec("c", "words", 2, "custom", ("ab", "cd"))); typ(t, "ab ")
t.handle(keys.BACKSPACE, 0); assert t.wi == 0
app.settings.backspace = "normal"
t = TypingTest(app, TestSpec("c", "words", 2, "custom", ("ab", "cd"))); typ(t, "ab ")
t.handle(keys.BACKSPACE, 0); assert t.wi == 1

# ---- min speed / accuracy
app.settings.min_acc = 90
t = TypingTest(app, TestSpec("c", "words", 3, "custom", ("aaa", "bbb", "ccc"))); typ(t, "xxx")
t.start -= 5; t.check_rules(time.time()); assert t.failed and "accuracy" in t.fail_reason
app.settings.min_acc = 0
app.settings.min_wpm = 120
t = TypingTest(app, TestSpec("c", "words", 3, "custom", ("aaa", "bbb", "ccc"))); typ(t, "a")
t.start -= 10; t.check_rules(time.time()); assert t.failed and "wpm" in t.fail_reason
r = t.result(); assert r.failed
app.settings.min_wpm = 0

# ---- funbox
app.settings.funbox = "reversed"
assert TypingTest(app, TestSpec("c", "words", 2, "custom", ("abc", "def"))).words[0] == "cba"
app.settings.funbox = "caps"
assert TypingTest(app, TestSpec("c", "words", 2, "custom", ("abc", "def"))).words[0] == "ABC"
app.settings.funbox = "random case"
assert TypingTest(app, TestSpec("c", "words", 1, "custom", ("abcdefghij",))).words[0].lower() == "abcdefghij"
app.settings.funbox = "off"


# ---- rendering: tape, mirror, memory, lowkey, header toggles, hints
def render(t, now=None):
    from minitype.engine.render import draw
    now = now or time.time()
    head, marks = t.status(now)
    draw(app.styles(), app.settings, head, t.words, t.typed, t.wi, 76, t.footer(), marks,
         t.wrong, keyboard_lines(app, t), t.hidden(now))
    return last_text()


words = tuple(("alpha beta gamma delta " * 20).split())
t = TypingTest(app, TestSpec("c", "words", len(words), "custom", words)); typ(t, "alpha beta ga")
txt = render(t); assert "esc menu" in txt and "wpm" in txt, txt
app.settings.tape = True
txt = render(t)
line = [l for l in txt.split("\n") if "gamma" in l]
assert len(line) == 1 and len(line[0]) <= 80, line
app.settings.tape = False
app.settings.funbox = "mirror"; txt = render(t); assert "ammag" in txt; app.settings.funbox = "off"
app.settings.memory = 2; t.start -= 5; txt = render(t)
assert "delta" not in txt and "___" in txt, txt
app.settings.memory = 0
app.settings.show_wpm = app.settings.show_timer = app.settings.show_progress = False
txt = render(t); assert "wpm" not in txt.split("\n")[0] and "left" not in txt
app.settings.show_wpm = app.settings.show_timer = app.settings.show_progress = True
app.settings.lowkey = "minimal"; txt = render(t); assert "esc menu" not in txt
t.handle(keys.UP, 0); txt = render(t); assert "esc menu" in txt, "hints pop back on an unused key"
typ(t, "m"); assert "esc menu" not in render(t)
app.settings.lowkey = "disguised"; txt = render(t)
assert txt.split("\n")[0].endswith(">") and "\x1b[3" not in "".join(frames[-1][0]), txt
app.settings.lowkey = "off"
app.settings.hints = False; assert "esc menu" not in render(t)
app.settings.hints = True

# ---- results with chart, heatmap and PB
t = TypingTest(app, TestSpec("15 words", "words", 3, "custom", ("the", "cat", "sat")))
typ(t, "the "); time.sleep(0.05); typ(t, "cxt "); time.sleep(0.05); typ(t, "sat"); t.start -= 3
r = t.result()
with feed([keys.RIGHT, keys.ENTER]):
    assert rs.show_results(app, r) == "menu"
txt = last_text(); print(txt)
assert "speed" in txt and "q w e r t" in txt and "personal best" in txt
for f in ("res_chart", "res_heatmap", "res_pb", "res_worst_keys", "res_session_keys",
          "res_bad_words", "res_history"):
    setattr(app.settings, f, False)
with feed([keys.ESC]):
    rs.show_results(app, r)
txt = last_text()
assert "speed" not in txt and "q w e" not in txt and "worst" not in txt and "session" not in txt, txt
for f in ("res_chart", "res_heatmap", "res_pb"):
    setattr(app.settings, f, True)
# second, faster run -> new PB
t = TypingTest(app, TestSpec("15 words", "words", 1, "custom", ("go",))); typ(t, "go")
t.start = time.time() - 0.01
r2 = t.result()
assert r2.wpm > r2.pb_before > 0 and app.history.pbs["15 words"]["wpm"] == round(r2.wpm, 1)
with feed([keys.ESC]):
    rs.show_results(app, r2)
assert "new personal best" in last_text()

# ---- menus in every style, at every size
for style in ("list", "sidebar", "tabs"):
    app.settings.ui_style = style
    for w in (100, 40, 20):
        SIZE[:] = [w, 30]
        with feed([keys.DOWN, keys.ESC]):
            assert mm.main_menu(app) == "quit"
        with feed([keys.DOWN, keys.RIGHT, keys.ESC]):
            sm.settings_menu(app)
        with feed([keys.ESC]):
            lm.learn_menu(app)
    SIZE[:] = [100, 30]
    with feed([keys.ESC]):
        sm.settings_menu(app)
    print(f"--- {style} ---")
    print(last_text())
SIZE[:] = [80, 24]
app.settings.ui_style = "tabs"
menu = Menu(sm.build_items(app), {}, "s", style="tabs")
assert menu.selected.section == "rules"
menu.handle("]"); assert menu.selected.section == "challenges"
for _ in range(10):
    menu.handle(keys.DOWN)
assert menu.selected.section == "challenges"
menu.handle(keys.PGUP); assert menu.selected.section == "rules"
app.settings.ui_style = "list"
# main menu: right changes time, enter starts it; hotkeys start modes
app.cursors.clear()
with feed([keys.RIGHT, keys.ENTER]):
    spec = mm.main_menu(app)
assert spec.kind == "time" and spec.amount == 60, spec
with feed(["3"]):
    assert mm.main_menu(app).source == "quote"
with feed(["4"]):
    assert mm.main_menu(app).kind == "zen"
with feed(["5"]):
    assert mm.main_menu(app).source == "code"
# hints off; an unused key pops them back
app.settings.hints = False
with feed(["%", keys.ESC]):
    mm.main_menu(app)
assert "arrows move" in strip("\n".join(frames[-1][2])), frames[-1][2]
with feed([keys.ESC]):
    mm.main_menu(app)
assert "arrows move" not in last_text()
app.settings.hints = True
# every settings row steps both ways
for it in sm.build_items(app):
    if it.label in ("word list", "edit keys", "save to disk", "reset", "book filter",
                    "theme creator"):
        continue
    before = it.value()
    it.action(); it.back()
    assert it.value() == before, it.label
# themes all render
for th in ("default", "ocean", "forest", "sunset", "mono"):
    app.settings.theme = th
    with feed([keys.ESC]):
        mm.main_menu(app)
app.settings.theme = "default"
with feed([keys.DOWN, keys.ESC]):
    pf.profile_screen(app)
print(last_text())
with feed([keys.RIGHT, keys.ENTER, "z", keys.TAB, keys.ESC]):
    ke.key_editor(app)
for name in ("programming", "left hand", "right hand", "home row"):
    assert app.load_words(name) and len(app.bank.words) > 40, (name, len(app.bank.words))
    print(name, len(app.bank.words))

# ---- saving roundtrip
app.toggle_saving(); app.settings.theme = "ocean"; app.save()
b = App(); b.load()
assert b.settings.theme == "ocean" and b.history.pbs == app.history.pbs and b.stats.word_speed
b.settings.apply({"quiet": True}); assert b.settings.theme == "mono"
print("ALL OK")
