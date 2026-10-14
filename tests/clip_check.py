import os, random, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minitype.terminal import console


def old(s, w):
    out, n, i = [], 0, 0
    while i < len(s):
        m = console.ANSI.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        if n >= w:
            break
        out.append(s[i])
        n += 1
        i += 1
    return "".join(out)


random.seed(1)
bits = ["a", "bc", " ", "\x1b[0m", "\x1b[38;2;1;2;3m", "\x1b[1m", "▓▒", "xyz"]
for _ in range(20000):
    s = "".join(random.choice(bits) for _ in range(random.randint(0, 12)))
    w = random.randint(-1, 14)
    assert old(s, w) == console.clip(s, w), (s, w)
print("clip matches the old one on 20000 random strings")
line = "".join("\x1b[38;2;1;2;3m" + "word " for _ in range(30))
for f in (old, console.clip):
    t = time.perf_counter()
    for _ in range(2000):
        f(line, 120)
    print(f.__name__, round((time.perf_counter() - t) / 2000 * 1000, 3), "ms/row")
print("ALL OK")
