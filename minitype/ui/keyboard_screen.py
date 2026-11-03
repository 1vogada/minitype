"""The keyboard screen (main menu k, with keyboard learn on): what the
keyboard app has learnt about each key. Laid out like the bad keys editor
(key_editor): a grid of keys, press one (or move to it) and its learning
data shows underneath - actuation now and what learning wants, presses,
its mistakes, the keys it gets mixed up with, and what the app changed.

The data is one status call (keyboard_app.status: the keys, and the
patterns the app found), made in the background when the screen opens and
every REFRESH seconds while it's open, so a key press never waits on it.
Keys pressed here only pick a key: they're not typing and go nowhere.
"""

import threading
import time

from .. import keyboard_app
from . import keyboard_learn, keyboard_suggest
from ..terminal import console, keys
from ..terminal.style import INV, RESET
from .menu import Hints, title_lines

ROWS = ("`1234567890-=", "qwertyuiop[]\\", "asdfghjkl;'", "zxcvbnm,./", " ")
REFRESH = 3.0       # seconds between status calls while the screen is open
POLL = 0.03         # how often the loop looks for a key or a new answer
HINTS = "press any key to see it   arrows move   esc back"
SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', "`1234567890-=[]\\;',./"))
WHY = (("misses", "pressed too light"), ("ghosts", "typed by brushing it"),
       ("doubles", "bounce"), ("typos", "wrong key"), ("slips", "wrong finger"),
       ("swaps", "typed the next key first"))


def key_id(v):
    """A key as the app names it, for matching: letters upper case, a
    shifted symbol its key (! -> 1), space "SPACE". None if it isn't one."""
    if not isinstance(v, str) or not v:
        return None
    if v == " " or v.strip().lower() == "space":
        return "SPACE"
    if len(v) == 1:
        v = SHIFTED.get(v, v)
    return v.upper()


def label(v):
    k = key_id(v)
    return "Space" if k == "SPACE" else k


class Poller:
    """Status calls in a daemon thread: one now, then every `every` seconds,
    until stop(). `answer` is the latest (None before the first), `seen`
    counts the answers so the screen knows to redraw."""

    def __init__(self, server, every=REFRESH):
        self.server, self.every = server, every
        self.answer, self.seen = None, 0
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name="keyboard-status")
        self.thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                answer = keyboard_app.status(self.server)
            except Exception:                   # status never raises; still, never here
                answer = keyboard_app.Answer(error=keyboard_app.NOT_RUNNING)
            self.answer, self.seen = answer, self.seen + 1
            self._stop.wait(self.every)

    def stop(self):
        self._stop.set()


def _dicts(v):
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _mm(v):
    return f"{v:.2f} mm"


def mistakes(entry):
    return sum(entry.get(f) for f, _ in WHY if type(entry.get(f)) is int and entry.get(f) > 0)


def find(items, key):
    return next((x for x in _dicts(items) if key_id(x.get("key")) == key), None)


def detail(answer, key):
    """The lines (plain text) for one key, from the app's status answer."""
    name = label(key)
    if answer is None:
        return [f"{name}", "asking the keyboard app..."]
    if not answer.ok:
        return [f"{name}", f"keyboard learn: {answer.error or keyboard_app.NOT_RUNNING}"]
    s = answer.state
    pat = s.get("patterns") if isinstance(s.get("patterns"), dict) else {}
    out = [name]
    k = find(s.get("keys"), key)
    if k:
        if _num(k.get("actuationMm")):
            out.append(f"actuation   {_mm(k['actuationMm'])} now")
        presses = k.get("presses") if type(k.get("presses")) is int else 0
        if _num(k.get("learntMm")):
            out.append(f"learnt      {_mm(k['learntMm'])}")
        else:
            need = s.get("minPresses") if type(s.get("minPresses")) is int else "?"
            out.append(f"learning    {presses} / {need} presses")
        out.append(f"presses     {presses}")
    p = find(pat.get("keys"), key)
    if p:
        parts = [f"hits {p['hits']}"] if type(p.get("hits")) is int else []
        for field, why in WHY:
            n = p.get(field)
            if type(n) is int:
                parts.append(f"{field} {n}" + (f" ({why})" if n else ""))
        if parts:
            out.append(" · ".join(parts))
    for pr in sorted(_dicts(pat.get("pairs")),
                     key=lambda x: -x["count"] if type(x.get("count")) is int else 0):
        want, typed, n = key_id(pr.get("expected")), key_id(pr.get("typed")), pr.get("count")
        if type(n) is int and n > 0 and want and typed and key in (want, typed):
            out.append(f"you typed {label(typed)} for {label(want)}: {n}x")
    for fg in sorted(_dicts(pat.get("fingers")),
                     key=lambda x: -x["count"] if type(x.get("count")) is int else 0):
        meant, typed, n = key_id(fg.get("meant")), key_id(fg.get("typed")), fg.get("count")
        if type(n) is int and n > 0 and meant and typed and key in (meant, typed):
            out.append(f"wrong finger: meant {label(meant)}, pressed {label(typed)}: {n}x")
    for sw in sorted(_dicts(pat.get("swaps")),
                     key=lambda x: -x["count"] if type(x.get("count")) is int else 0):
        first, second, n = key_id(sw.get("first")), key_id(sw.get("second")), sw.get("count")
        if type(n) is int and n > 0 and first and second and key in (first, second):
            out.append(f"typed {label(second)} before {label(first)}: {n}x")
    for sug in _dicts(pat.get("suggestions")):
        if key_id(sug.get("key")) == key and sug.get("why") in ("doubles", "slips"):
            out.append("waiting for your answer: " + (
                "bounce guard?" if sug["why"] == "doubles" else
                f"actuation to {_mm(sug['actuationMm'])} against wrong-finger presses?"
                if _num(sug.get("actuationMm")) else "deeper against wrong-finger presses?"))
    for a in _dicts(pat.get("adjusted")):
        if key_id(a.get("key")) != key:
            continue
        why = a.get("why") if isinstance(a.get("why"), str) and a.get("why") else ""
        mm = a.get("changeMm")
        said = keyboard_learn.guard_text(a)
        if said:
            out.append(f"changed: {said}")
        elif _num(mm) and round(mm, 2):
            way = "earlier" if mm < 0 else "later"
            out.append(f"changed: types {way} by {abs(round(mm, 2)):g} mm"
                       + (f" ({why})" if why else ""))
    if len(out) == 1:
        out.append("nothing learnt about it yet")
    return out


