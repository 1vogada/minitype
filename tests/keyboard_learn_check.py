"""Learn as you type on a magnetic keyboard: the keyboard app's client
(keyboard_app: the request it sends, its answers, the app not running or
answering an error), the settings rows (where they sit, a change sent
straight away) and the start-up question (asked, or not, and its answer
sent). The HTTP is faked, plus one real local server and a closed port."""
import json
import os
import re
import socket
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"
os.environ["COLORTERM"] = "truecolor"
from unittest import mock                                   # noqa: E402
from minitype import keyboard_app as ka, storage            # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.settings import Settings                      # noqa: E402
from minitype.terminal import console, keys                 # noqa: E402
from minitype.ui import keyboard_learn as kl                # noqa: E402
from minitype.ui import settings_menu as sm                 # noqa: E402
from minitype.ui.settings_tree import build_tree            # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.term_size = lambda: (110, 30)
console._last_size = (110, 30)
STATE = {"on": True, "percent": 70, "floorMm": 0.3, "minPresses": 20, "tunedKeys": 42,
         "learningKeys": 3, "lastApply": None, "lastError": None,
         "keys": [{"key": "W", "slot": 14, "presses": 23, "actuationMm": 1.2, "learntMm": 1.05}]}


class Fake:
    """urlopen stand-in: records each request, answers with `reply`
    (a dict, an exception to raise, or (status, dict) for an HTTP error)."""

    def __init__(self, reply):
        self.reply, self.sent = reply, []

    def __call__(self, req, timeout=None):
        self.sent.append((req.full_url, req.get_method(), json.loads(req.data), timeout))
        r = self.reply
        if isinstance(r, Exception):
            raise r
        if isinstance(r, tuple):
            import io
            import urllib.error
            raise urllib.error.HTTPError(req.full_url, r[0], "x", {},
                                         io.BytesIO(json.dumps(r[1]).encode()))
        body = json.dumps(r).encode() if not isinstance(r, bytes) else r
        return mock.MagicMock(__enter__=lambda s: mock.MagicMock(read=lambda: body),
                              __exit__=lambda *a: False)


def fake(reply):
    f = Fake(reply)
    return f, mock.patch("urllib.request.urlopen", f)


# ---------------------------------------------------------------- the client
assert ka.body("status") == {"action": "status"}
assert ka.body("on", percent=60, floor_mm=0.5) == {"action": "on", "percent": 60, "floorMm": 0.5}
assert ka.body("on", percent=99, floor_mm=5) == {"action": "on"}, "out of range: left out"
assert ka.body("on", percent=True) == {"action": "on"}
assert ka.body("apply") is None
assert ka.server_url("http://localhost:6869/") == "http://localhost:6869"
assert ka.server_url("ftp://x") == ka.SERVER and ka.server_url(None) == ka.SERVER
assert ka.server_url("http://") == ka.SERVER

f, p = fake(STATE)
with p:
    a = ka.switch(True, "http://127.0.0.1:7000")
assert f.sent == [("http://127.0.0.1:7000/api/learn/typing", "POST", {"action": "on"}, ka.TIMEOUT)]
assert a.ok and a.on and a.error is None
assert a.line() == "keyboard learn: on · 42 keys tuned · 3 learning", a.line()
f, p = fake(dict(STATE, on=False))
with p:
    a = ka.switch(False)
assert f.sent[0][0] == ka.SERVER + ka.PATH and f.sent[0][2] == {"action": "off"}
assert a.ok and not a.on and a.line() == "keyboard learn: off"
f, p = fake(dict(STATE, tunedKeys=1, learningKeys=0, lastError="keyboard not found"))
with p:
    assert ka.status().line() == "keyboard learn: on · 1 key tuned · keyboard not found"
assert f.sent[0][2] == {"action": "status"} and ka.TIMEOUT <= 1.5

for err in (ConnectionRefusedError(), socket.timeout(), OSError("down"),
            __import__("urllib.error").error.URLError("refused")):
    with fake(err)[1]:
        a = ka.status()
    assert not a.ok and a.error == ka.NOT_RUNNING, err
    assert a.line() == "keyboard learn: app not running"
with fake((409, {"error": "no keyboard connected"}))[1]:
    a = ka.status()
assert a.error == "no keyboard connected" and a.line() == "keyboard learn: no keyboard connected"
with fake((500, {}))[1]:
    assert ka.status().error == "error 500"
for odd in (b"not json", b"[1, 2]", {"percent": 3}, b""):
    with fake(odd)[1]:
        assert ka.status().error == "odd answer from the app", odd
assert ka.call("apply").error and not ka.call("apply").ok

# a closed port: nothing listens, which is normal
s = socket.socket()
s.bind(("127.0.0.1", 0))
closed = s.getsockname()[1]
s.close()
assert ka.status(f"http://127.0.0.1:{closed}").error == ka.NOT_RUNNING

