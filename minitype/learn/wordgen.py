"""Lesson words: real words where enough fit the unlocked letters, and
pronounceable made-up ones otherwise."""

import random

from .progress import ORDER

_model_cache = (None, None)


def _bump(table, key, c):
    d = table.setdefault(key, {})
    d[c] = d.get(c, 0) + 1


def _model(bank):
    """Letter-sequence statistics of the current word list, used to make up
    pronounceable words from whichever letters are unlocked."""
    global _model_cache
    if _model_cache[0] == bank.version:
        return _model_cache[1]
    m2, m1 = {}, {}
    for w in bank.words:
        if not (w.isalpha() and w.isascii() and w.islower()):
            continue
        s = "^^" + w + "$"
        for i in range(2, len(s)):
            _bump(m2, s[i - 2:i], s[i])
            _bump(m1, s[i - 1], s[i])
    _model_cache = (bank.version, (m2, m1))
    return m2, m1


def pseudo_word(bank, allowed, focus):
    """Make up a word from the allowed letters that contains the focus key.
    Tries a batch and keeps the one that leaned least on fallback statistics,
    which is what keeps them pronounceable."""
    m2, m1 = _model(bank)
    good = []
    for _ in range(40):
        out, back = "", 0
        while len(out) < 7:
            ctx = ("^^" + out)[-2:]
            opts = None
            for lvl, (table, k) in enumerate(((m2, ctx), (m1, ctx[-1]))):
                cand = {c: (n * (1 + max(0, len(out) - 3)) if c == "$" else n)
                        for c, n in table.get(k, {}).items()
                        if c in allowed or (c == "$" and len(out) >= 3)}
                if cand:
                    opts = cand
                    back += lvl
                    break
            if not opts:
                break
            c = random.choices(list(opts), list(opts.values()))[0]
            if c == "$":
                break
            out += c
        if 3 <= len(out) <= 7 and (focus is None or focus in out):
            good.append((back, random.random(), out))
    if good:
        return min(good)[2]
    w = "".join(random.choices(sorted(allowed), k=4))
    if focus and focus not in w:
        i = random.randrange(len(w))
        w = w[:i] + focus + w[i + 1:]
    return w


def natural_pool(bank, allowed, focus):
    return [w for w in bank.words
            if len(w) >= 3 and set(w) <= allowed
            and (focus is None or focus in w)]


def lesson_words(progress, bank, n):
    allowed = set(ORDER[:progress.unlocked()])
    foc = progress.focus_key()
    nat = natural_pool(bank, allowed, foc) if progress.config["natural"] else []
    p = min(1.0, len(nat) / 20)         # few real words -> lean on made-up ones
    out = []
    for _ in range(n):
        for _try in range(6):
            if nat and random.random() < p:
                w = random.choice(nat)
            else:
                w = pseudo_word(bank, allowed, foc)
            if not out or w != out[-1]:
                break
        out.append(w)
    return out
