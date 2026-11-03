"""The keyboard app's suggestions, asked at a calm moment (the results
after a test, or as the keyboard screen opens; never during a test).

The app doesn't change some things by itself: it logs them and waits for a
yes or no. Each suggestion in `patterns.suggestions` gets a box of its own,
in the start-up question's style (anywhere.pick_dialog); the answer goes to
the app in the background (keyboard_app.answer_suggestion). Esc answers
nothing: it's asked again next time. A key answered isn't asked again
while the app still lists it (the reply may not have landed yet).

    doubles: typed twice from one press (a bounce) -> the bounce guard,
             group 1, or group 2 (deeper, for the big keys)
"""

from .. import keyboard_app
from .anywhere import pick_dialog

# the big keys: their bounce guard is group 2, the deeper one
BIG = {"SPACE", "LSHIFT", "RSHIFT", "SHIFT", "ENTER", "RETURN", "BKSP", "BACKSPACE"}


def _id(key):
    return key.strip().upper().replace(" ", "") if isinstance(key, str) else None


def listed(answer):
    """The suggestions in an answer that can be asked (a key, a why)."""
    if answer is None or not answer.ok:
        return []
    pat = answer.state.get("patterns")
    sugs = pat.get("suggestions") if isinstance(pat, dict) else None
    if not isinstance(sugs, list):
        return []
    return [x for x in sugs if isinstance(x, dict) and _id(x.get("key"))
            and isinstance(x.get("why"), str)]


def pending(app):
    """The suggestions still to ask about. Keys answered and no longer listed
    are forgotten, so a new suggestion for them is asked again."""
    sugs = listed(app.keyboard_app)
    app.keyboard_answered &= {_id(x["key"]) for x in sugs}
    return [x for x in sugs if _id(x["key"]) not in app.keyboard_answered
            and question(x) is not None]


def question(sug):
    """(title, answers, preselected, hotkeys, groups) for a box, or None for
    a kind minitype doesn't know. groups[k] is answer k's bounce guard group
    (None: accept with no group), False for no."""
    key, n = sug["key"], sug.get("count")
    times = f" {n}x" if type(n) is int and n > 0 else ""
    if sug["why"] == "doubles":
        return (f"{key} typed twice from one press{times} (a bounce).\n"
                f"Put it in the keyboard's bounce guard?",
                ("group 1", "group 2", "no"), 1 if _id(key) in BIG else 0,
                ("1", "2", "n"), (1, 2, False))
    return None


def ask(app, redraw):
    """Ask about each pending suggestion, one box each, over redraw(); stop
    at esc (later). Returns the (key, accept, group) answers sent."""
    if not app.settings.keyboard_learn:
        return []
    sent = []
    for sug in pending(app):
        title, answers, choice, hotkeys, groups = question(sug)
        k = pick_dialog(app, redraw, title, answers, choice, hotkeys)
        if k is None:
            break                                  # esc: ask again later
        group = groups[k]
        accept = group is not False
        app.keyboard_answered.add(_id(sug["key"]))
        keyboard_app.answer_suggestion(sug["key"], accept, group if accept else None,
                                       app.settings.keyboard_server, lambda a: _landed(app, a))
        sent.append((sug["key"], accept, group if accept else None))
    return sent


def _landed(app, answer):
    if answer.ok:
        app.keyboard_app = answer
        app.keyboard_patterns = answer.state.get("patterns")
