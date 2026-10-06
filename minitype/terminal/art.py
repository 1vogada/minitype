"""Art for the corner of the screen, one picture per theme.

Each comes in several sizes, biggest first, and the biggest that fits on
screen is drawn. The "art style" setting picks which: revamp (the
default: hand-drawn line art over shaded ASCII scenery, one size, from
tools/make_revamp.py into art_revamp.py), blocks (pixel art in
block characters, each cell two colours), detailed (shaded ASCII) or
combined (every technique at once, for the pictures that have it; the
rest show in blocks), made by tools/make_art.py into art_detailed.py and
running across the whole bottom of the screen; on a screen wider than
they were drawn, their scenery grows on to the left (Picture.wider).
Then always the "OG" ones as the fallback: a
large one coloured from the theme's palette (art_large.py) and the small
one-colour one below (ART). THEME_ART says which picture a built-in theme
uses.
A theme in themes.json picks one with "art": a piece's name, or a list of
its own lines; without "art" it uses its base theme's.
"""

import base64
import json
import random
import re
import zlib
from functools import lru_cache
from typing import NamedTuple

from .art_detailed import BLOCKS as _BLOCKS
from .art_detailed import COMBINED as _COMBINED
from .art_detailed import DETAILED as _DETAILED
from .art_large import LARGE as _LARGE
from .art_revamp import REVAMP as _REVAMP


def _art(text):
    """A piece from a block of text: blank first/last lines dropped, the
    common left margin removed."""
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    margin = min((len(l) - len(l.lstrip(" ")) for l in lines if l.strip()), default=0)
    return [l[margin:].rstrip() for l in lines]


