"""Download the lyrics of your liked songs on Spotify, so the lyrics mode
has them offline and can pick one of your liked songs to type.

The liked songs list needs the user-library-read permission; a login from
before minitype asked for it is linked again first. Then each song's
lyrics are fetched (skipping ones already kept) with the progress on
screen; esc stops, and what's done so far stays done.
"""

import time

from .. import spotify
from ..terminal import console, keys
from ..terminal.style import RESET
from ..words import lyrics, lyrics_cache

GAP = 0.15            # seconds between songs: easy on the free lyrics site
GIVE_UP = 5           # this many failures in a row (offline, site down): stop


def _screen(app, title, lines):
    st = app.styles()
    out = ["", f"  {st.title}{title}{RESET}", ""] + [f"  {x}" for x in lines]
    console.present(out, None, ["", f"  {st.dim}esc: stop (what's done stays done){RESET}"])


def _stopped():
    """Whether esc (or ctrl-c) was pressed; other keys are ignored."""
    while keys.key_ready():
        if keys.read_key() in (keys.ESC, keys.CTRL_C):
            return True
    return False


def _relink(app):
    """A login with permission to read your liked songs: linked again when
    the kept one doesn't have it. Whether there is one now."""
    from .lyrics_mode import link
    if spotify.linked() and spotify.can(spotify.LIBRARY):
        return True
    if spotify.linked():
        _screen(app, "link spotify again", [
            "reading your liked songs needs one more permission than minitype",
            "asked for before - press enter to log in again, esc to cancel"])
        while True:
            k = keys.read_key()
            if k in (keys.ESC, keys.CTRL_C):
                app.notice = "liked songs: not downloaded"
                return False
            if k in (keys.ENTER, keys.SHIFT_ENTER):
                break
    return link(app)


def download(app, fetch=lyrics_cache.fetch, gap=GAP):
    """The download, start to finish; the outcome ends up in app.notice."""
    if not _relink(app):
        return
    try:
        songs = spotify.liked(lambda got, total: _screen(
            app, "download liked songs", [f"reading your liked songs... {got} of {total}"]))
    except spotify.SpotifyError as e:
        app.notice = f"spotify: {e}"
        return
    lyrics_cache.keep_liked(songs)
    got = had = none = failed = row = 0
    for n, t in enumerate(songs, 1):
        if _stopped():
            app.notice = f"stopped - {got + had} of {len(songs)} liked songs have lyrics kept"
            return
        artist = t["artist"].split(", ")[0]
        kept = lyrics_cache.get(t["title"], artist)
        if isinstance(kept, lyrics.Song):
            had += 1
            continue
        if kept == "none":
            none += 1
            continue
        _screen(app, "download liked songs", [
            f"{n} of {len(songs)}: {t['title']} - {t['artist']}", "",
            f"downloaded {got}   already kept {had}   no lyrics {none}   failed {failed}"])
        try:
            fetch(t["title"], artist, t["album"], t["duration"])
            got, row = got + 1, 0
        except lyrics.NoLyrics:
            none, row = none + 1, 0
        except lyrics.LyricsError as e:
            failed, row = failed + 1, row + 1
            if row >= GIVE_UP:
                app.notice = f"stopped: {e} - run it again later, it carries on"
                return
        time.sleep(gap)
    app.notice = (f"liked songs: {got + had} of {len(songs)} with lyrics kept"
                  + (f", {none} have none" if none else "")
                  + (f", {failed} failed (run it again)" if failed else ""))
