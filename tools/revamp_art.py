"""The hand-drawn subjects of the "revamp" art style, built into the app
by tools/make_revamp.py, each over its scene's scenery.

A picture is its text (one size), plus how to colour it:

    colours   rules like art_large.py: default, rows, chars, words, boxes
              (palette parts: dim text error extra accent good warn)
    tones     {characters: tone digit 0-9}: how light each is drawn (the
              shaded art colours); everything else is tone 6
    paint     optional grid the shape of the text: a part letter
              (d t e x a g w) wherever it should override the rules
    shade     optional grid the same way: a tone digit wherever it should
              override the tones
    ground    optional: the scenery items, instead of the scene's own
              background (a function of the height in rows)
    below     empty rows under the drawing (room for the tile)
    solid     every row hides the scenery from its first character to
              its last (a mountain range open at the bottom)
    tile      optional hand-drawn ground: lines repeated right across the
              screen along the bottom (city, fence, shelf), over the
              scenery, with tile_colours and tile_tones like the above

In the text a blank lets the scenery through and "§" is a blank that
doesn't. Drawn as ASCII artists draw: curves stepped with _,.-'"^ and
/ | \\ ( ), two or three shading levels, every line joined up.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artgen import scatter      # noqa: E402

OPAQUE = "§"
PICTURES = {}

# hand-drawn grounds, shared: (tile, colours, tones)
GRASS = (r"""
  \ | /  ,   \|/   ,,  \ |/  ,   \|/  ,  \| /   ,  \|/
`'"'`"'`"`'"'`"'"`'`"'`"'"`'`"'`"`'"'`"'"`'`"'"`'`"'`"
""", {"default": "good"}, {"\\|/,": "6", "`'\"": "4"})
FERNS = (r"""
 \\  //   \\|//    \\  //   \\|//   \\  //   \\|//
\\\\|////\\\\|////\\\\|////\\\\|////\\\\|////\\\\|//
""", {"default": "good"}, {"\\/": "5", "|": "6"})
SNOW = (r"""
       _..--''``''--.._              _..-''``''-.._
  _.--'                ''--.._..--''               ''--._
    *        .      *           .        *      .
