import os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.terminal import style, console
from minitype.context import App
from minitype.ui import settings_menu as sm

app = App()
s = app.settings
rows = {it.label: it for it in sm.build_items(app) if it.section != "ui"}   # the originals
row = rows["theme background"]
assert row.section == "theme" and row.value() == "theme" and row.preview
row.action(); assert s.theme_background == "always"
row.action(); assert s.theme_background == "off"
row.action(); assert s.theme_background == "theme"
for label, field in (("gradients", "theme_gradient"),
                     ("gradient flow", "theme_flow"), ("heat", "theme_heat"),
                     ("bold / italic", "theme_text_style")):
    row = rows[label]
    assert row.section == "theme" and row.value() == "on" and getattr(s, field), label
    assert row.preview, f"{label} shows the sample line"
    row.action(); assert row.value() == "off" and not getattr(s, field), label
    row.back(); assert getattr(s, field), label

# background
s.theme = "aurora"
assert app.styles().background and console._background
s.theme_background = "off"
assert app.styles().background == "" and console._background == ""
s.theme_background = "theme"
# always: themes without a background get one from their colours, a dark
# one for dark themes and a pale one for light ones; their own stays
aurora_bg = app.styles().background
s.theme_background = "always"
assert app.styles().background == aurora_bg
for t, dark in (("ocean", True), ("default", True), ("paper", False), ("high contrast light", False)):
    s.theme = t
    st = app.styles()
    assert st.background and console._background == st.background, t
    lum = style.luminance(style.rgb_of_code(st.background, 48))
    assert (lum < 0.2) if dark else (lum > 0.8), (t, lum)
s.theme = "mono"
assert app.styles().background == "", "mono keeps the terminal's own"
s.theme_background = "theme"
s.theme = "ocean"
assert app.styles().background == ""
s.theme = "aurora"

# gradient: off means plain text colour; the rest of the theme stays
st_on = app.styles()
s.theme_gradient = False
st_off = app.styles()
assert st_off.typed(0, 0) == st_off.ok and st_on.typed(0, 0) != st_on.ok
assert st_off.background == st_on.background and st_off.title == st_on.title
s.theme_gradient = True

# flow: off keeps the gradient but stops it moving
s.theme = "rainbow"
assert app.styles().typed(0, 0, now=0) != app.styles().typed(0, 0, now=1)
s.theme_flow = False
st = app.styles()
assert st.typed(0, 0, now=0) == st.typed(0, 0, now=1) and st.typed(0, 0) != st.typed(1, 0)
s.theme_flow = True

# heat
s.theme = "ember"
assert app.styles().typed(0, 0, combo=0) != app.styles().typed(0, 0, combo=20)
s.theme_heat = False
st = app.styles()
assert st.typed(0, 0, combo=0) == st.typed(0, 0, combo=20)
s.theme_heat = True

# bold / italic
assert app.styles().typed(0, 0).startswith(style.BOLD)
s.theme_text_style = False
assert not app.styles().typed(0, 0).startswith(style.BOLD)
s.theme = "vaporwave"
assert style.ITALIC not in app.styles().typed(0, 0)
s.theme_text_style = True
assert app.styles().typed(0, 0).startswith(style.ITALIC)

# everything off: a complex theme looks like a plain one, colours kept
s.theme_background = "off"
for f in ("theme_gradient", "theme_flow", "theme_heat", "theme_text_style"):
    setattr(s, f, False)
for t in sm.style.theme_names() if hasattr(sm, "style") else style.theme_names():
    s.theme = t
    st = app.styles()
    assert st.background == "" and st.typed(3, 2, combo=40, now=5) == st.ok, t
# the sample line follows the toggles
s.theme = "rainbow"
plain = rows["gradients"].preview()[0]
s.theme_gradient = True
fancy = rows["gradients"].preview()[0]
assert plain != fancy and re.sub(r"\x1b\[[0-9;]*m", "", plain) == __import__("minitype.ui.preview", fromlist=["SAMPLE"]).SAMPLE

# saved and loaded
app.save()
b = App(); b.load()
assert b.settings.theme_gradient and not b.settings.theme_heat and b.settings.theme_background == "off"
print("ALL OK")
