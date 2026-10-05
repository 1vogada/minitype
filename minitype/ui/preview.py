"""A sample line of a theme, drawn by the real typing renderer, for the
settings rows and the theme creator."""

import time

from ..engine.render import Painter, rows

SAMPLE = "the quick brown fox jumps"
SAMPLE_TYPED = ["the", "quick", "bri"]    # typed so far; the caret is on "w"
# the "u" of quick was mistyped as "y" and fixed; the "o" of brown is
# still wrong (an "i" was typed)
SAMPLE_WRONG = {(1, 1), (2, 2)}
SAMPLE_TYPOS = {(1, 1): "y", (2, 2): "i"}
SAMPLE_COMBO = 12


def theme_sample(app, custom=None):
    """The current theme as the typing screen draws it: typed letters
    (gradient, heat, style, pop, fade), a fixed mistake and a live one (as
    corrected letters and indicate typos say), the caret and untyped text
    (glitch), on one row or more with bounce and typos below. `custom`
    previews a (palette, effects) draft instead."""
    st = app.styles(custom)
    words = SAMPLE.split()
    typed = SAMPLE_TYPED + [""] * (len(words) - len(SAMPLE_TYPED))
    p = Painter(st, app.settings, words, typed, len(SAMPLE_TYPED) - 1, (),
                False, False, SAMPLE_WRONG, SAMPLE_COMBO, time.time(),
                SAMPLE_TYPOS)
    return rows(p, p.span(0, len(words)))
