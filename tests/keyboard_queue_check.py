"""Keyboard learn keeps typing that the app couldn't take: with the app down the
keystrokes go to keyboard_queue.json and are sent first once it answers again.
A test (finished or not) under 60% right keystrokes isn't sent at all."""

import json
import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"

import urllib.error                                              # noqa: E402
from minitype import keyboard_app as ka                          # noqa: E402
from minitype.engine import runner                               # noqa: E402

STATE = {"on": True, "tunedKeys": 0}
ev = lambda n, ok=True: [{"t": i, "expected": "a", "typed": "a" if ok else "s"} for i in range(n)]


class Resp:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


sent = []


def up(req, timeout=None):
    sent.append(json.loads(req.data))
    return Resp(STATE)


def down(req, timeout=None):
    raise urllib.error.URLError("refused")


# app down: kept
with mock.patch("urllib.request.urlopen", down):
    a = ka.send_queued(ev(5))
assert not a.ok and a.error == ka.NOT_RUNNING and len(ka.queued()) == 5
with mock.patch("urllib.request.urlopen", down):
    ka.send_queued(ev(3))
assert len(ka.queued()) == 8, "more typing adds to it"
# app back: the waiting ones go first, with the new ones, and the queue is empty
with mock.patch("urllib.request.urlopen", up):
    a = ka.send_queued(ev(2))
assert a.ok and sum(len(b["events"]) for b in sent) == 10 and ka.queued() == []
assert not os.path.exists(ka._queue_path())
# a refusal for a reason (learn off): not kept
def off(req, timeout=None):
    raise urllib.error.HTTPError("u", 409, "off", {}, None)
with mock.patch("urllib.request.urlopen", off):
    ka.send_queued(ev(4))
assert ka.queued() == []
# capped
with mock.patch("urllib.request.urlopen", down):
    ka.send_queued(ev(ka.MAX_QUEUED + 50))
assert len(ka.queued()) == ka.MAX_QUEUED

# the 60% gate
assert runner.keystroke_accuracy(ev(6) + ev(4, ok=False)) == 60.0
assert runner.keystroke_accuracy([{"t": 1, "expected": None, "typed": "x"}]) == 100.0


class App:
    class settings:
        keyboard_learn = True
        keyboard_server = ka.SERVER
    keyboard_app = keyboard_patterns = keyboard_sent = None


class T:
    keystrokes = ev(5) + ev(5, ok=False)       # 50%: dropped


t = T()
assert runner._send_keystrokes(App(), t) is None and t.keystrokes == []
t.keystrokes = ev(7) + ev(3, ok=False)         # 70%, finished or not: sent
with mock.patch("urllib.request.urlopen", up):
    th = runner._send_keystrokes(App(), t)
    th.join(5)
assert th is not None and not th.is_alive()
print("ALL OK")
