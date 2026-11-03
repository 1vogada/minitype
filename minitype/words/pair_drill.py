"""Mixed-up keys: a drill made from the keys you mix up (main menu, practice).

The keyboard app sees which keys get pressed for which: `patterns.fingers`
(the wrong finger pressed the key next to the one you meant: meant K,
typed L) and `patterns.pairs` (plain wrong keys). pairs_from() takes the
top few, fingers first; words() builds a test from them, like the bad keys
drill builds one from your bad keys (generator.bad_pool): words holding
both keys of a pair, the closer together the more often (k and l side
by side in "milk" come up more than in "lake"), and where words can't help (digits, symbols, a pair few
words hold) short runs of the two keys ("898", "9889").
"""

import random

TOP = 3             # pairs drilled at once, at most
MIN_WORDS = 8       # a pair with fewer words holding both gets runs instead
RUN = (2, 5)        # a run's length
CLOSE = 3           # letters apart that still count as close


def _char(v):
    """A key as a char to type: one character, lower case; "Space" etc. aren't."""
    if not isinstance(v, str) or len(v) != 1 or v.isspace():
        return None
    return v.lower()


def pairs_from(patterns, top=TOP):
    """[(a, b, count)] from the app's patterns: fingers (meant, typed) if it
    has any, else pairs (expected, typed); most first, the same two keys
    either way round counted together."""
    if not isinstance(patterns, dict):
        return []
    for field, want in (("fingers", "meant"), ("pairs", "expected")):
        found = {}
        items = patterns.get(field)
        for p in items if isinstance(items, list) else []:
            if not isinstance(p, dict):
                continue
            a, b, n = _char(p.get(want)), _char(p.get("typed")), p.get("count")
            if a and b and a != b and type(n) is int and n > 0:
                key = (a, b) if (b, a) not in found else (b, a)
                found[key] = found.get(key, 0) + n
        if found:
            ranked = sorted(found.items(), key=lambda kv: -kv[1])[:top]
            return [(a, b, n) for (a, b), n in ranked]
    return []


def closeness(word, a, b):
    """How close the nearest a and b sit in word (1 = side by side), or None
    if it doesn't hold both."""
    ia = [i for i, c in enumerate(word) if c == a]
    ib = [i for i, c in enumerate(word) if c == b]
    if not ia or not ib:
        return None
    return min(abs(i - j) for i in ia for j in ib)


def pool(bank_words, a, b):
    """The words for pair (a, b): those holding both, close ones repeated more."""
    out = []
    for w in bank_words:
        d = closeness(w.lower(), a, b)
        if d is not None:
            out += [w] * (3 if d == 1 else 2 if d <= CLOSE else 1)
    return out


def run(a, b, rng=random):
    """A short run of the two keys, both in it: "898", "kllk"."""
    n = rng.randint(*RUN)
    s = [rng.choice((a, b)) for _ in range(n)]
    if a not in s:
        s[rng.randrange(n)] = a
    if b not in s:
        s[(s.index(a) + 1) % n] = b
    return "".join(s)


def words(bank_words, pairs, count, rng=random):
    """`count` words drilling `pairs` ([(a, b, n)]), each pair as often as
    it's mixed up."""
    if not pairs:
        return []
    pools = {(a, b): pool(bank_words, a, b) for a, b, _ in pairs}
    weights = [n for _, _, n in pairs]
    out = []
    for _ in range(count):
        a, b, _ = rng.choices(pairs, weights)[0]
        p = pools[(a, b)]
        if len(set(p)) >= MIN_WORDS and rng.random() < 0.85:
            out.append(rng.choice(p))
        else:
            out.append(run(a, b, rng))
    return out


def label(pairs):
    """ "k↔l 8↔9" for the menu and the results."""
    return " ".join(f"{a}↔{b}" for a, b, _ in pairs)
