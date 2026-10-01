"""Long-term progress: totals, a speed chart and the daily goal."""

from ..terminal import console, keys
from ..terminal.style import RESET

SPARKS = "▁▂▃▄▅▆▇█"
CHART_RUNS = 40
BAR_WIDTH = 20


def fmt_time(secs):
    m = int(secs // 60)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m {int(secs % 60):02d}s"


def sparkline(values):
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    return "".join(SPARKS[int((v - lo) / span * (len(SPARKS) - 1))] for v in values)


def goal_line(app, st):
    """Today's typing time against the daily goal, or None if neither is set."""
    goal = app.settings.daily_goal
    today = app.history.today_seconds()
    if not goal:
        return f"{st.dim}today {fmt_time(today)}{RESET}" if today else None
    frac = min(1.0, today / (goal * 60))
    fill = int(frac * BAR_WIDTH)
    done = "  done!" if frac >= 1 else ""
    return (f"{st.dim}today {int(today // 60)}/{goal} min  {RESET}"
            f"{st.title}{'#' * fill}{RESET}{st.dim}{'.' * (BAR_WIDTH - fill)}"
            f"{done}{RESET}")


def draw(app):
    st = app.styles()
    dim, ok = st.dim, st.title
    h = app.history
    runs = h.completed()
    console.clear()
    print(f"\n  {ok}profile{RESET}\n")
    if not h.runs:
        print(f"  {dim}no tests yet{RESET}")
    else:
        wpms = [r["wpm"] for r in runs] or [0]
        last = runs[-10:] or [{"wpm": 0, "acc": 0}]
        avg = sum(r["wpm"] for r in last) / len(last)
        acc = sum(r["acc"] for r in last) / len(last)
        rows = [
            ("tests", f"{len(h.runs)}", "time typed", fmt_time(h.total_seconds())),
            ("top speed", f"{max(wpms):.0f} wpm", "average", f"{avg:.0f} wpm (last 10)"),
            ("accuracy", f"{acc:.1f}% (last 10)", "failed", f"{len(h.runs) - len(runs)}"),
        ]
        for a, av, b, bv in rows:
            print(f"  {dim}{a:<11}{RESET}{av:<20}{dim}{b:<12}{RESET}{bv}")

        chart = [r["wpm"] for r in runs[-CHART_RUNS:]]
        if len(chart) > 1:
            print(f"\n  {dim}speed, last {len(chart)} tests  "
                  f"{min(chart):.0f}-{max(chart):.0f} wpm{RESET}")
            print(f"  {ok}{sparkline(chart)}{RESET}")

        best = sorted(h.best_by_mode().items(), key=lambda kv: -kv[1])
        if best:
            print(f"\n  {dim}best by mode{RESET}")
            for mode, wpm in best[:8]:
                print(f"  {dim}{mode:<20}{RESET}{wpm:.0f}")

    goal = goal_line(app, st)
    if goal:
        print(f"\n  {goal}")
    if not app.saving():
        print(f"\n  {dim}saving is off: history is kept for this session only{RESET}")
    print(f"\n  {dim}esc back{RESET}")


def profile_screen(app):
    draw(app)
    while keys.read_key() not in (keys.ESC, keys.CTRL_C, keys.ENTER, "p"):
        pass
    return None
