import os, re, tempfile
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.ui import settings_menu as sm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
SIZE = [80, 30]
console.size = lambda: tuple(SIZE)


def run(presses, style="list", tabs="off", app=None):
    """Type into the settings menu; return the last frame as text, and the app."""
    app = app or App()
    app.settings.art = "off"             # plain help lines (boxed with art: help_box_check)
    app.settings.ui_style, app.settings.sidebar_tabs = style, tabs
    frames = []
    seq = iter(presses + [keys.CTRL_C])
    with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "present",
                              lambda lines, focus=None, pinned=(): frames.append(lines)):
        sm.settings_menu(app)
    # the frame before ctrl-c
    return strip("\n".join(frames[-1])), app


def labels(frame):
    return [re.sub(r"\s{2,}.*", "", l[3:]).strip() for l in frame.split("\n")
            if l.startswith(" > ") or l.startswith("   ") and not l.startswith("    ")]


typing = list

# no hotkeys any more: rows have no key column, and letters don't toggle anything
f, app = run(typing("p"))
assert app.settings.punctuation is False, "p no longer toggles punctuation"
f0, _ = run([])
assert " > difficulty" in f0, f0.split("\n")[3:6]

# plain search: only names containing the text stay; search bar hidden
f, _ = run(typing("car"))
print("== 'car' ==\n" + f)
assert "caret" in f and "pace caret" in f and "caret effect" in f
shown = [re.sub(r"\s{2,}.*", "", l[3:]).strip() for l in f.split("\n")
         if re.match(r"^ [> ] \S", l)]
assert set(shown) == {"caret", "pace caret", "caret effect"}, shown
assert "search  car" in f, "any search shows the bar"
# sections with no matches disappear, matches keep their headings
assert "typing screen" in f and "rules" not in f.split("\n")

# several words must all be in the name
f, _ = run(typing("pace car"))
rows = [l for l in f.split("\n") if re.match(r"^ [> ] \S", l)]
assert [r[3:].split("  ")[0] for r in rows] == ["pace caret"], rows

# backspace without # clears everything at once
f, _ = run(typing("caret") + [keys.BACKSPACE])
assert "difficulty" in f and "theme" in f, "whole search cleared"

# #tags: tag or section name; search bar shows; backspace deletes one char
f, _ = run(typing("#colour"))
print("== '#colour' ==\n" + f)
assert "search  #colour" in f and "theme" in f and "key heatmap" in f
assert "difficulty" not in f
f, _ = run(typing("#look"))
assert "theme" in f and "sound" in f and "difficulty" not in f
f, _ = run(typing("#colourx") + [keys.BACKSPACE])
assert "search  #colour " in f and "theme" in f, "one char deleted, bar still visible"
# removing the # keeps the bar (there's still a search), then backspace clears it all
f, _ = run(typing("ab#") + [keys.BACKSPACE])
assert "search  ab " in f
f, _ = run(typing("ab#") + [keys.BACKSPACE, keys.BACKSPACE])
assert "difficulty" in f and "search" not in f, "no # left: backspace cleared everything"
# [ and ] never go into the search; they switch sections, search kept
f, app = run(typing("#stats") + ["]", "]", keys.ENTER], style="tabs")   # past the ui tab
assert "search  #stats " in f and "[" not in f.split("\n")[3] and "]" not in f.split("\n")[3], f
assert app.settings.res_chart is False, "] ] moved to results, enter toggled its first row"
f, app = run(typing("#stats") + ["]", "[", keys.ENTER], style="tabs")
assert app.settings.show_timer is False, "[ came back to header"
f, app = run(["]", keys.ENTER], style="list")
assert app.settings.min_wpm == 20, "] jumps to challenges in list style too"
f, app = run([keys.SHIFT_TAB, keys.ENTER], style="tabs")
assert app.settings.daily_goal == 5, "shift-tab wraps back to progress"
# tag plus words: both must hold
f, _ = run(typing("#caret pace"))
assert "pace caret" in f and "ghost" not in f
# nothing matches
f, _ = run(typing("zzz"))
assert "nothing matches" in f
# enter / arrows / left-right work on the filtered list
f, app = run(typing("blind") + [keys.ENTER])
assert app.settings.blind is True
f, app = run(typing("#mistakes") + [keys.DOWN, keys.RIGHT])
assert app.settings.stop_on_error == "letter", app.settings.stop_on_error   # 2nd match
# esc clears the search first, a second esc leaves
app = App()
seq = iter(typing("theme") + [keys.ESC, keys.ESC])
frames = []
with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "present", lambda lines, *a, **k: frames.append(lines)):
    sm.settings_menu(app)                  # returns: second esc left the menu
assert "difficulty" in strip("\n".join(frames[-1]))

# layout updates in every style: tab bar and section buttons shrink to matches
for style, tabs in (("tabs", "off"), ("sidebar", "top"), ("sidebar", "left"), ("sidebar", "off")):
    f, _ = run(typing("#stats"), style=style, tabs=tabs)
    print(f"== #stats, {style}/{tabs} ==\n" + f)
    assert "challenges" not in f and "drills" not in f, (style, tabs)
    assert "typing screen" in f and "results" in f
    # sidebar-left starts on the section buttons: one more enter steps into the rows
    into_rows = [keys.ENTER] if tabs == "left" else []
    f, app = run(typing("#stats") + [keys.TAB, keys.TAB] + into_rows + [keys.ENTER],
                 style=style, tabs=tabs)
    # tab, tab moved past the ui tab to the results section, enter toggled its first row
    assert app.settings.res_chart is False, (style, tabs)
print("ALL OK")
