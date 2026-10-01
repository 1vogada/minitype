"""The save file. Nothing is written unless you switched saving on, which
creates the file. Switching it off deletes the file again.

Older versions kept only learn progress, in learn.json. That file still
counts as saving being on, is read if there's no newer save, and is
replaced by save.json on the next write.
"""

import json
import os


def _dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "minitype")


def path():
    return os.path.join(_dir(), "save.json")


def _legacy():
    return os.path.join(_dir(), "learn.json")


def enabled():
    return os.path.isfile(path()) or os.path.isfile(_legacy())


def write(data):
    if not enabled():
        return
    try:
        with open(path(), "w", encoding="utf-8") as f:
            json.dump(data, f)
        if os.path.isfile(_legacy()):
            os.remove(_legacy())
    except OSError:
        pass


def read():
    """The saved data, or None if there is none or it can't be read."""
    for p in (path(), _legacy()):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except (OSError, ValueError):
            continue
    return None


def toggle(data):
    if enabled():
        for p in (path(), _legacy()):
            try:
                os.remove(p)
            except OSError:
                pass
        return
    try:
        os.makedirs(_dir(), exist_ok=True)
        open(path(), "w").close()
    except OSError:
        return
    write(data)
