"""Learn as you type, for a magnetic (Hall-effect) keyboard: the MAX68HE.

The keyboard's own app runs a small local web server. While its "learn as
you type" is on, it watches how deep you press each key - in minitype or
anywhere else - and keeps moving each key's actuation point to your real
presses, by itself. minitype only switches it on and off and reads how far
it has got; it never applies anything and never asks to.

One endpoint, POST SERVER + PATH with a JSON body:
    {"action": "status" | "on" | "off"}   (optional "percent" 30..95, "floorMm" 0.1..2)
    {"action": "events", "events": [{"t", "expected", "typed"}, ...]}   (a test's keystrokes,
        at most MAX_EVENTS a call; see keystrokes.py - the app matches them to key depth)
and a JSON answer:
    {"on", "percent", "floorMm", "minPresses", "tunedKeys", "learningKeys",
     "lastApply", "lastError", "keys": [...]}
(the events answer may add "patterns": what the app made of the mistakes)
or, when something's wrong, a non-2xx status with {"error": "message"}.
The app not running at all is normal: most people don't have the keyboard.
Standard library only, a short timeout, and nothing here ever raises.
"""

import json
import threading
import time
import urllib.error
import urllib.request

SERVER = "http://localhost:6869"      # the keyboard app's server (settings: keyboard server)
PATH = "/api/learn/typing"
TIMEOUT = 1.0                         # seconds: it's on this machine, or it isn't running
ACTIONS = ("status", "on", "off")
PERCENT = (30, 95)                    # the range the server takes
FLOOR_MM = (0.1, 2.0)
NOT_RUNNING = "app not running"
MAX_EVENTS = 2000                     # keystrokes per events call
FLUSH = 2.5                           # seconds quitting waits for the last sends


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
    return _post(data, server, timeout)


def _post(data, server, timeout):
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


def events_body(events):
    return {"action": "events", "events": list(events)}


def batches(events, n=None):
    """The events in calls of at most n (MAX_EVENTS)."""
    n = n or MAX_EVENTS
    return [events[i:i + n] for i in range(0, len(events), n)]


def send_events(events, server=SERVER, timeout=TIMEOUT):
    """Every event, MAX_EVENTS a call; the last call's Answer (None when
    there was nothing to send). Stops at the first call that fails."""
    answer = None
    for part in batches(events):
        answer = _post(events_body(part), server, timeout)
        if not answer.ok:
            break
    return answer


_sending = []              # the threads still sending, for flush()
_lock = threading.Lock()


def post_events(events, server=SERVER, done=None):
    """send_events in a daemon thread, so nothing waits on it; `done(answer)`
    is called from that thread with the last Answer. Returns the thread
    (None when there's nothing to send)."""
    events = list(events)
    if not events:
        return None

    def run():
        try:
            answer = send_events(events, server)
            if done is not None and answer is not None:
                done(answer)
        except Exception:
            pass                               # never let it reach the screen
        finally:
            with _lock:
                if t in _sending:
                    _sending.remove(t)

    t = threading.Thread(target=run, daemon=True, name="keyboard-events")
    with _lock:
        _sending.append(t)
    t.start()
    return t


def flush(timeout=FLUSH):
    """Wait (up to `timeout` seconds in all) for the sends still going: on quit."""
    end = time.monotonic() + timeout
    with _lock:
        going = list(_sending)
    for t in going:
        t.join(max(0.0, end - time.monotonic()))
