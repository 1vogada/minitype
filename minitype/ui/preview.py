"""A sample line of a theme, drawn by the real typing renderer, for the
settings rows and the theme creator."""

import time

from ..engine.render import Painter, rows

SAMPLE = "the quick brown fox jumps"
SAMPLE_TYPED = ["the", "quick", "bro"]    # typed so far; the caret is on "w"
SAMPLE_WRONG = {(1, 1)}                   # the "u" of quick was a mistake
SAMPLE_COMBO = 12


def theme_sample(app, custom=None):
    """The current theme as the typing screen draws it: typed letters
    (gradient, heat, style, pop, fade), a mistake, the caret and untyped
    text (glitch), on one row or two with bounce. `custom` previews a
    (palette, effects) draft instead."""
    st = app.styles(custom)
    words = SAMPLE.split()
    typed = SAMPLE_TYPED + [""] * (len(words) - len(SAMPLE_TYPED))
    p = Painter(st, app.settings, words, typed, len(SAMPLE_TYPED) - 1, (),
                False, False, SAMPLE_WRONG, SAMPLE_COMBO, time.time())
    return rows(p, p.span(0, len(words)))
