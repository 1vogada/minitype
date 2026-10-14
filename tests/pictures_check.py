"""The picture sets stay in step, and no picture is silently dropped.

tools/make_revamp.py builds every name in art_wow.WOW but only saves the
names listed in revamp_art.PICTURES, so a "wow" picture that is not also
registered as a picture is built and then thrown away without a word. The
same shape of mistake applies to the other art data files. This checks the
sets agree, and that every picture a theme can draw exists in each of the
files the styles are served from.
"""
import os
import sys
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, os.path.join(ROOT, "tools")]

from minitype.terminal import art as art_mod
from minitype.terminal.art import ART, LARGE, THEME_ART         # noqa: E402
from revamp_art import PICTURES                                 # noqa: E402
import art_wow                                                  # noqa: E402

# the stored revamp data (art.py keeps it private; this check is about the
# data files agreeing, so it reads it the way the loader does)
REVAMP = art_mod._REVAMP

# every wow picture must be a registered picture, or its build is discarded
loose = sorted(set(art_wow.WOW) - set(PICTURES))
assert not loose, ("art_wow.WOW holds pictures that revamp_art.PICTURES does not, "
                   "so make_revamp.py builds and then drops them: " + ", ".join(loose))

# and the other way round, so a picture that lost its scene is noticed
gone = sorted(set(PICTURES) - set(art_wow.WOW))
assert not gone, ("revamp_art.PICTURES holds pictures with no scene in "
                  "art_wow.WOW, so they cannot be rebuilt: " + ", ".join(gone))

# the stored revamp data covers exactly those pictures
assert set(REVAMP) == set(PICTURES), (
    sorted(set(PICTURES) - set(REVAMP)) + sorted(set(REVAMP) - set(PICTURES)))

# a theme may only point at a picture that every style can serve
for theme, name in sorted(THEME_ART.items()):
    assert name in ART, (theme, name, "not in ART")
    assert name in REVAMP, (theme, name, "not in REVAMP (rebuild the revamp art)")

# LARGE is a smaller set (not every picture has a large hand-drawn version),
# but anything in it must be a real picture
assert set(LARGE) <= set(ART), sorted(set(LARGE) - set(ART))

print("ALL OK")
