import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from minitype.context import App
from minitype.words import hand_words, themed
from minitype.words.bank import WordBank

# hand letters from the layout rows
assert themed.hand_letters("qwerty", "left") == set("qwertasdfgzxcvb")
assert themed.hand_letters("qwerty", "right") == set("yuiophjklnm")
assert themed.hand_letters("dvorak", "left") == set("pyaoeuiqjkx")
assert themed.hand_letters("colemak", "left") == set("qwfpgarstdzxcvb")
assert themed.home_letters("qwerty") == set("asdfghjkl")

# every word in each list really is one-handed on that layout
for layout in ("qwerty", "colemak", "dvorak", "qwertz", "azerty"):
    for side, fn in (("left", themed.left_hand), ("right", themed.right_hand)):
        ws = fn(layout)
        keys = themed.hand_letters(layout, side)
        bad = [w for w in ws if not set(w) <= keys]
        assert not bad, (layout, side, bad[:5])
        print(f"{layout:8} {side:5} {len(ws):4}  {' '.join(ws[:10])}")
    hr = themed.home_row(layout)
    assert all(set(w) <= themed.home_letters(layout) for w in hr)
    print(f"{layout:8} home  {len(hr):4}  {' '.join(hr[:10])}")

# qwerty lists grew from 188 / 91 to the generated sizes, old curated words kept
L, R = themed.left_hand(), themed.right_hand()
assert len(L) >= 750 and len(R) >= 120, (len(L), len(R))
assert {"stewardess", "watercress", "were", "vested"} <= set(L)
assert {"you", "pumpkin", "lollipop", "yummy"} <= set(R)
assert "ninja" not in R, "the old curated list had it, but 'a' is a left-hand key"
# a layout with too few words falls back to built-in and says why
b = WordBank()
assert b.load("right hand", layout="dvorak") is False
assert b.source == "built-in" and "right hand words on dvorak" in b.note, b.note
# nothing blocked slipped through, generated lists are qwerty-clean
blocked = {"injun", "poon", "texas", "july", "honolulu", "fart"}
assert not blocked & set(L + R)
assert all(set(w) <= set("qwertasdfgzxcvb") for w in hand_words.LEFT)
assert all(set(w) <= set("yuiophjklnm") for w in hand_words.RIGHT)

# downloaded lists feed the pool (more words on other layouts)
b = WordBank()
b._cache["x"] = ["papaya", "yuppie", "Okay", "kiwi"]  # dvorak left hand, bar kiwi
b.load("left hand", layout="dvorak")
assert {"papaya", "yuppie", "okay"} <= set(b.words) and "kiwi" not in b.words, b.words
assert b.note == f"{len(b.words)} words, left hand on dvorak", b.note

# the app rebuilds the list when the layout changes
app = App()
app.load_words("right hand")
q = list(app.bank.words)
app.settings.layout = "colemak"
app.layout_changed()
assert app.bank.source == "right hand" and app.bank.words != q
assert all(set(w) <= themed.hand_letters("colemak", "right") for w in app.bank.words)
# dvorak has no right-hand words: built-in for now, but the choice is kept
app.settings.layout = "dvorak"
app.layout_changed()
assert app.bank.source == "built-in" and app.settings.word_source == "right hand"
assert "right hand words on dvorak" in app.bank.note
app.settings.layout = "qwerty"
app.layout_changed()
assert app.bank.source == "right hand" and app.bank.words == q, "back to qwerty restores it"
# a non-hand list is left alone on a layout change
app.load_words("programming"); v = app.bank.version
app.layout_changed(); assert app.bank.version == v
print("ALL OK")
