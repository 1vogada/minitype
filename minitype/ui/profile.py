"""Long-term progress: totals, a speed chart, personal bests and the daily
goal."""

from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Hints, title_lines

SPARKS = "▁▂▃▄▅▆▇█"
CHART_RUNS = 60
BAR_WIDTH = 20
HINTS = "esc back"


def fmt_time(secs):
    m = int(secs // 60)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m {int(secs % 60):02d}s"


def sparkline(values, lo=None, hi=None):
    lo = min(values) if lo is None else lo
    hi = max(values) if hi is None else hi
    span = (hi - lo) or 1
    top = len(SPARKS) - 1
    return "".join(SPARKS[max(0, min(top, int((v - lo) / span * top)))]
                   for v in values)


def goal_line(app, st):
    """Today's typing time against the daily goal, or None if neither is set."""
    goal = app.settings.daily_goal
    today = app.history.today_seconds()
    if not goal:
        return f"{st.dim}today {fmt_time(today)}{RESET}" if today else None
    frac = min(1.0, today / (goal * 60))
    bar = min(BAR_WIDTH, max(5, console.size()[0] - 30))
    fill = int(frac * bar)
    done = "  done!" if frac >= 1 else ""
    return (f"{st.dim}today {int(today // 60)}/{goal} min  {RESET}"
            f"{st.title}{'#' * fill}{RESET}{st.dim}{'.' * (bar - fill)}"
            f"{done}{RESET}")


def draw(app, st):
    dim, ok = st.dim, st.title
    h = app.history
    runs = h.completed()
    width = console.size()[0]
    lines = title_lines(app, st, "profile")
    if not h.runs:
        lines.append(f"  {dim}no tests yet{RESET}")
    else:
        wpms = [r["wpm"] for r in runs] or [0]
        last = runs[-10:] or [{"wpm": 0, "acc": 0}]
        avg = sum(r["wpm"] for r in last) / len(last)
        acc = sum(r["acc"] for r in last) / len(last)
        rows = [
            ("tests", f"{len(h.runs)}"),
            ("time typed", fmt_time(h.total_seconds())),
            ("top speed", f"{max(wpms):.0f} wpm"),
            ("average", f"{avg:.0f} wpm (last 10)"),
            ("accuracy", f"{acc:.1f}% (last 10)"),
            ("failed", f"{len(h.runs) - len(runs)}"),
        ]
        two_cols = width >= 64
        step = 2 if two_cols else 1
        for k in range(0, len(rows), step):
            line = "  " + "".join(f"{dim}{a:<12}{RESET}{v:<22}"
                                  for a, v in rows[k:k + step])
            lines.append(line)

        chart = [r["wpm"] for r in runs[-min(CHART_RUNS, width - 6):]]
        if len(chart) > 1:
            lines += ["", f"  {dim}speed, last {len(chart)} tests  "
                          f"{min(chart):.0f}-{max(chart):.0f} wpm{RESET}",
                      f"  {ok}{sparkline(chart)}{RESET}"]

        if h.pbs:
            lines += ["", f"  {dim}personal bests{RESET}"]
            for mode, pb in sorted(h.pbs.items(), key=lambda kv: -kv[1]["wpm"]):
                lines.append(f"  {dim}{mode:<24}{RESET}{pb['wpm']:.0f} wpm  "
                             f"{dim}{pb['acc']:.0f}%{RESET}")

    goal = goal_line(app, st)
    if goal:
        lines += ["", "  " + goal]
    if not app.saving():
        lines += ["", f"  {dim}saving is off: history is kept for this "
                      f"session only{RESET}"]
    return lines


def profile_screen(app):
    hints = Hints(app)
    top = 0
    while True:
        st = app.styles()
        lines = draw(app, st)
        console.present(lines, top, hints.lines(st, "up/down scroll   " + HINTS))
        key = keys.read_key()
        if key in (keys.ESC, keys.CTRL_C, keys.ENTER, "p"):
            return None
        handled = key in (keys.UP, keys.DOWN, keys.RESIZE)
        if key == keys.DOWN:
            top = min(len(lines) - 1, top + 3)
        elif key == keys.UP:
            top = max(0, top - 3)
        hints.note(key, handled)
