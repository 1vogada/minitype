"""The Spotify link, for the lyrics mode: what you're listening to now.

Spotify has no lyrics API - the lyrics come from LRCLIB (words/lyrics.py) -
but its Web API says which song is playing and how far into it you are, so
the lyrics mode can pick the song up and the karaoke caret can start where
the song is.

Spotify only lets a hobby app have five users (Development Mode, since
2026), so minitype doesn't ship one: you make your own free app at
developer.spotify.com/dashboard, with REDIRECT as its redirect URI, and
give minitype its client ID (settings -> words -> lyrics). Logging in is
the PKCE flow - no client secret: your browser opens Spotify's login, a
one-off local server on REDIRECT catches the answer, and the tokens are
kept in spotify.json next to the other saves.
"""

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import storage

PORT = 8888
REDIRECT = f"http://127.0.0.1:{PORT}/callback"        # Spotify wants the loopback address, not "localhost"
START = f"http://127.0.0.1:{PORT}/"     # the short link minitype opens: it sends you on to the login
SCOPES = "user-read-currently-playing user-read-playback-state"
AUTH = "https://accounts.spotify.com/authorize"
TOKEN = "https://accounts.spotify.com/api/token"
NOW = "https://api.spotify.com/v1/me/player/currently-playing"
FILE = "spotify.json"
LOGIN_WAIT = 180             # seconds to finish logging in in the browser


class SpotifyError(Exception):
    """Spotify couldn't be asked; the message says why, for the screen."""


def _path():
    return storage.path(FILE)


def _load():
    try:
        with open(_path(), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d):
    try:
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(d, f)
    except OSError as e:
        raise SpotifyError(f"couldn't save the login: {e}") from e


def linked():
    """Whether there's a Spotify login kept."""
    return bool(_load().get("refresh_token"))


def unlink():
    try:
        os.remove(_path())
    except OSError:
        pass


def _post(url, form):
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            why = json.loads(e.read().decode("utf-8")).get("error_description", "")
        except (OSError, ValueError):
            why = ""
        raise SpotifyError(f"spotify said no ({e.code}{': ' + why if why else ''})") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise SpotifyError("couldn't reach spotify - are you online?") from e


def _keep(d, client_id):
    old = _load()
    _save({"client_id": client_id,
           "access_token": d["access_token"],
           "refresh_token": d.get("refresh_token") or old.get("refresh_token"),
           "expires_at": time.time() + float(d.get("expires_in", 3600)) - 60})


def pkce():
    """(verifier, challenge) for the PKCE login."""
    verifier = secrets.token_urlsafe(64)[:100]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def login_url(client_id, challenge, state):
    return AUTH + "?" + urllib.parse.urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT,
        "code_challenge_method": "S256", "code_challenge": challenge,
        "scope": SCOPES, "state": state})


class _Server(HTTPServer):
    # on Windows "reuse" lets a second server listen on the same port and
    # take half the requests (minitype open twice): say the port is busy
    allow_reuse_address = os.name != "nt"


class Login:
    """A login in progress: a small server on PORT, in the background. Its
    START page sends the browser on to Spotify's login (`url`) - so the link
    opened, copied or typed is a short one with no "&" in it to be cut off
    (Windows can cut a long one there, and Spotify then finds no
    redirect_uri) - and REDIRECT catches Spotify's answer. Nothing blocks:
    ask `answered()` whenever you like (the screen does when you press
    enter), then `finish()` - or `cancel()`."""

    def __init__(self, client_id):
        client_id = (client_id or "").strip()
        if not client_id:
            raise SpotifyError("set your spotify client id first (settings -> words -> lyrics)")
        self.client_id = client_id
        self.verifier, challenge = pkce()
        self.state = secrets.token_urlsafe(16)
        self.url = login_url(client_id, challenge, self.state)
        self.got = {}
        self.start = START
        got, state, login_url_ = self.got, self.state, self.url

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                where = urllib.parse.urlparse(self.path)
                if where.path == "/":              # the start page: on to spotify's login
                    self.send_response(302)
                    self.send_header("Location", login_url_)
                    self.end_headers()
                    return
                q = urllib.parse.parse_qs(where.query)
                if where.path != "/callback" or not q:     # a favicon or the like
                    self.send_response(404)
                    self.end_headers()
                    return
                got.update({k: v[0] for k, v in q.items()})
                ok = "code" in got and got.get("state") == state
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(("<p style='font-family:monospace'>minitype: "
                                  + ("logged in - go back to minitype and press enter."
                                     if ok else "that didn't work - go back to minitype.")
                                  + "</p>").encode())

            def log_message(self, *a):
                pass

        try:
            self.server = _Server(("127.0.0.1", PORT), Handler)
        except OSError as e:
            raise SpotifyError(f"port {PORT} is busy - close what's using it and try again") from e
        self.server.timeout = 0.5
        self._stop = False
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        try:
            while not self._stop and not self.got:
                self.server.handle_request()
        finally:
            self.server.server_close()

    def answered(self):
        """Whether the browser has come back yet."""
        return bool(self.got)

    def finish(self):
        """Keep the tokens for the answer the browser brought. SpotifyError
        if it hasn't come back, or came back with no."""
        if not self.got:
            raise SpotifyError("no answer from the browser yet")
        if self.got.get("error"):
            raise SpotifyError(f"spotify said: {self.got['error']}")
        if self.got.get("state") != self.state or "code" not in self.got:
            raise SpotifyError("the login answer didn't match - try again")
        self.cancel()
        _keep(_post(TOKEN, {"grant_type": "authorization_code", "code": self.got["code"],
                            "redirect_uri": REDIRECT, "client_id": self.client_id,
                            "code_verifier": self.verifier}), self.client_id)

    def cancel(self):
        """Stop waiting; the port is free again when this returns."""
        self._stop = True
        if self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join(2)


