"""Song lyrics, for the lyrics mode, from LRCLIB (lrclib.net): a free, open
lyrics database with no key to sign up for. Lyrics come with timestamps
for most songs (LRC), which the karaoke caret follows.

Lyrics are fetched when a test starts and kept for that test only - they
are not written to disk.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple

API = "https://lrclib.net/api"
AGENT = "minitype (https://github.com/1vogada/minitype)"   # LRCLIB asks clients to say who they are
TIMEOUT = 8
WHOLE = 8          # fewer lines than this and an entry is a fragment
_STAMP = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)$")
_SECTION = re.compile(r"^\s*[\[(](verse|chorus|bridge|intro|outro|hook|pre-chorus|refrain)[^\])]*[\])]\s*$", re.I)


class LyricsError(Exception):
    """Lyrics couldn't be had; the message says why, for the screen."""


@dataclass(frozen=True)
class Song:
    title: str
    artist: str
    album: str = ""
    duration: float = 0.0
    lines: Tuple[Tuple[Optional[float], str], ...] = ()   # (seconds, or None unsynced; text)

    @property
    def synced(self):
        return bool(self.lines) and all(t is not None for t, _ in self.lines)

    @property
    def label(self):
        return f"{self.title} - {self.artist}" if self.artist else self.title


def parse(plain="", synced=""):
    """The lyric lines, as (seconds, text): timed from LRC text when there
    is any, else (None, text) from the plain lyrics. Empty lines and section
    labels ("[chorus]") are left out."""
    out = []
    for raw in (synced or "").splitlines():
        m = _STAMP.match(raw.strip())
        if m and m.group(3).strip() and not _SECTION.match(m.group(3)):
            out.append((int(m.group(1)) * 60 + float(m.group(2)), m.group(3).strip()))
    if out:
        return tuple(out)
    return tuple((None, line.strip()) for line in (plain or "").splitlines()
                 if line.strip() and not _SECTION.match(line))


def _get(path, params, timeout=TIMEOUT):
    url = f"{API}/{path}?" + urllib.parse.urlencode({k: v for k, v in params.items() if v})
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise LyricsError(f"the lyrics site said {e.code}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise LyricsError("couldn't reach the lyrics site (lrclib.net) - are you online?") from e


def _clean(text):
    """A name without the invisible characters some entries carry."""
    return " ".join((text or "").replace("﻿", " ").replace("​", "").split())


def _song(d):
    lines = parse(d.get("plainLyrics") or "", d.get("syncedLyrics") or "")
    artists = list(dict.fromkeys(a.strip() for a in _clean(d.get("artistName")).split(",") if a.strip()))
    return Song(_clean(d.get("trackName")), ", ".join(artists), _clean(d.get("albumName")),
                float(d.get("duration") or 0), lines)


def fetch(title, artist="", album="", duration=0.0):
    """The song's lyrics: the exact match first (when the artist is known),
    then the best search result - one with timestamps, closest in length."""
    title, artist = title.strip(), artist.strip()
    if not title:
        raise LyricsError("which song?")
    if artist:
        d = _get("get", {"track_name": title, "artist_name": artist, "album_name": album,
                         "duration": round(duration) if duration else None})
        if d and not d.get("instrumental"):
            song = _song(d)
            if len(song.lines) >= WHOLE:       # else a fragment: look further
                return song
    found = _get("search", {"track_name": title, "artist_name": artist} if artist
                 else {"q": title}) or []
    found = [d for d in found if not d.get("instrumental")
             and (d.get("plainLyrics") or d.get("syncedLyrics"))]
    if not found:
        who = f" by {artist}" if artist else ""
        raise LyricsError(f"no lyrics found for \"{title}\"{who}")

    # with no artist given, the one most entries name is the original (a
    # song's covers are each one entry, the original is on album after album)
    want = title.casefold()
    count = {}
    for d in found:
        key = _clean(d.get("artistName")).casefold()
        count[key] = count.get(key, 0) + 1

    def rank(d):
        off = abs(float(d.get("duration") or 0) - duration) if duration else 0
        same = _clean(d.get("trackName")).casefold() == want
        whole = len(parse(d.get("plainLyrics") or "", d.get("syncedLyrics") or "")) >= WHOLE
        who = _clean(d.get("artistName")).casefold()
        by = artist.casefold() in who if artist else True        # the artist you named
        return (not same, not by, not whole, not d.get("syncedLyrics"),
                0 if artist else -count[who], off)
    return _song(min(found, key=rank))


def split_query(text):
    """ "song - artist" (or "song by artist") into (song, artist)."""
    text = text.strip()
    for sep in (" - ", " – ", " by "):
        if sep in text:
            song, artist = text.split(sep, 1)
            return song.strip(), artist.strip()
    return text, ""
