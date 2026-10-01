import os
import random
import time

from ..config import MAX_EXTRA, RULE_GRACE
from ..learn.progress import ORDER
from ..learn.wordgen import lesson_words
from ..nav import MENU, QUIT
from ..terminal import console, keys
from ..words import code, funbox
from . import keyboard
from .render import draw
from .result import TestResult
from .scoring import score

FOOTER = "esc menu   tab restart   ctrl-bksp word   ctrl-q hide"
ZEN_FOOTER = "enter finish   esc menu   ctrl-q hide"
REDRAW_EVERY = 0.1
SLOW_WORDS = 20       # how many of your slowest words a drill draws from
MIN_SLOW_WORDS = 5    # tracked words needed before the drill is offered


class TypingTest:
    """State and rules of one test, independent of the screen."""

    HINTS = FOOTER

    def __init__(self, app, spec):
        self.app = app
        self.spec = spec
        s = app.settings
        self.diff = s.difficulty
        self.stop = s.stop_on_error
        self.learning = spec.source == "learn"
        self.note = ""
        self.words = self._make_words()
        self.typed = [""] * len(self.words)
        self.wi = self.keys = self.bad_keys = 0
        self.combo = self.best_combo = 0
        self.misses = {}
        self.presses = {}
        self.samples = []
        self.events = []
        self.start = None
        self.failed = False
        self.fail_reason = ""
        self.done = False       # ended from inside a key press
        self.wrong = False      # last key was rejected by stop on error
        self.prev_t = None
        self.word_start = None  # when the first char of the current word landed
        self.popped_hints = False
        self.n_before = app.learn.unlocked() if self.learning else 0

    # ---------------------------------------------------------------- words

    def _make_words(self):
        app, spec = self.app, self.spec
        src = spec.source
        if src == "custom":
            words = list(spec.words)
        elif src == "learn":
            return lesson_words(app.learn, app.bank, spec.amount)
        elif src == "quote":
            text, who = app.quotes.pick(app.settings.quote_length,
                                        app.settings.quote_source)
            self.note = who
            words = text.split()
        elif src == "code":
            self.note, words = code.pick(app.settings.code_lang)
        elif src == "slow":
            words = slow_words(app, spec.amount)
        else:
            words = app.generator.make(
                spec.amount if spec.kind == "words" else 200, src)
        return funbox.apply(words, app.settings.funbox)

    # ---------------------------------------------------------------- flow

    def finished(self, now):
        if self.done:
            return True
        if self.spec.kind == "words" and self.wi >= len(self.words):
            return True
        return bool(self.start and self.spec.kind == "time"
                    and now - self.start >= self.spec.amount)

    def check_rules(self, now):
        """Minimum speed and accuracy, once the test has had a moment."""
        s = self.app.settings
        if self.start is None or not (s.min_wpm or s.min_acc):
            return
        el = now - self.start
        if el < RULE_GRACE:
            return
        wpm, _, acc = self.score(el)
        if s.min_wpm and wpm < s.min_wpm:
            self._fail(f"below {s.min_wpm} wpm")
        elif s.min_acc and acc < s.min_acc:
            self._fail(f"below {s.min_acc}% accuracy")

    def top_up(self):
        """Timed tests get more words as you near the end of the list."""
        if self.spec.kind == "time" and self.spec.source in ("words", "numbers") \
                and self.wi > len(self.words) - 30:
            more = self.app.generator.make(100, self.spec.source)
            self.words += funbox.apply(more, self.app.settings.funbox)
            self.typed += [""] * 100

    def score(self, elapsed):
        return score(self.words, self.typed, self.wi, self.keys,
                     self.bad_keys, elapsed)

    def next_char(self):
        """The key you should press next, " " for space, None at the end."""
        if self.wi >= len(self.words):
            return None
        w, t = self.words[self.wi], self.typed[self.wi]
        return w[len(t)] if len(t) < len(w) else " "

    def hidden(self, now):
        """Memory mode: the words vanish a few seconds into the test."""
        m = self.app.settings.memory
        return bool(m and self.start and now - self.start >= m)

    def status(self, now):
        """Header line and caret marks for the current frame."""
        s = self.app.settings
        spec = self.spec
        marks = set()
        if s.lowkey == "disguised":
            return f"{os.getcwd()}>", marks
        parts = [spec.label]
        if self.start is not None:
            el = now - self.start
            if s.show_timer:
                parts.append(f"{el:.1f}s")
                if spec.kind == "time":
                    parts.append(f"{max(0, spec.amount - int(el))}s left")
            if s.show_progress and spec.kind == "words":
                parts.append(f"{self.wi}/{len(self.words)}")
            if s.show_wpm:
                parts.append(f"{self.score(el)[0]:.0f} wpm")
            if s.show_combo and self.combo > 4:
                parts.append(f"x{self.combo}")
            if s.ghost and self.app.stats.ghost:
                marks.add(self.app.stats.ghost_chars(el))
            if s.pace:
                marks.add(int(s.pace * 5 / 60 * el))
        flags = [f for f in (self.diff if self.diff != "normal" else "",
                             f"stop {self.stop}" if self.stop != "off" else "",
                             "blind" if s.blind else "",
                             s.funbox if s.funbox != "off" else "") if f]
        if flags:
            parts.append("[" + " ".join(flags) + "]")
        return "   ".join(parts), marks

    def footer(self):
        """Key hints, unless switched off or hidden by lowkey. Pressing a key
        that does nothing brings them back until you type again."""
        s = self.app.settings
        if (not s.hints or s.lowkey != "off") and not self.popped_hints:
            return ""
        return self.HINTS

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
            if self._can_backspace():
                self._backspace()
            return None
        if key in (keys.CTRL_BACKSPACE, keys.CTRL_W):
            if self._can_backspace():
                self._wipe_word()
            return None
        if key == keys.ENTER and self.spec.kind == "zen":
            self.done = True
            return None
        if not keys.is_char(key):
            self.popped_hints = key != keys.RESIZE
            return None
        self.popped_hints = False

        if self.start is None:
            self.start = time.time()
        el = time.time() - self.start
        if key == " ":
            self._space(el)
        else:
            self._char(key, el, dt)
        return None

    def _can_backspace(self):
        return self.diff == "normal" and self.app.settings.backspace != "off"

    def _back_ok(self, i):
        """Whether backspacing out of the current word may enter word i."""
        return self.app.settings.backspace == "freedom" \
            or self.typed[i] != self.words[i]

    def _backspace(self):
        self.wrong = False
        if self.typed[self.wi]:
            self.typed[self.wi] = self.typed[self.wi][:-1]
        elif self.wi > 0 and self._back_ok(self.wi - 1):
            self.wi -= 1                        # only back into a wrong word

    def _wipe_word(self):
        self.wrong = False
        if self.typed[self.wi]:
            self.typed[self.wi] = ""
        elif self.wi > 0 and self._back_ok(self.wi - 1):
            self.wi -= 1                        # step back and wipe that word
            self.typed[self.wi] = ""

    def _press(self, el, ok):
        self.keys += 1
        self.samples.append((el, self.keys))
        self.events.append((el, ok))

    def _due(self, c):
        self.presses[c] = self.presses.get(c, 0) + 1

    def _miss(self, want):
        self.bad_keys += 1
        self.combo = 0
        self.misses[want] = self.misses.get(want, 0) + 1
        self.app.stats.miss_key(want)
        if self.app.settings.sound:
            console.bell()

    def _hit(self):
        self.wrong = False
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)

    def _fail(self, reason):
        self.failed = self.done = True
        self.fail_reason = reason

    def _space(self, el):
        word, typed = self.words[self.wi], self.typed[self.wi]
        if not typed:
            return                              # ignore leading spaces
        self._due(" ")
        if typed != word and self.stop != "off" and self.diff != "master":
            # stop on error: the space is a wrong key and the cursor stays put
            self._press(el, False)
            j = len(typed)
            self._miss(word[j] if self.stop == "letter" and j < len(word) else " ")
            self.wrong = True
            return
        self._press(el, typed == word)
        if typed != word:
            self.bad_keys += 1
            self.combo = 0
            if not self.learning:
                self.app.stats.miss_word(word)
            if self.diff in ("expert", "master"):
                self._fail("wrong word")
                return
        else:
            self._hit()
            self._time_word(word, el)
        self.wi += 1
        self.word_start = None

    def _time_word(self, word, el):
        if self.word_start is not None and not self.learning:
            ms = (el - self.word_start) * 1000 / len(word)
            self.app.stats.word_time(word, ms)

    def _char(self, ch, el, dt):
        word = self.words[self.wi]
        if len(self.typed[self.wi]) >= len(word) + MAX_EXTRA:
            return
        j = len(self.typed[self.wi])
        want = word[j] if j < len(word) else "+"
        self._due(want)
        ok = j < len(word) and ch == word[j]
        self._press(el, ok)
        if j == 0:
            self.word_start = el
        if self.learning and j < len(word):
            if ok:
                if dt is not None and 0.03 < dt < 2.0:
                    self.app.learn.hit(ch, dt * 1000)
            else:
                self.app.learn.hit(word[j], None)
        if not ok:
            self._miss(want)
            if self.diff == "master":
                self._fail("wrong key")
                return
            if self.stop == "letter":
                self.wrong = True
                return                          # the key never lands
        else:
            self._hit()
        self.typed[self.wi] += ch
        # the last word of a word test ends as soon as it's long enough
        if self.spec.kind == "words" and self.wi == len(self.words) - 1 \
                and len(self.typed[self.wi]) >= len(word):
            if self.typed[self.wi] != word:
                if self.stop == "word":
                    return                      # fix it before you can finish
                self.bad_keys += 1
                if not self.learning:
                    self.app.stats.miss_word(word)
            else:
                self._time_word(word, el)
            self.wi += 1
            self.done = True

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
        result = TestResult(self.spec, wpm, raw, acc, elapsed, self.bad_keys,
                            self.best_combo, self.misses, self.failed, self.diff,
                            self.fail_reason, self.note, self.events, self.presses)
        result.pb_before = self.app.history.pb(result)
        self.app.history.add(result)
        self.app.save()
        return result