def link(client_id, open_browser=webbrowser.open, wait=LOGIN_WAIT):
    """Log in to Spotify in the browser and keep the tokens, waiting for the
    browser (up to `wait` seconds) - for scripts; the screen uses Login
    itself, so you say when you've logged in."""
    login = Login(client_id)
    open_browser(login.start)
    end = time.time() + wait
    while not login.answered() and time.time() < end:
        time.sleep(0.1)
    if not login.answered():
        login.cancel()
        raise SpotifyError("no answer from the browser - try linking again")
    login.finish()


def _token():
    d = _load()
    if not d.get("refresh_token"):
        raise SpotifyError("not linked to spotify yet")
    if time.time() < d.get("expires_at", 0) and d.get("access_token"):
        return d["access_token"]
    _keep(_post(TOKEN, {"grant_type": "refresh_token", "refresh_token": d["refresh_token"],
                        "client_id": d["client_id"]}), d["client_id"])
    return _load()["access_token"]


def now_playing():
    """What's playing: {id, title, artist, album, duration, progress,
    playing, at} (seconds; `at` is when this was asked, to carry progress
    on), or None when nothing is."""
    req = urllib.request.Request(NOW, headers={"Authorization": f"Bearer {_token()}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read()
            at = time.time()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SpotifyError("the spotify login ran out - link again") from e
        if e.code == 429:
            raise SpotifyError("spotify says too many requests - wait a minute") from e
        raise SpotifyError(f"spotify said {e.code}") from e
    except (urllib.error.URLError, OSError) as e:
        raise SpotifyError("couldn't reach spotify - are you online?") from e
    if not body:                                         # 204: nothing playing
        return None
    d = json.loads(body.decode("utf-8"))
    item = d.get("item") or {}
    if item.get("type") not in (None, "track"):          # a podcast: no lyrics
        return None
    return {"id": item.get("id") or f"{item.get('name')}|{item.get('duration_ms')}",
            "title": item.get("name") or "",
            "artist": ", ".join(a.get("name", "") for a in item.get("artists") or []),
            "album": (item.get("album") or {}).get("name") or "",
            "duration": (item.get("duration_ms") or 0) / 1000,
            "progress": float(d.get("progress_ms") or 0) / 1000,
            "playing": bool(d.get("is_playing")), "at": at}


class Follow:
    """Keeps up with Spotify while you type a song's lyrics: in the
    background it asks what's playing every EVERY seconds, so the karaoke
    caret follows a pause, a seek or a skip. When a different song comes on
    it fetches that one's lyrics too (`fetch(now) -> song`), and `next`
    holds (song, now) for the test to switch to. Nothing it does blocks the
    typing; a failed ask is simply tried again next time."""

    EVERY = 2.0
    RETRY = 10.0                         # seconds between lyrics fetches that failed

    def __init__(self, now, fetch, ask=None):
        self.now = dict(now)             # the latest answer (whole dicts swapped in: thread safe)
        self.next = None                 # (song, now) of a new song, its lyrics ready
        self.missing = ""                # a new song with no lyrics: its name
        self.busy = False                # ...because the lyrics site couldn't be asked
        self._failed, self._again = None, 0.0   # a song whose fetch failed, and when to retry
        self._fetch = fetch
        self._ask = ask or now_playing
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def position(self, t):
        """Seconds into the song at time t: carried on from the last answer
        while it plays, held while it's paused."""
        n = self.now
        return n["progress"] + (t - n["at"]) if n.get("playing") else n["progress"]

    @property
    def playing(self):
        return bool(self.now.get("playing"))

    def _loop(self):
        while not self._stop.wait(self.EVERY):
            try:
                got = self._ask()
            except Exception:            # offline for a moment, a token refresh: next time
                continue
            if not got:                  # nothing playing at all: hold where it was
                self.now = dict(self.now, playing=False, progress=self.position(time.time()),
                                at=time.time())
                continue
            if got.get("id") != self.now.get("id"):
                if got.get("id") == self._failed and time.time() < self._again:
                    continue                 # the lyrics site was busy: not every poll
                try:
                    song = self._fetch(got)
                except Exception:
                    # couldn't get them (the site busy, offline): hold the
                    # caret and keep the old song, so it's tried again
                    self._failed, self._again = got.get("id"), time.time() + self.RETRY
                    self.missing, self.busy = got.get("title", ""), True
                    self.now = dict(self.now, playing=False, progress=self.position(time.time()),
                                    at=time.time())
                    continue
                self.busy = False
                if song is not None and getattr(song, "lines", None):
                    self.next, self.missing = (song, got), ""
                else:
                    # no lyrics for it: the caret holds where it was (the
                    # new song's position means nothing in these lyrics)
                    self.missing = got.get("title", "")
                    self.now = dict(got, playing=False, at=time.time(),
                                    progress=self.position(time.time()))
                    continue
            self.now = got

    def stop(self):
        self._stop.set()