ART = {
    "keyboard": _art(r"""
         _____________________
        | [q][w][e][r][t][y] |
        |  [a][s][d][f][g]   |
        |   [z][x][c][v]     |
        |____[__________]____|
"""),
    "island": _art(r"""
             __ _.--..--._ _
          .-' _/  _/\_   \_'-.
         |__ /  _/\__/\_   \__|
            |__/ \_\__/   \_|
                  \__/
                  \__/
            .--._ \__/ _.--.
        ~~~~~~~~~~~~~~~~~~~~~~~~
          ~~~~ ~~~~~ ~~~~ ~~~
"""),
    "pines": _art(r"""
              ^           ^
             /^\    ^    /^\
            /^^^\  /^\  /^^^\
           /^^^^^\/^^^\/^^^^^\
          /^^^^^^/^^^^^\^^^^^^\
             |||    |||    |||
"""),
    "sunset": _art(r"""
             \   |   /
          .   \  |  /   .
            '. .---. .'
        ----- /     \ -----
        ~~~~~~~~~~~~~~~~~~~~~
          ~~~~~~~~~~~~~~~~~
             ~~~~~~~~~~~
"""),
    "stones": _art(r"""
             ,.,;.,;,.
           ,;;;;;;;;;;;,
          (  ;  .  ;  ;  )   ,;,
         ( .  ;    ;  .   ) (   )
          '--------------'   '-'
"""),
    "pine": _art(r"""
                *
               /|\
              /*|*\
             /  |  \
            /*  |  *\
           /____|____\
                |
"""),
    "leaf": _art(r"""
           .     /\     .
              __/  \__     ,
          ,   \        /
              >        <    .
          .  /___    ___\
                 \  /   ,
                  ||
"""),
    "cactus": _art(r"""
                  _              \ | /
                 | |            -- O --
              _  | |  _          / | \
             | | | | | |
             | |_| |_| |
              \___ ___/
                  | |
          ~~~~~~~~| |~~~~~~~~~~~~
"""),
    "flowers": _art(r"""
           _        _        _
         _( )_    _( )_    _( )_
        (_ o _)  (_ o _)  (_ o _)
          (_)      (_)      (_)
           |   ,    |   ,    |
         \\|//   \\ | //   \\|//
"""),
    "jungle": _art(r"""
           \|/   .-.   \|/
          --*-- (o o) --*--
           /|\  | O |  /|\
            |   /'''\   |
         ~~~|~~/     \~~|~~~
"""),
    "blossom": _art(r"""
           @     *     @
         __\\__  @  __//__   *
               \____/   @
           *    ||   __/    @
         _______||__/_________
"""),
    "lavender": _art(r"""
           :    :    :    :
          :*:  :*:  :*:  :*:
          :*:  :*:  :*:  :*:
           |    |    |    |
          \|/  \|/  \|/  \|/
         ~~~~~~~~~~~~~~~~~~~~
"""),
    "snowpeaks": _art(r"""
           *        /\        *
               /\  /  \   *
          *   /  \/ /\ \
             / /\  /  \ \    *
         ___/_/__\/____\_\_____
"""),
    "reef": _art(r"""
           ><(((('>        o
                     o   ><>
          ><>      ,,  0
            ,/\,   \\//      ,
           //  \\   ||      //\\
"""),
    "volcano": _art(r"""
                 (   )
                ( ) ( )
                  \|/
                 /\ /\
                /  V  \
               /  /\   \
          ____/__/  \___\____
"""),
    "bamboo": _art(r"""
           ||   ||      ||
           ||-  ||      ||_
           ||   ||_     ||
          _||   ||      ||
           ||   ||   -  ||
           ||   ||      ||
"""),
    "bat": _art(r"""
           /\                 /\
          / \'._   (\_/)   _.'/ \
         /_.''._'--('.')--'_.''._\
         | \_ / `;=/ " \=;` \ _/ |
          \/ `\__|`\___/`|__/`  \/
                  \(/|\)/
"""),
    "mountains": _art(r"""
            *         .        *
           .      /\      *
              /\ /  \  .
          *  /  \/ /\ \      .
            / /\  /  \ \
         __/_/__\/____\_\______
"""),
    "coffee": _art(r"""
              (  (
               )  )
            ........
            |      |]
            \      /
             `----'
"""),
    "sun": _art(r"""
              \  |  /
            '. .--. .'
           -- (    ) --
            .' '--' '.
              /  |  \
"""),
    "code": _art(r"""
          { }   </>   ( )
           function () {
             return 42;
           }
"""),
    "cat": _art(r"""
            /\_/\
           ( o.o )
            > ^ <
           /     \
          (_______)_/
"""),
    "rose": _art(r"""
               _
             _(_)_
            (_)@(_)
              (_)\
                 |
              \  |
               \ |
                \|
"""),
    "rain": _art(r"""
          1 0 1   0 1   1
          0   1 0 1   0 1
          1 0   1   0 1 0
            1 0   1 0   1
          0   1 0   1 0
"""),
    "monitor": _art(r"""
          ________________
         |  ____________  |
         | |>_          | |
         | |            | |
         | |____________| |
         |________________|
              _|____|_
"""),
    "plane": _art(r"""
          ______
          \     ''--..__
           \_____.---'''
            \  /
             \/
"""),
    "bolt": _art(r"""
               ____
              /   /
             /   /__
            /__    /
              /  /
             / /
            //
"""),
    "rainbow": _art(r"""
             ___________
           /  _______   \
          /  /  ___  \   \
         |  |  /   \  |   |
         |  |  |   |  |   |
"""),
    "party": _art(r"""
          ()     ()     ()
         (  )   (  )   (  )
          ()     ()     ()
           \     |     /
         *  \    |    /   *
          '  \   |   /  .
"""),
    "glitch": _art(r"""
          .-=[  0xDEAD  ]=-.
          |  @#$%  &*!?    |
          |  >_ sys.err    |
          '-=[  F4UL7  ]=-'
"""),
    "bubbles": _art(r"""
               o     O
            O     o     o
           o   ()     O
              o    O     ()
           ()    o    o
"""),
    "aurora": _art(r"""
          ~  ~~~  ~~  ~~~  ~
         ~~~  ~~~~  ~~~  ~~
           ~~   ~~~   ~~
              /\     /\
             /  \/\_/  \
         ___/           \___
"""),
    "grid": _art(r"""
                _.---._
              .'_______'.
             /___________\
            |_____________|
         ____\___________/____
         \    |   |   |   |   /
          \___|___|___|___|__/
"""),
    "fire": _art(r"""
                (  )
               (    )
                )  (
               (_  _)
             \  \/  /
            ==\====/==
"""),
    "jellyfish": _art(r"""
             .-'''-.
            /       \
            \_______/
             ( ) ( )
             ) ( ) (
            (   )   )
"""),
    "terminal": _art(r"""
          +------------------+
          | C:\> _           |
          | READY.           |
          +------------------+
"""),
    "palm": _art(r"""
             __\ | /__
            /  /|\  \
               /|
               ||
               ||
          ~~~~~||~~~~~~~~
"""),
    "lollipop": _art(r"""
              ___
             /   \
            | @ @ |
             \___/
               |
               |
"""),
    "moon": _art(r"""
            *     _.._    .
          .     .' .-'`  *
               /  /     .
           *   |  |   .
               \  '.___.;
            .   '._  _.'  *
"""),
    "summit": _art(r"""
        1 0      /\      0 1
          1    /\/##\     1
        0   /\/ \/###\  0
          /\/  /\  \###\
         /  \ /  \  \###\
        ^ ^ ^^ ^ ^^ ^ ^^ ^
"""),
}

