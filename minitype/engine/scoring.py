def score(words, typed, wi, keys, bad_keys, spaces, elapsed):
    """Returns (wpm, raw wpm, accuracy %)."""
    chars = spaces              # spaces typed after a cleanly finished word
    for i in range(min(wi + 1, len(words))):
        w, t = words[i], typed[i]
        chars += sum(1 for j, c in enumerate(t) if j < len(w) and c == w[j])
    mins = elapsed / 60
    wpm = (chars / 5) / mins if mins else 0
    raw = (keys / 5) / mins if mins else 0
    acc = 100 * (keys - bad_keys) / keys if keys else 0
    return wpm, raw, acc
