"""Build minitype/terminal/art_detailed.py from the scenes in
tools/art_scenes.py: every picture in ASCII ("detailed") and in block
characters ("blocks"), at each of its sizes.

    python tools/make_art.py              all of them
    python tools/make_art.py moon rose    just these (the rest are kept)
    python tools/make_art.py --show moon  print a scene in ASCII
    python tools/make_art.py --blocks moon  print it in blocks
"""

import base64
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import artgen                           # noqa: E402
from art_scenes import SCENES           # noqa: E402

OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_detailed.py")

HEADER = '''"""The detailed corner pictures, made by tools/make_art.py from the scenes
in tools/art_scenes.py - edit those and rebuild rather than this file.

DETAILED holds each picture in ASCII and BLOCKS in block characters, by
name, packed: base85 of zlib of JSON [span, sizes]. span says whether its
background runs across the whole bottom of the screen, and each size,
biggest first, is [width, rows, keep]. Each row is [indent, characters,
codes] in ASCII, plus background codes in blocks: a code for every
character, its colour and how light it is (see art.CODES), " " for none.
keep is where each row's focus starts: text may cut into a row left of
it, never right of it.
"""

'''

# a cell's colour letter and tone digit as one character: 7 x 10 codes
CODES = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+"
LETTERS = "dtexagw"


def code_of(part, tone):
    return " " if part == " " else CODES[LETTERS.index(part) * 10 + int(tone)]


def pack(lines, parts, tones, keep, bparts=None, btones=None):
    """[width, rows, keep], each row [indent, characters, codes(, back codes)]."""
    width = max(map(len, lines), default=0)
    rows = []
    for k, (l, p, t) in enumerate(zip(lines, parts, tones)):
        text = l.rstrip()
        lead = len(text) - len(text.lstrip())
        codes = "".join(" " if ch == " " else code_of(pc, tc)
                        for ch, pc, tc in zip(text[lead:], p[lead:], t[lead:]))
        row = [lead, text[lead:], codes]
        if bparts is not None:
            row.append("".join(code_of(bp, bt) for bp, bt in
                               zip(bparts[k][lead:len(text)], btones[k][lead:len(text)])))
        rows.append(row)
    return [width, rows, list(keep)]


def squeeze(data):
    return base64.b85encode(zlib.compress(json.dumps(data, separators=(",", ":")).encode(), 9)).decode()


def build(name):
    sc = SCENES[name]
    ascii_ = [pack(*artgen.render(sc, rows)) for rows in sc.sizes]
    blocks = []
    for rows in sc.sizes:
        lines, parts, tones, bparts, btones, keep = artgen.render_blocks(sc, rows)
        blocks.append(pack(lines, parts, tones, keep, bparts, btones))
    return squeeze([sc.span, ascii_]), squeeze([sc.span, blocks])


def load():
    if not os.path.exists(OUT):
        return {}, {}
    ns = {}
    with open(OUT, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("DETAILED", {}), ns.get("BLOCKS", {})


def write(detailed, blocks):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER)
        for title, data in (("DETAILED", detailed), ("BLOCKS", blocks)):
            f.write(f"{title} = {{\n")
            for name in SCENES:
                if name in data:
                    f.write(f"    {name!r}: (\n")
                    text = data[name]
                    for i in range(0, len(text), 72):
                        f.write(f"        {text[i:i + 72]!r}\n")
                    f.write("    ),\n")
            f.write("}\n\n")


def main(args):
    if args and args[0] in ("--show", "--blocks"):
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        for name in args[1:]:
            for rows in SCENES[name].sizes:
                if args[0] == "--show":
                    lines = artgen.render(SCENES[name], rows)[0]
                else:
                    lines = artgen.render_blocks(SCENES[name], rows)[0]
                print(f"===== {name} {rows}")
                print("\n".join(l[-120:] for l in lines))
        return
    names = args or list(SCENES)
    detailed, blocks = ({}, {}) if not args else load()
    for name in names:
        detailed[name], blocks[name] = build(name)
        print("built", name)
    write(detailed, blocks)


if __name__ == "__main__":
    main(sys.argv[1:])
