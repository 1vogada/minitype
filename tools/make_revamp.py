"""Build minitype/terminal/art_revamp.py: the "revamp" art style.

Each picture is a hand-drawn subject (tools/revamp_art.py) over scenery
that runs across the bottom of the screen, rendered in shape-matched
ASCII (tools/artgen_ascii.py) from the picture's scene in
tools/art_scenes.py - its background parts, or ones the picture gives.

In a drawing a blank lets the scenery show through, unless the drawing
closes it in (inside a tree, a moon), and "§" is a blank that never does. The subject is the focus: text may
cut into the scenery left of it, never into it.

    python tools/make_revamp.py              all of them
    python tools/make_revamp.py moon cat     just these (the rest are kept)
    python tools/make_revamp.py --show moon  print them, composed
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]

import art_combined                               # noqa: E402
import art_wow                                    # noqa: E402
import artgen                                     # noqa: E402
import artgen_ascii                               # noqa: E402
from art_scenes import SCENES                     # noqa: E402
from make_art import pack, squeeze                # noqa: E402
from revamp_art import OPAQUE, PICTURES           # noqa: E402
from minitype.terminal.art import LETTER_OF, _parts_of   # noqa: E402

OUT = os.path.join(HERE, "..", "minitype", "terminal", "art_revamp.py")
HEADER = '''"""The revamp corner pictures, made by tools/make_revamp.py: the big
pictures in tools/art_wow.py (every technique at once, for the themes that
have one) and otherwise the hand-drawn subjects in tools/revamp_art.py
over scenery rendered from tools/art_scenes.py - edit those and rebuild
rather than this file.

REVAMP holds each picture by name, packed like art_detailed.py: base85 of
zlib of JSON [span, [size]], the size [width, rows, keep], each row
[indent, characters, codes].
"""

'''


def enclosed(lines):
    """The blanks a drawing closes in: those that can't be reached from
    outside it through other blanks, going up, down, left or right. They
    hide the scenery, so a tree or a moon is solid, not see-through."""
    h = len(lines)
    w = max(map(len, lines), default=0)
    grid = [l.ljust(w) for l in lines]
    seen = set()
    todo = [(r, c) for r in range(-1, h + 1) for c in (-1, w)] +            [(r, c) for c in range(-1, w + 1) for r in (-1, h)]
    while todo:
        r, c = todo.pop()
        if (r, c) in seen:
            continue
        if 0 <= r < h and 0 <= c < w and grid[r][c] != " ":
            continue
        if not (-1 <= r <= h and -1 <= c <= w):
            continue
        seen.add((r, c))
        todo += [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    return {(r, c) for r in range(h) for c in range(w) if grid[r][c] == " " and (r, c) not in seen}


def compose(name):
    """The picture as (lines, parts, tones, keep, span)."""
    pic = PICTURES[name]
    rows = len(pic.lines)
    sc = SCENES.get(name)
    items = pic.ground(rows) if pic.ground else \
        [p for p in sc.parts_of(rows) if not getattr(p, "focus", True)] if sc else []
    span = bool(items or pic.tile) and (pic.span if pic.span is not None else True)
    width = max(map(len, pic.lines))
    if items:
        aspect = sc.aspect_of(rows) if sc and not pic.ground else width / (2 * rows)
        bg = artgen.Scene(aspect, items, span=span)
        chars, parts, tones = artgen_ascii.render(bg, rows, raw=True)
        cols = max(len(chars[0]), width)
        pad = cols - len(chars[0])
        chars = [[" "] * pad + row for row in chars]
        parts = [[" "] * pad + row for row in parts]
        tones = [[" "] * pad + row for row in tones]
    else:
        cols = max(width, artgen.SPAN_COLS) if span else width
        chars = [[" "] * cols for _ in range(rows)]
        parts = [[" "] * cols for _ in range(rows)]
        tones = [[" "] * cols for _ in range(rows)]
    left = cols - width - pic.margin if span else 0
    left = max(0, left)
    if left + width > cols:
        grow = left + width - cols
        for g in (chars, parts, tones):
            for row in g:
                row.extend([" "] * grow)
        cols += grow
    if pic.tile:
        # the hand-drawn ground, repeated from the right across the width
        tw = max(map(len, pic.tile))
        tnames = _parts_of(pic.tile, pic.tile_colours)
        top = rows - len(pic.tile)
        for r, tline in enumerate(pic.tile):
            tline = tline.ljust(tw)
            for c in range(min(cols, left + (width if pic.tile_under else 0))):  # not past the picture
                k = (c - cols) % tw
                ch = tline[k]
                if ch == " ":
                    continue
                if ch == OPAQUE:
                    chars[top + r][c], parts[top + r][c] = " ", " "
                    continue
                chars[top + r][c] = ch
                parts[top + r][c] = LETTER_OF[tnames[r][k]] if k < len(tnames[r]) else "d"
                tones[top + r][c] = pic.tile_tone(ch)
    names = _parts_of([l.replace(OPAQUE, " ") for l in pic.lines], pic.colours)
    shut = enclosed(pic.lines)
    keep = []
    for r, line in enumerate(pic.lines):
        first = None
        for k, ch in enumerate(line):
            if ch == " " and (r, k) in shut:
                ch = OPAQUE                        # inside the drawing: solid
            if ch == " ":
                continue
            c = left + k
            first = c if first is None else first
            if ch == OPAQUE:
                chars[r][c], parts[r][c], tones[r][c] = " ", " ", " "
                continue
            letter = pic.paint_at(r, k) or LETTER_OF[names[r][k]]
            chars[r][c], parts[r][c] = ch, letter
            tones[r][c] = pic.shade_at(r, k) or pic.tone_of_char(ch)
        keep.append(first if first is not None else cols)
    lines = ["".join(row).rstrip().ljust(cols) for row in chars]
    parts = ["".join(p if ch != " " else " " for p, ch in zip(prow, row)) for prow, row in zip(parts, chars)]
    tones = ["".join(t if ch != " " else " " for t, ch in zip(trow, row)) for trow, row in zip(tones, chars)]
    return lines, parts, tones, tuple(keep), span


def build(name):
    if name in art_wow.WOW:
        return build_wow(name)
    lines, parts, tones, keep, span = compose(name)
    return squeeze([span, [pack(lines, parts, tones, keep)]])


def build_wow(name):
    """A picture from tools/art_wow.py: every technique at once, in its
    theme's colours, at each of its sizes, biggest first (the app draws the
    biggest that fits)."""
    make = art_wow.WOW[name]
    pal = art_combined.Palette(make(art_combined.Palette("default")).theme)
    sc = make(pal)
    sizes = []
    for rows in sc.sizes:
        lines, parts, tones, bparts, btones, keep = art_combined.render(sc, rows, pal)
        sizes.append(pack(lines, parts, tones, keep, bparts, btones))
    return squeeze([sc.span, sizes])


def load():
    if not os.path.exists(OUT):
        return {}
    ns = {}
    with open(OUT, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("REVAMP", {})


def write(data):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER)
        f.write("REVAMP = {\n")
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
    if args and args[0] == "--show":
        names = [n for n in args[1:] or list(PICTURES) if n not in art_wow.WOW]
        width = int(os.environ.get("WIDTH", "90"))
        for name in names:
            lines = compose(name)[0]
            print(f"===== {name} ({len(lines)} rows)")
            print("\n".join(l[-width:].rstrip() for l in lines))
        return
    names = args or list(PICTURES)
    data = {} if not args else load()
    for name in names:
        data[name] = build(name)
        print("built", name)
    write(data)


if __name__ == "__main__":
    main(sys.argv[1:])