""", {"default": "text", "chars": {"*.": "dim"}}, {"_.-'`": "8", "*": "5"})


def ground_tile(kind):
    """Keyword arguments putting a shared ground under a picture."""
    tile, colours, tones = kind
    return {"tile": tile, "tile_colours": colours, "tile_tones": tones}


# shading ramps, darkest to brightest, and the tone each is drawn in
SHADE_TONES = {"@": "9", "%": "8", "#": "7", "*": "6", "+": "5", "=": "4", "-": "3",
               ":": "3", ".": "2"}


class Pic:
    def __init__(self, text, colours=None, tones=None, paint=None, ground=None,
                 span=None, margin=2, tile=None, tile_colours=None, tile_tones=None,
                 below=0, solid=False, shade=None, tile_under=True):
        lines = text.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        self.lines = [l.rstrip() for l in lines] + [""] * below
        if solid:
            # every row solid from its first character to its last
            self.lines = [(l[:len(l) - len(l.lstrip())] + l.strip().replace(" ", OPAQUE)) if l.strip() else l
                          for l in self.lines]
        self.colours = colours or {}
        self.tones = tones or {}
        self.paint = _grid(paint)
        self.shade = _grid(shade)
        self.ground, self.span, self.margin = ground, span, margin
        tile_lines = tile.split("\n") if tile else []
        while tile_lines and not tile_lines[0].strip():
            tile_lines.pop(0)
        while tile_lines and not tile_lines[-1].strip():
            tile_lines.pop()
        self.tile = tile_lines or None
        self.tile_colours = tile_colours or {"default": "dim"}
        self.tile_tones = tile_tones or {}
        self.tile_under = tile_under

    def tile_tone(self, ch):
        for chars, digit in self.tile_tones.items():
            if ch in chars:
                return digit
        return "5"

    def paint_at(self, r, k):
        if not self.paint or r >= len(self.paint) or k >= len(self.paint[r]):
            return None
        ch = self.paint[r][k]
        return ch if ch in "dtexagw" else None

    def shade_at(self, r, k):
        if not self.shade or r >= len(self.shade) or k >= len(self.shade[r]):
            return None
        ch = self.shade[r][k]
        return ch if ch.isdigit() else None

    def tone_of_char(self, ch):
        for chars, digit in self.tones.items():
            if ch in chars:
                return digit
        return "6"


def _grid(text):
    """A paint or shade grid's lines (a leading blank line, as in the
    pictures, is dropped)."""
    if not text:
        return None
    lines = text.split("\n")
    if lines and not lines[0].strip():
        lines.pop(0)
    return lines


def picture(name, text, **kw):
    PICTURES[name] = Pic(text, **kw)


# ---------------------------------------------------------------- midnight

picture("moon", r"""
                       _..--'
                   _.-%@@%/
                 .%@@%##/
                /@@%#*+(
               |@@%#*o|           ~--..__
               |@%#*+=|                  ``-..
   ~~--..__    |@@%o*+=(
           ``  \@@%#*+==\
                '%@@%##*+\._
                  `"%@@@%%%#*=-..__.-'
                      `""----""`
""", below=4, colours={"default": "warn",
                                "boxes": [(4, 5, 34, 60, "dim"), (6, 7, 0, 14, "dim")]},
        tones=SHADE_TONES,
        ground=lambda rows: scatter(-3.0, 0.0, 1.5, 0.62, 34, ["*", ".", "+", ".", "'"], "t", seed=7),
        tile=r"""
                  |                          _
      _____      _|_       ______           | |      ___
     |:.:.:|    |:::|     |.:.:.:|   ____   | |     |:::|
  ___|.:.:.|____|:.:|_____|:.:.:.|__|::::|__|.|_____|:.:|__
 |::.|:.:.:|:::.|:::|.:::.|.:.:.:|::|.:.:|::|:|.:::.|:::|::|
""", tile_colours={"default": "dim", "chars": {":": "warn"}}, tile_tones={":": "8", ".": "3"})


# ---------------------------------------------------------------- ocean

def _island_ground(rows):
    from art_scenes import sea
    from artgen import text
    boat = text(-0.55, 0.53, ["   |\\", "   | \\", "   |__\\", "\\______/"], "t", rows, False)
    glint = text(0.28, 0.78, ["-=====-", " -===-", "  ---"], "w", rows, False)
    return [sea(top=0.74), *boat, *glint]


picture("island", r"""
        \   |   /                   __ _.--..--._ _
      '. .-'''-. .'             _.-' _/   _/\_   \_'-._
   -- - (       ) - --        .'  __/  __/\  /\__  \__  '.
      .' '-...-' '.          |__.'   _/   \/   \_   '.__|
        /   |   \                |__/\__/ \__/ \__/\__|
                                         \__/
                v                         \__/
                         v                 \__/
                                            \__/
                                             \__/
                                      ___.--'\__/'--.___
                                .--''§§§.§§§§:§§§§.§§§§§''--.
""", colours={"default": "good",
              "boxes": [(0, 4, 0, 21, "warn"), (5, 7, 0, 30, "dim"), (5, 10, 40, 50, "extra"),
                        (10, 11, 30, 70, "warn")]},
        tones={"'`.-_:": "7"}, ground=_island_ground)


# ---------------------------------------------------------------- default

def _desk(rows):
    from art_scenes import desk
    return desk(rows, "x")


picture("keyboard", r"""
 ____ ____ ____ ____ ____ ____ ____ ____ ____ ____
||Q |||W |||E |||R |||T |||Y |||U |||I |||O |||P ||
||__|||__|||__|||__|||__|||__|||__|||__|||__|||__||
|/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|
   ____ ____ ____ ____ ____ ____ ____ ____ ____
  ||A |||S |||D |||F |||G |||H |||J |||K |||L ||
  ||__|||__|||__|||__|||__|||__|||__|||__|||__||
  |/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|/__\|
      ____ ____ ____ ____ ____ ____ ____
     ||Z |||X |||C |||V |||B |||N |||M ||
     ||__|||__|||__|||__|||__|||__|||__||
     |/__\|/__\|/__\|/__\|/__\|/__\|/__\|
""", below=2, colours={"default": "dim",
                       "chars": {"QWERTYUIOPASDFGHJKLZXCVBNM": "text"},
                       "boxes": [(5, 5, 17, 18, "accent"), (5, 5, 32, 33, "accent")]},
        tones={"|_/\\": "5", "QWERTYUIOPASDFGHJKLZXCVBNM": "8"}, ground=_desk)


# ---------------------------------------------------------------- forest

picture("pines", r"""
                         *                    _.._
                        /^\                 .' .-'`
         *             /'.'\               /  /
        /^\           /. ' .\              |  |
       /. .\         /_ '.' _\             \  '._.'
      /' . '\         /' . '\               '._.'
     /_ ' . _\       / . ' . \       *
      /. ' .\       /_' . ' ._\     /^\
     / ' . ' \       / ' . ' \     /. .\
    /_. ' . ._\     / . ' . ' \   /' . '\
     / . ' . \     /_' . ' . '_\ /_ ' . _\
    /_'_._._'_\   /_._._._._._._\ /. ' .\
        |#|              |#|     /_._._._\
        |#|              |#|        |#|
""", colours={"default": "good", "chars": {"|#": "extra", "*": "text"},
              "boxes": [(0, 6, 36, 60, "warn")]},
        tones={"'.": "4", "/\\^_": "7", "#": "5"})


# ---------------------------------------------------------------- sunset

def _sunset_ground(rows):
    from art_scenes import sea
    from artgen import text
    glint = text(0.42, 6 / 12, ["-=============-", "  -=========-", "    -=====-", "      ---"],
                 "w", rows, False)
    boat = text(-0.5, 2.6 / 12, ["   |\\", "   | \\", "   |__\\", "\\______/"], "d", rows, False)
    return [sea(top=5.95 / 12, part_lo="d", part_hi="x"), *glint, *boat]


picture("sunset", r"""
                      .         '         .
               '.           _.......__          .'
         .           _.--''`.:.:.:.:.:`''--._           .
            `.    .-'::::::::::::::::::::::::'-.     .'
               .'-==--==--==--==--==--==--==--=='.
   ~~~--..___ /=##=====##=====##=====##=====##====\ ___..--~~~
""", below=6, colours={"default": "warn", "rows": [(5, 5, "error")],
                       "chars": {"#": "error", "=": "error"},
                       "boxes": [(5, 5, 0, 13, "dim"), (5, 5, 49, 70, "dim"), (0, 3, 0, 9, "warn")]},
        tones={".:": "9", "-": "7", "=": "6", "#": "5"}, ground=_sunset_ground)


# ---------------------------------------------------------------- moss

picture("stones", r"""
                          .-""-.
                         ( ,;  ;)
                          '-..-'
                      .-''``  ``''-.
                     ( ,;     ;,    )
                      '-..______..-'
                 .-''```          ```''-.
                (    ,;    ;,      ;,    )
                 '-..________________..-'
  .-.      .-''```                      ```''-.
 (___)    (  ;,        ,;      ;,          ;   )
   |       '-..____________________________..-'
""", colours={"default": "dim", "chars": {",;": "good"},
              "boxes": [(9, 11, 0, 7, "warn")]},
        tones={"-.'`\"": "6", "()": "7", "_": "5", ",;": "7"})


# ---------------------------------------------------------------- pine

def _pine_ground(rows):
    from art_scenes import hills
    return [*scatter(-3.0, 0.0, 1.6, 0.5, 30, ["*", ".", "+", "'"], "t", seed=11),
            *hills(0.9, "t", seed=2)]


picture("pine", r"""
                                  .
                                 /|\
                                /'|'\
                               /''|''\
                                /'|'\
                               /''|''\
                              /'''|'''\
                               /''|''\
                              /'''|'''\
                             /''''|''''\
                            /'''''|'''''\
                              /'''|'''\
                             /''''|''''\
                            /'''''|'''''\
                           /''''''|''''''\
                                 |||
""", colours={"default": "good", "chars": {"|": "extra", ".": "warn"}},
        tones={"'": "4", "/\\": "7", "|": "5"}, ground=_pine_ground)


# ---------------------------------------------------------------- autumn

picture("leaf", r"""
                         |
          ,         .    |    .
                   /|\   |   /|\           '
       ~~--..  ___/ | \__|__/ | \___
             ``\     |    |    |    /     ,
                \    '.   |   .'   /
     '       __.-'     '. | .'     '-.__
        ,    \           '|'           /       ~~--.._
              '-.         |         .-'               ``
                 '-.      |      .-'
          '         '--.  |  .--'        ,
                        '-.|.-'
                           |
                           |
""", colours={"default": "error", "chars": {"|": "warn", "~-.`": "error"},
              "boxes": [(0, 13, 26, 27, "warn"), (3, 7, 0, 12, "dim"), (7, 8, 40, 60, "dim"),
                        (0, 13, 0, 9, "warn"), (0, 2, 40, 60, "warn"), (9, 11, 0, 12, "warn"),
                        (9, 11, 38, 60, "warn")]},
        tones={"'.-_": "7", "/\\": "7", "|": "6"}, ground=lambda rows: [])


# ---------------------------------------------------------------- desert

def _desert_ground(rows):
    return scatter(-3.0, 0.0, 1.6, 0.3, 4, ["v", "\\_v_/"], "d", seed=5)


picture("cactus", r"""
                       .--.     *            .   |   .
                      /:||:\       .-.          .-'-.
                      |:||:|      /:|:\     -- (     ) --
            .-.       |:||:|      |:|:|         '-.-'
           /:|:\      |:||:|      |:|:|      '   |   '
           |:|:|      |:||:|      |:|:|
           |:|:|      |:||:|------'|:|:|
           |:|:|      |:||:|::::::::::/
           |:|:'------|:||:|---------'
            \:::::::::|:||:|
     .-.     '--------|:||:|
    (:|:)             |:||:|
""", colours={"default": "good", "chars": {"*": "error"},
              "boxes": [(0, 4, 41, 60, "warn"), (10, 11, 4, 8, "extra")]},
        tones={":": "4", "|": "6", "-'./\\": "7"}, ground=_desert_ground, below=1,
        tile=r"""
           _.-~~~-._                     _.--~~--._
  __...--''         ''--..___...--''''`            `''--..__
 .   .   .     .   .     .    .   .   .     .   .     .    .
""", tile_colours={"default": "warn", "chars": {".": "dim"}}, tile_tones={"_.-~'`": "6", ".": "3"})


# ---------------------------------------------------------------- meadow

def _meadow_ground(rows):
    from art_scenes import grass
    return [grass(0.9), *scatter(-3.0, 0.0, 1.6, 0.16, 5, ["v", "~v~"], "d", seed=3)]


picture("flowers", r"""
                   _
      wWWWw      _(_)_        }{
      (___)      (_)@(_)               wWWWw
        Y          (_)                 (___)       _      }{
        |           |                    Y       _(_)_
       \|           |         .-.        |       (_)@(_)
        |           |/       ( @ )       |         (_)
        |           |         '-'        |/         |
        |/          |          |         |         \|
        |          \|         \|         |          |
       \|           |          |        \|          |
        |           |          |/        |          |/
        |           |          |         |          |
""", colours={"default": "good", "chars": {"wWY(_)": "error", "@": "warn", "}{": "accent"},
              "boxes": [(0, 3, 15, 25, "warn"), (3, 6, 47, 56, "extra"), (5, 7, 28, 35, "accent"),
                        (2, 3, 37, 44, "error")]},
        tones={"|\\/": "5", "_()wWY": "7", "@": "9"}, ground=_meadow_ground)


# ---------------------------------------------------------------- jungle

picture("jungle", r"""
~~~-.__.-~~~-.__.-~~~-.__.-~~~-.__.-~~~-.__.-~~~-.
  \/   )(      \/    |    \/   )(     \/    )(
        (/              |              \)          ()
        \)              |              (/          )(
                     |                      (  )
                  .-'''-.                    )(
                _/ _   _ \_
               (_|(o) (o)|_)
                 |  .-.  |
                  \ '-' /
                .-'`---'`-.
               / /       \ \_
                         (___)
""", colours={"default": "good", "boxes": [(4, 12, 15, 30, "warn"), (7, 7, 19, 26, "text"),
                                            (4, 5, 44, 48, "error")]},
        tones={"~-._": "6", "()/\\": "6", "o": "9", "'`": "5"}, ground=lambda rows: [],
        below=1, **ground_tile(FERNS))


# ---------------------------------------------------------------- cherry blossom

def _blossom_ground(rows):
    return scatter(0.0, 0.1, 1.5, 0.8, 9, [",", "'", "`", "."], "e", seed=9)


picture("blossom", r"""
       .-~~~-.      .-~~-.
  .-~~(  @ * @ )~~-(  * @  )~~-.
 ( @ *  @  *  @  *  @  *  @  * @ )
( *  @ *  @  *  \|/  @  *  @  *  @ )
 '-. @ * @ * .-~\|/~-. * @ * @ .-'
    '~~~~~~~'    \|/    '~~~~~~'
                  |
                  |\
                 /|
                / |
            ___/  |\___
""", colours={"default": "error", "chars": {"*": "text", "@": "error"},
              "boxes": [(3, 10, 15, 21, "extra"), (5, 10, 11, 25, "extra")]},
        tones={"@": "7", "*": "9", "~-.'()": "6"}, ground=_blossom_ground, below=1,
        **ground_tile(GRASS))


# ---------------------------------------------------------------- lavender

picture("lavender", r"""
                  *           *
            *    :*:    *    :*:    *
           :*:   :*:   :*:   :*:   :*:
           :*:   :*:   :*:   :*:   :*:
           :*:    \    :*:    /    :*:
             \     \    |    /     /
               \    \   |   /    /
                  \   \ | /   /
                     '-)|(.-'
                      / | \
                     /  |  \
                    '   |   '
""", colours={"default": "accent", "chars": {"\\/|'-.": "good", "()": "error"}},
        tones={"*": "8", ":": "5", "\\/|": "5"})


# ---------------------------------------------------------------- tundra

def _tundra_ground(rows):
    return scatter(-3.0, 0.0, 1.6, 0.6, 34, ["*", ".", "'", "+"], "t", seed=4)


picture("snowpeaks", r"""
           /\
          /''\
         /\/\/\         /\
        /      \       /''\
       /   /\   \     /\/\/\
      /   /  \   \   /      \
     /   /    \   \ /   /\   \
    /   /      \   /   /  \   \
   /   /        \ /   /    \   \
  /   /          /   /      \   \
""", colours={"default": "accent", "boxes": [(0, 2, 0, 20, "text"), (2, 4, 20, 40, "text")]},
        tones={"'": "9", "/\\": "7"}, ground=_tundra_ground, below=2, solid=True,
        **ground_tile(SNOW))


# ---------------------------------------------------------------- coral reef

def _reef_ground(rows):
    return scatter(-3.0, 0.15, 1.6, 0.75, 12, ["o", ".", "O", "o"], "t", seed=6)


picture("reef", r"""
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

      ><(((('>                 o
                                 O
                  <><         o
                                    <'))))><
   \ | /
    \|/  (@)                                  )  (
   \ |/  \|     ><>                          (    )
    \|/\ |/                 .-.-.             )  (
     |  \|                 (@ @ @)           (    )
                            '-'-'
""", colours={"default": "accent", "chars": {"><('": "warn", "@": "error", "oO": "text"},
              "boxes": [(6, 10, 2, 12, "error"), (7, 10, 44, 51, "good"), (9, 11, 26, 33, "extra"),
                        (0, 0, 0, 60, "dim")]},
        tones={"~-": "5"}, ground=_reef_ground,
        tile=r"""
 .  ,   .  _.-~-._  ,    .   ,  .   _.-~~-._    ,  .   ,
'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`'`
""", tile_colours={"default": "warn"}, tile_tones={".,": "4", "'`": "6"})


# ---------------------------------------------------------------- volcanic

picture("volcano", r"""
   (   )  (    )
 (    )  (  )  (  )
   (  (    )  (  )
     ) (  (  )  (
      '.  ^  .'
   *   _/^^^^\_   '
 '    /  \  /  \     *
     /  ' )(    \
    /  .'/  \ '. \
   /  ' /    \  '.\
  /  .'/      \   '\
 / .' /        \    \
/__________________ \
""", colours={"default": "dim", "chars": {"^": "error", "*'": "warn"},
              "boxes": [(4, 6, 0, 30, "error"), (7, 12, 3, 11, "error"), (7, 12, 12, 20, "warn"),
                        (6, 6, 0, 2, "warn"), (5, 6, 18, 30, "warn")]},
        tones={"()": "4", "^": "9", "'.": "8", "/\\_": "5"}, solid=True,
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.5, 14, ["'", ".", "*"], "w", seed=21),
        tile=r"""
     _    /\        _       /\    _         /\
 _/\/ \__/  \/\___/ \__/\_/  \__/ \_/\__/\_/  \_
""", tile_colours={"default": "dim"}, tile_tones={"_/\\": "4"})


