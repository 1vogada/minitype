def cycle(seq, cur, missing=-1, step=1):
    """The item `step` places after cur in seq, wrapping around. If cur isn't
    in seq it is treated as sitting at index `missing`, so the default gives
    seq[0]."""
    i = seq.index(cur) if cur in seq else missing
    return seq[(i + step) % len(seq)]
