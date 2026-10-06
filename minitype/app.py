from .context import App
from .engine.result import TestResult
from .engine.runner import run_test
from .engine.spec import TestSpec
from .nav import MENU, QUIT
from .terminal import console, keys
from .terminal.style import RESET
from .ui.anywhere import open_settings
from .ui.main_menu import main_menu
from .ui.results import show_results


def main():
    console.setup()
    keys.setup()                 # raw mode on Linux / macOS; restored below
    console.set_title("cmd")
    console.cursor(False)
    app = App()
    keys.on_settings_key(lambda: open_settings(app))      # ctrl-o, from anywhere
    try:
        app.load()
        console.clear()
        console.present(["", f"  {app.styles().dim}loading "
                             f"{app.settings.word_source}...{RESET}"])
        app.load_words(app.settings.word_source)
        state = MENU
        while state != QUIT:
            if isinstance(state, TestSpec):
                state = run_test(app, state)
            elif isinstance(state, TestResult):
                state = show_results(app, state)
            else:
                state = main_menu(app)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        app.save()
        console.cursor(True)
        console.clear()
        console.flush()
        keys.restore()


if __name__ == "__main__":
    main()