# ---------------------------------------------------------------- bamboo

picture("bamboo", r"""
      ||     =||=    ||
      ||\__   ||     ||
     =||='--. ||    =||=
      ||      ||     ||
      ||     =||__/  ||           .--.     .--.
      ||      |.--'  ||          ( (  \___/  ) )
     =||=     ||    =||=          \ ./  _ _  \. /
  __/ ||      ||     ||            |  (o) (o)  |
 '-'  ||     =||=    ||            |    (_)    |
      ||      ||     ||\__          \  '-^-'  /
     =||=     ||    =||='--.      .-'-._____.-'-.
      ||      ||     ||          /  /         \  \
      ||     =||=    ||         (__/    ___    \__)
""", colours={"default": "good", "boxes": [(4, 12, 30, 52, "text"), (5, 7, 30, 52, "text"),
                                            (7, 7, 36, 46, "dim")]},
        tones={"=": "8", "|": "5", "_/\\'-.": "6", "o": "9"}, ground=lambda rows: [], below=1,
        **ground_tile(GRASS))


# ---------------------------------------------------------------- dracula

def _dracula_ground(rows):
    return scatter(-3.0, 0.0, 1.6, 0.55, 26, ["*", ".", "+", "'"], "t", seed=13)


picture("bat", r"""
                                    _.._
  ^v^                             .' .-'`
                                 /  /       ^v^
         |>                      |  |
         |       |>              \  '.___.;
        /^\      |                '._  _.'
        | |     /^\        ^v^       ``
        | |_ _ _| |_ _ _
        |#|_|_|_|#|_|_|_|
        | |       | |   |
       _| |  .-.  | |   |_
      |   |  | |  |   ^  |
      |___|__|_|__|__|_|_|
""", colours={"default": "dim", "chars": {"#": "warn", ">": "error", "^v": "error"},
              "boxes": [(0, 6, 32, 48, "warn"), (11, 12, 13, 18, "warn")]},
        tones={"|_/\\": "6", "#": "9", ".'`;": "8"}, ground=_dracula_ground,
        tile=r"""
    _.--''``''--.._                 _..--''``''-._
_.-'               ''--..____..--''               ''-.._
""", tile_colours={"default": "dim"}, tile_tones={"_.-'`": "4"})


