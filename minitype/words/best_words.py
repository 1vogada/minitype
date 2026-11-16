"""Best words: a test made only of the words you type fastest and cleanest,
built from the history you already have, to push your top speed (the words
you can already fly through, so you practise going 180 instead of 120).

Speed comes from stats.word_speed (how fast you type each word correctly,
ms per char). Cleanliness comes from stats.word_clean (finished with no wrong
key) once a word has MIN_TYPED of those; before that it's estimated from the
per-key error rates the learn mode keeps (learn.stats: char -> [ms, presses,
misses]): the chance of typing every letter of the word without a miss.

A word is a candidate when it was timed at least MIN_TIMED times and is clean
enough: measured MIN_CLEAN or better, or estimated in the cleaner (1 - DROP)
share of your words. Of the candidates, the fastest MAX_POOL are the pool,
and a test draws faster words more often (weight (slowest / its ms) ** BIAS).
With fewer than MIN_POOL there's too little data: the menu says so and starts
the normal word test.

Its runs are their own mode ("best words", tagged "best" in the history):
they're kept out of the normal speed, accuracy and per-key statistics (the
profile shows them on their own rows), out of the word timings and bad-key
counts (so the pool doesn't feed on itself), and out of learn as you type
(no keystrokes go to the keyboard app).
"""

import math
import random

SOURCE = "best"         # TestSpec.source
LABEL = "best words"    # TestSpec.label, and the history mode
TAG = "best"            # a history run's "tag"
MIN_TYPED = 5           # finishes before word_clean is trusted over the estimate
MIN_CLEAN = 0.9         # measured share with no wrong key
DROP = 0.4              # estimated: the least clean 40% of the candidates are out
MIN_KEY_PRESSES = 30    # a key's error rate counts once it has this many presses
MIN_TIMED = 3           # times it was timed (typed correctly)
MIN_POOL = 20           # best words needed for the mode
MAX_POOL = 150
BIAS = 2                # how strongly faster words are drawn more often


def _key_errors(keys):
    return {c: v[2] / v[1] for c, v in (keys or {}).items()
            if isinstance(v, (list, tuple)) and len(v) >= 3 and v[1] >= MIN_KEY_PRESSES}


def _estimate(word, err):
    return math.prod(1 - err.get(c, 0.0) for c in word)


def eligible(stats, keys=None):
    """[(ms per char, word)] for the words fast and clean enough, fastest first."""
    err = _key_errors(keys)
    measured, guessed = [], []
    for w, speed in stats.word_speed.items():
        if not speed or speed[1] < MIN_TIMED:
            continue
        clean, typed = stats.word_clean.get(w, (0, 0))
        if typed >= MIN_TYPED:
            if clean >= MIN_CLEAN * typed:
                measured.append((speed[0], w))
        else:
            guessed.append((speed[0], w, _estimate(w, err)))
    if guessed and err:
        cut = sorted(e for _, _, e in guessed)[int(len(guessed) * DROP)]
        guessed = [g for g in guessed if g[2] >= cut]
    return sorted(measured + [(ms, w) for ms, w, _ in guessed])


def pool(stats, keys=None):
    """Your best words, fastest first; [] while there's too little data."""
    best = [w for _, w in eligible(stats, keys)[:MAX_POOL]]
    return best if len(best) >= MIN_POOL else []


def progress(stats, keys=None):
    """(best words found so far, MIN_POOL), for the menu."""
    return min(len(eligible(stats, keys)), MAX_POOL), MIN_POOL


def words(stats, n, rng=random, keys=None):
    """n words drawn from the pool, faster ones more often, no word twice in a
    row; [] with no pool."""
    p = pool(stats, keys)
    if not p:
        return []
    slowest = stats.word_speed[p[-1]][0]
    weight = [(slowest / max(stats.word_speed[w][0], 1.0)) ** BIAS for w in p]
    out = []
    for _ in range(n):
        w = rng.choices(p, weight)[0]
        while out and w == out[-1] and len(p) > 1:
            w = rng.choices(p, weight)[0]
        out.append(w)
    return out


def is_best(run):
    return run.get("tag") == TAG


def summary(history):
    """(tests, average speed, average accuracy, top speed) of the completed
    best-words runs, or None before there's one."""
    runs = [r for r in history.runs if is_best(r) and not r["failed"]]
    if not runs:
        return None
    sp = [history.speed(r) for r in runs]
    return len(runs), sum(sp) / len(sp), sum(r["acc"] for r in runs) / len(runs), max(sp)
