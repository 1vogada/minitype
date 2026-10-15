"""The upscaled art style: every picture's hand-drawn scene drawn bigger
for big windows (tools/make_art_upscaled.py), then its revamp sizes, so a
window too small for the big ones still gets the picture.
"""
import os
import sys
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path[:0] = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")]

from minitype.config import ART_STYLES                       # noqa: E402
from minitype.terminal import art as art_mod, style          # noqa: E402
from minitype.terminal.art import THEME_ART, resolve, revamp, upscaled   # noqa: E402
import make_art_upscaled                                     # noqa: E402

UPSCALED = art_mod._UPSCALED          # the stored data, as the loader sees it

assert "upscaled" in ART_STYLES and "upscaled" in art_mod.ART_STYLES
assert ART_STYLES[0] == "revamp", "revamp is still the default"

# drawn like the revamp pictures: blocks, shades, braille, and only the
# text a scene asks for itself (stars, sparkles, falling code)
BLOCKS = set(" █▀▄▌▐▁▂▃▅▆▇▔░▒▓▘▝▖▗▚▞▛▜▙▟▎▊▕") | {chr(c) for c in range(0x2800, 0x2900)}

assert set(UPSCALED) == set(art_mod._REVAMP), "every picture has its upscaled sizes"
for name in sorted(UPSCALED):
    big = upscaled(name)
    small = revamp(name)
    assert [len(p.lines) for p in big] == list(make_art_upscaled.SIZES), name
    assert len(big[-1].lines) > len(small[0].lines), (name, "bigger than the revamp sizes")
    for p in big:
        assert len({len(l) for l in p.lines}) == 1, (name, "ragged rows")
        assert p.back_parts and p.ext, (name, "backgrounds and the scene drawn on beyond it")
        assert set("".join(p.parts)) <= set("dtexagw "), name
        assert all((ch == " ") == (q == " ") for l, r in zip(p.lines, p.parts)
                   for ch, q in zip(l, r)), name
        width = len(p.lines[0])
        assert sum(k < width for k in p.keep) < len(p.lines), (name, "not all focus")
    # mostly blocks: a scene's own text is a sprinkle, not the picture
    cells = "".join(big[0].lines)
    assert sum(ch in BLOCKS for ch in cells) > 0.6 * len(cells), name

# every theme asks for the style and gets the big sizes, then the revamp ones
for theme in style.theme_names():
    if theme == "mono":
        continue
    name = THEME_ART[theme]
    pieces = style.theme_art(theme, "upscaled")
    want = upscaled(name) + revamp(name)
    assert [p.lines for p in pieces[:len(want)]] == [p.lines for p in want], theme
    assert [p.lines for p in resolve(name, "upscaled")[:len(want)]] == [p.lines for p in want]
print("ALL OK")
