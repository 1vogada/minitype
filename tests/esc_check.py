"""Esc on Windows: what's read after it to tell an escape sequence from a
plain esc is put back by minitype itself - msvcrt's own put-back holds one
character and raised OSError on a second (esc esc) or on "\\uffff"."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock

if os.name != "nt":
    print("ALL OK (windows only)")
    raise SystemExit

from minitype.terminal import _windows as W
from minitype.terminal.keynames import CLICK, ESC, UP, Mouse


def reads(chars, n, events=()):
    """Read n keys off the console holding `chars` (and mouse `events`)."""
    q = list(chars)
    W._pushed.clear()
    W._events[:] = list(events)
    with mock.patch.object(W.msvcrt, "kbhit", lambda: bool(q)), \
            mock.patch.object(W.msvcrt, "getwch", lambda: q.pop(0)), \
            mock.patch.object(W.msvcrt, "ungetwch", lambda c: 1 / 0), \
            mock.patch.object(W, "_key_for", lambda c: None), \
            mock.patch.object(W, "_with_shift", lambda vk: False):
        got = [W.read() for _ in range(n)]
    assert not q and not W._pushed, (q, W._pushed)
    return got


assert reads("\x1b\x1b\x1ba", 4) == [ESC, ESC, ESC, "a"], "esc esc: no second put-back"
assert reads("\x1b￿", 2)[0] == ESC, "a \\uffff after esc is put back too"
assert reads("\x1b[A", 1) == [UP], "an escape sequence still decodes"
assert reads("\x1b[", 2) == [ESC, "["], "esc and [ on their own"
assert reads("\x1bq", 2) == [ESC, "q"]
# esc with only the mouse waiting: esc at once, not a wait for a key
click = Mouse(CLICK, 1, 1)
q = ["\x1b"]
with mock.patch.object(W.msvcrt, "kbhit", lambda: bool(q)), \
        mock.patch.object(W.msvcrt, "getwch", lambda: q.pop(0) if q else 1 / 0), \
        mock.patch.object(W, "_key_for", lambda c: None), \
        mock.patch.object(W, "_with_shift", lambda vk: False), \
        mock.patch.object(W, "_pump", lambda: W._events.append(click) if not (q or W._events) else None), \
        mock.patch.dict(W._mouse, on=True):
    assert W.read() == ESC, "the mouse waiting isn't a key arriving"
    assert W.read() == CLICK
W._events.clear()
print("ALL OK")
