GRAY = "\x1b[90m"
WHITE = "\x1b[97m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
DARKRED = "\x1b[38;5;88m"
INV = "\x1b[7m"
DIM = "\x1b[2m"
UND = "\x1b[4m"
RESET = "\x1b[0m"


class Styles:
    """Colour codes, or monochrome equivalents when quiet mode is on."""

    def __init__(self, quiet=False):
        self.quiet = quiet
        if quiet:
            self.dim, self.ok, self.bad, self.extra = DIM, "", UND, UND + DIM
        else:
            self.dim, self.ok, self.bad, self.extra = GRAY, WHITE, RED, DARKRED
        self.title = self.ok or WHITE

    def conf_color(self, v):
        """Green at target, yellow getting there, red far off."""
        if self.quiet:
            return ""
        return GREEN if v >= 1 else YELLOW if v >= 0.6 else RED
