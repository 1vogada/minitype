"""Learn as you type, for a magnetic (Hall-effect) keyboard: the MAX68HE.

The keyboard's own app runs a small local web server. While its "learn as
you type" is on, it watches how deep you press each key - in minitype or
anywhere else - and keeps moving each key's actuation point to your real
presses, by itself. minitype only switches it on and off and reads how far
it has got; it never applies anything and never asks to.

One endpoint, POST SERVER + PATH with a JSON body:
    {"action": "status" | "on" | "off"}   (optional "percent" 30..95, "floorMm" 0.1..2)
and a JSON answer:
    {"on", "percent", "floorMm", "minPresses", "tunedKeys", "learningKeys",
     "lastApply", "lastError", "keys": [...]}
or, when something's wrong, a non-2xx status with {"error": "message"}.
The app not running at all is normal: most people don't have the keyboard.
Standard library only, a short timeout, and nothing here ever raises.
"""

import json
import urllib.error
import urllib.request

SERVER = "http://localhost:6869"      # the keyboard app's server (settings: keyboard server)
PATH = "/api/learn/typing"
TIMEOUT = 1.0                         # seconds: it's on this machine, or it isn't running
ACTIONS = ("status", "on", "off")
PERCENT = (30, 95)                    # the range the server takes
FLOOR_MM = (0.1, 2.0)
NOT_RUNNING = "app not running"


class Answer:
    """What the keyboard app said: `state` its reply (a dict), or `error`
    why there isn't one (NOT_RUNNING when nothing answered)."""

    def __init__(self, state=None, error=None):
        self.state = state
        self.error = error

    @property
    def ok(self):
        return self.state is not None

    @property
    def on(self):
        return bool(self.ok and self.state.get("on"))

    def line(self):
        """The short status: "keyboard learn: on · 42 keys tuned",
        "keyboard learn: off", "keyboard learn: app not running"."""
        if not self.ok:
            return f"keyboard learn: {self.error or NOT_RUNNING}"
        s = self.state
        if not s.get("on"):
            return "keyboard learn: off"
        parts = ["on"]
        tuned, learning = _count(s.get("tunedKeys")), _count(s.get("learningKeys"))
        parts.append(f"{tuned} key{'' if tuned == 1 else 's'} tuned")
        if learning:
            parts.append(f"{learning} learning")
        if isinstance(s.get("lastError"), str) and s["lastError"]:
            parts.append(_short(s["lastError"]))
        return "keyboard learn: " + " · ".join(parts)


def _count(v):
    return v if type(v) is int and v >= 0 else 0


def _short(text, n=40):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def server_url(server):
    """The server to ask: `server` if it's an http(s) address, else SERVER."""
    if isinstance(server, str):
        server = server.strip().rstrip("/")
        if server.startswith(("http://", "https://")) and len(server) > len("http://"):
            return server
    return SERVER


def body(action, percent=None, floor_mm=None):
    """The request body, or None if the action isn't one the server takes.
    A percent or floor outside the server's range is left out."""
    if action not in ACTIONS:
        return None
    out = {"action": action}
    if type(percent) is int and PERCENT[0] <= percent <= PERCENT[1]:
        out["percent"] = percent
    if isinstance(floor_mm, (int, float)) and not isinstance(floor_mm, bool) \
            and FLOOR_MM[0] <= floor_mm <= FLOOR_MM[1]:
        out["floorMm"] = floor_mm
    return out


def call(action, server=SERVER, percent=None, floor_mm=None, timeout=TIMEOUT):
    """Ask the keyboard app; always an Answer, never an exception."""
    data = body(action, percent, floor_mm)
    if data is None:
        return Answer(error=f"unknown action {action!r}")
    req = urllib.request.Request(
        server_url(server) + PATH, data=json.dumps(data).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            reply = _json(r.read())
    except urllib.error.HTTPError as e:
        try:
            reply = _json(e.read())
        except Exception:
            reply = None
        why = reply.get("error") if isinstance(reply, dict) else None
        return Answer(error=_short(why) if isinstance(why, str) and why else f"error {e.code}")
    except (urllib.error.URLError, OSError, ValueError):
        return Answer(error=NOT_RUNNING)       # refused, timed out, no such host
    except Exception:
        return Answer(error=NOT_RUNNING)
    if not isinstance(reply, dict) or not isinstance(reply.get("on"), bool):
        return Answer(error="odd answer from the app")
    return Answer(state=reply)


def _json(raw):
    try:
        return json.loads(raw.decode("utf-8")) if raw else None
    except (ValueError, UnicodeDecodeError):
        return None


def status(server=SERVER):
    return call("status", server)


def switch(on, server=SERVER):
    """Learning on or off."""
    return call("on" if on else "off", server)
