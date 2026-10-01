"""Funbox modifiers that change the words you type. "mirror" doesn't change
the words at all - the renderer flips how each one is drawn."""

import random


def _random_case(w):
    return "".join(c.upper() if random.random() < 0.5 else c.lower() for c in w)


MODIFIERS = {
    "reversed": lambda w: w[::-1],
    "caps": str.upper,
    "random case": _random_case,
}


def apply(words, mode):
    f = MODIFIERS.get(mode)
    return [f(w) for w in words] if f else list(words)
