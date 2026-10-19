"""The lyrics mode: lyrics from LRCLIB, the Spotify link, the karaoke caret.
No network: LRCLIB and Spotify are stood in for; the Spotify login runs
against its real local callback server, with a pretend browser."""
import json
import os
import tempfile
import threading
import time
import urllib.parse
import urllib.request

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock                                    # noqa: E402
from minitype import spotify                                 # noqa: E402
from minitype.context import App                             # noqa: E402
from minitype.engine.runner import TypingTest                # noqa: E402
from minitype.ui import lyrics_mode, main_menu as mm         # noqa: E402
from minitype.ui import settings_menu as sm                  # noqa: E402
from minitype.words import lyrics                            # noqa: E402

LRC = "\n".join(f"[00:{10 + 3 * k:02d}.00] line {k} of the song" for k in range(10))

# ---------------------------------------------------------------- parsing
lines = lyrics.parse("", "[00:01.50] Hello, world!\n[00:04.00] [Chorus]\n[00:05.00]\n[01:02.25] again")
assert lines == ((1.5, "Hello, world!"), (62.25, "again")), lines
assert lyrics.parse("one\n\n[Verse 2]\ntwo", "") == ((None, "one"), (None, "two"))
assert lyrics.split_query("one - metallica") == ("one", "metallica")
assert lyrics.split_query("hello by adele") == ("hello", "adele")
assert lyrics.split_query("just a song") == ("just a song", "")


# ---------------------------------------------------------------- finding the song
def entry(title, artist, synced=LRC, n=None, dur=200):
    text = synced if n is None else "\n".join(f"[00:{k:02d}.00] x{k}" for k in range(n))
    return {"trackName": title, "artistName": artist, "albumName": "a", "duration": dur,
            "instrumental": False, "plainLyrics": "p", "syncedLyrics": text}


calls = []


def fake_get(path, params, timeout=8):
    calls.append((path, params))
    if path == "get":
        return entry("One", "Metallica", n=1)                    # a fragment
    return [entry("One", "Cover Band"), entry("One", "Metallica"), entry("One", "Metallica"),
            entry("Something Else", "Metallica")]


with mock.patch.object(lyrics, "_get", fake_get):
    song = lyrics.fetch("One", "Metallica")
    assert [c[0] for c in calls] == ["get", "search"], "a fragment from get: search instead"
    assert song.artist == "Metallica" and song.synced and len(song.lines) == 10
    calls.clear()
    song = lyrics.fetch("one")                                   # no artist: the original
    assert song.artist == "Metallica" and calls[0][0] == "search", (song, calls)
with mock.patch.object(lyrics, "_get", lambda *a, **k: []):
    try:
        lyrics.fetch("nothing", "nobody")
        raise AssertionError("should have raised")
    except lyrics.LyricsError as e:
        assert "no lyrics found" in str(e)
assert lyrics._song(entry("x", "A, A, B")).artist == "A, B", "artists named twice once"
assert lyrics._song(entry("x", "﻿A﻿")).artist == "A", "invisible characters gone"

# ---------------------------------------------------------------- the test and the karaoke caret
app = App()
app.settings.punctuation = "off"
song = lyrics.Song("One", "Metallica", lines=((10.0, "Hello, there"), (20.0, "world")))
spec = lyrics_mode.spec_for(song)
t = TypingTest(app, spec)
assert t.words == ["Hello", "there", "world"] and t.note == "One - Metallica"
assert t.timing == [(10.0, 0), (20.0, 12), (None, 18)], t.timing
assert t.song_offset(0) is None, "nothing before the test starts"
t.start = 1000.0
assert t.song_offset(1000.0) == 0, "the song starts with your first key, at its first line"
assert t.song_offset(1005.0) == 6, "halfway between two lines' starts: halfway between them"
assert t.song_offset(1010.0) == 12 and t.song_offset(5000.0) == 18
app.settings.karaoke = True
assert t.song_offset(1005.0) in t.status(1005.0)[1], "the caret is drawn"
app.settings.karaoke = False
assert t.song_offset(1005.0) not in t.status(1005.0)[1]
# a song already playing (spotify) carries on from where it is
t2 = TypingTest(app, lyrics_mode.spec_for(song, (15.0, 500.0)))
t2.start = 503.0
assert t2.song_offset(503.0) == 9, t2.song_offset(503.0)   # 18s into the song
# unsynced lyrics: words, no caret
t3 = TypingTest(app, lyrics_mode.spec_for(lyrics.Song("s", "a", lines=((None, "just words"),))))
t3.start = 1.0
assert t3.words == ["just", "words"] and t3.song_offset(5.0) is None
app.settings.punctuation = "on"
assert TypingTest(app, spec).words == ["Hello,", "there", "world"], "punctuation kept when on"

# ---------------------------------------------------------------- the menus
assert any(it.label == "lyrics" and it.key == "l" for it in mm.build_items(app))
labels = {it.label for it in sm.build_items(app)}
assert {"lyrics from", "karaoke", "spotify", "spotify client id"} <= labels
with mock.patch.object(lyrics_mode, "prompt", lambda *a, **k: "One - Metallica"), \
        mock.patch.object(lyrics, "_get", fake_get), \
        mock.patch.object(lyrics_mode, "_say", lambda *a: None):
    app.settings.lyrics_source = "search"
    got = lyrics_mode.lyrics_test(app)
    assert got.source == "lyrics" and got.label == "One - Metallica" and len(got.lines) == 10
