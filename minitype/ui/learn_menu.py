from ..engine.spec import TestSpec
from ..learn.progress import ORDER
from ..terminal import console, keys
from ..terminal.style import RESET
from .menu import Item, Menu


def draw(app, menu, details):
    st = app.styles()
    dim, ok = st.dim, st.title
    learn = app.learn
    n = learn.unlocked()
    foc = learn.focus_key()
    console.clear()
    print(f"\n  {ok}learn{RESET}\n")

    top, mid, low = [], [], []
    for i, c in enumerate(ORDER):
        if i >= n:
            top.append(f"{dim}{c}{RESET}")
            mid.append(" ")
        else:
            v = learn.conf(c)
            col = ok if v is None else st.conf_color(v)
            top.append(f"{col}{c}{RESET}")
            mid.append("." if v is None else "*" if v >= 1
                       else str(min(9, int(v * 10))))
        low.append("^" if c == foc else " ")
    print("  " + " ".join(top))
    print("  " + dim + " ".join(mid) + RESET)
    print("  " + dim + " ".join(low) + RESET)

    if foc is None:
        fc = "none"
    elif learn.conf(foc) is None:
        fc = f"{foc} (new)"
    else:
        fc = f"{foc} {learn.conf(foc) * 100:.0f}%"
    print(f"\n  {dim}{n}/{len(ORDER)} letters   focus {fc}{RESET}")

    if details:
        print(f"\n  {dim}key  wpm  conf    n  miss{RESET}")
        for c in ORDER[:n]:
            s = learn.stats.get(c)
            if s and s[1]:
                v = learn.conf(c)
                cs = " new" if v is None else f"{v * 100:3.0f}%"
                print(f"  {dim}{c}    {12000 / s[0]:3.0f}  {cs}  "
                      f"{s[1]:3d}  {s[2]:3d}{RESET}")
            else:
                print(f"  {dim}{c}      -     -    0    0{RESET}")

    print()
    menu.render(st, label_width=14)
    menu.render_help(st)
    print(f"\n  {dim}arrows move   left/right change   space start   esc back{RESET}")


def confirm_reset(app):
    print(f"\n  {app.styles().dim}reset all progress? y/n{RESET}")
    console.flush()
    if keys.read_key() == "y":
        app.learn.reset()


def lesson(app):
    return TestSpec("learn", "words", app.learn.config["words"], "learn")


def _toggle_item(key, label, learn, name, help):
    def flip():
        learn.toggle(name)

    return Item(key, label, flip,
                lambda: "on" if learn.config[name] else "off",
                back=flip, help=help)


def build_items(app, view):
    learn = app.learn
    cfg = learn.config

    def flip_details():
        view["details"] = not view["details"]

    def on_off(v):
        return "on" if v else "off"

    return [
        Item("s", "start", lambda: lesson(app), group=-1,
             help="type the lesson; every word contains your focus key"),
        Item("t", "target", learn.cycle_target, lambda: f"{cfg['target']} wpm",
             back=lambda: learn.cycle_target(-1),
             help="speed every key must reach before the next letter unlocks"),
        Item("+", "letters", lambda: learn.add_letters(1),
             lambda: f"at least {cfg['letters']}",
             back=lambda: learn.add_letters(-1),
             help="minimum letters in play, more unlock as you reach the target"),
        Item("l", "length", learn.cycle_length, lambda: f"{cfg['words']} words",
             back=lambda: learn.cycle_length(-1),
             help="words per lesson"),
        _toggle_item("n", "natural", learn, "natural",
                     "real words where enough fit, made-up ones otherwise"),
        _toggle_item("c", "capitals", learn, "capitals",
                     "capitalise some words; capitals aren't timed"),
        _toggle_item("u", "punctuation", learn, "punctuation",
                     "end some words with punctuation; it isn't timed"),
        Item("d", "details", flip_details, lambda: on_off(view["details"]),
             back=flip_details, help="per-key speed table"),
        Item("p", "save to disk", app.toggle_saving,
             lambda: on_off(app.saving()), back=app.toggle_saving,
             help="keep progress, settings and history between sessions"),
        Item("x", "reset", lambda: confirm_reset(app), group=1,
             help="forget all learn progress"),
    ]


def learn_menu(app):
    """Returns a lesson spec to start, or None to go back."""
    learn = app.learn
    view = {"details": False}
    menu = Menu(build_items(app, view), app.cursors, "learn")
    extra = {
        "=": lambda: learn.add_letters(1),
        "-": lambda: learn.add_letters(-1),
        "_": lambda: learn.add_letters(-1),
    }
    while True:
        draw(app, menu, view["details"])
        key = keys.read_key()
        if key == " ":
            return lesson(app)
        if key in (keys.ESC, keys.CTRL_C):
            app.save()
            return None
        if key in extra:
            extra[key]()
        else:
            _, result = menu.handle(key)
            if result is not None:
                return result
        app.save()
