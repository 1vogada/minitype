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
assert lines == ((1.5, "Hello, world!"), (4.0, ""), (62.25, "again")), lines   # a break kept
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
assert 0 < t.song_offset(1001.0) < 11, "partway through the line"
assert t.song_offset(1005.0) == 11, "the line's sung, then the caret waits for the next"
assert t.song_offset(1010.0) == 12 and t.song_offset(5000.0) == 18
app.settings.karaoke = True
assert t.song_offset(1005.0) in t.status(1005.0)[1], "the caret is drawn"
app.settings.karaoke = False
assert t.song_offset(1005.0) not in t.status(1005.0)[1]
# a song already playing (spotify) carries on from where it is
t2 = TypingTest(app, lyrics_mode.spec_for(song, (15.0, 500.0), now=503.0))
t2.start = 503.0
assert t2.song_offset(503.0) == 11, t2.song_offset(503.0)   # 18s into the song: waiting
# joining a song partway: the test starts at the line being sung now
three = lyrics.Song("Three", "B", lines=((10.0, "first line"), (20.0, "second line"),
                                        (30.0, "third line")))
mid = lyrics_mode.spec_for(three, (21.0, 500.0, True, "x"), now=504.0)    # 25s in
assert [x for _, x in mid.lines] == ["second line", "third line"] and mid.amount == 2
tm = TypingTest(app, mid)
tm.start = 504.0
assert tm.words[0] == "second" and tm.song_offset(504.0) == 11, tm.song_offset(504.0)   # sung, waiting
assert len(lyrics_mode.spec_for(three, (5.0, 500.0, True, "x"), now=501.0).lines) == 3, \
    "before the first line: all of it"
assert len(lyrics_mode.spec_for(three, (25.0, 500.0, False, "x"), now=900.0).lines) == 2, \
    "paused: where it's paused"
assert len(lyrics_mode.spec_for(three).lines) == 3, "typed in by name: all of it"
# tab, following spotify: the same song from the line being sung now -
# back to an earlier line too (the whole song is kept), forward past this one
from minitype.engine import runner                               # noqa: E402
from minitype.terminal import keys                               # noqa: E402


class Where:
    playing, missing, next, busy = True, "", None, False
    now = {"progress": 12.0, "at": time.time(), "playing": False, "id": "x"}


tm.follow = Where()
back = tm.handle(keys.TAB, 505.0)
assert [x for _, x in back.lines] == ["first line", "second line", "third line"], back.lines
assert back.label == mid.label and back.song_at[:3] == (12.0, Where.now["at"], False)
Where.now = dict(Where.now, progress=31.0)
assert [x for _, x in tm.handle(keys.TAB, 506.0).lines] == ["third line"]
assert "tab sync to the song" in runner.LYRICS_FOOTER
tm.follow = None
assert tm.handle(keys.TAB, 507.0) is mid, "not following spotify: tab restarts"
top = tm.handle(keys.CTRL_I, 508.0)
assert [x for _, x in top.lines] == ["first line", "second line", "third line"] and top.amount == 3
assert top.song_at == mid.song_at, "ctrl-i: the song from its first line, still followed"
assert "ctrl-i song start" in runner.LYRICS_FOOTER
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
# on a port of its own, so a minitype you have open (on 8888) can't answer
import socket                                                 # noqa: E402
with socket.socket() as _s:
    _s.bind(("127.0.0.1", 0))
    spotify.PORT = _s.getsockname()[1]
spotify.REDIRECT = f"http://127.0.0.1:{spotify.PORT}/callback"
spotify.START = f"http://127.0.0.1:{spotify.PORT}/"
verifier, challenge = spotify.pkce()
import base64, hashlib                                       # noqa: E401,E402
assert challenge == base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
url = spotify.login_url("CID", challenge, "S")
q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
assert q["redirect_uri"] == [spotify.REDIRECT] and q["code_challenge_method"] == ["S256"]
assert "user-read-currently-playing" in q["scope"][0] and spotify.REDIRECT.startswith("http://127.0.0.1:")


