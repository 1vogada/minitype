"""Build minitype/terminal/art_detailed.py from the scenes in
tools/art_scenes.py.

    python tools/make_art.py            all of them
    python tools/make_art.py moon rose  just these (the rest are kept)
    python tools/make_art.py --show moon  print a scene instead
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import artgen                           # noqa: E402
from art_scenes import SCENES           # noqa: E402

OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_detailed.py")

HEADER = '''"""The detailed corner pictures, made by tools/make_art.py from the scenes
in tools/art_scenes.py - edit those and rebuild rather than this file.

DETAILED maps a picture's name to (span, sizes): span says whether its
background runs across the whole bottom of the screen, and each size,
biggest first, is (width, rows, keep). Each row is (indent, characters,
codes): a code for every character, its colour and how light it is (see
art.CODES). keep is where each row's focus starts: text may cut into a
row left of it, never right of it.
"""

DETAILED = {
'''


# a cell's colour letter and tone digit as one character: 7 x 10 codes
CODES = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+"
LETTERS = "dtexagw"


def pack(lines, parts, tones, keep):
    """(width, rows, keep), each row (indent, characters, codes)."""
    width = max(map(len, lines), default=0)
    rows = []
    for l, p, t in zip(lines, parts, tones):
        text = l.rstrip()
        lead = len(text) - len(text.lstrip())
        codes = "".join(" " if ch == " " else CODES[LETTERS.index(pc) * 10 + int(tc)]
                        for ch, pc, tc in zip(text[lead:], p[lead:], t[lead:]))
        rows.append((lead, text[lead:], codes))
    return width, tuple(rows), keep


def build(name):
    sc = SCENES[name]
    return sc.span, tuple(pack(*artgen.render(sc, rows)) for rows in sc.sizes)


def load():
    if not os.path.exists(OUT):
        return {}
    ns = {}
    with open(OUT, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns["DETAILED"]


def write(data):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER)
        for name in SCENES:
            if name not in data:
                continue
            span, sizes = data[name]
            f.write(f"    {name!r}: ({span}, (\n")
            for width, rows, keep in sizes:
                f.write(f"        ({width}, (\n")
                for row in rows:
                    f.write(f"            {row!r},\n")
                f.write(f"        ), {keep!r}),\n")
            f.write("    )),\n")
        f.write("}\n")


def main(args):
    if args and args[0] == "--show":
        for name in args[1:]:
            for rows in SCENES[name].sizes:
                lines = artgen.render(SCENES[name], rows)[0]
                print(f"===== {name} {rows}")
                print("\n".join(l[-120:] for l in lines))
        return
    names = args or list(SCENES)
    data = {} if not args else load()
    for name in names:
        data[name] = build(name)
        print("built", name)
    write(data)


if __name__ == "__main__":
    main(sys.argv[1:])
