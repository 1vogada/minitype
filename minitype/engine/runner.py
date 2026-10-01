import time

from ..config import MAX_EXTRA
from ..learn.wordgen import lesson_words
from ..nav import MENU, QUIT
from ..terminal import console, keys
from .render import draw
from .result import TestResult
from .scoring import score

FOOTER = "esc menu   tab restart   ctrl-bksp word   ctrl-q hide"
REDRAW_EVERY = 0.1


class TypingTest:
    """State and rules of one test, independent of the screen."""

    def __init__(self, app, spec):
        self.app = app
        self.spec = spec
        self.diff = app.settings.difficulty
        self.learning = spec.source == "learn"
        if spec.source == "custom":
            words = list(spec.words)
        elif self.learning:
            words = lesson_words(app.learn, app.bank, spec.amount)
        else:
            words = app.generator.make(
                spec.amount if spec.kind == "words" else 200, spec.source)
        self.words = words
        self.typed = [""] * len(words)
        self.wi = self.keys = self.bad_keys = self.spaces = 0
        self.combo = self.best_combo = 0
        self.misses = {}
        self.samples = []
        self.start = None
        self.failed = False
        self.done = False       # ended from inside a key press
        self.prev_t = None
        self.n_before = app.learn.unlocked() if self.learning else 0

    # ---------------------------------------------------------------- flow

    def finished(self, now):
        if self.done:
            return True
        if self.spec.kind == "words" and self.wi >= len(self.words):
            return True
        return bool(self.start and self.spec.kind == "time"
                    and now - self.start >= self.spec.amount)

    def top_up(self):
        """Timed tests get more words as you near the end of the list."""
        if self.spec.kind == "time" and self.spec.source != "custom" \
                and self.wi > len(self.words) - 30:
            self.words += self.app.generator.make(100, self.spec.source)
            self.typed += [""] * 100

    def score(self, elapsed):
        return score(self.words, self.typed, self.wi, self.keys,
                     self.bad_keys, self.spaces, elapsed)

    def status(self, now):
        """Header line and caret marks for the current frame."""
        s = self.app.settings
        spec = self.spec
        marks = set()
        if self.start is None:
            head = f"{spec.label}   0.0s"
        else:
            el = now - self.start
            wpm = self.score(el)[0]
            head = f"{spec.label}   {el:.1f}s"
            if spec.kind == "time":
                head += f"   {max(0, spec.amount - int(el))}s left"
            else:
                head += f"   {self.wi}/{len(self.words)}"
            head += f"   {wpm:.0f} wpm"
            if self.combo > 4:
                head += f"   x{self.combo}"
            if s.ghost and self.app.stats.ghost:
                marks.add(self.app.stats.ghost_chars(el))
            if s.pace:
                marks.add(int(s.pace * 5 / 60 * el))
        flags = [f for f in (self.diff if self.diff != "normal" else "",
                             "blind" if s.blind else "") if f]
        if flags:
            head += "   [" + " ".join(flags) + "]"
        return head, marks

    # ---------------------------------------------------------------- input

    def handle(self, key, now):
        """Apply one key press. Returns a navigation value to leave the test
        early, otherwise None."""
        dt = None if self.prev_t is None else now - self.prev_t
        self.prev_t = now

        if key == keys.ESC:
            return MENU
        if key == keys.TAB:
            return self.spec
        if key in (keys.CTRL_C, keys.CTRL_D):
            return QUIT
        if key == keys.BACKSPACE:
            self._backspace()
            return None
        if key in (keys.CTRL_BACKSPACE, keys.CTRL_W):
            self._wipe_word()
            return None
        if not keys.is_char(key):
            return None

        if self.start is None:
            self.start = time.time()
        el = time.time() - self.start
        if key == " ":
            self._space(el)
        else:
            self._char(key, el, dt)
        return None

    def _backspace(self):
        if self.diff != "normal":
            return
        if self.typed[self.wi]:
            self.typed[self.wi] = self.typed[self.wi][:-1]
        elif self.wi > 0 and self.typed[self.wi - 1] != self.words[self.wi - 1]:
            self.wi -= 1                        # only back into a wrong word

    def _wipe_word(self):
        if self.diff != "normal":
            return
        if self.typed[self.wi]:
            self.typed[self.wi] = ""
        elif self.wi > 0:
            self.wi -= 1                        # step back and wipe that word
            self.typed[self.wi] = ""

    def _space(self, el):
        word = self.words[self.wi]
        if not self.typed[self.wi]:
            return                              # ignore leading spaces
        self.keys += 1
        self.samples.append((el, self.keys))
        if self.typed[self.wi] != word:
            self.bad_keys += 1
            self.combo = 0
            if not self.learning:
                self.app.stats.miss_word(word)
            if self.diff in ("expert", "master"):
                self.failed = self.done = True
                return
        else:
            self.spaces += 1
            self._hit()
        self.wi += 1

    def _char(self, ch, el, dt):
        word = self.words[self.wi]
        if len(self.typed[self.wi]) >= len(word) + MAX_EXTRA:
            return
        j = len(self.typed[self.wi])
        self.typed[self.wi] += ch
        self.keys += 1
        self.samples.append((el, self.keys))
        if self.learning and j < len(word):
            if ch == word[j]:
                if dt is not None and 0.03 < dt < 2.0:
                    self.app.learn.hit(ch, dt * 1000)
            else:
                self.app.learn.hit(word[j], None)
        if j >= len(word) or ch != word[j]:
            self.bad_keys += 1
            self.combo = 0
            want = word[j] if j < len(word) else "+"
            self.misses[want] = self.misses.get(want, 0) + 1
            self.app.stats.miss_key(want)
            if self.diff == "master":
                self.failed = self.done = True
                return
        else:
            self._hit()
        # the last word of a word test ends as soon as it's long enough
        if self.spec.kind == "words" and self.wi == len(self.words) - 1 \
                and len(self.typed[self.wi]) >= len(word):
            if self.typed[self.wi] != word:
                self.bad_keys += 1
                if not self.learning:
                    self.app.stats.miss_word(word)
            self.wi += 1
            self.done = True

    def _hit(self):
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)

    # ---------------------------------------------------------------- end

    def result(self):
        """Wrap up: record the run and return its result, or MENU if nothing
        was typed."""
        if self.start is None:
            return MENU
        elapsed = time.time() - self.start
        wpm, raw, acc = self.score(elapsed)
        if self.learning:
            self.app.learn.finish(self.n_before)
        if not self.failed:
            self.app.stats.ghost[:] = self.samples
            self.app.stats.history.append(wpm)
        return TestResult(self.spec, wpm, raw, acc, elapsed, self.bad_keys,
                          self.best_combo, self.misses, self.failed, self.diff)


def run_test(app, spec):
    test = TypingTest(app, spec)
    width = console.width()
    last_draw = 0.0
    dirty = True
    console.clear()
    while not test.finished(time.time()):
        test.top_up()
        now = time.time()
        if dirty or now - last_draw > REDRAW_EVERY:
            head, marks = test.status(now)
            draw(app.styles(), app.settings.blind, head, test.words, test.typed,
                 test.wi, width, FOOTER, marks)
            last_draw = now
            dirty = False

        if not keys.key_ready():
            time.sleep(0.01)
            continue

        key = keys.read_key()
        dirty = True
        nav = test.handle(key, time.time())
        if nav is not None:
            return nav
    return test.result()
