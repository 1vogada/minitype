"""Write the data the browser version (web/) shares with the terminal one:
the built-in word list, quotes, code snippets, themes, keyboard layouts and
the learn mode's letter order, as JSON in web/src/data/.

    python tools/export_web_data.py

Run it again after changing any of those in minitype/.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("MINITYPE_DIR", os.path.join(ROOT, ".web-export-tmp"))

from minitype.config import LAYOUTS  # noqa: E402
from minitype.learn.progress import ORDER  # noqa: E402
from minitype.terminal.style import (COMPLEX, RAINBOW, THEMES, Styles,  # noqa: E402
                                     rgb_of_code)
from minitype.words.builtin import BUILTIN  # noqa: E402
from minitype.words.code import SNIPPETS  # noqa: E402
from minitype.words.quotes import BUILTIN_QUOTES  # noqa: E402
from minitype.words.themed import THEMED  # noqa: E402

OUT = os.path.join(ROOT, "web", "src", "data")


def hexof(code, layer=38):
    c = rgb_of_code(code, layer) if code else None
    return "#%02x%02x%02x" % c if c else None


def theme(name):
    st = Styles(name, background="theme")
    e = st.effects
    return {
        "dim": hexof(st.dim), "text": hexof(st.ok), "error": hexof(st.bad),
        "extra": hexof(st.extra), "accent": hexof(st.title), "good": hexof(st.good),
        "warn": hexof(st.warn),
        "background": hexof(e.background, 48),
        "made_background": None if st.quiet else st.made_background(),
        "gradient": [hexof(c) for c in e.gradient], "by": e.by, "flow": e.flow,
        "heat": [hexof(c) for c in e.heat], "bold": e.bold, "italic": e.italic,
        "bounce": e.bounce, "shake": e.shake, "pop": e.pop, "fade": e.fade,
        "caret": e.caret_fx, "glitch": e.glitch, "mono": st.quiet,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    names = [n for n in list(THEMES) + list(COMPLEX) if n != "mono"] + ["mono"]
    data = {
        "words.json": list(BUILTIN),
        "quotes.json": [{"text": q[0], "source": q[1], "genres": list(q[2]) if len(q) > 2 else []}
                        for q in BUILTIN_QUOTES],
        "code.json": {lang: [{"name": n, "text": t} for n, t in items]
                      for lang, items in SNIPPETS.items()},
        "themes.json": {"order": names, "themes": {n: theme(n) for n in names},
                        "rainbow": [hexof(c) for c in RAINBOW]},
        "themed.json": {name: {layout: make(layout) for layout in LAYOUTS}
                        for name, make in THEMED.items()},
        "layouts.json": {"layouts": {k: list(v) for k, v in LAYOUTS.items()}, "order": ORDER},
    }
    for name, value in data.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, ensure_ascii=False, indent=None, separators=(",", ":"))
            f.write("\n")
        print(name, len(json.dumps(value)))


if __name__ == "__main__":
    main()
