import ctypes
from unittest import mock
from minitype.terminal import keys
from minitype.terminal import _windows as win

assert keys.backend is win, "on Windows the msvcrt back end is used"


def decode(chars, shift=False, ready=True):
    """read_key on a scripted input stream (Windows back end)."""
    stream = list(chars)
    ungot = []

    def getch():
        return ungot.pop() if ungot else stream.pop(0)
    with mock.patch.object(win, "_getch", getch), \
            mock.patch.object(win, "ready", lambda: ready if stream or ungot else False), \
            mock.patch.object(win, "_with_shift", lambda vk: shift), \
            mock.patch.object(win.msvcrt, "ungetwch", ungot.append):
        k = keys.read_key(resize=False)
        return k, "".join(ungot) + "".join(stream)


# the three ways shift-tab can arrive
assert decode("\x00\x0f")[0] == keys.SHIFT_TAB
assert decode("\xe0\x0f")[0] == keys.SHIFT_TAB
assert decode("\t", shift=True)[0] == keys.SHIFT_TAB
assert decode("\x1b[Z")[0] == keys.SHIFT_TAB
# and plain tab / esc are untouched
assert decode("\t")[0] == keys.TAB
assert decode("\x1b", ready=False)[0] == keys.ESC
k, rest = decode("\x1bx")
assert k == keys.ESC and rest == "x", "a key typed right after esc is kept"
# VT arrows too
assert [decode(f"\x1b[{c}")[0] for c in "ABCD"] == [keys.UP, keys.DOWN, keys.RIGHT, keys.LEFT]
# ordinary keys
assert decode("a")[0] == "a" and decode("\r")[0] == keys.ENTER and decode("\x08")[0] == keys.BACKSPACE

# the INPUT_RECORD layout matches Windows (20 bytes, key event at offset 4)
assert ctypes.sizeof(win._InputRecord) == 20
assert win._InputRecord.key.offset == 4


# shift-enter the same way
assert decode("\r", shift=True)[0] == keys.SHIFT_ENTER
assert decode("\r")[0] == keys.ENTER


# _with_shift reads the Shift flag off the key event in the queue
def fake_kernel32(records):
    class K:
        @staticmethod
        def GetStdHandle(n):
            return 1

        @staticmethod
        def PeekConsoleInputW(h, recs, size, pn):
            for i, (typ, down, vk, state) in enumerate(records):
                recs[i].type, recs[i].key.down = typ, down
                recs[i].key.vk, recs[i].key.state = vk, state
            pn._obj.value = len(records)
            return 1
    return K


class FakeWindll:
    def __init__(self, records):
        self.kernel32 = fake_kernel32(records)
        self.user32 = type("U", (), {"GetAsyncKeyState": staticmethod(lambda vk: 0)})


cases = [
    ([(1, 1, 0x10, 0x10), (1, 1, 0x09, 0x10)], True),    # shift down, then tab with shift
    ([(1, 1, 0x09, 0x00)], False),                       # plain tab
    ([(2, 0, 0, 0), (1, 0, 0x09, 0x10), (1, 1, 0x09, 0x10)], True),  # mouse, key-up skipped
]
for records, want in cases:
    with mock.patch.object(win.ctypes, "windll", FakeWindll(records)):
        assert win._with_shift(win.VK_TAB) is want, (records, want)
# only the asked-for key counts: shift on a tab says nothing about enter
with mock.patch.object(win.ctypes, "windll",
                       FakeWindll([(1, 1, 0x09, 0x10), (1, 1, 0x0D, 0x00)])):
    assert win._with_shift(win.VK_TAB) is True
    assert win._with_shift(win.VK_RETURN) is False
print("ALL OK")