def browser(url):
    """A browser that logs straight in: from the start page (whose redirect
    it reads, without going on to spotify) back to the redirect uri."""
    if url == spotify.START:
        import http.client
        for _ in range(50):
            try:
                c = http.client.HTTPConnection("127.0.0.1", spotify.PORT, timeout=2)
                c.request("GET", "/")
                r = c.getresponse()
                assert r.status == 302, r.status
                url = r.getheader("Location")
                break
            except ConnectionError:
                time.sleep(0.1)
        assert url.startswith(spotify.AUTH) and "redirect_uri=" in url, url
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
assert got.song_at[:3] == (61.0, 777.0, True) and got.label == "One - Metallica"
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
            browser(state["login"].start)
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
assert opened == [spotify.START], "the browser gets the short start link (nothing to cut off)"
assert any("not yet" in s for s in screens), "enter too early: not yet"
assert copied == [opened[0]] and any("link copied" in s for s in screens)
assert "press" in screens[0] and "enter" in screens[0] and "esc: cancel" in screens[0]
spotify.unlink()
# esc cancels, and frees the port for the next login straight away
screens.clear()
assert run_link([keys.ESC]) is False and not spotify.linked() and "not linked" in app.notice
again = spotify.Login("CID")
again.cancel()
# ---------------------------------------------------------------- following spotify while you type
from minitype import media                                       # noqa: E402
from minitype.engine import runner                               # noqa: E402
spotify.Follow.EVERY = 0.02
answers = []


def ask():
    return answers.pop(0) if answers else None


one = {"id": "1", "title": "One", "artist": "Metallica", "album": "a", "duration": 400,
       "progress": 10.0, "playing": True, "at": time.time()}
f = spotify.Follow(one, lambda now: song, ask=lambda: dict(answers[0]) if answers else dict(f.now))
t0 = time.time()
assert abs(f.position(t0 + 2) - (10.0 + (t0 + 2 - one["at"]))) < 0.01, "carries on while playing"
answers[:] = [dict(one, playing=False, progress=33.0, at=time.time())]
for _ in range(100):
    if not f.playing:
        break
    time.sleep(0.01)
assert not f.playing and f.position(time.time() + 50) == 33.0, "paused: the caret holds"
answers[:] = [dict(one, id="2", title="Two", playing=True, progress=1.0, at=time.time())]
for _ in range(200):
    if f.next:
        break
    time.sleep(0.01)
assert f.next and f.next[1]["title"] == "Two", "a new song: its lyrics fetched, ready to switch"
f.stop()
# a new song with no lyrics: noted, the caret held
g = spotify.Follow(one, lambda now: None, ask=lambda: dict(one, id="3", title="Three", progress=99.0))
for _ in range(200):
    if g.missing:
        break
    time.sleep(0.01)
assert g.missing == "Three" and g.next is None and not g.playing
assert g.position(time.time()) < 99, "the caret didn't jump to the other song's time"
g.stop()

# the test uses it: the caret where spotify says, the header says paused
playing_spec = lyrics_mode.spec_for(song, lyrics_mode.song_at(dict(one, progress=10.0, at=1000.0)), now=1000.0)
assert len(playing_spec.song_at) == 4 and playing_spec.song_at[3] == "1"
tt = TypingTest(app, playing_spec)
tt.start = 1000.0


class Still:
    playing, missing, next = False, "", None

    def position(self, t):
        return 15.0


tt.follow = Still()
assert tt.song_offset(5000.0) == tt.song_offset(1000.0), "held while the music's paused"
assert "music paused" in tt.status(1001.0)[0]
assert "ctrl-p pause music" in (tt.footer() or runner.LYRICS_FOOTER)
# a song with nothing playing at the start: held too
paused_spec = lyrics_mode.spec_for(song, (15.0, 500.0, False, "1"))
tp = TypingTest(app, paused_spec)
tp.start = 600.0
mid = tp.timing[1][1] - 1                                    # 15s: the first line sung, waiting
assert tp.song_offset(600.0) == tp.song_offset(900.0) == mid, "paused when the test began: held"

# spotify moved on: the test switches to the new song
class Moved(Still):
    playing = True
    next = (lyrics.Song("Two", "Band", lines=((1.0, "second song"),)), dict(one, id="2", title="Two"))

    def stop(self):
        pass


with mock.patch.object(lyrics_mode, "follow_for", lambda spec: Moved()), \
        mock.patch.object(runner, "draw", lambda *a, **k: None), \
        mock.patch.object(keys, "key_ready", lambda: False):
    nxt = runner.run_test(app, playing_spec)
assert nxt.source == "lyrics" and nxt.label == "Two - Band" and nxt.song_at[3] == "2"

