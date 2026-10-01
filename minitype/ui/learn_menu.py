from ..engine.spec import TestSpec
from ..learn.progress import ORDER
from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Item, Menu, title_lines
from .screen import menu_loop

HINTS = "arrows move   left/right change   space start   [ ] tabs   esc back"


def letter_strip(app, st):
    """Every letter in unlock order, coloured by speed, with a marker row
    and a caret under the focus key."""
    learn = app.learn
    n = learn.unlocked()
    foc = learn.focus_key()
    top, mid, low = [], [], []
    for i, c in enumerate(ORDER):
        if i >= n:
            top.append(f"{st.dim}{c}{RESET}")
            mid.append(" ")
        else:
            v = learn.conf(c)
            col = st.title if v is None else st.conf_color(v)
            top.append(f"{col}{c}{RESET}")
            mid.append("." if v is None else "*" if v >= 1
                       else str(min(9, int(v * 10))))
        low.append("^" if c == foc else " ")
    if foc is None:
        fc = "none"
    elif learn.conf(foc) is None:
        fc = f"{foc} (new)"
    else:
        fc = f"{foc} {learn.conf(foc) * 100:.0f}%"
    return ["  " + " ".join(top),
            "  " + st.dim + " ".join(mid) + RESET,
            "  " + st.dim + " ".join(low) + RESET,
            "",
            f"  {st.dim}{n}/{len(ORDER)} letters   focus {fc}{RESET}"]


def details_table(app, st):
    learn = app.learn
    lines = ["", f"  {st.dim}key  wpm  conf    n  miss{RESET}"]
    for c in ORDER[:learn.unlocked()]:
        s = learn.stats.get(c)
        if s and s[1]:
            v = learn.conf(c)
            cs = " new" if v is None else f"{v * 100:3.0f}%"
            lines.append(f"  {st.dim}{c}    {12000 / s[0]:3.0f}  {cs}  "
                         f"{s[1]:3d}  {s[2]:3d}{RESET}")
        else:
            lines.append(f"  {st.dim}{c}      -     -    0    0{RESET}")
    return lines


def draw(app, st, menu, view):
    lines = title_lines(app, st, "learn") + letter_strip(app, st)
    if view["details"]:
        lines += details_table(app, st)
    lines.append("")
    body, focus = menu.render(st, label_width=14)
    focus += len(lines)
    return lines + body, focus


def confirm_reset(app):
    st = app.styles()
    console.present(title_lines(app, st, "learn")
                    + [f"  {st.dim}reset all learn progress? y/n{RESET}"])
    key = keys.read_key()
    while key == keys.RESIZE:
        key = keys.read_key()
    if key == "y":
        app.learn.reset()


def lesson(app):
    return TestSpec("learn", "words", app.learn.config["words"], "learn")


def build_items(app, view):
    learn = app.learn
    cfg = learn.config

    def toggle(key, label, name, help):
        def flip():
            learn.toggle(name)
        return Item(key, label, flip,
                    lambda: "on" if cfg[name] else "off",
                    back=flip, help=help, section="lesson")

    def flip_details():
        view["details"] = not view["details"]

    return [
        Item("s", "start", lambda: lesson(app), section="lesson",
             help="type the lesson; every word contains your focus key"),
        Item("t", "target", learn.cycle_target, lambda: f"{cfg['target']} wpm",
             back=lambda: learn.cycle_target(-1), section="lesson",
             help="speed every key must reach before the next letter unlocks"),
        Item("+", "letters", lambda: learn.add_letters(1),
             lambda: f"at least {cfg['letters']}",
             back=lambda: learn.add_letters(-1), section="lesson",
             help="minimum letters in play, more unlock as you reach the target"),
        Item("l", "length", learn.cycle_length, lambda: f"{cfg['words']} words",
             back=lambda: learn.cycle_length(-1), section="lesson",
             help="words per lesson"),
        toggle("n", "natural", "natural",
               "real words where enough fit, made-up ones otherwise"),
        toggle("c", "capitals", "capitals",
               "capitalise some words; capitals aren't timed"),
        toggle("u", "punctuation", "punctuation",
               "end some words with punctuation; it isn't timed"),

        Item("d", "details", flip_details,
             lambda: "on" if view["details"] else "off",
             back=flip_details, help="per-key speed table", section="progress"),
        Item("p", "save to disk", app.toggle_saving,
             lambda: "on" if app.saving() else "off", back=app.toggle_saving,
             section="progress",
             help="keep progress, settings and history between sessions"),
        Item("x", "reset", lambda: confirm_reset(app), section="progress",
             help="forget all learn progress"),
    ]


def learn_menu(app):
    """Returns a lesson spec to start, or None to go back."""
    learn = app.learn
    view = {"details": False}
    menu = Menu(build_items(app, view), app.cursors, "learn")
    extra_keys = {
        "=": lambda: learn.add_letters(1),
        "-": lambda: learn.add_letters(-1),
        "_": lambda: learn.add_letters(-1),
    }

    def extra(key):
        if key == " ":
            return True, lesson(app)
        if key in extra_keys:
            extra_keys[key]()
            app.save()
            return True, None
        return False, None

    result = menu_loop(app, menu, lambda st, m: draw(app, st, m, view), HINTS,
                       extra=extra)
    app.save()
    return result
