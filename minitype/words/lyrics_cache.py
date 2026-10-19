"""Lyrics kept on disk: every song's lyrics once they've been fetched, and
your liked songs' lyrics downloaded in one go (ui/lyrics_library.py), so
the lyrics mode works offline and when the lyrics site is down.

One small file per song in a lyrics folder next to the saves, named by the
song (title and first artist), so a song is found again however it was
asked for - typed in, playing on Spotify, or one of your liked songs. A
song with no lyrics anywhere is noted too, so a download doesn't ask for
it again for a while. The liked songs list itself is kept in liked.json.
"""

import hashlib
import json
import os
import shutil
import time

from .. import storage
from . import lyrics
from .lyrics import Song

FOLDER = "lyrics"
LIKED = "liked.json"
RETRY_NONE = 30 * 24 * 3600      # a song with no lyrics: asked for again after a month


def _dir():
    return storage.path(FOLDER)


def key(title, artist):
    """The name a song is kept under: its title and first artist, in any case."""
    first = (artist or "").split(", ")[0]
    return f"{title.strip().casefold()}|{first.strip().casefold()}"


def _file(title, artist):
    return os.path.join(_dir(), hashlib.sha1(key(title, artist).encode("utf-8")).hexdigest()[:20]
                        + ".json")


def _read(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def get(title, artist):
    """The kept lyrics of a song: a Song, "none" when it's known to have
    none (recently), or None when it's not kept."""
    d = _read(_file(title, artist))
    if not d:
        return None
    if d.get("none"):
        return "none" if time.time() - d.get("at", 0) < RETRY_NONE else None
    return Song(d.get("title", title), d.get("artist", artist), d.get("album", ""),
                d.get("duration") or 0.0, tuple((t, x) for t, x in d.get("lines", [])))


def put(title, artist, song):
    """Keep a song's lyrics (song None: it has none). Whether it was written."""
    if song is None or not song.lines:
        d = {"none": True, "at": time.time(), "title": title, "artist": artist}
    else:
        d = {"title": song.title, "artist": song.artist, "album": song.album,
             "duration": song.duration, "lines": [list(x) for x in song.lines]}
    p = _file(title, artist)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(p + ".tmp", p)
        return True
    except OSError:
        return False


def fetch(title, artist="", album="", duration=0.0):
    """lyrics.fetch, through the kept lyrics: a kept song comes from disk,
    a fetched one is kept. Raises lyrics.NoLyrics for a song known to have
    none, LyricsError when the site couldn't be asked."""
    got = get(title, artist)
    if isinstance(got, Song):
        return got
    if got == "none":
        who = f" by {artist}" if artist else ""
        raise lyrics.NoLyrics(f"no lyrics found for \"{title}\"{who}")
    try:
        song = lyrics.fetch(title, artist, album, duration)
    except lyrics.NoLyrics:
        put(title, artist, None)
        raise
    put(title, artist, song)
    return song


def count():
    """How many songs' lyrics are kept."""
    try:
        return sum(1 for n in os.listdir(_dir()) if n.endswith(".json")
                   and not (_read(os.path.join(_dir(), n)) or {}).get("none"))
    except OSError:
        return 0


def clear():
    """Forget every kept song's lyrics (the liked songs list too)."""
    shutil.rmtree(_dir(), ignore_errors=True)
    try:
        os.remove(storage.path(LIKED))
    except OSError:
        pass


def keep_liked(songs):
    """Keep the liked songs list ({id, title, artist, album, duration})."""
    try:
        with open(storage.path(LIKED), "w", encoding="utf-8") as f:
            json.dump(songs, f)
    except OSError:
        pass


def liked():
    """The kept liked songs list (empty until it's been downloaded)."""
    try:
        with open(storage.path(LIKED), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def liked_with_lyrics():
    """The liked songs whose lyrics are kept, as Songs."""
    out = []
    for t in liked():
        s = get(t.get("title", ""), t.get("artist", ""))
        if isinstance(s, Song) and s.lines:
            out.append(s)
    return out