THEME_ART = {
    "default": "keyboard",
    "ocean": "island",
    "forest": "pines",
    "sunset": "sunset",
    "moss": "stones",
    "pine": "pine",
    "autumn": "leaf",
    "desert": "cactus",
    "meadow": "flowers",
    "jungle": "jungle",
    "cherry blossom": "blossom",
    "lavender": "lavender",
    "tundra": "snowpeaks",
    "coral reef": "reef",
    "volcanic": "volcano",
    "bamboo": "bamboo",
    "dracula": "bat",
    "nord": "mountains",
    "gruvbox": "coffee",
    "solarized": "sun",
    "monokai": "code",
    "catppuccin": "cat",
    "rose pine": "rose",
    "matrix": "rain",
    "amber": "monitor",
    "paper": "plane",
    "high contrast": "bolt",
    "high contrast cyan": "bolt",
    "high contrast magenta": "bolt",
    "high contrast green": "bolt",
    "high contrast orange": "bolt",
    "high contrast light": "bolt",
    "rainbow": "rainbow",
    "party": "party",
    "glitch": "glitch",
    "bubbly": "bubbles",
    "aurora": "aurora",
    "synthwave": "grid",
    "ember": "fire",
    "deep sea": "jellyfish",
    "phosphor": "terminal",
    "vaporwave": "palm",
    "candy": "lollipop",
    "midnight": "moon",
    "summit": "summit",
}

ART_NAMES = list(ART)

# the big coloured versions, for terminals with room; ART is the fallback
LARGE = {name: (_art(text), colours) for name, (text, colours) in _LARGE.items()}

PARTS = ("dim", "text", "error", "extra", "accent", "good", "warn")
# the one-letter names art_detailed.py uses for them
PART_LETTERS = dict(zip("dtexagw", PARTS))
LETTER_OF = {part: letter for letter, part in PART_LETTERS.items()}

ART_STYLES = ("revamp", "blocks", "detailed", "og", "combined")


# art_detailed.py stores a character's colour letter and tone (0-9, how
# light it is) as one code: CODES[letter's index * 10 + tone]
CODES = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+"
OG_TONE = "6"                 # the plain colour when shading


class Piece(NamedTuple):
    """One size of a picture: its lines, a colour letter for every
    character (" " for blanks), a tone digit for every character (how
    light it is, for shaded colours), and for every row the column its
    focus starts at. Text may cut into a row left of that, never past it.
    A spanning piece can lose columns on its left to fit the screen.
    Block pieces also have a background colour letter and tone for every
    character (" " for the terminal's own)."""
    lines: tuple
    parts: tuple
    tones: tuple
    keep: tuple
    span: bool = False
    back_parts: tuple = None
    back_tones: tuple = None


