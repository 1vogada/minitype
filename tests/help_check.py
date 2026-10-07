import os, re, tempfile
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.ui import settings_menu as sm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
SIZE = [60, 16]
console.size = console.term_size = lambda: tuple(SIZE)
out = []


def run(style, presses):
    app = App()
    app.settings.border = "off"          # rows are parsed by their first columns
    app.settings.art = "off"             # help is plain lines (with art it's boxed: help_box_check)
    app.settings.ui_style = style
    seq = iter(presses + [keys.ESC])
    with mock.patch.object(keys, "read_key", lambda panic=True, resize=True: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        sm.settings_menu(app)
    frame = strip(out[-1].split("\x1b[H")[-1])
    print(f"===== {style}, {SIZE[0]}x{SIZE[1]} =====")
    print(frame)
    return frame


from minitype.ui.settings_menu import build_items
HELP, FIRST = {}, {}
for _it in build_items(App()):
    HELP.setdefault(_it.label, _it.help_text())
    # two rows can share a label ("fade" in effects and in art fade): either help counts
    FIRST.setdefault(_it.label, set()).add(_it.help_text().split()[0])


def check_inline(frame):
    """The selected row is on screen and the next line starts its help."""
    rows = frame.split("\n")
    assert len(rows) <= SIZE[1], len(rows)
    sel = next(i for i, r in enumerate(rows) if r.startswith(" > "))
    label = re.match(r"^ > (.+?)(\s{2,}|$)", rows[sel]).group(1).strip()
    label_col = len(rows[sel]) - len(rows[sel][2:].lstrip()) - 0
    help_col = len(rows[sel + 1]) - len(rows[sel + 1].lstrip())
    assert help_col > label_col and any(w in rows[sel + 1] for w in FIRST[label]), rows[sel:sel + 2]


# every position of a long scrolled list keeps the help under the selection
for n in range(0, 45, 4):
    check_inline(run("list", [keys.DOWN] * n))
# tabs: every tab, a few rows down
for t in range(8):
    check_inline(run("tabs", [keys.TAB] * t + [keys.DOWN] * 2))
# sidebar keeps it in the right-hand panel
f = run("sidebar", [keys.DOWN] * 20)
rows = f.split("\n")
sel = next(i for i, r in enumerate(rows) if r.startswith(" > "))
label = next(l for l in HELP if f" {l}  " in rows[sel])
assert rows[sel].rstrip().endswith(f"| {label}"), rows[sel]
assert HELP[label].split()[0] in "\n".join(rows[sel:sel + 6])
for n in range(0, 45, 4):
    rows = run("sidebar", [keys.DOWN] * n).split("\n")
    sel = next(i for i, r in enumerate(rows) if r.startswith(" > "))
    assert rows[sel].split("| ")[1].strip(), ("panel not beside selection", n, rows[sel])

# narrow: sidebar falls back to list with inline help, long help wraps
SIZE[:] = [30, 12]
f = run("sidebar", [keys.DOWN] * 2)
rows = f.split("\n")
sel = next(i for i, r in enumerate(rows) if r.startswith(" > "))
assert "normal:" in rows[sel + 1] and all(len(r) <= 29 for r in rows), rows
print("ALL OK")
