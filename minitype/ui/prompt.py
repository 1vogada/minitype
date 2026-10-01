from ..terminal import console, keys


def prompt(label):
    """Single line of input. Returns None on escape."""
    console.cursor(True)
    console.clear()
    console.write(f"\n  {label} ")
    console.flush()
    buf = []
    while True:
        key = keys.read_key()
        if key in (keys.ESC, keys.CTRL_C):
            console.cursor(False)
            return None
        if key == keys.ENTER:
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
