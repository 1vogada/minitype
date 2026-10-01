from ..terminal import console, keys


def prompt(label, initial=""):
    """Single line of input, starting with `initial` already typed.
    Returns None on escape."""
    console.cursor(True)
    console.clear()
    console.write(f"\n  {label} {initial}")
    console.flush()
    buf = list(initial)
    while True:
        key = keys.read_key()
        if key in (keys.ESC, keys.CTRL_C):
            console.cursor(False)
            return None
        if key in (keys.ENTER, keys.SHIFT_ENTER):
            break
        if key == keys.BACKSPACE:
            if buf:
                buf.pop()
                console.write("\b \b")
                console.flush()
        elif keys.is_char(key):
            buf.append(key)
            console.write(key)
            console.flush()
    console.cursor(False)
    return "".join(buf).strip()
