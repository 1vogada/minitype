"""The upscaled art style: stored data, glyphs, and the fallback.

The style is built one picture at a time (tools/make_art_upscaled.py), so
this checks the pictures that exist rather than assuming all of them do.
"""
import os
import re
import sys
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path[:0] = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")]

from minitype.config import ART_STYLES                       # noqa: E402
from minitype.terminal import art as art_mod, style          # noqa: E402
from minitype.terminal.art import ART, THEME_ART, resolve, revamp, upscaled   # noqa: E402

UPSCALED = art_mod._UPSCALED          # the stored data, as the loader sees it

assert "upscaled" in ART_STYLES and "upscaled" in art_mod.ART_STYLES
assert ART_STYLES[0] == "revamp", "revamp is still the default"

# only the block / braille set may be invented: a cell must not draw random
# text, except for a glyph the scene itself asked for (stars, sparkles)
ALLOWED = set(" █▀▄▌▐▁▂▃▅▆▇▔░▒▓")
ALLOWED |= set("▘▝▖▗▚▞▛▜▙▟")
ALLOWED |= {chr(c) for c in range(0x2800, 0x2900)}

assert UPSCALED, "no upscaled pictures are built"

for name in sorted(UPSCALED):
    sizes = upscaled(name)
    assert sizes, name
    big = sizes[0]
    assert len(big.lines) == 28, (name, len(big.lines))
    assert len({len(l) for l in big.lines}) == 1, (name, "ragged rows")
    assert big.back_parts, (name, "upscaled pictures carry background colours")
    for row in big.lines:
        bad = set(row) - ALLOWED - set(".,'`*+~°·oO0v_/\\|-)(][<>")
        assert not bad, (name, "unexpected characters", bad)
    assert set("".join(big.parts)) <= set("dtexagw "), name
    assert set("".join(big.back_parts)) <= set("dtexagw "), name
    assert all((ch == " ") == (p == " ") for l, q in zip(big.lines, big.parts)
               for ch, p in zip(l, q)), name
    # the same subject rule as the other styles: not every row is focus
    width = len(big.lines[0])
    assert sum(k < width for k in big.keep) < len(big.lines), (name, "not all focus")

# every theme can ask for the style: a picture with no upscaled version
# falls back to its revamp picture, so nothing comes back empty
for theme in style.theme_names():
    if theme == "mono":
        continue
    pieces = style.theme_art(theme, "upscaled")
    assert pieces, (theme, "no art at all")
    name = THEME_ART[theme]
    want = upscaled(name) or revamp(name)
    assert [p.lines for p in pieces[:len(want)]] == [p.lines for p in want], theme

# a picture that was never built falls back, and one that was is used as it is
assert resolve(THEME_ART["ocean"], "upscaled"), "the ocean theme resolves"
assert [p.lines for p in style.theme_art("ocean", "upscaled")[:1]] == \
    [p.lines for p in upscaled(THEME_ART["ocean"])[:1]], "ocean draws the upscaled picture"
missing = next(n for n in ART if n not in UPSCALED)
assert upscaled(missing) == [], (missing, "should have no upscaled version")
assert [p.lines for p in resolve(missing, "upscaled")[:1]] == [p.lines for p in revamp(missing)[:1]], \
    (missing, "should fall back to revamp")

print("ALL OK")
