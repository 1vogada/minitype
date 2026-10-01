def score(words, typed, wi, keys, bad_keys, elapsed):
    """Returns (wpm, raw wpm, accuracy %)."""
    # spaces after cleanly finished words count as correct characters
    chars = sum(1 for i in range(min(wi, len(words))) if typed[i] == words[i])
    for i in range(min(wi + 1, len(words))):
        w, t = words[i], typed[i]
        chars += sum(1 for j, c in enumerate(t) if j < len(w) and c == w[j])
    mins = elapsed / 60
    wpm = (chars / 5) / mins if mins else 0
    raw = (keys / 5) / mins if mins else 0
    acc = 100 * (keys - bad_keys) / keys if keys else 0
    return wpm, raw, acc


def speed_series(events, elapsed, buckets):
    """Split the test into `buckets` equal slices and return (wpm, errors)
    for each: correct presses in the slice as words per minute, and how many
    wrong presses landed in it."""
    if elapsed <= 0 or buckets <= 0:
        return []
    size = elapsed / buckets
    ok = [0] * buckets
    bad = [0] * buckets
    for t, good in events:
        b = min(buckets - 1, int(t / size))
        if good:
            ok[b] += 1
        else:
            bad[b] += 1
    return [((n / 5) / (size / 60), e) for n, e in zip(ok, bad)]
