"""The Linux / macOS keyboard back end, run on Windows by feeding it the
bytes a terminal would send. termios doesn't exist here, so raw-mode setup
is checked against a stand-in module."""
import importlib, os, sys, tempfile, types
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import _posix as px
from minitype.terminal import keynames as K


def decode(data, ready_after=True):
    """Feed raw bytes; return every key read until they run out."""
    buf = bytearray(data.encode("utf-8") if isinstance(data, str) else data)

    def read_byte():
        return bytes([buf.pop(0)]) if buf else b""

    def ready(timeout=0):
        return bool(px._pending) or (bool(buf) and ready_after)
    out = []
    with mock.patch.object(px, "_read_byte", read_byte), mock.patch.object(px, "ready", ready):
        while buf or px._pending:
            out.append(px.read())
    return out


# printable, unicode (cyrillic is 2 bytes in UTF-8, emoji 4)
assert decode("ab") == ["a", "b"]
assert decode("чаша") == ["ч", "а", "ш", "а"]
assert decode("é😀") == ["é", "😀"]
# control keys as Linux / macOS terminals send them
assert decode("\r") == [K.ENTER] and decode("\n") == [K.ENTER]
assert decode("\x7f") == [K.BACKSPACE], "backspace is DEL on unix"
assert decode("\x08") == [K.CTRL_BACKSPACE], "ctrl-backspace sends BS in most terminals"
assert decode("\x1b\x7f") == [K.CTRL_BACKSPACE], "alt/option-backspace deletes a word"
assert decode("\t") == [K.TAB]
assert decode("\x03\x04\x11\x17") == [K.CTRL_C, K.CTRL_D, K.CTRL_Q, K.CTRL_W]
# arrows and friends, both CSI and SS3 (application mode) forms
assert decode("\x1b[A\x1b[B\x1b[C\x1b[D") == [K.UP, K.DOWN, K.RIGHT, K.LEFT]
assert decode("\x1bOA\x1bOD") == [K.UP, K.LEFT]
assert decode("\x1b[H\x1b[F\x1bOH\x1bOF") == [K.HOME, K.END, K.HOME, K.END]
assert decode("\x1b[1~\x1b[4~\x1b[7~\x1b[8~") == [K.HOME, K.END, K.HOME, K.END]
assert decode("\x1b[5~\x1b[6~\x1b[3~\x1b[2~") == [K.PGUP, K.PGDN, K.DELETE, K.INSERT]
assert decode("\x1b[1;5C") == [K.RIGHT], "ctrl-arrow still an arrow"
assert decode("\x1b[Z") == [K.SHIFT_TAB]
# shift-enter / shift-tab from terminals that report modifiers
assert decode("\x1b[13;2u") == [K.SHIFT_ENTER], "kitty / CSI u"
assert decode("\x1b[13u") == [K.ENTER]
assert decode("\x1b[9;2u") == [K.SHIFT_TAB]
assert decode("\x1b[127;5u") == [K.CTRL_BACKSPACE]
assert decode("\x1b[27;2;13~") == [K.SHIFT_ENTER], "xterm modifyOtherKeys"
assert decode("\x1b[97;2u") == ["a"], "a plain letter reported as CSI u"
# esc on its own, and esc followed quickly by a letter (alt-x): the letter is kept
assert decode("\x1b", ready_after=False) == [K.ESC]
assert decode("\x1bx") == [K.ESC, "x"]
# junk never hangs
assert decode("\x1b[" + "9" * 40 + "A") == [K.UNKNOWN] + ["9"] * 23 + ["A"]
assert decode("\x01") == [K.UNKNOWN]
assert decode(b"") == []
# end of input reads as ctrl-d rather than looping forever
with mock.patch.object(px, "_read_byte", lambda: b""):
    assert px.read() == K.CTRL_D
print("decoding ok")

# ---------------------------------------------------------------- raw mode
calls = []
fake = types.SimpleNamespace(
    IXON=0x400, ICRNL=0x100, INLCR=0x40, ISTRIP=0x20,
    ICANON=0x2, ECHO=0x8, ISIG=0x1, IEXTEN=0x8000, VMIN=6, VTIME=5,
    TCSANOW=0, TCSADRAIN=1,
    tcgetattr=lambda fd: [0xFFFF, 0, 0, 0xFFFF, 0, 0, [0] * 32],
    tcsetattr=lambda fd, when, mode: calls.append((when, mode)),
)
tty = types.SimpleNamespace(isatty=lambda: True, fileno=lambda: 0)
with mock.patch.dict(sys.modules, {"termios": fake}), mock.patch.object(px.sys, "stdin", tty):
    px.setup()
    when, mode = calls[-1]
    assert when == fake.TCSANOW
    for flag in ("IXON", "ICRNL", "INLCR", "ISTRIP"):
        assert not mode[0] & getattr(fake, flag), flag
    for flag in ("ICANON", "ECHO", "ISIG", "IEXTEN"):
        assert not mode[3] & getattr(fake, flag), flag
    assert mode[6][fake.VMIN] == 1 and mode[6][fake.VTIME] == 0
    px.setup()
    assert len(calls) == 1, "setting up twice doesn't save raw mode as the original"
    px.restore()
    assert calls[-1] == (fake.TCSADRAIN, [0xFFFF, 0, 0, 0xFFFF, 0, 0, [0] * 32]), "original back"
    px.restore()
    assert len(calls) == 2, "restoring twice is harmless"
# not a terminal (piped input): leaves everything alone
notty = types.SimpleNamespace(isatty=lambda: False, fileno=lambda: 0)
with mock.patch.dict(sys.modules, {"termios": fake}), mock.patch.object(px.sys, "stdin", notty):
    px.setup()
    assert len(calls) == 2
print("raw mode ok")

# ---------------------------------------------------------------- the app on "linux"
import minitype.terminal.keys as keys
with mock.patch.object(os, "name", "posix"):
    importlib.reload(keys)
    assert keys.backend is px, "posix picks the termios back end"
importlib.reload(keys)
assert keys.backend.__name__.endswith("_windows")

# a whole menu session driven by unix key bytes
with mock.patch.object(os, "name", "posix"):
    importlib.reload(keys)
from minitype.terminal import console
from minitype.context import App
from minitype.ui import main_menu as mm
import minitype.ui.screen as screen
console.present = lambda *a, **k: None
console.size = lambda: (100, 30)
buf = bytearray(b"\x1b[B\x1b[B\x1b[B\r")      # down down down enter -> zen
with mock.patch.object(px, "_read_byte", lambda: bytes([buf.pop(0)])), \
        mock.patch.object(px, "ready", lambda timeout=0: bool(buf) or bool(px._pending)), \
        mock.patch.object(screen, "keys", keys), mock.patch.object(mm, "keys", keys, create=True):
    app = App()
    spec = mm.main_menu(app)
assert spec.kind == "zen", spec
importlib.reload(keys)

# opening the books folder uses open / xdg-open off Windows
from minitype.ui import book_menu as bm
for platform, opener in (("darwin", "open"), ("linux", "xdg-open")):
    with mock.patch.object(bm.os, "name", "posix"), mock.patch.object(bm.sys, "platform", platform), \
            mock.patch.object(bm.subprocess, "Popen") as popen:
        bm._open_folder(App())
        assert popen.call_args[0][0][0] == opener, platform
print("ALL OK")
