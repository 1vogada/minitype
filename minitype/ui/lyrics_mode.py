"""The lyrics mode: type out a song's lyrics.

The song comes from what you type in ("song - artist"), or - with the
lyrics source set to spotify - from what Spotify is playing, linking to it
first if it isn't yet (see spotify.py). The lyrics come from LRCLIB
(words/lyrics.py). With karaoke on, a caret moves through the words where
the song is; for a song Spotify is playing it starts where the song is now.
"""

from .. import spotify
from ..engine.spec import TestSpec
from ..terminal import console
from ..terminal.style import RESET
from ..words import lyrics
from .prompt import prompt

SPOTIFY_HELP = ("spotify client id - make a free app at developer.spotify.com/dashboard "
                f"with the redirect uri {spotify.REDIRECT}, then paste its client id:")


def _say(app, text):
    console.present(["", f"  {app.styles().dim}{text}{RESET}"])


def spec_for(song, song_at=()):
    """A test of the song's lyrics."""
    return TestSpec(song.label, "words", len(song.lines), "lyrics",
                    lines=song.lines, song_at=tuple(song_at))


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


def link(app):
    """Link to spotify in the browser (asking for the client id first if
    needed). True if it worked; a notice says why if not."""
    cid = ask_client_id(app)
    if not cid:
        return False
    _say(app, "log in to spotify in the browser that just opened... (3 minutes)")
    try:
        spotify.link(cid)
    except spotify.SpotifyError as e:
        app.notice = f"spotify: {e}"
        return False
    app.notice = "linked to spotify"
    return True


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
    song = lyrics.fetch(now["title"], now["artist"].split(", ")[0], now["album"], now["duration"])
    # the song is playing: the karaoke caret starts where it is now
    at = (now["progress"], now["at"]) if now["playing"] else ()
    return song, at


def lyrics_test(app):
    """The test for the lyrics mode, or None (backed out, or a notice says
    what went wrong)."""
    try:
        if app.settings.lyrics_source == "spotify":
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
            song, at = lyrics.fetch(title, artist), ()
    except lyrics.LyricsError as e:
        app.notice = str(e)
        return None
    if not song.lines:
        app.notice = f"no lyrics found for {song.label}"
        return None
    return spec_for(song, at)
