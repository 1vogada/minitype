"""The lyrics mode: type out a song's lyrics.

The song comes from what you type in ("song - artist"), or - with the
lyrics source set to spotify - from what Spotify is playing, linking to it
first if it isn't yet (see spotify.py). The lyrics come from LRCLIB
(words/lyrics.py). With karaoke on, a caret moves through the words where
the song is; for a song Spotify is playing it starts where the song is now.
"""

import time
from dataclasses import replace

from .. import spotify
from ..engine.spec import TestSpec
from ..terminal import console
from ..terminal.style import RESET
from ..words import lyrics, lyrics_cache
from .prompt import prompt

SPOTIFY_HELP = ("spotify client id - make a free app at developer.spotify.com/dashboard "
                f"with the redirect uri {spotify.REDIRECT}, then paste its client id:")


def _say(app, text):
    console.present(["", f"  {app.styles().dim}{text}{RESET}"])


def song_at(now):
    """A spec's song_at for what spotify says is playing: (seconds in, when,
    playing, track id)."""
    return (now["progress"], now["at"], bool(now["playing"]), now.get("id", ""))


def _fetch_playing(now):
    return lyrics_cache.fetch(now["title"], now["artist"].split(", ")[0], now["album"],
                              now["duration"])


def follow_for(spec):
    """A spotify.Follow for a test of what spotify is playing (else None):
    the caret follows a pause, seek or skip, and a new song's lyrics are
    fetched for the test to switch to."""
    if spec.source != "lyrics" or len(spec.song_at) < 4:
        return None
    pos, at, playing, track = spec.song_at[:4]
    return spotify.Follow({"progress": pos, "at": at, "playing": playing, "id": track},
                          _fetch_playing)


def from_here(lines, song_at, now=None):
    """The lines from the one being sung now on: a song spotify is already
    partway through starts there, not at its first line. Untimed lyrics,
    or a song not started yet, keep every line."""
    if not song_at:
        return lines
    pos, at = song_at[:2]
    playing = song_at[2] if len(song_at) > 2 else True
    t = pos + ((time.time() if now is None else now) - at) if playing else pos
    start = 0
    for i, (stamp, _) in enumerate(lines):
        if stamp is not None and stamp <= t:
            start = i
    return lines[start:]


def spec_for(song, song_at=(), now=None):
    """A test of the song's lyrics, from where the song is now."""
    lines = from_here(song.lines, song_at, now)
    return TestSpec(song.label, "words", len(lines), "lyrics",
                    lines=lines, song_at=tuple(song_at), whole=tuple(song.lines))


def from_start(spec):
    """Ctrl-i in a lyrics test: the song again from its first line (a song
    spotify is playing starts partway, where it was)."""
    whole = spec.whole or spec.lines
    return replace(spec, lines=whole, amount=len(whole))


def synced(spec, now, t=None):
    """Tab in a song spotify is playing: the same song again, from the line
    being sung now (`now` is the latest of what spotify says)."""
    whole = spec.whole or spec.lines
    return spec_for(lyrics.Song(spec.label, "", lines=whole), song_at(now), t)


def ask_client_id(app):
    """The spotify client id: asked for when there's none yet; None if
    you back out."""
    s = app.settings
    if not s.spotify_client_id:
        v = prompt(SPOTIFY_HELP)
        if not v:
            return None
        s.spotify_client_id = v.strip()
        app.save_settings()
    return s.spotify_client_id


