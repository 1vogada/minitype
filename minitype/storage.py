"""Files minitype keeps, all in the app's own folder (next to README.md) so
you can see them:

    settings.json   your settings, always kept up to date
    save.json       history, personal bests, word timings and learn progress;
                    only written once you switch "save to disk" on, which
                    creates it. Switching it off deletes it again.

Set MINITYPE_DIR to keep them somewhere else. If the app folder can't be
written to (an installed copy, say), they go to %LOCALAPPDATA%\\minitype.

Older versions kept the save in %LOCALAPPDATA%\\minitype (save.json, or
learn.json before that). If there's no save here yet, that one is read,
written here on the next save, and removed.
"""

import json
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE = "save.json"
SETTINGS = "settings.json"


def _old_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "minitype")


def data_dir():
    d = os.environ.get("MINITYPE_DIR")
    if d:
        return d
    return APP_DIR if os.access(APP_DIR, os.W_OK) else _old_dir()


def path(name=SAVE):
    return os.path.join(data_dir(), name)


def _legacy():
    """Saves from older versions, newest first, that aren't in data_dir."""
    old = _old_dir()
    if os.path.normcase(old) == os.path.normcase(data_dir()):
        return [os.path.join(old, "learn.json")]
    return [os.path.join(old, SAVE), os.path.join(old, "learn.json")]


def _existing_legacy():
    return [p for p in _legacy() if os.path.isfile(p)]


def _read_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _write_json(p, data):
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, p)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- settings

def read_settings():
    return _read_json(path(SETTINGS))


def write_settings(data):
    _write_json(path(SETTINGS), data)


# ---------------------------------------------------------------- save file

def enabled():
    return os.path.isfile(path()) or bool(_existing_legacy())


def write(data):
    if not enabled():
        return
    if _write_json(path(), data):
        for p in _existing_legacy():     # moved here now, drop the old copy
            try:
                os.remove(p)
            except OSError:
                pass


def read():
    """The saved data, or None if there is none or it can't be read."""
    for p in [path()] + _existing_legacy():
        data = _read_json(p)
        if data is not None:
            return data
    return None


def toggle(data):
    if enabled():
        for p in [path()] + _existing_legacy():
            try:
                os.remove(p)
            except OSError:
                pass
        return
    try:
        os.makedirs(data_dir(), exist_ok=True)
        open(path(), "w").close()
    except OSError:
        return
    write(data)