class ZenTest(TypingTest):
    """No target text: whatever you type is the text. Enter finishes."""

    HINTS = ZEN_FOOTER

    def _make_words(self):
        return [""]

    def finished(self, now):
        return self.done

    def check_rules(self, now):
        pass

    def _can_backspace(self):
        return True

    def _backspace(self):
        if self.typed[self.wi]:
            self.typed[self.wi] = self.words[self.wi] = self.typed[self.wi][:-1]
        elif self.wi > 0:
            self.words.pop()
            self.typed.pop()
            self.wi -= 1

    def _wipe_word(self):
        if self.typed[self.wi]:
            self.typed[self.wi] = self.words[self.wi] = ""
        else:
            self._backspace()

    def _space(self, el):
        if not self.typed[self.wi]:
            return
        self._press(el, True)
        self._hit()
        self.wi += 1
        self.words.append("")
        self.typed.append("")

    def _char(self, ch, el, dt):
        self._press(el, True)
        self._due(ch)
        self._hit()
        self.typed[self.wi] += ch
        self.words[self.wi] = self.typed[self.wi]


def slow_words(app, n):
    """A drill of n words drawn from your slowest ones."""
    pool = app.stats.slowest(SLOW_WORDS)
    if not pool:
        return app.generator.make(n)
    return [random.choice(pool) for _ in range(n)]


