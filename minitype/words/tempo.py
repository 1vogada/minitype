"""A song's tempo (BPM), for the lyrics mode's header.

Spotify stopped giving its tempo data (audio features) to apps made after
November 2024, so this asks Deezer's free, keyless API: a search for the
song, then the track's "bpm" - 0 when Deezer doesn't know it, in which case
other releases of the same song are tried. Answers are kept in tempo.json
next to the saves (unknown ones too, for a month), so a song is only asked
about once.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import storage

API = "https://api.deezer.com"
AGENT = "minitype (https://github.com/1vogada/minitype)"
FILE = "tempo.json"
TIMEOUT = 8
TRIES = 4                       # releases of the song to ask before giving up
RETRY_UNKNOWN = 30 * 24 * 3600  # an unknown tempo: asked for again after a month


def _get(path):
    req = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _key(title, artist):
    return f"{title.strip().casefold()}|{(artist or '').split(', ')[0].strip().casefold()}"


def _load():
    try:
        with open(storage.path(FILE), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _keep(key, bpm):
    d = _load()
    d[key] = {"bpm": bpm, "at": round(time.time())}
    try:
        with open(storage.path(FILE), "w", encoding="utf-8") as f:
            json.dump(d, f)
    except OSError:
        pass


def _candidates(title, artist, duration, get):
    """Deezer's tracks for the song: same title and artist first, the
    closest in length first among those."""
    first = (artist or "").split(", ")[0]
    found = get("search?q=" + urllib.parse.quote(f"{first} {title}")).get("data") or []
    want_t, want_a = title.casefold(), first.casefold()

    def rank(x):
        t = (x.get("title") or "").casefold()
        a = ((x.get("artist") or {}).get("name") or "").casefold()
        return (not t.startswith(want_t), a != want_a,
                abs((x.get("duration") or 0) - duration) if duration else 0)
    return sorted(found, key=rank)


def bpm(title, artist="", duration=0.0, ask=None):
    """The song's tempo in beats a minute, or None when it's unknown or
    Deezer can't be reached. ask(path) stands in for the web (tests)."""
    key = _key(title, artist)
    kept = _load().get(key)
    if kept and (kept["bpm"] or time.time() - kept.get("at", 0) < RETRY_UNKNOWN):
        return kept["bpm"] or None
    get = ask or _get
    try:
        for t in _candidates(title, artist, duration, get)[:TRIES]:
            b = float(get(f"track/{t['id']}").get("bpm") or 0)
            if b > 0:
                _keep(key, round(b, 1))
                return round(b, 1)
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None                       # offline, or a strange answer: not kept
    _keep(key, 0)
    return None
