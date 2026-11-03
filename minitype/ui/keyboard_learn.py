"""Learn as you type on a magnetic keyboard (see keyboard_app): the
question at start-up, switching it from settings, and the status line.

At start, with "ask at start" on, a box asks whether to learn; the answer
becomes the keyboard learn setting and goes to the keyboard app. With it
off, the setting goes to the app as it is, unasked. Changing the setting
sends it straight away. Nothing else is ever asked: the app applies what it
learns by itself.

With it on, each test's keystrokes go to the app as the test ends
(runner._send_keystrokes, in the background); its answer may say what it made
of your mistakes ("patterns"), and the results show that in a line or two.
"""

import time

from .. import keyboard_app
from ..terminal import console
from ..terminal.style import RESET
from .anywhere import ask_dialog

QUESTION = "Learn your keyboard's actuation while you type?"
WAIT = 0.3          # seconds the results wait for the keystrokes' answer, at most
SOME = 2            # a pattern counts from this many
WIDTH = 76          # a pattern line is cut to this
KEY_WHY = (("misses", "often missed (pressed too light)"),
           ("ghosts", "typed by brushing it"),
           ("doubles", "typed twice (bounce)"))


def send(app):
    """Tell the keyboard app what the setting says; keep its answer."""
    s = app.settings
    app.keyboard_app = keyboard_app.switch(s.keyboard_learn, s.keyboard_server)
    return app.keyboard_app


def refresh(app, wait=WAIT):
    """The results screen: wait (WAIT at most) for the test's keystrokes'
    answer, which is the status too; without one, one status call. Only when
    learning is meant to be on, so someone without the keyboard never waits."""
    s = app.settings
    if not s.keyboard_learn:
        return app.keyboard_app
    sent = app.keyboard_sent
    if sent is not None and sent[1] is not None:
        sent[1].join(max(0.0, sent[0] + wait - time.time()))
        if not sent[1].is_alive() and app.keyboard_patterns is not None:
            return app.keyboard_app            # answered: no second call
    app.keyboard_app = keyboard_app.status(s.keyboard_server)
    if app.keyboard_app.ok:                    # status answers carry the patterns too
        app.keyboard_patterns = app.keyboard_app.state.get("patterns")
    return app.keyboard_app


def status_line(app, st):
    """The dim status line, or None while keyboard learn is off."""
    if not app.settings.keyboard_learn or app.keyboard_app is None:
        return None
    return f"{st.dim}{app.keyboard_app.line()}{RESET}"


def pattern_lines(app, st):
    """The dim lines under the status line: what the app made of the last
    test's mistakes (pattern_text), none when it said nothing."""
    if not app.settings.keyboard_learn:
        return []
    return [f"{st.dim}{line}{RESET}" for line in pattern_text(app.keyboard_patterns)]


def pattern_text(patterns):
    """At most two lines from the app's "patterns": the worst key and the most
    mixed-up pair ("keyboard: 8 often missed (pressed too light) · 8→9 mixed
    up 4x"), then what it changed ("keyboard: lowered 8 by 0.1 mm")."""
    if not isinstance(patterns, dict):
        return []
    found = []
    worst = None                                  # (count, key, why)
    for k in _dicts(patterns.get("keys")):
        for field, why in KEY_WHY:
            n = _n(k.get(field))
            if n >= SOME and (worst is None or n > worst[0]) and _key(k.get("key")):
                worst = (n, _key(k.get("key")), why)
    if worst:
        found.append(f"{worst[1]} {worst[2]}")
    pair = max(((_n(p.get("count")), _key(p.get("expected")), _key(p.get("typed")))
                for p in _dicts(patterns.get("pairs"))), default=None)
    if pair and pair[0] >= SOME and pair[1] and pair[2]:
        found.append(f"{pair[1]}→{pair[2]} mixed up {pair[0]}x")
    fast = patterns.get("fastErrorShare")
    if found and isinstance(fast, (int, float)) and not isinstance(fast, bool) and fast >= 0.6:
        found.append("most when typing fast")
    changed = []
    for a in _dicts(patterns.get("adjusted"))[:3]:
        mm, key = a.get("changeMm"), _key(a.get("key"))
        said = guard_text(a)
        if key and said:
            changed.append(f"{key}: {said}")
        elif key and isinstance(mm, (int, float)) and not isinstance(mm, bool) and round(mm, 2):
            changed.append(f"{'lowered' if mm < 0 else 'raised'} {key} by {abs(round(mm, 2)):g} mm")
    return [_fit(part) for part in (found, changed) if part]


GUARD = (("accepted", "put in the bounce guard (you said yes)"),
         ("dismissed", "bounce guard dismissed (you said no)"),
         ("suggested", "suggested for the bounce guard"))


def guard_text(a):
    """What an `adjusted` entry about a suggestion says (accepted, dismissed
    or suggested), or None for an actuation change."""
    texts = GUARD
    for field, text in texts:
        if a.get(field) is True:
            return text
    return None


def _fit(parts):
    """ "keyboard: a · b · c", leaving out the parts after the first that
    don't fit in WIDTH."""
    line = "keyboard: " + parts[0]
    for p in parts[1:]:
        if len(line) + 3 + len(p) <= WIDTH:
            line += " · " + p
    return keyboard_app._short(line, WIDTH)


def _dicts(v):
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _n(v):
    return v if type(v) is int and v > 0 else 0


def _key(v):
    """A key as the line shows it."""
    if not isinstance(v, str) or not v or len(v) > 12:
        return None
    return {" ": "space", "": "backspace"}.get(v, v)


def at_start(app):
    """The start-up question (if asked for), then the setting to the app."""
    s = app.settings
    if s.keyboard_ask:
        h = console.size()[1]
        st = app.styles()
        behind = ["", f"  {st.title}minitype{RESET}"] + [""] * max(0, h - 2)
        answer = ask_dialog(app, lambda: console.present(behind), QUESTION,
                            ("on", "off"), choice=0 if s.keyboard_learn else 1, esc=None)
        if answer is not None and answer != s.keyboard_learn:
            s.keyboard_learn = answer
            app.save_settings()
    return send(app)