# ---------------------------------------------------------------- nord

def _nord_ground(rows):
    return scatter(-3.0, 0.0, 1.6, 0.4, 24, ["*", ".", "+", "'"], "t", seed=17)


picture("mountains", r"""
             /\
            /''\      /\
      /\   / /\ \    /''\
     /''\ / /  \ \  / /\ \
    / /\ \ /    \ \/ /  \ \
   / /  \ \      \  /    \ \
  /_/    \_\______\/______\_\
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  \ \    / /      /\      / /
   \ \  / /      /  \    / /
  ~ \ \/ / ~  ~ / /\ \ ~/ / ~
     \  /      / /  \ \/ /
""", colours={"default": "accent", "chars": {"'": "text", "~": "dim"},
              "boxes": [(8, 11, 0, 40, "dim")]},
        tones={"'": "9", "/\\_": "7", "~": "5"}, ground=_nord_ground, solid=True,
        tile=r"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  ~  ~~   ~ ~~~  ~   ~~ ~  ~~~ ~   ~  ~~  ~ ~~~   ~
 ~~ ~  ~~~   ~  ~~ ~~   ~~   ~ ~~~ ~~  ~  ~~ ~ ~~~
   ~  ~ ~~ ~   ~~  ~ ~ ~~ ~~  ~    ~ ~~ ~~   ~  ~
""", tile_colours={"default": "dim"}, tile_tones={"~": "4"})


# ---------------------------------------------------------------- gruvbox

picture("coffee", r"""
    (  )   (   )  )
     ) (   )  (  (
     ( )  (    ) )
    _____________
   <_____________> ___
   |             |/ _ \
   |               | | |
   |               |_| |
___|             |\___/
/    \___________/    \
\_____________________/
""", colours={"default": "warn", "rows": [(0, 2, "dim")],
              "boxes": [(3, 4, 3, 18, "text")]},
        tones={"()": "4", "_<>": "7", "|/\\": "6"}, ground=lambda rows: [], below=1,
        tile=r"""
______________________________________________________
=--~~--==__==--~--=___==-~~--=_____==----~-------=====
""", tile_colours={"default": "extra"}, tile_tones={"_": "7", "=-~": "4"})


# ---------------------------------------------------------------- solarized

picture("sun", r"""
        \     |     /
   \     \    |    /     /         .--.
     '.   \   |   /   .'        .-(    ).
       '. .-'''''''-. .'        (___.__)__)
   --.   .'         '.   .--
      '-/             \-'
 ------ |             | ------
      .-\             /-.
   --'   '.         .'   '--          .--.
       .' '-.......-' '.             (    )-.
     .'   /   |   \   '.            (___.___)
   /     /    |    \     \
""", colours={"default": "warn", "boxes": [(0, 11, 30, 60, "text")]},
        tones={"\\|/-.'": "7", "()_": "6"}, ground=lambda rows: [])


# ---------------------------------------------------------------- monokai

_CODE = r"""
.------------------------------------------.
| o o o    type.py                         |
|------------------------------------------|
|  1  def race(words):                     |
|  2      for w in words:  # go fast!      |
|  3          yield w.upper()              |
|  4                                       |
|  5  print("minitype", 120, "wpm")_       |
'------------------------------------------'
"""


def _code_paint(text):
    """Syntax colours for the editor: keywords, names, strings, numbers,
    the comment, the window's buttons."""
    import re
    rows = []
    for line in text.strip("\n").split("\n"):
        p = [" "] * len(line)

        def mark(a, b, letter):
            for k in range(a, b):
                p[k] = letter
        for m in re.finditer(r"\b(def|for|in|yield)\b", line):
            mark(m.start(), m.end(), "e")
        for m in re.finditer(r"\b(race|upper|print)\b", line):
            mark(m.start(), m.end(), "g")
        for m in re.finditer(r'"[^"]*"', line):
            mark(m.start(), m.end(), "w")
        for m in re.finditer(r"\b\d{2,}\b", line):
            mark(m.start(), m.end(), "x")
        for m in re.finditer(r"#.*?(?=\s*\|)", line):
            mark(m.start(), m.end(), "d")
        for m in re.finditer(r"^\|\s+(\d)", line):
            mark(m.start(1), m.end(1), "d")
        if "o o o" in line:
            k = line.index("o o o")
            p[k], p[k + 2], p[k + 4] = "e", "w", "g"
        if line.rstrip().endswith("|") and "_" in line and "print" in line:
            p[line.index(")_") + 1] = "a"
        rows.append("".join(p))
    return "\n" + "\n".join(rows)


picture("code", _CODE, colours={"default": "dim", "words": {"type": "text", "py": "text"}},
        paint=_code_paint(_CODE), tones={"|-'.": "4"}, ground=lambda rows: [])


# ---------------------------------------------------------------- catppuccin

picture("cat", r"""
                  /\       /\
                 /  \_____/  \
                (   o     o   )
                (      ^      )
                 \   '-^-'   /
                  '-._____.-'
                   /       \
                  /  |   |  \
                 (   |   |   )
                  \  |   |  /_____
   .--.           (__|___|__)     )
  (  @ )~~~~~                 ___/
   '--'
""", colours={"default": "text", "chars": {"o": "accent", "^": "error"},
              "boxes": [(10, 12, 0, 13, "error")]},
        tones={"/\\()_|": "7", "'-.": "6"}, below=1, **ground_tile(GRASS),
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.55, 20, ["*", ".", "+"], "t", seed=19))


