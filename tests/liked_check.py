"""Liked songs: the spotify list, the lyrics kept on disk, the download
and the liked source of the lyrics mode. Nothing here goes online."""

import io
import json
import os
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from unittest import mock                                        # noqa: E402
from minitype import spotify, storage                            # noqa: E402
from minitype.context import App                                 # noqa: E402
from minitype.terminal import console, keys                      # noqa: E402
from minitype.ui import lyrics_library, lyrics_mode              # noqa: E402
from minitype.ui import settings_menu as sm                      # noqa: E402
from minitype.words import lyrics, lyrics_cache                  # noqa: E402

# ---------------------------------------------------------------- the permission, the liked list
spotify._save({"client_id": "c", "access_token": "a", "refresh_token": "r",
               "expires_at": time.time() + 999, "scope": "user-read-currently-playing"})
assert spotify.linked() and not spotify.can(spotify.LIBRARY), "an older login lacks it"
assert "user-library-read" in spotify.SCOPES
spotify._keep({"access_token": "b", "expires_in": 3600, "scope": spotify.SCOPES}, "c")
assert spotify.can(spotify.LIBRARY)
spotify._keep({"access_token": "d", "expires_in": 3600}, "c")
assert spotify.can(spotify.LIBRARY), "a refresh without a scope keeps the old one"


def track(i):
    return {"track": {"type": "track", "id": f"t{i}", "name": f"Song {i}",
                      "artists": [{"name": "Band"}, {"name": "Guest"}],
                      "album": {"name": "LP"}, "duration_ms": 200000}}


pages = {
    f"{spotify.LIKED}?limit=50&offset=0": {"items": [track(i) for i in range(50)], "total": 52,
                                           "next": f"{spotify.LIKED}?limit=50&offset=50"},
    f"{spotify.LIKED}?limit=50&offset=50": {"items": [track(50), track(51),
                                                      {"track": {"type": "episode"}}],
                                            "total": 52, "next": None},
}
asked = []


def urlopen(req, timeout=None):
    asked.append(req.full_url)
    assert req.get_header("Authorization") == "Bearer d"
    return io.BytesIO(json.dumps(pages[req.full_url]).encode())


steps = []
with mock.patch.object(urllib.request, "urlopen", urlopen):
    songs = spotify.liked(lambda got, total: steps.append((got, total)))
assert len(songs) == 52 and len(asked) == 2 and steps == [(50, 52), (52, 52)], (len(songs), steps)
assert songs[0] == {"id": "t0", "title": "Song 0", "artist": "Band, Guest", "album": "LP",
                    "duration": 200.0}, songs[0]

# ---------------------------------------------------------------- lyrics kept on disk
one = lyrics.Song("One", "Metallica", "AJFA", 446.0, ((1.0, "I can't remember"), (5.0, "anything")))
assert lyrics_cache.get("One", "Metallica") is None
assert lyrics_cache.put("One", "Metallica", one)
assert lyrics_cache.get("ONE", "metallica, someone") == one, "found in any case, by first artist"
assert lyrics_cache.count() == 1
calls = []


def fake_fetch(title, artist="", album="", duration=0.0):
    calls.append(title)
    if title.startswith("Nothing"):
        raise lyrics.NoLyrics("no lyrics found")
    if title.startswith("Busy"):
        raise lyrics.LyricsError("busy")
    return lyrics.Song(title, artist, album, duration, ((0.0, f"words of {title}"),))


with mock.patch.object(lyrics, "fetch", fake_fetch):
    assert lyrics_cache.fetch("One", "Metallica") == one and calls == [], "kept: not asked"
    assert lyrics_cache.fetch("Two", "B").lines and calls == ["Two"]
    assert lyrics_cache.fetch("Two", "B").lines and calls == ["Two"], "fetched once, then kept"
    for _ in range(2):
        try:
            lyrics_cache.fetch("Nothing here", "B")
            raise AssertionError("no lyrics")
        except lyrics.NoLyrics:
            pass
    assert calls.count("Nothing here") == 1, "none: noted, not asked again"
    try:
        lyrics_cache.fetch("Busy one", "B")
    except lyrics.NoLyrics:
        raise AssertionError("a busy site isn't no lyrics")
    except lyrics.LyricsError:
        pass
    assert lyrics_cache.get("Busy one", "B") is None, "a failure isn't kept"
