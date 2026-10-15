"""Build minitype/terminal/art_upscaled.py: the "upscaled" art style.

The same hand-drawn scenes as the revamp style (tools/art_wow*.py), drawn
in truecolour (tools/art_truecolor.py): every cell its exact two colours
instead of the theme's 70, so skies are smooth gradients instead of bands
and grain, edges are anti-aliased and shading inside a subject shows. At
every size the revamp style has, and bigger ones for big windows (SIZES):
the scenes are colour fields, so a bigger picture is more detail, not the
small one stretched. Each size carries the scene drawn on beyond it
(tools/art_extend.py), out to WIDE columns.

    python tools/make_art_upscaled.py              every picture
    python tools/make_art_upscaled.py island moon  just these (the rest are kept)
    python tools/make_art_upscaled.py -j4 ...      four at a time
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]

import art_combined                               # noqa: E402
import art_extend                                 # noqa: E402
import art_wow                                    # noqa: E402
from make_art import squeeze                      # noqa: E402
from revamp_art import PICTURES                   # noqa: E402

SIZES = (44, 36, 28, 22, 16)    # biggest first: the app draws the biggest that fits
WIDE = 300                      # columns each is drawn out to, with its extension
# a colour as three characters, 6 bits a channel (steps of 4 out of 255,
# finer than the eye sees in a gradient); "!!!" for none
ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/"
OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_upscaled.py")
HEADER = '''"""The upscaled corner pictures, made by tools/make_art_upscaled.py: the
same hand-drawn scenes as the revamp style, drawn in truecolour (every
cell its exact colours) at the revamp sizes and bigger ones for big
windows. Edit the scenes in tools/art_wow*.py and rebuild rather than this
file.

UPSCALED holds each picture by name, packed like art_revamp.py: base85 of
zlib of JSON [span, [size]], the size [width, rows, keep, extension, 1]
(the 1: truecolour), each row [characters, colours, back colours], a colour
three characters of ALPHA in tools/make_art_upscaled.py ("!!!" for none).
"""

'''


def colour(c):
    if c is None:
        return "!!!"
    return "".join(ALPHA[min(63, round(v * 63 / 255))] for v in c)


def grid(lines, fg, bg):
    """Rows packed: [characters, colours, back colours]."""
    return [[line, "".join(map(colour, f)), "".join(map(colour, b))]
            for line, f, b in zip(lines, fg, bg)]


def packed(sc, rows, pal):
    """One size of a scene in truecolour, packed, with its extension."""
    (lines, fg, bg, keep), ext = art_extend.render_ext(sc, rows, pal, WIDE, truecolour=True)
    size = [len(lines[0]), grid(lines, fg, bg), list(keep), None, 1]
    if ext:
        left, up, top, side = ext
        size[3] = [left, up, [len(top[0][0]), grid(*top), []], [left, grid(*side), []]]
    return size


def build(name):
    """A picture from tools/art_wow*.py at the upscaled sizes, packed."""
    make = art_wow.WOW[name]
    pal = art_combined.Palette(make(art_combined.Palette("default")).theme)
    sc = make(pal)
    return squeeze([sc.span, [packed(sc, rows, pal) for rows in SIZES]])


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


def done(packed_text):
    """Whether a stored picture is already in truecolour (so a build can
    pick up where it stopped)."""
    import base64
    import json
    import zlib
    sizes = json.loads(zlib.decompress(base64.b85decode(packed_text)))[1]
    return [len(sz) > 4 and sz[4] == 1 for sz in sizes] == [True] * len(SIZES)         and [len(sz[1]) for sz in sizes] == list(SIZES)


def main(args):
    """Builds the pictures asked for (all by default), writing the file
    after each one, so a build that is stopped keeps what it finished.
    Without --again, pictures already built in truecolour are skipped."""
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    jobs, again = 1, "--again" in args
    args = [a for a in args if a != "--again"]
    if args and args[0].startswith("-j"):
        jobs, args = int(args[0][2:] or 4), args[1:]
    names = args or [n for n in PICTURES if n in art_wow.WOW]
    for name in names:
        if name not in art_wow.WOW:
            raise SystemExit(f"no such picture: {name}")
    data = load()
    if not again:
        names = [n for n in names if not (n in data and done(data[n]))]
    print(len(names), "to build:", " ".join(names), flush=True)
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(jobs) as pool:
            futures = {pool.submit(build, name): name for name in names}
            for k, future in enumerate(as_completed(futures), 1):
                name = futures[future]
                data[name] = future.result()
                write(data)
                print(f"built {name} ({k}/{len(names)})", flush=True)
    else:
        for k, name in enumerate(names, 1):
            data[name] = build(name)
            write(data)
            print(f"built {name} ({k}/{len(names)})", flush=True)
    print("wrote", OUT, len(data), "pictures")


if __name__ == "__main__":
    main(sys.argv[1:])
