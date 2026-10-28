"""A slow screen doesn't slow your wpm: keys are timed when they're pressed
(by the key thread), not when the test gets round to them after a frame."""
import os, tempfile, threading, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.context import App
from minitype.engine import runner
from minitype.engine.spec import TestSpec
from minitype.terminal import console, keys

WORDS = ("alpha", "beta", "gamma", "delta")
TEXT = " ".join(WORDS)
GAP = 0.1               # a key every 100 ms: 600 letters a minute, 120 wpm
FRAME = 0.15            # and every frame takes 150 ms to draw


def typing(frame):
    """Type TEXT at GAP through the real key thread, with each frame
    taking `frame` seconds. Returns the result."""
    pressed = []                 # keys "on the keyboard", as they're pressed
    lock = threading.Lock()

    def press():
        for ch in TEXT:
            with lock:
                pressed.append(ch)
            time.sleep(GAP)

    def ready():
        with lock:
            return bool(pressed)

    def read():
        with lock:
            return pressed.pop(0)

    app = App()
    app.settings.wpm_system = "classic"
    with mock.patch.object(keys.backend, "ready", ready), \
            mock.patch.object(keys.backend, "read", read), \
            mock.patch.object(console, "present", lambda *a, **k: time.sleep(frame)), \
            mock.patch.object(console, "size", lambda: (80, 24)):
        threading.Thread(target=press, daemon=True).start()
        return runner.run_test(app, TestSpec("c", "words", len(WORDS), "custom", WORDS))


want = len(TEXT) / 5 / ((len(TEXT) - 1) * GAP / 60)       # first key to last
r = typing(FRAME)
assert r.wpm > want * 0.8, ("a slow screen slowed the wpm", round(r.wpm), round(want))
assert r.elapsed < (len(TEXT) - 1) * GAP * 1.25, r.elapsed
fast = typing(0.0)
assert abs(fast.wpm - r.wpm) < want * 0.15, (round(fast.wpm), round(r.wpm))
assert not keys._stamper["thread"], "the key thread stops with the test"
assert keys._stamped.empty()
print("ALL OK")
