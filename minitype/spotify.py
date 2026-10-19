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


def _catch(state, wait=LOGIN_WAIT):
    """Wait for the browser to come back to REDIRECT; the code it brings."""
    got = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            ok = "code" in got and got.get("state") == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(("<p style='font-family:monospace'>minitype: "
                              + ("linked to spotify - you can close this tab."
                                 if ok else "that didn't work - try again from minitype.")
                              + "</p>").encode())

        def log_message(self, *a):
            pass

    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        raise SpotifyError(f"port {PORT} is busy - close what's using it and try again") from e
    server.timeout = 1
    end = time.time() + wait
    try:
        while not got and time.time() < end:
            server.handle_request()
    finally:
        server.server_close()
    if not got:
        raise SpotifyError("no answer from the browser - try linking again")
    if got.get("error"):
        raise SpotifyError(f"spotify said: {got['error']}")
    if got.get("state") != state or "code" not in got:
        raise SpotifyError("the login answer didn't match - try again")
    return got["code"]


def link(client_id, open_browser=webbrowser.open):
    """Log in to Spotify in the browser and keep the tokens."""
    client_id = (client_id or "").strip()
    if not client_id:
        raise SpotifyError("set your spotify client id first (settings -> words -> lyrics)")
    verifier, challenge = pkce()
    state = secrets.token_urlsafe(16)
    url = login_url(client_id, challenge, state)
    threading.Timer(0.3, lambda: open_browser(url)).start()   # once the server is listening
    code = _catch(state)
    _keep(_post(TOKEN, {"grant_type": "authorization_code", "code": code,
                        "redirect_uri": REDIRECT, "client_id": client_id,
                        "code_verifier": verifier}), client_id)


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
    """What's playing: {title, artist, album, duration, progress, playing,
    at} (seconds; `at` is when this was asked, to carry progress on), or
    None when nothing is."""
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
    return {"title": item.get("name") or "",
            "artist": ", ".join(a.get("name", "") for a in item.get("artists") or []),
            "album": (item.get("album") or {}).get("name") or "",
            "duration": (item.get("duration_ms") or 0) / 1000,
            "progress": float(d.get("progress_ms") or 0) / 1000,
            "playing": bool(d.get("is_playing")), "at": at}
