"""Replay: a test is recorded key by key, rebuilt exactly at any moment, and
the replay screen plays, pauses, seeks and changes speed."""
import os, re, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.context import App
from minitype.engine import runner
from minitype.engine.replay import Replay
from minitype.engine.spec import TestSpec
from minitype.terminal import console, keys
from minitype.ui import replay as rp, results

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
SPEC = TestSpec("c", "words", 3, "custom", ("cat", "dog", "owl"))
clock = [1000.0]


def play(app, presses, gap=0.25):
    """Run a test through the real loop, a key every `gap` seconds."""
    seq = iter(presses)

    def read():
        clock[0] += gap
        return next(seq)
    import contextlib
    with mock.patch.object(runner.time, "time", lambda: clock[0]), \
            mock.patch.object(runner.time, "sleep", lambda s: None), \
            mock.patch.object(keys, "stamping", contextlib.nullcontext), \
            mock.patch.object(keys, "key_ready", lambda: True), \
            mock.patch.object(keys.backend, "read", read), \
            mock.patch.object(console, "write", lambda s: None), \
            mock.patch.object(console, "flush", lambda: None):
        return runner.run_test(app, SPEC)


app = App()
# a typo fixed with backspace, a wrong letter left in, then the rest
r = play(app, list("cx") + [keys.BACKSPACE] + list("at dpg owl"))
rep = r.replay
assert isinstance(rep, Replay) and rep.words == ["cat", "dog", "owl"], rep
assert len(rep.frames) == 13, len(rep.frames)
assert abs(rep.length - 3.0) < 1e-6, rep.length       # 13 keys, 0.25s apart, from the first
typed, wi, errors, typos, combo, wrong, n = rep.at(0.25)
assert typed[0] == "cx" and wi == 0 and (0, 1) in errors and typos[(0, 1)] == "x", typed
typed, wi, *_ = rep.at(0.5)
assert typed[0] == "c", typed                          # the backspace
typed, wi, errors, typos, *_ = rep.at(rep.length)
assert typed == ["cat", "dpg", "owl"] and (1, 1) in errors and (0, 1) in errors, typed
assert rep.at(-1)[0] == ["", "", ""] and rep.at(-1)[6] == 0
assert rep.wpm(typed, rep.length) > 0 and rep.wpm(typed, 0) == 0

# frames hold what changed, not the whole test
assert all(len(f[2]) <= 2 for f in rep.frames), [f[2] for f in rep.frames]

# the replay screen: plays to the end, pauses, seeks, changes speed; esc leaves
now = [0.0]
out = []


def screen(presses, step=0.5):
    seq = iter(presses)
    ready = iter([False, True] * 50)

    def key_ready():
        now[0] += step
        return next(ready)
    out.clear()
    with mock.patch.object(rp.time, "time", lambda: now[0]), \
            mock.patch.object(rp.time, "sleep", lambda s: None), \
            mock.patch.object(keys, "key_ready", key_ready), \
            mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        assert rp.replay_screen(app, rep) is None
    return [strip(o) for o in out if o.startswith("\x1b[H")]


f = screen([keys.UP, " ", keys.RIGHT, keys.ESC])
head = lambda frame: next(l for l in frame.splitlines() if "replay" in l)
assert "1x" in head(f[0]) and "0.0s / 3.0s" in head(f[0]), head(f[0])
assert "2x" in head(f[2]), head(f[2])
assert "paused" in head(f[4]), head(f[4])
paused_at = float(re.search(r"([\d.]+)s /", head(f[4])).group(1))
assert f"{min(3.0, paused_at + rp.SEEK):.1f}s" in head(f[6]), (paused_at, head(f[6]))

# to the end: it stops there and space plays it again from the start
f = screen([keys.UP, keys.UP, keys.UP, keys.ESC], step=1.0)
assert "end - space plays again" in head(f[-1]) and "3.0s / 3.0s" in head(f[-1]), head(f[-1])
assert "cat dog owl" in f[-1], f[-1]      # a wrong letter shows as the right one, in red

# the results screen offers it
assert results.REPLAY_KEY == "r"
calls = []
with mock.patch.object(results, "replay_screen", lambda a, rr: calls.append(rr)), \
        mock.patch.object(keys, "read_key", iter(["r", keys.ESC]).__next__), \
        mock.patch.object(console, "write", lambda s: None), \
        mock.patch.object(console, "flush", lambda: None):
    results.show_results(app, r)
assert calls == [rep], calls
print("ALL OK")