# ctrl-p: the music and the test pause together, and resume together
presses = []
seq = iter([keys.CTRL_P, "x", keys.CTRL_P, keys.ESC])


def read_key(*a, **k):
    return next(seq)


with mock.patch.object(media, "play_pause", lambda: presses.append(1) or True), \
        mock.patch.object(runner, "draw", lambda *a, **k: None), \
        mock.patch.object(keys, "key_ready", lambda: True), \
        mock.patch.object(keys, "read_key", read_key), \
        mock.patch.object(lyrics_mode, "follow_for", lambda spec: None), \
        mock.patch("minitype.ui.anywhere.resume_dialog", lambda *a, **k: True):
    app.settings.esc_pause = False
    out = runner.run_test(app, lyrics_mode.spec_for(song))
# before typing: ctrl-p only toggles the music; typing "x" starts the test;
# then ctrl-p pauses both and resumes both; esc leaves
assert len(presses) == 3, presses
# ---------------------------------------------------------------- the lyrics site busy (503)
import io                                                        # noqa: E402
import urllib.error                                              # noqa: E402
calls = []


def busy_then(answer, times):
    def urlopen(req, timeout=None):
        calls.append(1)
        if len(calls) <= times:
            raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, io.BytesIO(b""))
        return io.BytesIO(json.dumps(answer).encode())
    return urlopen


with mock.patch.object(lyrics, "RETRY", (0, 0)), \
        mock.patch.object(urllib.request, "urlopen", busy_then({"ok": 1}, 2)):
    assert lyrics._get("get", {}) == {"ok": 1} and len(calls) == 3, "retried till it answered"
calls.clear()
with mock.patch.object(lyrics, "RETRY", (0, 0)), \
        mock.patch.object(urllib.request, "urlopen", busy_then({}, 9)):
    try:
        lyrics._get("get", {})
        raise AssertionError("should have given up")
    except lyrics.LyricsError as e:
        assert "busy or down" in str(e) and "503" in str(e) and len(calls) == 3, e

# following spotify: a busy site holds the caret and tries again later
tries = []


def flaky(now):
    tries.append(1)
    if len(tries) == 1:
        raise lyrics.LyricsError("busy")
    return song


spotify.Follow.RETRY = 0.05
h = spotify.Follow(one, flaky, ask=lambda: dict(one, id="4", title="Four", progress=5.0,
                                                at=time.time()))
for _ in range(100):
    if h.busy:
        break
    time.sleep(0.01)
assert h.busy and h.missing == "Four" and h.now["id"] == "1" and not h.playing
tb = TypingTest(app, playing_spec)
tb.start = 1000.0
tb.follow = h
assert "lyrics site busy - retrying Four" in tb.status(1001.0)[0]
for _ in range(300):
    if h.next:
        break
    time.sleep(0.01)
assert h.next and h.next[1]["title"] == "Four" and not h.busy, "retried and got them"
h.stop()
# ---------------------------------------------------------------- lyrics' own tape, punctuation, lines
from minitype.engine import render                               # noqa: E402
from minitype.ui import settings_tree                            # noqa: E402
from minitype.engine.spec import TestSpec                        # noqa: E402
import re                                                        # noqa: E402


def render_strip(x):
    return re.sub(r'\x1b\[[0-9;]*m', '', x)


ls = App()
ls.settings.punctuation, ls.settings.tape = "off", "off"
bars = lyrics.Song("B", "C", lines=((1.0, "Hello, there"), (2.0, "big world"), (3.0, "bye")))
lt = TypingTest(ls, lyrics_mode.spec_for(bars))
assert lt.words[0] == "Hello" and lt.breaks == {2, 4}, (lt.words, lt.breaks)
assert lt.punctuation() == "off" and lt.tape() == "off" and lt.line_breaks()[1] == "new line"
ls.settings.lyrics_punctuation, ls.settings.lyrics_tape = "on", "on"
lt = TypingTest(ls, lyrics_mode.spec_for(bars))
assert lt.words[0] == "Hello," and lt.punctuation() == "on" and lt.tape() == "on"
ls.settings.lyrics_punctuation = "forgive"
assert TypingTest(ls, lyrics_mode.spec_for(bars))._forgive()
ls.settings.lowercase = True
assert TypingTest(ls, lyrics_mode.spec_for(bars)).words[0] == "hello,", "same: all lowercase"
ls.settings.lyrics_capitals = "on"
assert TypingTest(ls, lyrics_mode.spec_for(bars)).words[0] == "Hello,", "on: as sung"
ls.settings.lowercase, ls.settings.lyrics_capitals = False, "off"
assert TypingTest(ls, lyrics_mode.spec_for(bars)).words[0] == "hello,", "off: lowercase"
assert TypingTest(ls, TestSpec("x", "words", 1, "custom", words=("Ab",))).words == ["Ab"],     "only lyrics"
ls.settings.lyrics_capitals, ls.settings.stop_on_error = "forgive", "off"
fc = TypingTest(ls, lyrics_mode.spec_for(bars))
assert fc.words[0] == "Hello,", "forgive: the capital still shows"
for ch in "hello, ":
    fc.handle(ch, 1.0)