# a real local server: the request as it arrives
got = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        got.append((self.path, self.headers["Content-Type"],
                    json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
        out = json.dumps(dict(STATE, on=got[-1][2]["action"] != "off")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}"
assert ka.switch(False, url).line() == "keyboard learn: off"
assert ka.status(url).on
assert got == [("/api/learn/typing", "application/json", {"action": "off"}),
               ("/api/learn/typing", "application/json", {"action": "status"})], got
srv.shutdown()


# ---------------------------------------------------------------- settings
d = Settings()
assert d.keyboard_learn is False and d.keyboard_ask is True
assert d.keyboard_server == ka.SERVER
d.apply({"keyboard_learn": "yes", "keyboard_ask": 0})          # wrong types: skipped
assert d.keyboard_learn is False and d.keyboard_ask is True

app = App()
app.load()
assert app.keyboard_app is None
tree = build_tree(sm.raw_items(app))
ingame = next(t for t in tree if t.name == "in-game")
screen = next(c for c in ingame.children if getattr(c, "name", "") == "screen")
mag = next(c for c in screen.children if getattr(c, "name", "") == "magnetic keyboard")
assert [it.label for it in mag.children] == ["keyboard learn", "ask at start", "keyboard server"]
assert all(t.name != "other" for t in tree), "every row placed"
row = mag.children[0]
assert row.value() == "off"
f, p = fake(STATE)
with p:
    row.action()                                     # on: sent straight away
assert app.settings.keyboard_learn and f.sent[-1][2] == {"action": "on"}
assert row.value() == "on" and app.keyboard_app.on
f, p = fake(ConnectionRefusedError())
with p:
    row.back()                                       # and off again
assert not app.settings.keyboard_learn and f.sent[-1][2] == {"action": "off"}
assert row.value() == "off  (app not running)"
ask_row = mag.children[1]
ask_row.action()
assert not app.settings.keyboard_ask and ask_row.value() == "off"
ask_row.action()
assert app.settings.keyboard_ask
# the server's address: only an http(s) one is taken, and it's told at once
server_row = mag.children[2]
for typed, want in (("ftp://nope", ka.SERVER), ("http://127.0.0.1:7001/", "http://127.0.0.1:7001")):
    f, p = fake(dict(STATE, on=False))
    with p, mock.patch("minitype.ui.prompt.prompt", lambda *a: typed):
        server_row.action()
    assert app.settings.keyboard_server == want, (typed, app.settings.keyboard_server)
assert f.sent[-1][0] == "http://127.0.0.1:7001/api/learn/typing"
app.settings.keyboard_server = ka.SERVER


# ---------------------------------------------------------------- the start-up question
def start(app, presses, reply=STATE):
    out = []
    seq = iter(presses)
    f, p = fake(reply)
    with p, mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        kl.at_start(app)
    assert next(seq, None) is None, "every key used"
    return f.sent, [strip(o) for o in out if o.startswith("\x1b[H")]


def saved():
    return json.load(open(storage.path(storage.SETTINGS), encoding="utf-8"))


app = App()
app.load()
sent, frames = start(app, [keys.LEFT, keys.ENTER])        # off is marked first; left: on
assert app.settings.keyboard_learn and [x[2] for x in sent] == [{"action": "on"}]
assert kl.QUESTION in frames[0] and "on" in frames[0] and "off" in frames[0]
assert any(">" in line and " off " in line for line in frames[0].splitlines()), "off marked"
assert any(">" in line and " on " in line for line in frames[1].splitlines())
assert saved()["keyboard_learn"] is True
box = [line for line in frames[0].splitlines() if "╔" in line]
assert box and box[0].count("═") >= len(kl.QUESTION), "the box fits the question"

sent, _ = start(app, [keys.ENTER])                         # on is marked now: enter keeps it
assert app.settings.keyboard_learn and [x[2] for x in sent] == [{"action": "on"}]
sent, _ = start(app, ["n"])
assert not app.settings.keyboard_learn and [x[2] for x in sent] == [{"action": "off"}]
assert saved()["keyboard_learn"] is False
sent, _ = start(app, ["y"])
assert app.settings.keyboard_learn and [x[2] for x in sent] == [{"action": "on"}]
sent, _ = start(app, [keys.ESC])                           # esc: as it was, still sent
assert app.settings.keyboard_learn and [x[2] for x in sent] == [{"action": "on"}]
# the app not running: no fuss, the answer kept
sent, _ = start(app, ["n"], reply=ConnectionRefusedError())
assert not app.settings.keyboard_learn and app.keyboard_app.error == ka.NOT_RUNNING

# ask at start off: nothing asked, the setting sent as it is
app.settings.keyboard_ask = False
for on in (True, False):
    app.settings.keyboard_learn = on
    sent, frames = start(app, [])
    assert frames == [] and [x[2] for x in sent] == [{"action": "on" if on else "off"}]
app.settings.keyboard_ask = True


# ---------------------------------------------------------------- the status line
st = app.styles()
app.settings.keyboard_learn = False
app.keyboard_app = ka.Answer(state=STATE)
assert kl.status_line(app, st) is None, "learn off: nothing shown"
f, p = fake(STATE)
with p:
    kl.refresh(app)
assert f.sent == [], "learn off: no call"
app.settings.keyboard_learn = True
with p:
    kl.refresh(app)
assert [x[2] for x in f.sent] == [{"action": "status"}]
assert strip(kl.status_line(app, st)) == "keyboard learn: on · 42 keys tuned · 3 learning"
app.keyboard_app = ka.Answer(error=ka.NOT_RUNNING)
assert strip(kl.status_line(app, st)) == "keyboard learn: app not running"
app.keyboard_app = None
assert kl.status_line(app, st) is None
print("ALL OK")
