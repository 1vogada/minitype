"""The lyrics header: the speed a song needs and its tempo (from Deezer,
faked here - nothing goes online), each with its own switch."""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from minitype.context import App                                 # noqa: E402
from minitype.engine.runner import TypingTest                    # noqa: E402
from minitype.ui import lyrics_mode                              # noqa: E402
from minitype.ui import settings_menu as sm                      # noqa: E402
from minitype.words import lyrics, tempo                         # noqa: E402

# ---------------------------------------------------------------- tempo from deezer
asked = []
TRACKS = {1: 0, 2: 0, 3: 123.4, 9: 0}


def deezer(path):
    asked.append(path)
    if path.startswith("search"):
        return {"data": [
            {"id": 9, "title": "Cover of Song", "artist": {"name": "Other"}, "duration": 200},
            {"id": 1, "title": "Song", "artist": {"name": "Band"}, "duration": 300},
            {"id": 2, "title": "Song (Live)", "artist": {"name": "Band"}, "duration": 210},
            {"id": 3, "title": "Song", "artist": {"name": "Band"}, "duration": 201}]}
    return {"bpm": TRACKS[int(path.split("/")[1])]}


assert tempo.bpm("Song", "Band, Guest", 200, ask=deezer) == 123.4
assert asked[1:] == ["track/3"], "the same song, closest in length, first"
asked.clear()
assert tempo.bpm("song", "band", 200, ask=deezer) == 123.4 and asked == [], "kept"
TRACKS[3] = 0
assert tempo.bpm("Other", "Band", 200, ask=deezer) is None
assert len([p for p in asked if p.startswith("track")]) == tempo.TRIES, "a few releases tried"
asked.clear()
assert tempo.bpm("Other", "Band", 200, ask=deezer) is None and asked == [], "unknown: kept too"


def offline(path):
    raise OSError("offline")


assert tempo.bpm("New", "Band", ask=offline) is None
assert "new|band" not in tempo._load(), "offline isn't kept: asked again next time"

# ---------------------------------------------------------------- the header
app = App()
song = lyrics.Song("One", "Metallica", "", 446.0,
                   ((10.0, "abcd efgh ijkl mnop"), (14.0, "qrst uvwx"), (20.0, "yz")))
t = TypingTest(app, lyrics_mode.spec_for(song))
assert t.spec.song == ("One", "Metallica", 446.0)
need = t.song_wpm()
chars = t.points[-1][1] - t.points[0][1]
assert abs(need - (chars / 5) / ((t.points[-1][0] - 10.0) / 60)) < 1e-9 and 20 < need < 200, need
t.bpm = 105.4
head = t.status(time.time())[0]
assert f"song {need:.0f} wpm" in head and "105 bpm" in head, head
app.settings.show_song_wpm = app.settings.show_bpm = False
head = t.status(time.time())[0]
assert "song" not in head.replace("One - Metallica", "") and "bpm" not in head, head
untimed = TypingTest(app, lyrics_mode.spec_for(lyrics.Song("s", "a", lines=((None, "x y"),))))
assert untimed.song_wpm() is None
# looked up in the background, only when it's switched on
got = []
real = tempo.bpm
tempo.bpm = lambda title, artist="", duration=0.0: got.append((title, artist)) or 99.0
t.look_up_tempo()
time.sleep(0.05)
assert got == [] and t.bpm == 105.4, "switched off: not asked"
app.settings.show_bpm = True
t.bpm = None
t.look_up_tempo()
for _ in range(100):
    if t.bpm:
        break
    time.sleep(0.01)
assert t.bpm == 99.0 and got == [("One", "Metallica")]
tempo.bpm = real
# tab keeps the song, so its tempo
assert lyrics_mode.synced(t.spec, {"progress": 12.0, "at": time.time(), "playing": True,
                                   "id": "x"}).song == t.spec.song
labels = {it.label for it in sm.build_items(app)}
assert {"show song wpm", "show bpm"} <= labels or {"song wpm", "bpm"} <= labels, labels
print("ALL OK")
