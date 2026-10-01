GRAY = "\x1b[90m"
WHITE = "\x1b[97m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
DARKRED = "\x1b[38;5;88m"
INV = "\x1b[7m"
DIM = "\x1b[2m"
UND = "\x1b[4m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"


def c256(n):
    return f"\x1b[38;5;{n}m"


# name -> (dim, ok, bad, extra, accent, good, warn)
THEMES = {
    "default": (GRAY, WHITE, RED, DARKRED, WHITE, GREEN, YELLOW),
    "ocean": (c256(67), c256(195), c256(203), c256(131), c256(81), c256(79), c256(221)),
    "forest": (c256(65), c256(194), c256(167), c256(95), c256(114), c256(77), c256(179)),
    "sunset": (c256(96), c256(224), c256(197), c256(125), c256(215), c256(150), c256(222)),
    "mono": None,
}


class Styles:
    """Colour codes for the current theme. The mono theme, and the disguised
    lowkey mode, use only dim/underline so nothing on screen is coloured."""

    def __init__(self, theme="default", lowkey="off"):
        self.lowkey = lowkey
        self.quiet = theme == "mono" or lowkey == "disguised"
        if self.quiet:
            self.dim, self.ok, self.bad, self.extra = DIM, "", UND, UND + DIM
            self.title = "" if lowkey == "disguised" else WHITE
            self.good = self.warn = ""
        else:
            (self.dim, self.ok, self.bad, self.extra,
             self.title, self.good, self.warn) = THEMES.get(theme) or THEMES["default"]

    def conf_color(self, v):
        """Good at target, warning getting there, bad far off."""
        if self.quiet:
            return ""
        return self.good if v >= 1 else self.warn if v >= 0.6 else self.bad
