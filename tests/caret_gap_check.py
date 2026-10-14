import json, os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.settings import Settings
from minitype.engine.render import Painter, tape_line, SPACE_DOT
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.terminal.style import INV, UND

app = App()
st = app.styles()
s = app.settings
assert s.caret == "underline" and s.word_gap == "blank", "new defaults"
spec = TestSpec("c", "words", 3, "custom", ("cat", "dog", "owl"))


def paint(t, wrong=None):
    return Painter(st, s, t.words, t.typed, t.wi, (), t.wrong if wrong is None else wrong,
                   False, t.error_marks())


t = TypingTest(app, spec)
for ch in "ca":
    t.handle(ch, time.time())
cells = paint(t).word(0)
# the letter to type: underlined, in the untyped colour - not bright, not inverted
assert cells[2] == (st.dim + UND, "t", 2), cells[2]
assert INV not in cells[2][0] and st.ok not in cells[2][0]
# typed letters stay bright, letters further on stay dim
assert cells[0][0] == st.ok and paint(t).word(1)[0][0] == st.dim
# a wrong key (stop on error): the underline turns red, still no inverse
cells = paint(t, wrong=True).word(0)
assert cells[2][0] == st.bad + UND
# at the end of a word the caret sits on the space: a bright underline
t.handle("t", time.time())
gap = paint(t).gap(0)
assert gap == (st.title + UND, " ", 3), gap
# block caret: inverted letter, red inverted after a wrong key
s.caret = "block"
t2 = TypingTest(app, spec)
t2.handle("c", time.time())
assert paint(t2).word(0)[1][0] == INV
assert paint(t2, wrong=True).word(0)[1][0] == st.bad + INV
s.caret = "underline"

# word gaps between words that aren't the caret
t3 = TypingTest(app, spec)
s.word_gap = "blank";     assert paint(t3).gap(1) == ("", " ", 7)
s.word_gap = "dots";      assert paint(t3).gap(1) == (st.dim, SPACE_DOT, 7)
s.word_gap = "underline"; assert paint(t3).gap(1) == (st.dim + UND, " ", 7)

# tape mode finds the caret by position even when gaps are underlined too
s.tape = True
words = tuple(("alpha beta gamma " * 30).split())
t4 = TypingTest(app, TestSpec("c", "words", len(words), "custom", words))
for w in words[:40]:
    for ch in w:
        t4.handle(ch, time.time())
    t4.handle(" ", time.time())
line = tape_line(paint(t4), 60)[0]          # one row (two with bounce)
plain = re.sub(r"\x1b\[[0-9;]*m", "", line)
caret_pos = plain.index(words[40][0]) if False else None
# the caret letter (dim+underline) is about a third of the way in, not at the start
first_ul = line.find(st.dim + UND + words[40][0])
before = re.sub(r"\x1b\[[0-9;]*m", "", line[:first_ul])
assert 15 <= len(before) <= 25, (len(before), plain)
s.tape = False
s.word_gap = "blank"

# 'from middle' mode: starts pre-padded at the middle and scrolls continuously
s.tape = "from middle"
t_mid = TypingTest(app, TestSpec("c", "words", len(words), "custom", words))
line_mid0 = tape_line(paint(t_mid), 60, mode="from middle")[0]
plain_mid0 = re.sub(r"\x1b\[[0-9;]*m", "", line_mid0)
# starts with exactly 30 padding spaces, so the first letter is at column 30
assert plain_mid0.startswith(" " * 30), repr(plain_mid0[:35])
assert plain_mid0[30] == words[0][0], f"expected '{words[0][0]}' at 30, got '{plain_mid0[30]}'"

# after typing 1 letter, it scrolls left instantly (29 padding spaces)
t_mid.handle(words[0][0], time.time())
line_mid1 = tape_line(paint(t_mid), 60, mode="from middle")[0]
plain_mid1 = re.sub(r"\x1b\[[0-9;]*m", "", line_mid1)
assert plain_mid1.startswith(" " * 29), repr(plain_mid1[:35])
assert plain_mid1[29] == words[0][0] and plain_mid1[30] == words[0][1]

# across subsequent keystrokes, caret stays locked at column 30
for ch in words[0][1:]:
    t_mid.handle(ch, time.time())
t_mid.handle(" ", time.time())
for ch in words[1]:
    t_mid.handle(ch, time.time())
line_mid_later = tape_line(paint(t_mid), 60, mode="from middle")[0]
first_ul_mid = line_mid_later.find(UND)
before_mid = re.sub(r"\x1b\[[0-9;]*m", "", line_mid_later[:first_ul_mid])
assert len(before_mid) == 30, (len(before_mid), line_mid_later)
s.tape = "off"

# old settings carry over: boolean tape -> on/off
n = Settings(); n.apply({"tape": True}); assert n.tape == "on"
n = Settings(); n.apply({"tape": False}); assert n.tape == "off"
n = Settings(); n.apply({"tape": "from middle"}); assert n.tape == "from middle"

# old settings carry over: show spaces on -> dots
n = Settings(); n.apply({"show_spaces": True}); assert n.word_gap == "dots"
n = Settings(); n.apply({"show_spaces": True, "word_gap": "underline"}); assert n.word_gap == "underline"
n = Settings(); n.apply({"show_spaces": False}); assert n.word_gap == "blank"
n = Settings(); n.apply({"word_gap": "zigzag"}); assert n.word_gap == "blank"
# your saved settings.json (read only)
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
with open(SETTINGS_FILE if os.path.exists(SETTINGS_FILE) else os.devnull, encoding="utf-8") as f:
    mine = json.load(f) if os.path.exists(SETTINGS_FILE) else {}
n = Settings(); n.apply(mine)
assert n.caret and n.word_gap, "your settings load"
print("ALL OK")