# the lyrics mode goes through it: a song you typed works offline next time
app = App()
app.settings.lyrics_source = "search"
with mock.patch.object(lyrics_mode, "prompt", lambda *a, **k: "Two - B"), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(lyrics, "fetch", lambda *a, **k: (_ for _ in ()).throw(
            lyrics.LyricsError("offline"))):
    spec = lyrics_mode.lyrics_test(app)
assert spec and spec.label == "Two - B", (spec, app.notice)

# ---------------------------------------------------------------- the download
lyrics_cache.clear()
assert lyrics_cache.count() == 0 and lyrics_cache.liked() == []
liked = [{"id": f"t{i}", "title": t, "artist": "Band, Guest", "album": "LP", "duration": 200.0}
         for i, t in enumerate(["Alpha", "Beta", "Nothing at all", "Gamma"])]
lyrics_cache.put("Beta", "Band", lyrics.Song("Beta", "Band", lines=((0.0, "kept already"),)))
calls.clear()
shown = []
with mock.patch.object(spotify, "liked", lambda progress=None: liked), \
        mock.patch.object(console, "present", lambda out, *a, **k: shown.append(out)), \
        mock.patch.object(keys, "key_ready", lambda: False):
    with mock.patch.object(lyrics, "fetch", fake_fetch):
        lyrics_library.download(app, gap=0)
assert calls == ["Alpha", "Nothing at all", "Gamma"], calls
assert "3 of 4 with lyrics kept" in app.notice and "1 have none" in app.notice, app.notice
assert len(lyrics_cache.liked()) == 4 and len(lyrics_cache.liked_with_lyrics()) == 3
assert any("downloaded" in " ".join(o) for o in shown), "the progress is on screen"
# running it again asks for nothing new
calls.clear()
with mock.patch.object(spotify, "liked", lambda progress=None: liked), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "key_ready", lambda: False), \
        mock.patch.object(lyrics, "fetch", fake_fetch):
    lyrics_library.download(app, gap=0)
assert calls == [], calls
# esc stops it; the site down: it stops after a few failures in a row
lyrics_cache.clear()
presses = iter([keys.ESC])
with mock.patch.object(spotify, "liked", lambda progress=None: liked), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "key_ready", lambda: True), \
        mock.patch.object(keys, "read_key", lambda *a, **k: next(presses)):
    lyrics_library.download(app, gap=0)
assert app.notice.startswith("stopped") and lyrics_cache.count() == 0, app.notice
busy = [dict(t, title=f"Busy {i}") for i, t in enumerate(liked * 2)]
calls.clear()
with mock.patch.object(spotify, "liked", lambda progress=None: busy), \
        mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "key_ready", lambda: False), \
        mock.patch.object(lyrics, "fetch", fake_fetch):
    lyrics_library.download(app, gap=0)
assert len(calls) == lyrics_library.GIVE_UP and "carries on" in app.notice, (calls, app.notice)
# an older login: linked again first (or nothing happens)
spotify._save(dict(spotify._load(), scope="user-read-currently-playing"))
with mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "read_key", lambda *a, **k: keys.ESC), \
        mock.patch.object(spotify, "liked", lambda progress=None: 1 / 0):
    lyrics_library.download(app)
assert "not downloaded" in app.notice
relinked = []
with mock.patch.object(console, "present", lambda *a, **k: None), \
        mock.patch.object(keys, "read_key", lambda *a, **k: keys.ENTER), \
        mock.patch.object(lyrics_mode, "link", lambda a: relinked.append(1) or False):
    lyrics_library.download(app)
assert relinked == [1]

# ---------------------------------------------------------------- the liked source
lyrics_cache.clear()
app.settings.lyrics_source = "liked"
assert lyrics_mode.lyrics_test(app) is None and "download liked songs" in app.notice
lyrics_cache.keep_liked(liked)
for t in ("Alpha", "Gamma"):
    lyrics_cache.put(t, "Band", lyrics.Song(t, "Band", lines=((0.0, f"words of {t}"),)))
picked = {lyrics_mode.lyrics_test(app).label for _ in range(20)}
assert picked == {"Alpha - Band", "Gamma - Band"}, picked
a, b = lyrics_mode.lyrics_test(app), lyrics_mode.lyrics_test(app)
assert a.label != b.label and not a.song_at, "not the same song twice in a row; not followed"

# ---------------------------------------------------------------- settings
labels = {it.label for it in sm.build_items(app)}
assert {"download liked songs", "clear kept lyrics"} <= labels
kept = next(it for it in sm.build_items(app) if it.label == "download liked songs")
assert kept.value() == "2 songs kept, 4 liked", kept.value()
assert os.path.isdir(storage.path("lyrics"))
print("ALL OK")
