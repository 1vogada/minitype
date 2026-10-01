from ..config import KEYS
from ..terminal import console, keys
from ..terminal.style import INV, RESET

COLS = 6


def draw(app, cursor):
    st = app.styles()
    dim, ok = st.dim, st.title
    stats = app.stats
    console.clear()
    print(f"\n  {ok}bad keys{RESET}\n")
    print(f"  {dim}+ always   - never   * auto, currently active{RESET}\n")
    auto = set(stats.auto_keys())
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
            cells.append(f"{mark}{c}{sym}{RESET}{dim}{str(n or ''):<3}{RESET}")
        print("  " + " ".join(cells))
    live = " ".join(stats.bad_keys()) or "none yet"
    print(f"\n  {dim}drilling: {live}{RESET}")
    print(f"\n  {dim}arrows move   enter cycle   or press any key to cycle it{RESET}")
    print(f"  {dim}tab reset all   esc back{RESET}")


def key_editor(app):
    """Per-key control over what the bad-key pool is built from."""
    moves = {keys.LEFT: -1, keys.RIGHT: 1, keys.UP: -COLS, keys.DOWN: COLS}
    cursor = app.cursors.get("keys", 0)
    while True:
        draw(app, cursor)
        key = keys.read_key()
        if key == keys.TAB:
            app.stats.key_state.clear()
        elif key in (keys.ESC, keys.CTRL_C):
            app.cursors["keys"] = cursor
            return None
        elif key in moves:
            cursor = (cursor + moves[key]) % len(KEYS)
        elif key in (keys.ENTER, " "):
            app.stats.cycle_key(KEYS[cursor])
        elif keys.is_char(key) and key.lower() in KEYS:
            cursor = KEYS.index(key.lower())
            app.stats.cycle_key(key.lower())
