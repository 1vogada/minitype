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
FAV_KEY = "f"
FAV_HINT = "   f favourite"


def is_fav(app, result):
    return any(q["text"] == result.quote for q in app.settings.fav_quotes)


def toggle_fav(app, result):
    """Add the quote of this result to the favourites, or take it out."""
    favs = app.settings.fav_quotes
    if is_fav(app, result):
        favs[:] = [q for q in favs if q["text"] != result.quote]
    else:
        favs.append({"text": result.quote, "source": result.note})
    app.save_settings()


def _time(r):
    """The test's time - and, in active wpm, the part of it spent typing
    when long stops were left out."""
    if r.system == "active" and r.active_secs and r.elapsed - r.active_secs >= 1:
        return f"{r.elapsed:5.1f}s ({r.active_secs:.1f}s typing)"
    return f"{r.elapsed:5.1f}s"


def headline(app, st, r):
    dim, ok = st.dim, st.title
    lines = []
    if r.failed:
        why = r.fail_reason or r.difficulty
        lines.append(f"  {st.bad}failed{RESET} {dim}({why}){RESET}")
    else:
        other = (("classic", r.classic) if r.system == "active" else ("active", r.active))
        aside = (f"   {dim}{other[1]:.1f} {other[0]}{RESET}"
                 if other[1] and abs(other[1] - r.wpm) >= 0.05 else "")
        lines.append(f"  {ok}{r.wpm:5.1f}{RESET} wpm{aside}")
    lines.append(f"  {dim}{r.raw:5.1f} raw   {r.acc:5.1f}% acc   "
                 f"{_time(r)}   {r.errors} errors   combo {r.best_combo}{RESET}")
    if r.note or r.quote:
        star = f"{st.title}★{RESET} " if r.quote and is_fav(app, r) else ""
        lines.append(f"  {star}{dim}{'- ' + r.note if r.note else ''}{RESET}")
    return lines


def pb_lines(app, st, r):
    if not r.counted:
        return [f"  {st.dim}hacker mode - just for fun, not kept{RESET}"]
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


# the heatmap's own colours, for a theme whose three don't tell apart
HEAT_FALLBACK = ((95, 215, 95), (255, 175, 0), (255, 95, 95))   # clean, some misses, many
HEAT_APART = 90           # how far apart (rgb distance) any two must be to use the theme's


def heat_colours(st):
    """(clean, some misses, many misses) escape codes: the theme's good,
    warn and bad when they are clearly different colours, else a plain
    green, amber and red (a grey theme's good and warn can be two near
    identical greys, and the middle band of the heatmap disappears)."""
    from ..terminal.style import _code, rgb_of_code
    theme = (st.good or st.ok, st.warn, st.bad)
    rgbs = [rgb_of_code(c or "") for c in theme]
    if all(rgbs) and all(sum((a - b) ** 2 for a, b in zip(x, y)) ** 0.5 >= HEAT_APART
                         for i, x in enumerate(rgbs) for y in rgbs[i + 1:]):
        return theme
    return tuple(_code(c, 38) for c in HEAT_FALLBACK)


def heatmap_lines(app, st, r):
    """The keyboard with each key coloured by how often it was missed."""
    if not app.settings.res_heatmap or not r.presses:
        return []
    clean, some, many = heat_colours(st)
    colors = {}
    keyset = set("".join(LAYOUTS.get(app.settings.layout, LAYOUTS["qwerty"])))
    for c, n in r.presses.items():
        c = c.lower()
        if c not in keyset:
            continue
        rate = r.misses.get(c, 0) / n
        colors[c] = clean if rate == 0 else some if rate < 0.1 else many
    lines = keyboard.render(st, app.settings.layout, None, colors)
    # the key to the colours: each word in the colour it stands for
    legend = (f"  {st.dim}keys:{RESET} {clean}clean{RESET}{st.dim},{RESET} "
              f"{some}some misses{RESET}{st.dim},{RESET} {many}many misses{RESET}")
    return ["", legend] + lines[:-1]


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
        most = sorted(flagged, key=lambda c: -stats.errors.get(c, 0))     # most missed first
        txt = "; ".join(f"{c} - {stats.errors.get(c, 0)}" for c in most)
        lines.append(f"  {dim}session keys: {txt}{RESET}")
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
        console.present(lines, 0, choices + hints.lines(
            st, HINTS + (FAV_HINT if result.quote else "")))
        key = keys.read_key()
        if key == keys.RESIZE:
            continue
        if key == keys.ESC:
            return MENU
        if key == keys.CTRL_C:
            return QUIT
        if key == FAV_KEY and result.quote:
            toggle_fav(app, result)
            continue
        handled, choice = menu.handle(key)
        hints.note(key, handled)
        if choice is not None:
            return choice

