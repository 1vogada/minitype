"""Build minitype/terminal/art_upscaled.py: the "upscaled" art style.

Each picture is the same scene as its revamp picture, drawn with
tools/art_upscaled.py at braille resolution. That is a lot of data, so this
grows one picture at a time:

    python tools/make_art_upscaled.py island moon     just these
    python tools/make_art_upscaled.py                 every picture asked for
                                                      (a long wait)

A picture not built here has no upscaled version, and the app falls back to
its revamp picture for that theme.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]

import art_combined                               # noqa: E402
import art_upscaled                               # noqa: E402
import art_wow                                    # noqa: E402
from make_art import pack, squeeze                # noqa: E402

OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_upscaled.py")
HEADER = '''"""The upscaled corner pictures, made by tools/make_art_upscaled.py: the
same scenes as the revamp style, drawn at braille resolution (see
tools/art_upscaled.py). Only the pictures listed here exist in this style;
a theme without one falls back to its revamp picture.

UPSCALED holds each picture by name, packed like art_revamp.py: base85 of
zlib of JSON [span, [size]], the size [width, rows, keep], each row
[indent, characters, codes, back codes].
"""

'''


def build(name):
    """A picture from tools/art_wow.py, at each of its sizes."""
    make = art_wow.WOW[name]
    pal = art_combined.Palette(make(art_combined.Palette("default")).theme)
    sc = make(pal)
    sizes = []
    for rows in sc.sizes:
        lines, parts, tones, bparts, btones, keep = art_upscaled.render(sc, rows, pal)
        sizes.append(pack(lines, parts, tones, keep, bparts, btones))
    return squeeze([sc.span, sizes])


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
        for name in sorted(data):
            f.write(f"    {name!r}: (\n")
            text = data[name]
            for i in range(0, len(text), 72):
                f.write(f"        {text[i:i + 72]!r}\n")
            f.write("    ),\n")
        f.write("}\n")


def main(args):
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    names = args or ["island"]
    data = load() if args else {}
    for name in names:
        if name not in art_wow.WOW:
            raise SystemExit(f"no such picture: {name}")
        data[name] = build(name)
        print("built", name)
    write(data)
    print("wrote", OUT, "pictures:", ", ".join(sorted(data)))


if __name__ == "__main__":
    main(sys.argv[1:])