def _copy(text):
    """Put text on the clipboard; whether it worked."""
    import shutil
    import subprocess
    import sys
    cmd = (["clip"] if sys.platform == "win32" else ["pbcopy"] if sys.platform == "darwin"
           else ["wl-copy"] if shutil.which("wl-copy") else ["xclip", "-selection", "clipboard"])
    try:
        subprocess.run(cmd, input=text, text=True, check=True, timeout=5,
                       capture_output=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _login_screen(app, login, status):
    st = app.styles()
    dim, title = st.dim, st.title
    lines = ["", f"  {title}link spotify{RESET}", "",
             f"  log in to spotify in your browser (it should have opened),",
             f"  then come back here and press {title}enter{RESET}.", "",
             f"  {dim}didn't open? open this in your browser (c copies it):{RESET}",
             f"  {title}{login.start}{RESET}"]
    lines += ["", f"  {dim}if spotify shows an error about the redirect uri, add {spotify.REDIRECT}",
              f"  to your app at developer.spotify.com/dashboard; INVALID_CLIENT: press i{RESET}"]
    if status:
        lines += ["", f"  {status}"]
    console.present(lines, None, ["", f"  {dim}enter: I've logged in   c: copy the link   "
                                     f"i: change client id   esc: cancel{RESET}"])


def link(app):
    """Link to spotify (asking for the client id first if needed): the
    browser opens Spotify's login and this asks you to press enter once
    you've logged in - nothing waits on its own. True if it worked; a
    notice says why if not."""
    import webbrowser
    from ..terminal import keys
    cid = ask_client_id(app)
    if not cid:
        return False
    try:
        login = spotify.Login(cid)
    except spotify.SpotifyError as e:
        app.notice = f"spotify: {e}"
        return False
    webbrowser.open(login.start)
    status = ""
    try:
        while True:
            _login_screen(app, login, status)
            key = keys.read_key()
            if key == keys.RESIZE:
                continue
            if key in (keys.ESC, keys.CTRL_C):
                app.notice = "spotify: not linked"
                return False
            if key == "c":
                status = "link copied" if _copy(login.start) else "couldn't copy - type the link above"
            elif key == "i":
                login.cancel()
                app.settings.spotify_client_id = ""
                cid = ask_client_id(app)
                if not cid:
                    app.notice = "spotify: not linked"
                    return False
                try:
                    login = spotify.Login(cid)
                except spotify.SpotifyError as e:
                    app.notice = f"spotify: {e}"
                    return False
                webbrowser.open(login.start)
                status = "new client id - log in again in the browser"
            elif key in (keys.ENTER, keys.SHIFT_ENTER):
                if not login.answered():
                    status = ("not yet - the browser hasn't come back. Finished logging in? "
                              "Check the redirect uri above")
                    continue
                try:
                    login.finish()
                except spotify.SpotifyError as e:
                    app.notice = f"spotify: {e}"
                    return False
                app.notice = "linked to spotify"
                return True
    finally:
        login.cancel()


def _from_spotify(app):
    """(song, song_at) for what's playing, or None (with a notice)."""
    if not spotify.linked() and not link(app):
        return None
    _say(app, "asking spotify what's playing...")
    try:
        now = spotify.now_playing()
    except spotify.SpotifyError as e:
        app.notice = f"spotify: {e}"
        return None
    if not now:
        app.notice = "spotify isn't playing a song right now"
        return None
    _say(app, f"looking up the lyrics of {now['title']}...")
    song = _fetch_playing(now)
    # the karaoke caret starts where the song is now, and follows it
    return song, song_at(now)


def _liked_song(app):
    """A random one of your liked songs whose lyrics are downloaded, not the
    last one you typed; None (with a notice) when there are none yet."""
    import random
    songs = lyrics_cache.liked_with_lyrics()
    if not songs:
        app.notice = ("no liked songs' lyrics yet - settings > words > lyrics > "
                      "download liked songs")
        return None
    last = getattr(app, "last_liked", None)
    pick = random.choice([s for s in songs if s.label != last] or songs)
    app.last_liked = pick.label
    return pick


def lyrics_test(app):
    """The test for the lyrics mode, or None (backed out, or a notice says
    what went wrong)."""
    try:
        if app.settings.lyrics_source == "liked":
            song, at = _liked_song(app), ()
            if song is None:
                return None
        elif app.settings.lyrics_source == "spotify":
            got = _from_spotify(app)
            if got is None:
                return None
            song, at = got
        else:
            q = prompt("song - artist (or just the song):")
            if not q:
                return None
            title, artist = lyrics.split_query(q)
            _say(app, f"looking up the lyrics of {title}...")
            song, at = lyrics_cache.fetch(title, artist), ()
    except lyrics.LyricsError as e:
        app.notice = str(e)
        return None
    if not song.lines:
        app.notice = f"no lyrics found for {song.label}"
        return None
    return spec_for(song, at)
