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
CTRL_P = "ctrl-p"
CTRL_LBRACKET = "ctrl-["   # Windows only: elsewhere it is the same byte as esc
CTRL_RBRACKET = "ctrl-]"
CTRL_I = "ctrl-i"     # Windows only: elsewhere ctrl-i is the same byte as tab
UNKNOWN = "unknown"
RESIZE = "resize"   # not a key: the terminal changed size while waiting

# final byte of an "ESC [ x" sequence (and "ESC O x"), which every terminal
# sends for these
CSI = {
    "A": UP, "B": DOWN, "C": RIGHT, "D": LEFT,
    "H": HOME, "F": END, "Z": SHIFT_TAB,
}


# The mouse (the mouse setting): read like keys, each event a Mouse - its
# name with the cell it happened on. HOVER is the mouse moving with no
# button down; MOUSE is anything else it does (a release, a drag, another
# button), which read_key passes over.
CLICK = "click"
HOVER = "hover"
WHEEL_UP, WHEEL_DOWN = "wheel-up", "wheel-down"
MOUSE = "mouse"


class Mouse(str):
    """A mouse event: CLICK, HOVER, WHEEL_UP, WHEEL_DOWN or MOUSE, at column x and
    row y of the terminal, both from 0 at the top left."""

    def __new__(cls, name, x=0, y=0):
        event = super().__new__(cls, name)
        event.x, event.y = x, y
        return event
