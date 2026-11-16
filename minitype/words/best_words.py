"""Best words: a test made only of the words you type best, fast and clean,
from your history (stats.word_speed: how fast you type each word correctly;
stats.word_clean: how often you type it with no wrong key at all).

A word counts as one of your best only with enough history behind it:
typed at least MIN_TYPED times, at least MIN_CLEAN of them clean, and timed
correctly at least MIN_TIMED times. Of the words that make it, the fastest
half are your best (at most MAX_POOL). With fewer than MIN_POOL best words
there's too little data: the menu says so and starts the normal word test.

Its runs are their own mode ("best words", tagged "best" in the history):
they're kept out of the normal speed, accuracy and per-key statistics (the
profile shows them on their own rows), out of the word timings and bad-key
counts (so the pool doesn't feed on itself), and out of learn as you type
(no keystrokes go to the keyboard app).
"""

import random

SOURCE = "best"         # TestSpec.source
LABEL = "best words"    # TestSpec.label, and the history mode
TAG = "best"            # a history run's "tag"
MIN_TYPED = 5           # times a word was finished
MIN_CLEAN = 0.9         # share of them with no wrong key
MIN_TIMED = 3           # times it was timed (typed correctly)
MIN_POOL = 20           # best words needed for the mode
MAX_POOL = 150


def eligible(stats):
    """[(ms per char, word)] for the words with enough clean history, fastest first."""
    out = []
    for w, (clean, typed) in stats.word_clean.items():
        speed = stats.word_speed.get(w)
        if typed < MIN_TYPED or clean < MIN_CLEAN * typed or not speed or speed[1] < MIN_TIMED:
            continue
        out.append((speed[0], w))
    return sorted(out)


def pool(stats):
    """Your best words, fastest first; [] while there's too little data."""
    ok = eligible(stats)
    best = [w for _, w in ok[:min(MAX_POOL, len(ok) // 2)]]
    return best if len(best) >= MIN_POOL else []


def progress(stats):
    """(best words found so far, MIN_POOL), for the menu."""
    return min(len(eligible(stats)) // 2, MAX_POOL), MIN_POOL


def words(stats, n, rng=random):
    """n words drawn from the pool, no word twice in a row; [] with no pool."""
    p = pool(stats)
    if not p:
        return []
    out = []
    for _ in range(n):
        w = rng.choice(p)
        if out and w == out[-1] and len(p) > 1:
            w = rng.choice([x for x in p if x != out[-1]])
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
