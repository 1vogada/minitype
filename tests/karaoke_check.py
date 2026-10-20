"""The karaoke caret's sync: lines sung at the song's own pace, word-timed
lyrics, the offset setting, and Spotify's jitter smoothed out."""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from minitype import spotify                                     # noqa: E402
from minitype.context import App                                 # noqa: E402
from minitype.engine import karaoke                              # noqa: E402
from minitype.engine.runner import TypingTest                    # noqa: E402
from minitype.ui import lyrics_mode                              # noqa: E402
from minitype.ui import settings_menu as sm                      # noqa: E402
from minitype.words import lyrics                                # noqa: E402

# ---------------------------------------------------------------- a line, then the wait
# a dense song: 20 letters every 2 seconds is 10 a second
dense = [(2.0 * k, "abcd efgh ijkl mnopq") for k in range(10)] + [(40.0, "after the solo")]
words, breaks, starts, pts = karaoke.layout(dense)
assert breaks == {4 * k for k in range(1, 11)} and starts[0] == (0.0, 0)
assert abs(karaoke._rate([(t, 21 * k, 21 * k + 20, ()) for k, (t, _) in enumerate(dense)])
           - 10.0) < 0.01
# the last dense line starts at 18s: sung by ~20.3s, then the caret waits through the solo
c = 21 * 9 + 20
assert karaoke.position(pts, 21.0) == c and karaoke.position(pts, 39.9) == c, \
    (karaoke.position(pts, 21.0), c)
assert karaoke.position(pts, 40.0) == c + 1, "the next line, on time"
# a dense line's end is never past the next line's start
assert all(t1 >= t0 and c1 >= c0 for (t0, c0), (t1, c1) in zip(pts, pts[1:])), "forward only"
assert karaoke.position(pts, 1.0) < 21 <= karaoke.position(pts, 2.0)

# ---------------------------------------------------------------- word-timed lyrics (enhanced LRC)
lrc = "[00:10.00]<00:10.00>Hello <00:11.00>there <00:14.00>world\n[00:20.00]<00:20.00>bye"
lines = lyrics.parse("", lrc)
assert karaoke.plain(lines[0][1]) == "Hello there world"
words, breaks, starts, pts = karaoke.layout(lines)
assert words == ["Hello", "there", "world", "bye"], words
assert karaoke.position(pts, 11.0) == 6, "on its word's time"
assert karaoke.position(pts, 13.9) < 12 <= karaoke.position(pts, 14.0), "waits for 'world'"
app = App()
app.settings.punctuation = "on"
tt = TypingTest(app, lyrics_mode.spec_for(lyrics.Song("s", "a", lines=lines)))
assert tt.words == words, "the tags never reach the words"
app.settings.punctuation = "off"
tags = lyrics.parse("", "[00:01.00]<00:01.00>Hey, <00:02.00>you!")
assert TypingTest(app, lyrics_mode.spec_for(lyrics.Song("s", "a", lines=tags))).words == \
    ["Hey", "you"]

# ---------------------------------------------------------------- the offset setting
song = lyrics.Song("s", "a", lines=((10.0, "one two three four"), (30.0, "five")))
t = TypingTest(app, lyrics_mode.spec_for(song, (10.0, 100.0, True, "x"), now=100.0))
t.start = 100.0
base = t.song_offset(101.0)
app.settings.karaoke_offset = 1000
assert t.song_offset(101.0) > base and t.song_offset(100.0) == base, "on by a second"
app.settings.karaoke_offset = -1000
assert t.song_offset(102.0) == base, "back by a second"
app.settings.karaoke_offset = 0
row = next(it for it in sm.build_items(app) if it.label == "karaoke offset")
assert row.value() == "0 ms"
row.action()
assert app.settings.karaoke_offset == 250 and row.value() == "+250 ms"
app.settings.karaoke_offset = 0

