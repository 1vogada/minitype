"""Learn progress on disk. Progress is only written if you switched saving
on, which creates the file. Switching it off deletes the file again."""

import json
import os


def path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "minitype", "learn.json")


def enabled():
    return os.path.isfile(path())


def write(data):
    if not enabled():
        return
    try:
        with open(path(), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def read():
    """The saved data, or None if there is none or it can't be read."""
    try:
        with open(path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def toggle(data):
    p = path()
    if enabled():
        try:
            os.remove(p)
        except OSError:
            pass
        return
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
    except OSError:
        return
    write(data)
