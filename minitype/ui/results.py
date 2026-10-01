from ..nav import MENU, QUIT
from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Item, Menu


def draw(app, r):
    st = app.styles()
    dim, ok = st.dim, st.title
    stats = app.stats
    console.clear()
    if r.failed:
        print(f"\n  {dim}failed ({r.difficulty}){RESET}\n")
    else:
        print(f"\n  {ok}{r.wpm:5.1f}{RESET} wpm")
    print(f"  {dim}{r.raw:5.1f} raw{RESET}")
    print(f"  {dim}{r.acc:5.1f}% acc{RESET}")
    print(f"  {dim}{r.elapsed:5.1f}s   {r.errors} errors   combo {r.best_combo}{RESET}")
    if r.spec.source == "learn":
        for line in app.learn.report():
            print(f"  {dim}{line}{RESET}")

    if r.misses:
        worst = sorted(r.misses.items(), key=lambda kv: -kv[1])[:5]
        s = "  ".join(f"{k if k != ' ' else '_'}x{v}" for k, v in worst)
        print(f"\n  {dim}worst keys  {s}{RESET}")

    flagged = stats.bad_keys()
    if flagged:
        s2 = "  ".join(f"{c}x{stats.errors.get(c, 0)}" for c in flagged)
        print(f"  {dim}session keys {s2}{RESET}")

    if stats.missed:
        worst = sorted(stats.missed.items(), key=lambda kv: -kv[1])[:5]
        s3 = "  ".join(f"{w}x{n}" for w, n in worst)
        print(f"  {dim}bad words    {s3}{RESET}")

    if stats.history:
        recent = "  ".join(f"{v:.0f}" for v in stats.history[-5:])
        print(f"\n  {dim}session  {recent}   best {stats.best():.0f}{RESET}")

    print("\n")   # blank line, then the row the choices are drawn over


def show_results(app, result):
    menu = Menu([
        Item(keys.TAB, "restart", lambda: result.spec),
        Item("m", "menu", lambda: MENU),
        Item("q", "quit", lambda: QUIT),
    ], horizontal=True)
    draw(app, result)
    while True:
        console.write("\x1b[1A\r\x1b[K")   # redraw just the choice row
        menu.render_inline(app.styles())
        console.flush()
        key = keys.read_key()
        if key == keys.ESC:
            return MENU
        if key == keys.CTRL_C:
            return QUIT
        _, choice = menu.handle(key)
        if choice is not None:
            return choice