# ---------------------------------------------------------------- matrix

def _rain(seed=42, rows=14, cols=58):
    """Columns of falling glyphs: text, a colour grid (bright heads) and a
    shade grid (tails fading)."""
    import random
    rnd = random.Random(seed)
    glyphs = "0123456789ABCDEFZ=+-<>/?#$%"
    text = [[" "] * cols for _ in range(rows)]
    paint = [[" "] * cols for _ in range(rows)]
    shade = [[" "] * cols for _ in range(rows)]
    for col in range(1, cols, 3):
        top = rnd.randint(-7, 7)
        length = rnd.randint(5, 13)
        for r in range(max(0, top), min(rows, top + length)):
            text[r][col] = rnd.choice(glyphs)
            from_head = top + length - 1 - r
            paint[r][col] = "t" if from_head == 0 else "g"
            shade[r][col] = "9" if from_head == 0 else str(max(1, 8 - from_head))
    join = lambda g: "\n" + "\n".join("".join(row).rstrip() for row in g)
    return join(text), join(paint), join(shade)


_RAIN, _RAIN_PAINT, _RAIN_SHADE = _rain()
picture("rain", _RAIN, colours={"default": "good"}, paint=_RAIN_PAINT, shade=_RAIN_SHADE,
        ground=lambda rows: [], solid=True, tile=_rain(seed=7, cols=60)[0], tile_colours={"default": "good"},
        tile_tones={"0123456789": "3", "ABCDEFZ": "4", "=+-<>/?#$%": "2"})