assert fc.typed[0] == "Hello," and fc.bad_keys == 0 and fc.wi == 1, (fc.typed, fc.bad_keys)
fc.handle("T", 2.0)
assert fc.bad_keys == 1, "a capital where there's none is still wrong"
ls.settings.lyrics_capitals = "on"
strict = TypingTest(ls, lyrics_mode.spec_for(bars))
strict.handle("h", 1.0)
assert strict.bad_keys == 1, "on: shift needed"
ls.settings.lyrics_capitals = "same"
other = TypingTest(ls, TestSpec("x", "words", 3, "custom", words=("a", "b", "c")))
assert other.punctuation() == "off" and other.tape() == "off" and other.line_breaks()[0] == (), \
    "only lyrics tests use them"
# the words wrap at each of the song's lines; a marker shows the gap instead
assert render.wrap(["aa", "bb", "cc", "dd"], 80, {2}) == [(0, 2), (2, 4)]
assert render.wrap(["aa", "bb", "cc", "dd"], 80) == [(0, 4)]
seen = []
with mock.patch.object(console, "present", lambda out, *a, **k: seen.append(out)):
    st = ls.styles()
    words = ["Hello", "there", "big", "world", "bye"]
    for tape, split in (("off", "new line"), ("off", "marker"), ("on", "new line"), ("off", "off")):
        render.draw(st, ls.settings, "", words, [""] * 5, 0, 80, "", tape=tape,
                    breaks={2, 4}, split=split)
plain = [[render_strip(x) for x in out if render_strip(x).strip()] for out in seen]
assert [x.strip() for x in plain[0][:3]] == ["Hello there", "big world", "bye"], plain[0]
assert "there / big world / bye" in plain[1][0], plain[1]
assert "there / big world / bye" in plain[2][0], "tape: always the marker"
assert "there big world bye" in plain[3][0]
names = [x for page in settings_tree.TREE for x in str(page).split("'")]
assert "song lines" in names and "lyrics tape" in names and "lyrics punctuation" in names
# ---------------------------------------------------------------- music notes left out
lrc = "\n".join(["[00:01.00] ♪", "[00:05.00]Hello ♪ there", "[00:09.00]♪ ♫", "[00:20.00]world",
               "[00:25.00]♪"])
got = lyrics.parse("", lrc)
assert got == ((5.0, "Hello there"), (9.0, ""), (20.0, "world"), (25.0, "")), got
assert lyrics.parse("\n".join(["♪ ♪", "la la ♫", "♪"]), "") == ((None, "la la"),)
assert lyrics.parse("♪", "[00:01.00]♪") == (), "nothing but notes: no lyrics"
gt = TypingTest(App(), lyrics_mode.spec_for(lyrics.Song("s", "a", lines=got)))
assert gt.words == ["Hello", "there", "world"] and gt.breaks == {2}, (gt.words, gt.breaks)
gt.start = 100.0
assert gt.song_offset(100.0) == 0 and gt.song_offset(104.0) == 12   # the song starts with your first key
assert gt.song_offset(110.0) == gt.song_offset(114.0) == 12 < gt.song_offset(118.0), "the break: the caret waits at the line's end"
# lyrics kept before this lose their notes too
from minitype.words import lyrics_cache                          # noqa: E402
lyrics_cache.put("Old", "B", lyrics.Song("Old", "B", lines=((1.0, "♪"), (2.0, "hi ♪"))))
assert lyrics_cache.get("Old", "B").lines == ((2.0, "hi"),)
print("ALL OK")