def _decode(lead, codes, width):
    """Colour letters and tone digits from a row of codes."""
    idx = [None if c == " " else CODES.index(c) for c in codes]
    parts = "".join(" " if i is None else "dtexagw"[i // 10] for i in idx)
    tones = "".join(" " if i is None else str(i % 10) for i in idx)
    return (" " * lead + parts).ljust(width), (" " * lead + tones).ljust(width)


def _unpack(span, size):
    width, rows, keep = size
    lines, parts, tones, bparts, btones = [], [], [], [], []
    for row in rows:
        lead, text, codes = row[:3]
        lines.append((" " * lead + text).ljust(width))
        p, t = _decode(lead, codes, width)
        parts.append(p)
        tones.append(t)
        if len(row) > 3:
            p, t = _decode(lead, row[3], width)
            bparts.append(p)
            btones.append(t)
    back = (tuple(bparts), tuple(btones)) if bparts else (None, None)
    return Piece(tuple(lines), tuple(parts), tuple(tones), tuple(keep), span, *back)


def _load(packed):
    return json.loads(zlib.decompress(base64.b85decode(packed)))


@lru_cache(maxsize=None)
def detailed(name):
    """A picture's shaded-ASCII sizes, biggest first ([] if it has none)."""
    if name not in _DETAILED:
        return []
    span, sizes = _load(_DETAILED[name])
    return [_unpack(span, size) for size in sizes]


@lru_cache(maxsize=None)
def blocks(name):
    """A picture's block-character sizes, biggest first ([] if none)."""
    if name not in _BLOCKS:
        return []
    span, sizes = _load(_BLOCKS[name])
    return [_unpack(span, size) for size in sizes]


@lru_cache(maxsize=None)
def revamp(name):
    """A picture's revamp version (hand-drawn line art over shaded
    scenery, one size) as a one-piece list; [] if it has none."""
    if name not in _REVAMP:
        return []
    span, sizes = _load(_REVAMP[name])
    return [_unpack(span, size) for size in sizes]


@lru_cache(maxsize=None)
def combined(name):
    """A picture's combined sizes (every technique at once: blocks, eighths,
    shades, braille and text), biggest first; [] for the pictures that
    don't have one."""
    if name not in _COMBINED:
        return []
    span, sizes = _load(_COMBINED[name])
    return [_unpack(span, size) for size in sizes]


def _og(lines, colours):
    """An OG picture as a piece: all of it is focus."""
    parts = tuple("".join(" " if ch == " " else LETTER_OF[part]
                          for ch, part in zip(line, row))
                  for line, row in zip(lines, _parts_of(lines, colours)))
    tones = tuple("".join(" " if c == " " else OG_TONE for c in p) for p in parts)
    return Piece(tuple(lines), parts, tones, (0,) * len(lines))


def resolve(value, style="blocks"):
    """A theme's "art" value as a list of pieces, biggest first. A name
    gives the picture's sizes in the style (revamp, blocks, detailed or
    combined; none for og; a picture with no combined version is drawn in
    blocks)
    and then the OG ones, large and coloured, then small; a list of lines
    is a single piece in the accent colour. None for anything else
    (including "none")."""
    if isinstance(value, str) and value in ART:
        pieces = list({"blocks": blocks, "detailed": detailed,
                       "combined": lambda n: combined(n) or blocks(n),
                       "revamp": revamp}
                      .get(style, lambda n: [])(value))
        if value in LARGE:
            pieces.append(_og(*LARGE[value]))
        return pieces + [_og(ART[value], {})]
    if isinstance(value, list) and value and all(isinstance(l, str) for l in value):
        return [_og([l.rstrip() for l in value], {})]
    return None


def _parts_of(lines, colours):
    """Which palette part every character of the picture takes."""
    default = colours.get("default", "accent")
    out = []
    for r, line in enumerate(lines):
        parts = [default] * len(line)
        for r0, r1, part in colours.get("rows", ()):
            if r0 <= r <= r1:
                parts = [part] * len(line)
        for chars, part in colours.get("chars", {}).items():
            for c, ch in enumerate(line):
                if ch in chars:
                    parts[c] = part
        for word, part in colours.get("words", {}).items():
            for m in re.finditer(r"\b" + re.escape(word) + r"\b", line):
                parts[m.start():m.end()] = [part] * (m.end() - m.start())
        for r0, r1, c0, c1, part in colours.get("boxes", ()):
            if r0 <= r <= r1:
                for c in range(c0, min(c1 + 1, len(line))):
                    parts[c] = part
        out.append(parts)
    return out


class Picture:
    """A piece painted in a theme's colours, ready for the screen."""

    def __init__(self, piece, palette, reset):
        self.lines, self.keep, self.span = piece.lines, piece.keep, piece.span
        self.width = max(map(len, piece.lines), default=0)
        self.height = len(piece.lines)
        self._codes = []
        backs = (zip(piece.back_parts, piece.back_tones) if piece.back_parts
                 else ((None, None) for _ in piece.parts))
        for parts, tones, (bparts, btones) in zip(piece.parts, piece.tones, backs):
            row = []
            for k, (p, t) in enumerate(zip(parts, tones)):
                part = PART_LETTERS.get(p)
                code = palette.get((part, t)) or palette.get(part, "")
                if bparts and bparts[k] != " ":
                    back = PART_LETTERS[bparts[k]]
                    code += palette.get(("bg", back, btones[k])) or palette.get(("bg", back), "")
                row.append(code)
            self._codes.append(row)
        self._reset = reset
        self._wider = {}

    def wider(self, width):
        """The picture `width` columns wide, for a spanning picture on a
        screen wider than it was drawn at: its scenery grows on to the left
        (see _grow). Anything else, or a width it already fits, gives the
        picture itself back."""
        if not self.span or width <= self.width:
            return self
        if width not in self._wider:
            order = _grow(self, width - self.width)
            if order is None:
                return self
            if len(self._wider) > 8:          # a window being dragged wider
                self._wider.clear()
            pic = object.__new__(Picture)
            pic.span, pic.height, pic.width = True, self.height, width
            pic.lines = tuple("".join(line[c] for c in order) + line for line in self.lines)
            pic._codes = [[codes[c] for c in order] + codes for codes in self._codes]
            pic.keep = tuple(k + len(order) for k in self.keep)
            pic._reset, pic._wider = self._reset, {}
            self._wider[width] = pic
        return self._wider[width]

    def row(self, r, start=0):
        """Row r from column `start` on, styled; runs of one colour share
        a code. A blank keeps the colour before it (it shows no ink),
        unless a background is involved: then it takes its own, so a
        background never runs on into blanks that don't have one."""
        out, cur = [], None
        line, codes = self.lines[r], self._codes[r]
        for c in range(start, len(line)):
            ch = line[c]
            blank_ok = ch == " " and "48;" not in codes[c] and "48;" not in (cur or "")
            if not blank_ok and codes[c] != cur:
                cur = codes[c]
                out.append(self._reset + cur)
            out.append(ch)
        return "".join(out).rstrip() + self._reset


def _grow(pic, n):
    """n columns of new scenery for the left of a spanning picture, as the
    indices of its own columns to copy, left to right; None if it has too
    little scenery left of its focus to grow from.

    Built leftwards like a texture is grown: runs of the picture's own
    background columns, each run starting at a column whose right-hand
    neighbour looks like the column it's put next to, so every seam lines
    up. Runs are of random length from random places (seeded by the
    picture, so it's the same every frame), which keeps it from looking
    like the same strip over and over."""
    room = min(pic.keep)
    if room < 12:
        return None
    cols = [tuple((pic.lines[r][c], pic._codes[r][c]) for r in range(pic.height))
            for c in range(room)]
    same = [[sum(x == y for x, y in zip(a, b)) for b in cols] for a in cols]
    rng = random.Random(pic.width * 7919 + pic.height * 31 + room)
    out, cur, run = [], 0, 0          # cur: the column at the left edge so far
    recent = []                       # where the last few runs came from
    while len(out) < n:
        if run > 0 and cur > 0:
            cur, run = cur - 1, run - 1               # carry on along the run
        else:
            # jump somewhere else: not close by, not where the last few runs
            # came from, and where the seam fits well
            near = room // 4
            far = [j for j in range(room - 1)
                   if all(abs(j - k) > near for k in recent + [cur - 1])] \
                or [j for j in range(room - 1) if abs(j + 1 - cur) > near] \
                or list(range(room - 1))
            best = max(same[cur][j + 1] for j in far)
            fits = [j for j in far if same[cur][j + 1] >= best - max(2, pic.height // 6)]
            cur, run = rng.choice(fits), rng.randint(room // 6, room // 2)
            recent = (recent + [cur])[-3:]
        out.append(cur)
    return out[::-1]


@lru_cache(maxsize=64)
def _paint(piece, palette, reset):
    return Picture(piece, dict(palette), reset)


def paint(piece, palette, reset="\x1b[0m"):
    """The piece as a Picture: palette maps each part (PARTS) to an escape
    code, for shaded colours (part, tone digit) to one per tone, and for
    block pieces ("bg", part) and ("bg", part, tone) to background codes.
    The same piece and palette give the same Picture back."""
    return _paint(piece, tuple(palette.items()), reset)