# ---------------------------------------------------------------- amber

picture("monitor", r"""
.----------------------------.
| .------------------------. |
| |  C:\> minitype         | |
| |  ready. 0 wpm          | |
| |  > _                   | |
| |                        | |
| '------------------------' |
|   ___               o  == |
'----------------------------'
       /______________\
  .--------------------------.
 / [][][][][][][][][][][][]  /
'---------------------------'
""", colours={"default": "dim", "boxes": [(2, 4, 3, 26, "accent"), (7, 7, 22, 22, "warn")]},
        tones={"|-'._/[]": "5"}, ground=lambda rows: [])


# ---------------------------------------------------------------- paper

def _paper_ground(rows):
    from artgen import text
    return [*text(-1.2, 0.2, ["   .--.", ".-(    ).", "(___.__)__)"], "d", rows, False),
            *text(-2.4, 0.45, ["  .--.", " (    )-.", "(___.___)"], "d", rows, False)]


picture("plane", r"""
                                   ,
                             _,--'`/          .  '  .
                        ,.-'`    _/       .  '        '.
                  _,.-'`       ./      '                .
             _.-''        __,.'|    .                    :
       _,.-'`    __,..--''     \ '                       '
  __,..---''''``                |                     .'
  `'''--..,__                   |               . '
             `''---..,__        |
                        ``''--..|
""", colours={"default": "text", "boxes": [(1, 8, 33, 60, "dim")]},
        tones={"_,.-'`/|\\": "7"}, ground=_paper_ground)


# ---------------------------------------------------------------- high contrast

picture("bolt", r"""
          .--~~~--.
     .-~~(         )~~-.          ,  '  ,  '
   (      .------.      )        '  ,  '  ,
    '-.._(________)_..-'          ,  '  ,  '
           /   /                 '  ,  '  ,
          /   /___
         /       /
        /__   __/
          /  /
         / /
        / /
       //
       '
""", colours={"default": "accent", "rows": [(0, 3, "text")],
              "boxes": [(1, 4, 32, 50, "dim")]},
        tones={"/_": "9", "~-.'()": "7"}, solid=True, ground=lambda rows: [])


# ---------------------------------------------------------------- rainbow

picture("rainbow", r"""
                      __..----..__
                 _.-################-._
              _.######%%%%%%%%%%%%######._
            _/####%%%%%%%======%%%%%%%####\_
           /###%%%%%================%%%%%###\
         _####%%%%====++++++++++++====%%%%####_
         ###%%%%====+++++::::::+++++====%%%%###
        ###%%%====++++::::::::::::++++====%%%###
    .--.###%%%===+++::::'      '::::+++==   .--.\
  .(    ).%%%===+++:::'          ':::+++= .(    )-.
 (___.____)-.===+++::|            |::+++=(___.____)
""", colours={"default": "error", "chars": {"%": "warn", "=": "good", "+": "accent", ":": "extra",
                                             "'|": "extra"},
              "boxes": [(8, 10, 0, 11, "text"), (8, 10, 40, 52, "text")]},
        tones={"#%=+:": "7"}, ground=lambda rows: [], **ground_tile(GRASS))


# ---------------------------------------------------------------- party

picture("party", r"""
  .-.     .-.             *
 (   )   (   )   .-.            '
  '-'     '-'   (   )   ,                 '
   \       |     '-'                *
    \      |     /           '   \ | /
     \     |    /              -- ( ) --,
       i   i   i                 / | \*
     __|___|___|__        *
    {~~~~~~~~~~~~~}
    |  ~ ~ ~ ~ ~  |     '
    |_____________|
""", colours={"default": "text", "chars": {"*": "warn", "'": "error", ",": "good", "i": "warn"},
              "boxes": [(0, 2, 0, 5, "error"), (0, 2, 8, 13, "accent"), (1, 3, 16, 21, "good"),
                        (8, 10, 4, 18, "extra"), (4, 6, 29, 40, "warn")]},
        tones={"()": "7", "\\|/": "5"}, ground=lambda rows: [], below=1,
        tile=r"""
______________________________________________________
""", tile_colours={"default": "dim"})


# ---------------------------------------------------------------- glitch

