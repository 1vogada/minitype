"""Build minitype/terminal/art_upscaled.py: the "upscaled" art style.

The same hand-drawn scenes as the revamp style (tools/art_wow*.py), drawn
bigger - SIZES rows tall - for big windows: the scenes are colour fields,
so a bigger picture is more detail, not the small one stretched. Each size
also carries the scene drawn on beyond it (tools/art_extend.py), out to
WIDE columns. The app offers these first and then the revamp sizes, so a
window too small for them still gets its picture (art.resolve).

    python tools/make_art_upscaled.py              every picture
    python tools/make_art_upscaled.py island moon  just these (the rest are kept)
    python tools/make_art_upscaled.py -j4 ...      four at a time
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]

import art_combined                               # noqa: E402
import art_wow                                    # noqa: E402
from make_art import squeeze                      # noqa: E402
from make_revamp import packed                    # noqa: E402
from revamp_art import PICTURES                   # noqa: E402

SIZES = (44, 36)            # biggest first; the revamp ones (28, 22, 16) come after
WIDE = 320                  # columns each is drawn out to, with its extension
OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_upscaled.py")
HEADER = '''"""The upscaled corner pictures, made by tools/make_art_upscaled.py: the
same hand-drawn scenes as the revamp style, drawn bigger for big windows
(more detail, not the small picture stretched). Edit the scenes in
tools/art_wow*.py and rebuild rather than this file. The app offers these
sizes first and then the revamp ones (art.resolve).

UPSCALED holds each picture by name, packed like art_revamp.py: base85 of
zlib of JSON [span, [size]], the size [width, rows, keep, extension], each
row [indent, characters, codes, back codes].
"""

'''


def build(name):
    """A picture from tools/art_wow*.py at the upscaled sizes, packed."""
    make = art_wow.WOW[name]
    pal = art_combined.Palette(make(art_combined.Palette("default")).theme)
    sc = make(pal)
    return squeeze([sc.span, [packed(sc, rows, pal, WIDE) for rows in SIZES]])


def load():
    if not os.path.exists(OUT):
        return {}
    ns = {}
    with open(OUT, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("UPSCALED", {})


def write(data):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER)
        f.write("UPSCALED = {\n")
        for name in PICTURES:
            if name in data:
                f.write(f"    {name!r}: (\n")
                text = data[name]
                for i in range(0, len(text), 72):
                    f.write(f"        {text[i:i + 72]!r}\n")
                f.write("    ),\n")
        f.write("}\n")


def main(args):
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    jobs = 1
    if args and args[0].startswith("-j"):
        jobs, args = int(args[0][2:] or 4), args[1:]
    names = args or [n for n in PICTURES if n in art_wow.WOW]
    for name in names:
        if name not in art_wow.WOW:
            raise SystemExit(f"no such picture: {name}")
    data = load() if args else {}
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            for name, built in zip(names, pool.map(build, names)):
                data[name] = built
                print("built", name, flush=True)
    else:
        for name in names:
            data[name] = build(name)
            print("built", name, flush=True)
    write(data)
    print("wrote", OUT, len(data), "pictures")


if __name__ == "__main__":
    main(sys.argv[1:])
