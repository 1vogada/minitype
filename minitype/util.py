def cycle(seq, cur, missing=-1, step=1):
    """The item `step` places after cur in seq, wrapping around. If cur isn't
    in seq it is treated as sitting at index `missing`, so the default gives
    seq[0]."""
    i = seq.index(cur) if cur in seq else missing
    return seq[(i + step) % len(seq)]


def step_number(seq, cur, step=1):
    """Like cycle for a sorted list of numbers, but a value typed in
    between (35 in 0, 10 .. 100) steps to its neighbour (40, or 30 going
    back) instead of jumping to the start."""
    if cur in seq:
        return cycle(seq, cur, step=step)
    if step > 0:
        return next((v for v in seq if v > cur), seq[0])
    return next((v for v in reversed(seq) if v < cur), seq[-1])
