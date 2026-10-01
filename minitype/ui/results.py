from ..config import LAYOUTS
from ..engine import keyboard
from ..engine.scoring import speed_series
from ..nav import MENU, QUIT
from ..terminal import console, keys
from ..terminal.style import RESET
from ..words import books
from .menu import Hints, Item, Menu, title_lines
from .profile import goal_line, sparkline

HINTS = "left/right choose   enter select   tab restart   esc menu"


def headline(app, st, r):
    dim, ok = st.dim, st.title
    lines = []
    if r.failed:
        why = r.fail_reason or r.difficulty
        lines.append(f"  {st.bad}failed{RESET} {dim}({why}){RESET}")
    else:
        lines.append(f"  {ok}{r.wpm:5.1f}{RESET} wpm")
    lines.append(f"  {dim}{r.raw:5.1f} raw   {r.acc:5.1f}% acc   "
                 f"{r.elapsed:5.1f}s   {r.errors} errors   combo {r.best_combo}{RESET}")
    if r.note:
        lines.append(f"  {dim}- {r.note}{RESET}")
    return lines


def pb_lines(app, st, r):
    if not app.settings.res_pb or r.failed or r.spec.source == "zen":
        return []
    if r.wpm > r.pb_before:
        if r.pb_before:
            return [f"  {st.good or st.title}new personal best!{RESET} "
                    f"{st.dim}+{r.wpm - r.pb_before:.1f} wpm{RESET}"]
        return [f"  {st.dim}first run of this mode: personal best set{RESET}"]
    return [f"  {st.dim}personal best {r.pb_before:.1f} "
            f"({r.wpm - r.pb_before:+.1f}){RESET}"]


def chart_lines(app, st, r):
    """Speed through the test as a sparkline, with an x under every slice
    that had errors."""
    if not app.settings.res_chart or r.elapsed < 1 or not r.events:
        return []
    width = console.size()[0] - 6
    buckets = max(2, min(width, int(r.elapsed), 60))
    series = speed_series(r.events, r.elapsed, buckets)
    speeds = [v for v, _ in series]
    marks = "".join("x" if e else " " for _, e in series)
    return ["", f"  {st.dim}speed  0-{max(speeds):.0f} wpm over "
                f"{r.elapsed:.0f}s{RESET}",
            f"  {st.title}{sparkline(speeds, 0)}{RESET}",
            f"  {st.bad}{marks.rstrip()}{RESET}" if marks.strip() else ""]


def heatmap_lines(app, st, r):
    """The keyboard with each key coloured by how often it was missed."""
    if not app.settings.res_heatmap or not r.presses:
        return []
    colors = {}
    keyset = set("".join(LAYOUTS.get(app.settings.layout, LAYOUTS["qwerty"])))
    for c, n in r.presses.items():
        c = c.lower()
        if c not in keyset:
            continue
        rate = r.misses.get(c, 0) / n
        colors[c] = (st.good or st.ok) if rate == 0 else \
            st.warn if rate < 0.1 else st.bad
    lines = keyboard.render(st, app.settings.layout, None, colors)
    return ["", f"  {st.dim}keys: clean, some misses, many misses{RESET}"] + lines[:-1]


def detail_lines(app, st, r):
    s, stats, dim = app.settings, app.stats, st.dim
    lines = []
    if r.spec.source == "learn":
        lines += [f"  {dim}{line}{RESET}" for line in app.learn.report()]
    if s.res_worst_keys and r.misses:
        worst = sorted(r.misses.items(), key=lambda kv: -kv[1])[:5]
        txt = "  ".join(f"{k if k != ' ' else '_'}x{v}" for k, v in worst)
        lines += ["", f"  {dim}worst keys   {txt}{RESET}"]
    flagged = stats.bad_keys()
    if s.res_session_keys and flagged:
        txt = "  ".join(f"{c}x{stats.errors.get(c, 0)}" for c in flagged)
        lines.append(f"  {dim}session keys {txt}{RESET}")
    if s.res_bad_words and stats.missed:
        worst = sorted(stats.missed.items(), key=lambda kv: -kv[1])[:5]
        txt = "  ".join(f"{w}x{n}" for w, n in worst)
        lines.append(f"  {dim}bad words    {txt}{RESET}")
    if s.res_history and stats.history:
        recent = "  ".join(f"{v:.0f}" for v in stats.history[-5:])
        lines += ["", f"  {dim}session  {recent}   best {stats.best():.0f}{RESET}"]
    goal = goal_line(app, st)
    if goal:
        lines.append("  " + goal)
    return lines


def draw(app, st, r, menu):
    if app.settings.lowkey == "disguised":
        lines = title_lines(app, st, "results")
    else:
        lines = [""]
    lines += headline(app, st, r) + pb_lines(app, st, r)
    lines += chart_lines(app, st, r) + heatmap_lines(app, st, r)
    lines += detail_lines(app, st, r)
    return lines, ["", menu.render_inline(st)]


def choice_items(app, result):
    spec = result.spec
    items = [
        Item(keys.TAB, "restart", lambda: spec),
        Item("m", "menu", lambda: MENU),
        Item("q", "quit", lambda: QUIT),
    ]
    if spec.source == "book":
        def again():
            books.set_page(app, spec.book, spec.page)   # retyping: back to this page
            return spec

        def next_page():
            nxt = books.neighbour(app, spec, 1)
            if nxt is None:
                app.notice = f"that was the last page of {spec.book}"
                return MENU
            return nxt
        items[0] = Item(keys.TAB, "restart", again)
        items.insert(0, Item("n", "next page", next_page))
    return items


def show_results(app, result):
    menu = Menu(choice_items(app, result), horizontal=True)
    hints = Hints(app)
    while True:
        st = app.styles()
        lines, choices = draw(app, st, result, menu)
        console.present(lines, 0, choices + hints.lines(st, HINTS))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        if key == keys.ESC:
            return MENU
        if key == keys.CTRL_C:
            return QUIT
        handled, choice = menu.handle(key)
        hints.note(key, handled)
        if choice is not None:
            return choice

