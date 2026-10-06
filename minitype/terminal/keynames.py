"""Names for keys that aren't printable characters, shared by the keyboard
back ends. Names are always longer than one character, so a key is
either one of these or a single printable character."""

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
HOME, END, PGUP, PGDN = "home", "end", "pgup", "pgdn"
INSERT, DELETE = "insert", "delete"
ENTER, SHIFT_ENTER = "enter", "shift-enter"
TAB, SHIFT_TAB, ESC = "tab", "shift-tab", "esc"
BACKSPACE, CTRL_BACKSPACE = "backspace", "ctrl-backspace"
CTRL_C, CTRL_D, CTRL_Q, CTRL_W = "ctrl-c", "ctrl-d", "ctrl-q", "ctrl-w"
CTRL_O = "ctrl-o"
UNKNOWN = "unknown"
RESIZE = "resize"   # not a key: the terminal changed size while waiting

# final byte of an "ESC [ x" sequence (and "ESC O x"), which every terminal
# sends for these
CSI = {
    "A": UP, "B": DOWN, "C": RIGHT, "D": LEFT,
    "H": HOME, "F": END, "Z": SHIFT_TAB,
}