def keyboard_lines(app, test):
    """The on-screen keyboard for this frame, if it's switched on. In learn
    mode keys are coloured by confidence and locked ones stay dim; otherwise
    your bad keys show red."""
    s = app.settings
    if s.lowkey != "off" or s.keyboard == "off" \
            or (s.keyboard == "learn" and not test.learning):
        return ()
    st = app.styles()
    if test.learning:
        learn = app.learn
        colors = {}
        for c in ORDER[:learn.unlocked()]:
            v = learn.conf(c)
            colors[c] = st.title if v is None else st.conf_color(v) or st.title
        foc = learn.focus_key()
        under = (foc,) if foc else ()
    else:
        colors = {c: st.bad for c in app.stats.bad_keys()}
        under = ()
    return keyboard.render(st, s.layout, test.next_char(), colors, under)


def run_test(app, spec):
    test = (ZenTest if spec.kind == "zen" else TypingTest)(app, spec)
    last_draw = 0.0
    dirty = True
    while True:
        now = time.time()
        test.check_rules(now)
        if test.finished(now):
            break
        test.top_up()
        size = console.size()
        if dirty or now - last_draw > REDRAW_EVERY:
            head, marks = test.status(now)
            draw(app.styles(), app.settings, head, test.words, test.typed,
                 test.wi, max(10, size[0] - 4), test.footer(), marks, test.wrong,
                 keyboard_lines(app, test), test.hidden(now))
            last_draw = now
            dirty = False

        if not keys.key_ready():
            time.sleep(0.01)
            dirty = dirty or console.size() != size
            continue

        key = keys.read_key(resize=False)
        dirty = True
        nav = test.handle(key, time.time())
        if nav is not None:
            return nav
    return test.result()