with mock.patch.object(lyrics_mode, "prompt", lambda *a, **k: "nothing at all"), \
        mock.patch.object(lyrics, "_get", lambda *a, **k: []), \
        mock.patch.object(lyrics_mode, "_say", lambda *a: None):
    assert lyrics_mode.lyrics_test(app) is None and "no lyrics found" in app.notice

# ---------------------------------------------------------------- spotify: the login
verifier, challenge = spotify.pkce()
import base64, hashlib                                       # noqa: E401,E402
assert challenge == base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
url = spotify.login_url("CID", challenge, "S")
q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
assert q["redirect_uri"] == [spotify.REDIRECT] and q["code_challenge_method"] == ["S256"]
assert "user-read-currently-playing" in q["scope"][0] and spotify.REDIRECT.startswith("http://127.0.0.1:")


def browser(url):
    """A browser that logs straight in: comes back to the redirect uri."""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    back = spotify.REDIRECT + "?" + urllib.parse.urlencode({"code": "C0DE", "state": q["state"][0]})
    for _ in range(50):
        try:
            urllib.request.urlopen(back, timeout=2).read()
            return
        except OSError:
            time.sleep(0.1)


posted = []


def fake_post(url, form):
    posted.append(form)
    return {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600}


assert not spotify.linked()
with mock.patch.object(spotify, "_post", fake_post):
    spotify.link("CID", open_browser=browser)
assert posted[0]["grant_type"] == "authorization_code" and posted[0]["code"] == "C0DE"
assert posted[0]["code_verifier"] and "client_secret" not in posted[0], "PKCE: no secret"
assert spotify.linked() and json.load(open(spotify._path()))["refresh_token"] == "RT"
# an old token is refreshed
d = json.load(open(spotify._path()))
d["expires_at"] = 0
json.dump(d, open(spotify._path(), "w"))
posted.clear()
with mock.patch.object(spotify, "_post", fake_post):
    assert spotify._token() == "AT" and posted[0]["grant_type"] == "refresh_token"


# ---------------------------------------------------------------- spotify: what's playing
class Reply:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


playing = {"is_playing": True, "progress_ms": 61000,
           "item": {"type": "track", "name": "One", "duration_ms": 446000,
                    "album": {"name": "...And Justice for All"},
                    "artists": [{"name": "Metallica"}, {"name": "Guest"}]}}
with mock.patch.object(urllib.request, "urlopen", lambda *a, **k: Reply(json.dumps(playing).encode())):
    now = spotify.now_playing()
assert (now["title"], now["artist"], now["progress"], now["duration"]) == ("One", "Metallica, Guest", 61.0, 446.0)
with mock.patch.object(urllib.request, "urlopen", lambda *a, **k: Reply(b"")):
    assert spotify.now_playing() is None, "204: nothing playing"
podcast = dict(playing, item={"type": "episode", "name": "talk"})
with mock.patch.object(urllib.request, "urlopen", lambda *a, **k: Reply(json.dumps(podcast).encode())):
    assert spotify.now_playing() is None, "a podcast has no lyrics"
# the menu with spotify: the playing song, the caret where it is now
app.settings.lyrics_source = "spotify"
with mock.patch.object(spotify, "now_playing", lambda: dict(now, at=777.0)), \
        mock.patch.object(lyrics, "_get", fake_get), \
        mock.patch.object(lyrics_mode, "_say", lambda *a: None):
    got = lyrics_mode.lyrics_test(app)
assert got.song_at == (61.0, 777.0) and got.label == "One - Metallica"
with mock.patch.object(spotify, "now_playing", lambda: None), \
        mock.patch.object(lyrics_mode, "_say", lambda *a: None):
    assert lyrics_mode.lyrics_test(app) is None and "isn't playing" in app.notice
spotify.unlink()
assert not spotify.linked()

# ---------------------------------------------------------------- the login screen: it asks
from minitype.terminal import console, keys                      # noqa: E402
app.settings.spotify_client_id = "CID"
screens, opened, copied = [], [], []
state = {"login": None}
real_login = spotify.Login


def remember_login(cid):
    state["login"] = real_login(cid)
    return state["login"]


def pressed(seq):
    """Keys for the login screen; "BACK" stands for the browser coming back."""
    it = iter(seq)

    def read(*a, **k):
        key = next(it)
        if key == "BACK":
            browser(state["login"].url)
            key = next(it)
        return key
    return read


def run_link(seq):
    with mock.patch.object(keys, "read_key", pressed(seq)), \
            mock.patch.object(console, "present", lambda lines, focus=None, pinned=():
                              screens.append("\n".join(list(lines) + list(pinned)))), \
            mock.patch("webbrowser.open", opened.append), \
            mock.patch.object(spotify, "Login", remember_login), \
            mock.patch.object(lyrics_mode, "_copy", lambda t: copied.append(t) or True), \
            mock.patch.object(spotify, "_post", fake_post):
        return lyrics_mode.link(app)


# enter before logging in: it says so and keeps asking; c copies the link;
# then the browser comes back and enter links it
ok = run_link([keys.ENTER, "c", "BACK", keys.ENTER])
assert ok and spotify.linked() and app.notice == "linked to spotify"
assert opened and opened[0].startswith(spotify.AUTH), "the browser was sent to the login"
assert any("not yet" in s for s in screens), "enter too early: not yet"
assert copied == [opened[0]] and any("link copied" in s for s in screens)
assert "press" in screens[0] and "enter" in screens[0] and "esc: cancel" in screens[0]
spotify.unlink()
# esc cancels, and frees the port for the next login straight away
screens.clear()
assert run_link([keys.ESC]) is False and not spotify.linked() and "not linked" in app.notice
again = spotify.Login("CID")
again.cancel()
print("ALL OK")
