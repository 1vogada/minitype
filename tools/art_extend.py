"""More of a scene than its picture shows: the same scene drawn further up
and further left, so the app can fill a big window with the scene itself
instead of copying columns or guessing a sky.

A picture spans (its scenery runs on to the left) and sits at the bottom
right, so on a wide window it grows leftwards and on a tall one upwards.
The scenes in tools/art_wow*.py are colour fields defined everywhere, so
the extension is simply more of the field, drawn cell by cell exactly as
the picture is (art_combined.draw) - the picture itself is unchanged and
the seam between them is invisible.

Text (stars, sparkles, falling glyphs) is the one thing a scene only
places where its picture is. In the extension it is carried on from the
picture's own: the stars of its top band repeated upwards and the text of
each row repeated leftwards, each copy shifted at random, and only on to
cells of the same kind (sky stars stay in the sky) - sparse specks over a
continuous sky, so the repeat doesn't show.
"""
import copy
import random

import art_combined as ac

TALLER = 0.5          # rows drawn above a picture: this share of its height
WIDE = 260            # columns a picture is drawn out to, with the extension


def render_ext(scene, rows, pal, wide=WIDE, taller=TALLER):
    """The picture `rows` tall (as art_combined.render gives it) and its
    extension: (picture, ext). ext is None for a picture that doesn't
    span, else (left, up, top, side): `left` columns and `up` rows more,
    `top` the rows above it (left + its width wide) and `side` the columns
    left of it (its height tall), each as (chars, parts, tones, back
    parts, back tones) lists of rows."""
    pal = pal or ac.Palette(scene.theme)
    unit, cw, cols, x_left = ac.geometry(scene, rows)
    texts = {(r, c): (ch, rgb, foc) for c, r, ch, rgb, foc in scene.texts(rows, x_left, cw, unit)
             if 0 <= r < rows and 0 <= c < cols}
    picture = ac._trim(scene, *ac.draw(scene, rows, pal, range(rows), range(cols), texts)[:6])
    if not scene.span:
        return picture, None
    lines = picture[0]
    width, height = len(lines[0]) if lines else 0, len(lines)
    first = rows - height                 # rows the picture dropped off its top
    left = max(0, wide - width)
    up = int(rows * taller)
    if not (left or up):
        return picture, None

    def kind(r, c):
        """What a cell is (the scene's tag at its middle): text is only
        carried on to cells of the same kind as where it came from."""
        return scene.field(x_left + (c + 0.5) * cw, (r + 0.5) * unit)[3]

    # a scene is drawn for its picture: anywhere beyond it that it can't
    # be worked out (a power of a negative number above its top...) takes
    # the scene at the nearest point of the picture instead of failing
    field = scene.field

    def safe(x, y):
        try:
            got = field(x, y)
            if not isinstance(got[0][0], complex):
                return got
        except (TypeError, ValueError, ZeroDivisionError, OverflowError, IndexError):
            pass
        return field(max(x, x_left), max(y, 0.0))
    scene = copy.copy(scene)
    scene.field = safe

    top_rows, top_cols = range(first - up, first), range(-left, width)
    side_rows, side_cols = range(first, rows), range(-left, 0)
    seed = sum(map(ord, scene.theme)) * 7919 + rows
    top_texts = _carry_up(texts, kind, first, rows, width, top_rows, top_cols, seed)
    side_texts = _carry_left(texts, kind, first, width, side_rows, side_cols, seed + 1)
    top = ac.draw(scene, rows, pal, top_rows, top_cols, top_texts)[:5]
    side = ac.draw(scene, rows, pal, side_rows, side_cols, side_texts)[:5]
    return picture, (left, up, _joined(top), _joined(side))


def _joined(grid):
    return tuple([("".join(row)) for row in g] for g in grid)


def _carry_up(texts, kind, first, rows, width, row_range, col_range, seed):
    """The texts of the picture's top band (not its subject), repeated up
    over the rows above it, each copy shifted sideways at random."""
    band = max(2, int((rows - first) * 0.4))
    pattern = [(r - first, c, t) for (r, c), t in texts.items()
               if first <= r < first + band and not t[2] and 0 <= c < width]
    out, rng = {}, random.Random(seed)
    span = col_range.stop - col_range.start
    k = 0
    while row_range.stop - k * band > row_range.start:
        k += 1
        shift = rng.randrange(span)
        for dr, c, t in pattern:
            r = first - k * band + dr
            cc = (c + shift - col_range.start) % span + col_range.start
            if r in row_range and kind(r, cc) == kind(first + dr, c):
                out[(r, cc)] = t
    return out


def _carry_left(texts, kind, first, width, row_range, col_range, seed):
    """Each row's texts (not its subject), repeated on leftwards over the
    columns left of the picture, each copy shifted at random."""
    rows_of = {}
    for (r, c), t in texts.items():
        if r >= first and not t[2] and 0 <= c < width:
            rows_of.setdefault(r, []).append((c, t))
    out, rng = {}, random.Random(seed)
    k = 0
    while -k * width > col_range.start:
        k += 1
        shift = rng.randrange(width // 4)
        for r, items in rows_of.items():
            if r not in row_range:
                continue
            for c, t in items:
                cc = c - k * width + shift
                if cc in col_range and kind(r, cc) == kind(r, c):
                    out[(r, cc)] = t
    return out
