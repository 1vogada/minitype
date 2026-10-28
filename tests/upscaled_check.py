"""The upscaled art style: every picture's hand-drawn scene drawn in
truecolour (every cell its exact colours) at the revamp sizes and bigger
ones for big windows (tools/make_art_upscaled.py).
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

# the style is built picture by picture (tools/make_art_upscaled.py writes
# after each); the ones in truecolour are checked in full, the rest only
# have to fall back to revamp cleanly (below)
built = [n for n in sorted(UPSCALED) if make_art_upscaled.done(UPSCALED[n])]
assert built, "no truecolour pictures built"
for name in built:
    big = upscaled(name)
    small = revamp(name)
    assert [len(p.lines) for p in big] == list(make_art_upscaled.SIZES), name
    assert {len(p.lines) for p in small} <= {len(p.lines) for p in big},         (name, "every revamp size too, so a normal window gets it as well")
    for p in big:
        assert len({len(l) for l in p.lines}) == 1, (name, "ragged rows")
        assert p.rgb and p.ext, (name, "truecolour, and the scene drawn on beyond it")
        fg, bg = p.rgb
        assert all(c is None or (len(c) == 3 and all(0 <= v <= 255 for v in c))
                   for rows in (fg, bg) for row in rows for c in row), name
        # every cell shows something: ink, or a background behind a blank
        assert all(f is not None or b is not None for frow, brow in zip(fg, bg)
                   for f, b in zip(frow, brow)), (name, "no holes")
        width = len(p.lines[0])
        # at the smallest size a tall subject (the cactus, the reef's
        # jellyfish) can reach every row, as revamp's cactus already does
        assert len(p.lines) <= 16 or sum(k < width for k in p.keep) < len(p.lines), \
            (name, "not all focus")
    # truecolour: far more colours than the theme's 70 - except the pictures
    # flat by design (matrix code rain, the paper plane, phosphor terminal)
    if name not in ("rain", "plane", "terminal"):
        assert len({c for row in big[2].rgb[1] + big[2].rgb[0] for c in row if c}) > 150, name
    # mostly blocks: a scene's own text is a sprinkle, not the picture
    cells = "".join(big[0].lines)
    assert sum(ch in BLOCKS for ch in cells) > 0.6 * len(cells), name

# every theme asks for the style and gets the big sizes, then the revamp ones
for theme in style.theme_names():
    if theme == "mono":
        continue
    name = THEME_ART[theme]
    pieces = style.theme_art(theme, "upscaled")
    want = art_mod._upscaled_or_revamp(name)
    assert any(len(p.lines) <= 16 for p in want), (theme, "something for a small window")
    assert [p.lines for p in pieces[:len(want)]] == [p.lines for p in want], theme
    assert [p.lines for p in resolve(name, "upscaled")[:len(want)]] == [p.lines for p in want]
print("ALL OK")
