from ..config import KEYS
from ..terminal import console, keys
from ..terminal.style import INV, RESET
from .menu import Hints, title_lines

COLS = 6
HINTS = ("arrows move   enter cycle   or press any key to cycle it   "
         "tab reset all   esc back")


def draw(app, st, cursor):
    dim, ok = st.dim, st.title
    stats = app.stats
    lines = title_lines(app, st, "bad keys")
    lines.append(f"  {dim}+ always   - never   * auto, currently active{RESET}")
    lines.append("")
    auto = set(stats.auto_keys())
    focus = len(lines)
    for i in range(0, len(KEYS), COLS):
        cells = []
        for j, c in enumerate(KEYS[i:i + COLS], i):
            state = stats.key_state.get(c, "auto")
            sym = "+" if state == "on" else "-" if state == "off" else \
                  ("*" if c in auto else " ")
            n = stats.errors.get(c, 0)
            mark = ok if state == "on" or c in auto else dim
            if j == cursor:
                mark += INV
                focus = len(lines)
            cells.append(f"{mark}{c}{sym}{RESET}{dim}{str(n or ''):<3}{RESET}")
        lines.append("  " + " ".join(cells))
    live = " ".join(stats.bad_keys()) or "none yet"
    lines += ["", f"  {dim}drilling: {live}{RESET}"]
    return lines, focus


def key_editor(app):
    """Per-key control over what the bad-key pool is built from."""
    moves = {keys.LEFT: -1, keys.RIGHT: 1, keys.UP: -COLS, keys.DOWN: COLS}
    cursor = app.cursors.get("keys", 0)
    hints = Hints(app)
    while True:
        st = app.styles()
        lines, focus = draw(app, st, cursor)
        console.present(lines, focus, hints.lines(st, HINTS))
        key = keys.read_key()
        handled = True
        if key == keys.RESIZE:
            continue
        if key == keys.TAB:
            app.stats.key_state.clear()
        elif key in (keys.ESC, keys.CTRL_C):
            app.cursors["keys"] = cursor
            app.save_settings()
            return None
        elif key in moves:
            cursor = (cursor + moves[key]) % len(KEYS)
        elif key in (keys.ENTER, " "):
            app.stats.cycle_key(KEYS[cursor])
        elif keys.is_char(key) and key.lower() in KEYS:
            cursor = KEYS.index(key.lower())
            app.stats.cycle_key(key.lower())
        else:
            handled = False
        hints.note(key, handled)