# ---------------------------------------------------------------- spotify's jitter
f = spotify.Follow.__new__(spotify.Follow)
f.now, f._starts = {"id": "1", "playing": True, "progress": 0.0, "at": 1000.0}, []
f.SEEK, f.KEEP = spotify.Follow.SEEK, spotify.Follow.KEEP


def answer(at, progress, **kw):
    return dict({"id": "1", "playing": True, "progress": progress, "at": at}, **kw)


f.now = f._steady(answer(1000.0, 0.0))
f.now = f._steady(answer(1002.0, 1.2))          # 0.8s stale: the caret doesn't jump back
assert f.position(1002.0) == 2.0, f.position(1002.0)
f.now = f._steady(answer(1004.0, 4.0))          # on time again
assert f.position(1004.0) == 4.0
f.now = f._steady(answer(1006.0, 30.0))         # a seek: taken at once
assert f.position(1006.0) == 30.0
f.now = f._steady(answer(1008.0, 31.0, playing=False))
assert f.position(1100.0) == 31.0 and f._starts == [], "paused: held, starts over"
f.now = f._steady(answer(1110.0, 31.0))
assert f.position(1111.0) == 32.0, "played on"
f.now = f._steady(answer(1112.0, 1.0, id="2"))
assert f.position(1112.0) == 1.0, "a new song: its own clock"
# ---------------------------------------------------------------- the caret on typed letters
from minitype.engine.render import Painter, UND                   # noqa: E402
st = app.styles()
p = Painter(st, app.settings, ["hello", "world"], ["hel", ""], 0, {1, 8}, False, False)
typed_cell, untyped_cell = p.word(0)[1], p.word(1)[2]
assert typed_cell[0] == st.typed(1, 0, 0, 0) + UND, "a typed letter stays lit, underlined"
assert untyped_cell[0] == st.dim + UND, "an untyped one is dimmed"
assert Painter(st, app.settings, ["ab", "cd"], ["ab", "c"], 1, {2}, False, False).gap(0)[0] == UND
# ---------------------------------------------------------------- ctrl-[ / ctrl-] nudge the offset
from unittest import mock                                         # noqa: E402
from minitype.engine import runner                                # noqa: E402
from minitype.terminal import _windows as win, keys               # noqa: E402
app.settings.karaoke_offset = 0
t.follow = type("F", (), {"playing": True, "missing": "", "next": None, "busy": False,
                          "now": {}, "position": lambda self, x: 10.0})()
for _ in range(3):
    assert t.handle(keys.CTRL_RBRACKET, 200.0) is None
assert app.settings.karaoke_offset == 75
t.handle(keys.CTRL_LBRACKET, 200.0)
assert app.settings.karaoke_offset == 50
assert "sync +50 ms" in t.status(time.time())[0]
assert "sync" not in t.status(time.time() + 5)[0], "only for a moment"
app.settings.karaoke_offset = 4990
t.handle(keys.CTRL_RBRACKET, 200.0)
assert app.settings.karaoke_offset == 5000, "kept in range"
assert "ctrl-[ ] offset" in runner.LYRICS_FOOTER
t.follow = None
app.settings.karaoke_offset = 0
t.handle(keys.CTRL_RBRACKET, 200.0)
assert app.settings.karaoke_offset == 0, "only following spotify"
# windows tells ctrl-[ from esc by the key behind it
for vk, want in ((win.VK_LBRACKET, keys.CTRL_LBRACKET), (0x1B, keys.ESC)):
    with mock.patch.object(win, "_getch", lambda: ""),             mock.patch.object(win, "_key_for", lambda ch, v=vk: v if ch == "" else None),             mock.patch.object(win, "_with_shift", lambda v: False),             mock.patch.object(win, "ready", lambda: False):
        assert win.read() == want, (vk, want)
with mock.patch.object(win, "_getch", lambda: ""),         mock.patch.object(win, "_key_for", lambda ch: None),         mock.patch.object(win, "_with_shift", lambda v: False):
    assert win.read() == keys.CTRL_RBRACKET
print("ALL OK")