def draw(app, st, answer, cursor):
    dim, ok = st.dim, st.title
    lines = title_lines(app, st, "keyboard")
    state = answer.state if answer is not None and answer.ok else {}
    pat = state.get("patterns") if isinstance(state.get("patterns"), dict) else {}
    lines.append(f"  {dim}bright: learnt   ·n: mistakes{RESET}")
    lines.append("")
    focus = len(lines)
    r0, c0 = cursor
    for r, row in enumerate(ROWS):
        cells = []
        for c, ch in enumerate(row):
            k = key_id(ch)
            entry = find(state.get("keys"), k) or {}
            n = mistakes(find(pat.get("keys"), k) or {})
            mark = ok if _num(entry.get("learntMm")) else dim
            if (r, c) == (r0, c0):
                mark += INV
                focus = len(lines)
            cells.append(f"{mark}{label(ch)}{RESET}{dim}{('·' + str(n)) if n else '':<4}{RESET}")
        lines.append("  " + " " * r + " ".join(cells))
    lines.append("")
    key = key_id(ROWS[r0][c0])
    lines += [f"  {ok if i == 0 else ''}{line}{RESET}" for i, line in enumerate(detail(answer, key))]
    if answer is not None and answer.ok:
        lines += ["", f"  {dim}{answer.line()}{RESET}"]
    if not app.settings.keyboard_learn:
        lines += [f"  {dim}keyboard learn is off (settings: in-game › screen › magnetic keyboard){RESET}"]
    return lines, focus


def place(ch):
    """Where key ch sits in ROWS, or None."""
    k = key_id(ch)
    for r, row in enumerate(ROWS):
        for c, x in enumerate(row):
            if key_id(x) == k:
                return r, c
    return None


def move(cursor, key):
    r, c = cursor
    if key == keys.LEFT:
        c = (c - 1) % len(ROWS[r])
    elif key == keys.RIGHT:
        c = (c + 1) % len(ROWS[r])
    elif key in (keys.UP, keys.DOWN):
        r = (r + (-1 if key == keys.UP else 1)) % len(ROWS)
        c = min(c, len(ROWS[r]) - 1)
    return r, c


def keyboard_screen(app, every=REFRESH):
    """Until esc. Never sends anything but status calls."""
    poller = Poller(app.settings.keyboard_server, every)
    cursor = app.cursors.get("keyboard", (1, 0))
    if not (isinstance(cursor, (tuple, list)) and len(cursor) == 2
            and 0 <= cursor[0] < len(ROWS) and 0 <= cursor[1] < len(ROWS[cursor[0]])):
        cursor = (1, 0)
    hints = Hints(app)
    seen, dirty, size = -1, True, None
    asked, frame = False, None
    try:
        while True:
            if poller.seen != seen:
                seen, dirty = poller.seen, True
                if poller.answer is not None:
                    app.keyboard_app = poller.answer         # the menu's status line too
            if console.size() != size:
                size, dirty = console.size(), True
            if dirty:
                st = app.styles()
                lines, focus = draw(app, st, poller.answer, cursor)
                frame = (lines, focus, hints.lines(st, HINTS))
                console.present(*frame)
                dirty = False
            if not asked and seen > 0:           # app.keyboard_app is that answer now
                asked = True                    # the app's suggestions, once, as it opens
                if keyboard_suggest.ask(app, lambda: console.present(*frame)):
                    dirty = True
            if not keys.key_ready():
                time.sleep(POLL)
                continue
            key = keys.read_key(resize=False)
            dirty, handled = True, True
            if key in (keys.ESC, keys.CTRL_C):
                return None
            if key in (keys.LEFT, keys.RIGHT, keys.UP, keys.DOWN):
                cursor = move(cursor, key)
            elif keys.is_char(key) and place(key) is not None:
                cursor = place(key)
            else:
                handled = False
            hints.note(key, handled)
    finally:
        poller.stop()
        app.cursors["keyboard"] = tuple(cursor)