def _glitch():
    """MINITYPE in figlet's small letters, sliced and shifted, with
    noise bars: text and a paint grid splitting it red and cyan."""
    letters = {
        "M": [" __  __ ", "|  \\/  |", "| |\\/| |", "|_|  |_|"],
        "I": [" ___ ", "|_ _|", " | | ", "|___|"],
        "N": [" _  _ ", "| \\| |", "| .` |", "|_|\\_|"],
        "T": [" _____ ", "|_   _|", "  | |  ", "  |_|  "],
        "Y": [" __   __", " \\ \\ / /", "  \\ V / ", "   |_|  "],
        "P": [" ___ ", "| _ \\", "|  _/", "|_|  "],
        "E": [" ___ ", "| __|", "| _| ", "|___|"],
    }
    logo = ["".join(letters[ch][k] for ch in "MINITYPE") for k in range(4)]
    rows = [" " * 8 + "=#=  ==%=   #==", ""]
    for k, (line, shift) in enumerate(zip(logo, (0, 0, 3, -2))):
        rows.append(" " * (4 + shift) + line)
    rows += ["", " %==  =#=      ==%#=   =", "                    #=   ==", "", " " * 30 + "=%="]
    paint = []
    for k, row in enumerate(rows):
        p = "".join(" " if ch == " " else ("e" if (i // 7 + k) % 3 == 0 else "a" if (i // 7 + k) % 3 == 1 else "t")
                    for i, ch in enumerate(row))
        paint.append(p)
    return "\n" + "\n".join(rows), "\n" + "\n".join(paint)


_GLITCH, _GLITCH_PAINT = _glitch()
picture("glitch", _GLITCH, colours={"default": "text"}, paint=_GLITCH_PAINT,
        tones={"=#%": "5"}, ground=lambda rows: [])


# ---------------------------------------------------------------- bubbly

picture("bubbles", r"""
                  o            .-''-.
      _.-''''-._              / ,    \
    .'  ,       '.           |  '     |         o
   /  ,'          \           \      /
  |  '             |  .        '-..-'
  |                |                                .
   \              /         o
    '.          .'                   .-.
      '-.____.-'                    ( ' )       O
                            .        '-'
                       .-.
                      ( ' )                 o
    o                  '-'
""", colours={"default": "accent", "chars": {",'": "text", "oO.": "extra"},
              "boxes": [(0, 4, 28, 40, "extra"), (7, 9, 35, 42, "error"), (10, 12, 22, 28, "good")]},
        tones={"-_.'`": "7", "/\\|()": "7"}, ground=lambda rows: [])


# ---------------------------------------------------------------- synthwave

def _synth():
    """A striped sun over a neon grid running to the horizon."""
    rows = [r"""         _.--''''--._""",
            r"""      .-'::::::::::::'-.""",
            r"""    .'::::::::::::::::::'.""",
            r"""   /::::::::::::::::::::::\ """,
            r"""  |========================|""",
            "   " + OPAQUE * 24,
            r"""  |------------------------|"""]
    rows = [" " * 14 + r for r in rows]
    hz, vx, width = 7, 29, 58
    grid = [[" "] * width for _ in range(6)]
    grid[0] = list("_" * width)
    for d in range(1, 6):
        if d in (2, 4):
            grid[d] = list("_" * width)
        if d >= 2:
            for k in range(-7, 8):
                x = round(vx + k * 2.2 * d)
                if 0 <= x < width:
                    grid[d][x] = "|" if k == 0 else "/" if k < 0 else "\\"
    rows += ["".join(g) for g in grid]
    paint = []
    for k, row in enumerate(rows):
        letter = "w" if k < 3 else "e" if k < 7 else "x" if k == hz else "a"
        paint.append("".join(" " if ch == " " else letter for ch in row))
    return "\n" + "\n".join(rows), "\n" + "\n".join(paint)


_SYNTH, _SYNTH_PAINT = _synth()
picture("grid", _SYNTH, paint=_SYNTH_PAINT, solid=True, tile_under=False, tones={":": "8", "=": "7", "-": "6", "_/\\|": "6"},
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.45, 26, ["*", ".", "+", "'"], "t", seed=23),
        tile=r"""
______________________________________________________

___/________/________/________/________/________/_____
         /        /        /        /        /
_______/________/________/________/________/________/_
     /        /        /        /        /        /
""", tile_colours={"default": "accent", "rows": [(0, 0, "extra")]}, tile_tones={"_/": "5"})


# ---------------------------------------------------------------- aurora

def _aurora():
    import math
    rows = [[" "] * 58 for _ in range(10)]
    shade = [[" "] * 58 for _ in range(10)]
    for col in range(58):
        top = 1 + 2.0 * math.sin(col / 6.5) + 1.0 * math.sin(col / 2.7 + 1)
        length = 4.5 + 2 * math.sin(col / 4.1 + 2)
        for r in range(10):
            d = r - top
            if 0 <= d < length:
                frac = d / length
                if frac < 0.4:
                    ch = "|"
                elif frac < 0.75:
                    ch = ":" if (col + r) % 2 == 0 else "|"
                else:
                    ch = "." if (col + r) % 2 == 0 else " "
                rows[r][col] = ch
                shade[r][col] = str(max(2, 9 - int(frac * 8)))
    join = lambda g: "\n" + "\n".join("".join(r).rstrip() for r in g)
    return join(rows), join(shade)


_AURORA, _AURORA_SHADE = _aurora()
picture("aurora", _AURORA, colours={"default": "good", "boxes": [(0, 9, 20, 40, "accent"),
                                                                  (0, 9, 44, 60, "extra")]},
        shade=_AURORA_SHADE, below=3,
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.6, 30, ["*", ".", "+", "'"], "t", seed=29),
        tile=r"""
   /\        /\     /\          /\       /\    /\
  /  \  /\  /  \   /  \   /\   /  \ /\  /  \  /  \
 /    \/  \/    \ /    \ /  \ /    V  \/    \/    \
""", tile_colours={"default": "dim"}, tile_tones={"/\\V": "3"})


# ---------------------------------------------------------------- ember

