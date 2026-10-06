import json, os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import style, console, keys
from minitype.context import App
from minitype.ui import settings_menu as sm

names = style.theme_names()
for t in ("dracula", "nord", "gruvbox", "solarized", "monokai", "catppuccin",
          "rose pine", "matrix", "amber", "paper", "high contrast"):
    assert t in names, t
    s = style.Styles(t)
    assert s.ok.startswith("\x1b[38;5;") and s.bad != s.ok and not s.quiet
assert len(names) == 46 and names[-1] == "mono"
for t in ("cyan", "magenta", "green", "orange", "light"):
    assert f"high contrast {t}" in names, t
# the dark high-contrast ones share bright white text and pure red errors
for t in ("high contrast", "high contrast cyan", "high contrast magenta",
          "high contrast green", "high contrast orange"):
    s = style.Styles(t)
    assert s.ok == "\x1b[38;5;231m" and s.bad == "\x1b[38;5;196m", t
accents = {style.Styles(t).title for t in names if t.startswith("high contrast")}
assert len(accents) == 6, "each has its own accent"
light = style.Styles("high contrast light")
assert light.ok == "\x1b[38;5;16m", "black text for light terminals"
# accent letters: typed text takes the accent colour, nothing else changes
for t in ("dracula", "nord", "high contrast cyan"):
    off, on = style.Styles(t), style.Styles(t, accent_text=True)
    assert on.ok == off.title != off.ok, t
    assert (on.dim, on.bad, on.extra, on.title) == (off.dim, off.bad, off.extra, off.title)
assert style.Styles("mono", accent_text=True).ok == "", "no colour in mono"
assert style.Styles("dracula", "disguised", True).ok == "", "no colour when disguised"
assert style.Styles("mono").quiet
assert style.Styles("nope").ok == style.THEMES["default"][1], "unknown falls back"

# the example file is valid and loads
example = os.path.join(os.path.dirname(os.path.dirname(style.__file__)), "..", "themes.example.json")
with open(example, encoding="utf-8") as f:
    ex = json.load(f)
path = os.path.join(HOME, "themes.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(ex, f)
assert style.theme_names()[len(names):len(names) + 2] == ["my theme", "true colour"]
s = style.Styles("my theme")
assert s.dim == "\x1b[38;5;240m" and s.title == "\x1b[38;5;81m"
s = style.Styles("true colour")
assert s.ok == "\x1b[38;2;230;230;230m" and s.bad == "\x1b[38;2;255;107;107m"
assert style.custom_error() == ""

# mistakes: the broken theme is skipped, the good one stays, and it says why
time.sleep(0.02)
with open(path, "w", encoding="utf-8") as f:
    json.dump({"good": ex["my theme"],
               "missing": {"dim": 1},
               "badhex": dict(ex["my theme"], text="#zzzzzz"),
               "big": dict(ex["my theme"], text=300),
               "nord": ex["my theme"]}, f)
os.utime(path, (time.time() + 2, time.time() + 2))
assert style.theme_names()[len(names):] == ["good"], style.theme_names()
err = style.custom_error()
for name in ("missing", "badhex", "big", "nord"):
    assert name in err, (name, err)
# not even json
with open(path, "w") as f:
    f.write("{ nope")
os.utime(path, (time.time() + 4, time.time() + 4))
assert style.theme_names() == names and style.custom_error()
# removing the file removes the themes
os.remove(path)
assert style.theme_names() == names and style.custom_error() == ""

# settings keep a custom theme across a restart, and drop one that's gone
with open(path, "w", encoding="utf-8") as f:
    json.dump(ex, f)
app = App()
app.settings.theme = "true colour"
app.save()
b = App(); b.load()
assert b.settings.theme == "true colour"
os.remove(path)
c = App(); c.load()
assert c.settings.theme == "default", "a theme that no longer exists isn't applied"

# the settings row cycles through all of them, custom ones included
with open(path, "w", encoding="utf-8") as f:
    json.dump(ex, f)
app = App()
row = next(it for it in sm.build_items(app) if it.label == "theme")
seen = []
for _ in range(len(style.theme_names())):
    row.action()
    seen.append(app.settings.theme)
assert set(seen) == set(style.theme_names()) and "true colour" in seen
assert "themes.json" in row.help_text()
# the toggle is in the look section and reaches what the test screen draws with
items = sm.build_items(app)
acc = next(it for it in items if it.label == "accent letters")
assert acc.section == "theme" and acc.value() == "off"
app.settings.theme = "nord"
before = app.styles().ok
acc.action()
assert app.settings.accent_text and acc.value() == "on"
assert app.styles().ok == app.styles().title != before
acc.back()
assert app.styles().ok == before
print("ALL OK")