picture("fire", r"""
      .        '
   '      (          .
         ) )    (
    .   ( (  )   )  '
       ) )  ( ( (
      ( (  ) ) ) )
   '   ) )( ( ( (  )
      ( (  ) )) ) (    .
       \ \(  ( ( / /
   .    \ \) ) )/ /
     ____\_\___/_/____
    /____/\_____/\____\
    \____\/_____\/____/
""", colours={"default": "error", "chars": {".'": "warn"},
              "boxes": [(4, 9, 8, 16, "warn"), (10, 12, 0, 30, "extra")]},
        tones={"()": "7", "\\/": "6", "_": "5", ".'": "9"}, ground=lambda rows: [],
        tile=r"""
  .   ,    .     '   .    ,     .   '    .   ,
""", tile_colours={"default": "dim"})


# ---------------------------------------------------------------- deep sea

picture("jellyfish", r"""
                     _.-~~~~-._       .
  o                .'  .   .   '.
                  /  .   .   .   \            O
                 (_________________)
   _.-._           ) ( ) ( ) ( ) (
  (_____)         ( ) ( ) ( ) ( ) )       o
  ) ( ) (          ) ( ) ) ( ( ) (
 ( ) ) ( )        (   ) (   ) (   )
  ) (   o          )   (     )   (
                  (     )   (     )
""", colours={"default": "extra", "chars": {"oO.": "text"},
              "boxes": [(4, 8, 0, 12, "accent")]},
        tones={"()": "6", "_.-~'": "7"}, below=1,
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.8, 14, ["o", ".", "O"], "d", seed=31),
        tile=r"""
  )(     (    )(       )     )(    (      )(    )
 (  )   ) )  (  )     ( (   (  )  ) )    (  )  ( (
""", tile_colours={"default": "good"}, tile_tones={"()": "4"})


# ---------------------------------------------------------------- phosphor

picture("terminal", r"""
.-------------------------------------------.
| ~ $ minitype --time 30                    |
|                                           |
|   the quick brown fox jumps over the_     |
|                                           |
|   wpm 112   acc 98%   [########--]        |
| ~ $ _                                     |
'-------------------------------------------'
""", colours={"default": "dim", "words": {"minitype": "text", "the": "text", "quick": "text",
                                          "brown": "text", "fox": "text", "jumps": "text",
                                          "over": "text", "wpm": "good", "acc": "good",
                                          "112": "accent", "98": "accent"},
              "chars": {"#": "good", "$~": "good"}},
        tones={"|-'.": "4"}, ground=lambda rows: [])


# ---------------------------------------------------------------- vaporwave

picture("palm", r"""
                               __ _.--..--._ _
      _.--''''--._          .-' _/   _/\_   \_'-.
    .'::::::::::::'.       |__ /   _/\__/\_   \__|
   /::::::::::::::::\         |___/\_\__/  \___|
  |==================|               \__/
  |------------------|                \__/
   \________________/                  \__/
                                        \__/
~^~^~^~^~^~^~^~^~^~^~^~                  \__/
  ~^~^~^~^~^~^~^~^~^~                     \__/

A  E  S  T  H  E  T  I  C
""", colours={"default": "extra", "rows": [(0, 2, "warn"), (3, 6, "error"), (8, 9, "accent"),
                                            (11, 11, "text")],
              "boxes": [(0, 9, 26, 60, "extra")]},
        tones={":": "8", "=": "7", "-": "6", "~^": "7"},
        ground=lambda rows: scatter(-3.0, 0.0, 1.6, 0.5, 22, ["*", ".", "+"], "t", seed=37))


# ---------------------------------------------------------------- candy

picture("lollipop", r"""
      _.--''''--._
    .'  _.--''--._'.
   /  .'  _.--._  '.\
  |  /  .'  __  '.  \|     ___
  |  |  |  (@ )  |  ||    >(@@@)<
  |  \  '.  ''  .'  /|
   \  '.  '-..-'  .'/
    '.  '-.____.-' .'             ___
      '-.________.-'            }(:::){
            ||
            ||
            ||
""", colours={"default": "error", "chars": {"|": "text"},
              "boxes": [(1, 7, 4, 18, "extra"), (2, 6, 7, 15, "warn"), (3, 4, 25, 34, "accent"),
                        (7, 8, 30, 40, "good"), (9, 11, 10, 15, "text")]},
        tones={"_.-'": "7", "@": "9"}, below=1,
        ground=lambda rows: [], tile=r"""
______________________________________________________
""", tile_colours={"default": "dim"})


# ---------------------------------------------------------------- summit

_CODE_GLYPHS = "0123456789ABCDEFHJKLPRSTUXZ=+-<>/?#$%"


def _code_wall(rows=12, cols=60, seed=8):
    """A wall of code, one glyph every other column."""
    import random
    rnd = random.Random(seed)
    return "\n" + "\n".join(" ".join(rnd.choice(_CODE_GLYPHS) for _ in range(cols // 2)) + " "
                            for _ in range(rows))


picture("summit", r"""
              |>
              |
             /\
            /''\
           /\/\/\
          /      \    .
         /  /\    \  /\
        /  /  \    \/  \
       /  /    \   /    \
      /  /      \ /  /\  \
     /  /        /  /  \  \
    /  /        /  /    \  \
""", colours={"default": "accent", "chars": {">": "error", "|": "text", "'": "text"},
              "boxes": [(2, 4, 0, 30, "text")]},
        tones={"'": "9", "/\\": "7"}, solid=True, ground=lambda rows: [],
        tile=_code_wall(), tile_colours={"default": "dim"}, tile_tones={_CODE_GLYPHS: "3"})


# ---------------------------------------------------------------- rose pine

picture("rose", r"""
       .-~~-.
     .' .-. '.
    /  ( @ )  \
   |  .'-~-'.  |
    \(       )/
     '-.___.-'
         |
     .-. | .-.
    (   \|/   )
     '-. | .-'
         |
         |
""", colours={"default": "good", "boxes": [(0, 5, 0, 20, "error"), (1, 3, 7, 12, "extra")]},
        tones={"~-.'": "7", "@": "9", "()": "7", "|\\/": "5"}, ground=lambda rows: [],
        **ground_tile(GRASS))
