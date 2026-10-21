import os
import random
import string
import time

from .. import media
from ..config import MAX_EXTRA, NUMBER_RANGES, RULE_GRACE
from ..learn.progress import ORDER
from ..learn.wordgen import lesson_words
from ..nav import MENU, QUIT
from ..terminal import console, keys
from ..words import books, code, funbox
from . import keyboard
from . import karaoke, speed
from .render import draw
from .result import TestResult
from .scoring import correct_chars, score

FOOTER = "esc menu   tab restart   ctrl-bksp word   ctrl-o settings   ctrl-q hide"
ZEN_FOOTER = "enter finish   esc menu   ctrl-o settings   ctrl-q hide"
LYRICS_FOOTER = ("esc menu   tab sync to the song   ctrl-i song start   ctrl-p pause music   "
                 "ctrl-[ ] offset   ctrl-o settings   ctrl-q hide")
NUDGE = 25            # ms ctrl-[ / ctrl-] move the karaoke offset by
NUDGE_SHOWN = 2.0     # seconds the header shows the new offset
BOOK_FOOTER = ("esc menu   tab restart   pgdn next page   pgup previous page   "
               "ctrl-q hide")
REDRAW_EVERY = 0.1
REDRAW_ANIMATED = 0.05    # smoother when the theme has things moving
SPACE_TYPO = "_"          # how a wrong space shows with indicate typos
SLOW_WORDS = 20       # how many of your slowest words a drill draws from
MIN_SLOW_WORDS = 5    # tracked words needed before the drill is offered
QUOTE_PUNCT = string.punctuation + "“”‘’—–…«»"
LYRIC_QUOTES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'", "´": "'",
                              "“": '"', "”": '"', "„": '"'})   # lyrics: typeable quotes


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
        self.quote = ""        # the quote as picked, for favouriting
        self.timing = []       # lyrics: (seconds, char offset) where each line starts
        self.points = []       # ...and where the karaoke caret is when (karaoke.py)
        self.nudged = -1e9     # when ctrl-[ / ctrl-] last moved the karaoke offset
        self.bpm = None        # lyrics: the song's tempo, once looked up (in the background)
        self.follow = None     # lyrics from spotify: keeps up with it (spotify.Follow)
        self.breaks = set()    # lyrics: the words that start a line of the song
        self.words = self._make_words()
        self.typed = [""] * len(self.words)
        self.wi = self.keys = self.bad_keys = 0
        self.combo = self.best_combo = 0
        self.misses = {}
        self.presses = {}
        self.samples = []
        self.events = []
        self.key_times = []     # every typing key (backspaces too), for active wpm
        self.song_marks = []    # lyrics: (song seconds, char offset you're on) at each of them
        self.start = None
        self.failed = False
        self.fail_reason = ""
        self.done = False       # ended from inside a key press
        self.wrong = False      # last key was rejected by stop on error
        self.err_marks = set()  # (word, letter) positions that had a wrong key
        self.typo_keys = {}     # (word, letter) -> the last wrong key pressed there
        self.missed_words = set()  # words that already had a wrong key counted
        self.last_error = -1.0  # when the last wrong key came (for shake)
        self.prev_t = None
        self.word_start = None  # when the first char of the current word landed
        self.popped_hints = False
        self.abandoned = False  # left from the ctrl-o settings: back to the menu
        self.n_before = app.learn.unlocked() if self.learning else 0

    # ---------------------------------------------------------------- words

    def _make_words(self):
        app, spec = self.app, self.spec
        src = spec.source
        if src in ("custom", "book"):
            words = list(spec.words)
        elif src == "learn":
            return lesson_words(app.learn, app.bank, spec.amount)
        elif src == "quote":
            text, who = app.quotes.pick(app.settings.quote_length,
                                        app.settings.quote_source,
                                        app.settings.quote_genre)
            self.note = who
            self.quote = text
            if app.settings.punctuation == "off":
                text = text.replace("—", " ").replace("--", " ")
                words = [w.strip(QUOTE_PUNCT).replace(",", "") for w in text.split()]
                words = [w for w in words if w]
            else:
                words = text.split()
        elif src == "lyrics":
            words = self._lyric_words()
        elif src == "code":
            self.note, words = code.pick(app.settings.code_lang)
        elif src == "slow":
            words = slow_words(app, spec.amount)
        else:
            words = app.generator.make(
                spec.amount if spec.kind == "words" else 200, src)
        if not app.settings.apostrophes:
            words = [w.replace("'", "").replace("’", "").replace("‘", "") for w in words]
            words = [w for w in words if w]
        words = funbox.apply(words, app.settings.funbox)
        if self.lowercase():
            words = [w.lower() for w in words]
        return words

    def _lyric_words(self):
        """A song's words, line after line, with when they're sung for the
        karaoke caret (see karaoke.py). Curly quotes become the ones on your
        keyboard; punctuation off strips it all - the apostrophes inside
        words too ("there's" is typed theres), as you'd sing it."""
        strip = self.punctuation() == "off"

        def tidy(w):
            w = w.translate(LYRIC_QUOTES)
            if strip:
                w = w.strip(QUOTE_PUNCT).replace(",", "").replace("'", "")
            return w
        words, self.breaks, starts, self.points = karaoke.layout(self.spec.lines, tidy)
        self.timing = starts + [(None, sum(len(w) + 1 for w in words))]
        self.note = self.spec.label             # the song, on the results
        return words

    def song_time(self, now):
        """Seconds into the song at `now`, or None before the test starts: a
        song spotify is playing is where spotify says (followed while you
        type: paused, seeked, carried on); otherwise the song starts with
        your first key, at its first line. The karaoke offset setting moves
        it on (or back), for speakers that play late."""
        if not self.points or self.start is None:
            return None
        if self.follow is not None:
            t = self.follow.position(now)
        elif self.spec.song_at:
            pos, at = self.spec.song_at[:2]
            playing = self.spec.song_at[2] if len(self.spec.song_at) > 2 else True
            t = pos + (now - at) if playing else pos
        else:
            t = self.points[0][0] + (now - self.start)
        return t + self.app.settings.karaoke_offset / 1000

    def song_offset(self, now):
        """Where the singer is, as a char offset into the words (the karaoke
        caret), or None."""
        t = self.song_time(now)
        return None if t is None else karaoke.position(self.points, t)

    # ---------------------------------------------------------------- flow

    def resume_after(self, pause):
        """Carry on after `pause` seconds away (the settings): every clock
        the test keeps moves on by that much, as if no time had passed."""
        self.start += pause
        for name in ("prev_t", "word_start"):
            if getattr(self, name) is not None:
                setattr(self, name, getattr(self, name) + pause)
        if self.last_error >= 0:
            self.last_error += pause

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
        """(wpm, raw, accuracy) in the wpm system the settings pick."""
        if self.app.settings.wpm_system == "classic":
            return self.classic(elapsed)
        return self.active(elapsed)

    def classic(self, elapsed):
        """Over the whole clock, from the first key."""
        return score(self.words, self.typed, self.wi, self.keys,
                     self.bad_keys, elapsed)

    def active(self, elapsed):
        """Over the time you were typing (speed.py): long stops and waiting
        for the singer left out."""
        _, _, acc = self.classic(elapsed)
        secs = self.active_seconds(elapsed)
        if secs < 0.05:                    # not enough typing to tell: the clock
            return self.classic(elapsed)
        wpm, raw = speed.wpm(correct_chars(self.words, self.typed, self.wi), self.keys, secs)
        return wpm, raw, acc

    def active_seconds(self, elapsed):
        return speed.active_seconds(self.key_times, elapsed, self._waits(elapsed))

    def _active(self, now):
        """Note a typing key for active wpm, and in a timed song where the
        singer was."""
        if self.start is None:
            return
        self.key_times.append(now - self.start)
        if self.points:
            done = sum(len(w) + 1 for w in self.words[:self.wi]) + len(self.typed[self.wi])                 if self.wi < len(self.words) else self.timing[-1][1]
            self.song_marks.append((self.song_time(now), done))

    def _waits(self, elapsed):
        """How much of the gap after each key was spent ahead of the singer:
        the caret hadn't got to the letter you were on yet."""
        if not self.song_marks:
            return ()
        out = []
        ends = [m[0] for m in self.song_marks[1:]] + [self.song_time(self.start + elapsed)]
        for (gap, ((s0, c), s1)) in zip(speed.gaps(self.key_times, elapsed),
                                        zip(self.song_marks, ends)):
            r = karaoke.reach(self.points, c + 1)       # the singer at the next letter
            if s0 is None or s1 is None or r <= s0:
                out.append(0.0)                         # you were behind: typing
            elif s1 <= r:
                out.append(gap)                         # ahead all the gap
            else:
                out.append(gap * (r - s0) / max(s1 - s0, 1e-6))
        return out

    def song_wpm(self):
        """The speed the song needs: its words (as typed, spaces too) over
        the time from its first line to its last line sung, or None for
        lyrics without timestamps."""
        if len(self.points) < 2:
            return None
        secs = self.points[-1][0] - self.points[0][0]
        chars = self.points[-1][1] - self.points[0][1]
        return (chars / 5) / (secs / 60) if secs > 0 else None

    def look_up_tempo(self):
        """Ask for the song's tempo in the background; the header shows it
        once it's in."""
        if not self.spec.song or not self.app.settings.show_bpm:
            return
        import threading
        from ..words import tempo
        title, artist, secs = self.spec.song

        def ask():
            self.bpm = tempo.bpm(title, artist, secs)
        threading.Thread(target=ask, daemon=True).start()

    def nudge(self, ms):
        """Ctrl-[ / ctrl-] following spotify: the karaoke offset back or on
        by ms, kept in the settings; the header shows it for a moment."""
        s = self.app.settings
        lo, hi = NUMBER_RANGES["karaoke_offset"]
        s.karaoke_offset = max(lo, min(hi, s.karaoke_offset + ms))
        self.app.save_settings()
        self.nudged = time.time()

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
            racing = s.ghost and self.app.stats.ghost       # a ghost replaying your last run
            if s.show_combo and self.combo > 4 and not racing:
                parts.append(f"x{self.combo}")             # (hidden while you race it)
            if racing:
                marks.add(self.app.stats.ghost_chars(el))
            if s.pace:
                marks.add(int(s.pace * 5 / 60 * el))
            if spec.source == "lyrics" and s.karaoke:
                sung = self.song_offset(now)
                if sung is not None:
                    marks.add(sung)
        if spec.source == "lyrics":
            need = self.song_wpm() if s.show_song_wpm else None
            if need:
                parts.append(f"song {need:.0f} wpm")
            if s.show_bpm and self.bpm:
                parts.append(f"{self.bpm:.0f} bpm")
        if self.follow is not None:
            if now - self.nudged < NUDGE_SHOWN:
                parts.append(f"sync {s.karaoke_offset:+d} ms")
            if not self.follow.playing:
                parts.append("music paused")
            if self.follow.missing:
                parts.append(f"lyrics site busy - retrying {self.follow.missing}"
                             if getattr(self.follow, "busy", False)
                             else f"no lyrics for {self.follow.missing}")
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
        if self.spec.source == "lyrics":
            return (LYRICS_FOOTER if self.follow is not None
                    else LYRICS_FOOTER.replace("tab sync to the song", "tab restart")
                                       .replace("ctrl-i song start   ", "")
                                       .replace("ctrl-[ ] offset   ", ""))
        return BOOK_FOOTER if self.spec.source == "book" else self.HINTS

    # ---------------------------------------------------------------- input

    def handle(self, key, now):
        """Apply one key press. Returns a navigation value to leave the test
        early, otherwise None."""
        dt = None if self.prev_t is None else now - self.prev_t
        self.prev_t = now

        if key == keys.ESC:
            return MENU
        if key == keys.TAB:
            if self.follow is not None:       # a song spotify is playing: from where it is now
                from ..ui.lyrics_mode import synced     # the ui imports the engine
                return synced(self.spec, self.follow.now)
            return self.spec
        if key in (keys.CTRL_LBRACKET, keys.CTRL_RBRACKET) and self.follow is not None:
            self.nudge(-NUDGE if key == keys.CTRL_LBRACKET else NUDGE)
            return None
        if key == keys.CTRL_I and self.spec.source == "lyrics":
            from ..ui.lyrics_mode import from_start     # the ui imports the engine
            return from_start(self.spec)
        if key in (keys.CTRL_C, keys.CTRL_D):
            return QUIT
        if self.spec.source == "book" and key in (keys.PGDN, keys.PGUP):
            # skip a page without finishing this one
            return books.neighbour(self.app, self.spec,
                                   1 if key == keys.PGDN else -1)
        if key == keys.BACKSPACE:
            if self._can_backspace():
                self._backspace()
                self._active(time.time())
            return None
        if key in (keys.CTRL_BACKSPACE, keys.CTRL_W):
            if self._can_backspace():
                self._wipe_word()
                self._active(time.time())
            return None
        if key in (keys.ENTER, keys.SHIFT_ENTER) and self.spec.kind == "zen":
            self.done = True
            return None
        if not keys.is_char(key):
            self.popped_hints = key != keys.RESIZE
            return None
        self.popped_hints = False

        if self.start is None:
            self.start = time.time()
        el = time.time() - self.start
        self._active(self.start + el)
        if self.hacker():
            self._hack(el)
        elif key == " ":
            self._space(el)
        else:
            self._char(key, el, dt)
        return None

    def hacker(self):
        """The hacker funbox: every key finishes a word, like a hacker in a
        film. Just for fun - a run isn't kept as a best or in your stats."""
        return self.app.settings.funbox == "hacker" and self.spec.kind != "zen"

    def _hack(self, el):
        """Any key: the rest of the word you're on, and the space after it,
        typed for you - all of it right."""
        if self.wi >= len(self.words):
            return
        word = self.words[self.wi]
        for _ in word[len(self.typed[self.wi]):] + " ":
            self._press(el, True)
            self._hit()
        self.typed[self.wi] = word
        self.wi += 1
        self.word_start = None
        if self.spec.kind == "words" and self.wi >= len(self.words):
            self.done = True

    def _can_backspace(self):
        """Whether backspace works: the backspace setting decides, and
        expert / master switch it off. Except that with stop on error
        "word" you can't leave a wrong word, so backspace always works
        inside one - without it you'd be stuck there."""
        s = self.app.settings
        if self.stop == "word" and self.typed[self.wi] \
                and self.typed[self.wi] != self.words[self.wi][:len(self.typed[self.wi])]:
            return True
        return self.diff == "normal" and s.backspace != "off"

    def error_marks(self):
        """Letters that had a wrong key at some point; the renderer decides
        how a fixed one looks (the corrected letters setting)."""
        return self.err_marks

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
        self.missed_words.add(self.wi)
        self.last_error = time.time()
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

    def _forgive(self):
        """Whether punctuation can be skipped without a mistake."""
        return self.punctuation() == "forgive"

    def punctuation(self):
        """The punctuation setting for this test: lyrics have their own
        (unless it's "same")."""
        s = self.app.settings
        if self.spec.source == "lyrics" and s.lyrics_punctuation != "same":
            return s.lyrics_punctuation
        return s.punctuation

    def lowercase(self):
        """Whether the words are all lower case: lyrics have their own
        capitals setting (on: as sung, off: all lowercase)."""
        s = self.app.settings
        if self.spec.source == "lyrics" and s.lyrics_capitals != "same":
            return s.lyrics_capitals == "off"
        return s.lowercase

    def _caps_forgive(self):
        """Lyrics capitals on forgive: capitals show, but the lower case
        letter counts too (no shift needed)."""
        return self.spec.source == "lyrics" and self.app.settings.lyrics_capitals == "forgive"

    def _same(self, ch, want):
        """Whether key ch types the letter want."""
        return ch == want or (self._caps_forgive() and want.isupper() and ch == want.lower())

    def tape(self):
        """The tape setting for this test: lyrics have their own too."""
        s = self.app.settings
        if self.spec.source == "lyrics" and s.lyrics_tape != "same":
            return s.lyrics_tape
        return s.tape

    def line_breaks(self):
        """(word indices that start a song's line, how to show them)."""
        if not self.breaks:
            return (), "off"
        return self.breaks, self.app.settings.lyrics_lines

    def _space(self, el):
        word, typed = self.words[self.wi], self.typed[self.wi]
        if not typed:
            return                              # ignore leading spaces
        if self._forgive() and typed == word.rstrip(QUOTE_PUNCT) != word:
            typed = self.typed[self.wi] = word   # trailing punctuation skipped
        self._due(" ")
        if typed != word and self.stop != "off" and self.diff != "master":
            # stop on error: the space is a wrong key and the cursor stays put
            self._press(el, False)
            j = len(typed)
            self._miss(word[j] if self.stop == "letter" and j < len(word) else " ")
            if j < len(word):
                self.err_marks.add((self.wi, j))
                self.typo_keys[(self.wi, j)] = SPACE_TYPO
            self.wrong = True
            return
        self._press(el, typed == word)
        if typed != word:
            if self.wi not in self.missed_words:
                self.bad_keys += 1      # a wrong word with no wrong key in it
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
        if self._forgive():
            # punctuation you leave out is typed for you: the next key matches
            # the letter after it, not the mark itself
            while j < len(word) and word[j] in QUOTE_PUNCT and j + 1 < len(word) \
                    and ch != word[j] and self._same(ch, word[j + 1]):
                self.typed[self.wi] += word[j]
                j += 1
        want = word[j] if j < len(word) else "+"
        self._due(want)
        ok = j < len(word) and (self._same(ch, word[j]) or (self._forgive()
                                                  and ch in ("'", "’", "‘") and word[j] in ("'", "’", "‘")))
        if ok and j < len(word) and ch != word[j]:
            ch = word[j]
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
            if j < len(word):
                self.err_marks.add((self.wi, j))
                self.typo_keys[(self.wi, j)] = ch
            if self.diff == "master":
                self._fail("wrong key")
                return
            if self.stop == "letter":
                self.wrong = True
                return                          # the key never lands
        else:
            self._hit()
        self.typed[self.wi] += ch
        if self._forgive() and self.spec.kind == "words" and self.wi == len(self.words) - 1:
            t = self.typed[self.wi]
            if len(t) < len(word) and word.startswith(t) and not word[len(t):].strip(QUOTE_PUNCT):
                self.typed[self.wi] = word      # only skipped punctuation left
        # the last word of a word test ends as soon as it's long enough
        if self.spec.kind == "words" and self.wi == len(self.words) - 1 \
                and len(self.typed[self.wi]) >= len(word):
            if self.typed[self.wi] != word:
                if self.stop == "word":
                    return                      # fix it before you can finish
                if self.wi not in self.missed_words:
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
        classic, active = self.classic(elapsed)[0], self.active(elapsed)[0]
        if self.learning:
            self.app.learn.finish(self.n_before)
        counted = not self.hacker()             # a hacker run is just for fun
        if not self.failed and counted:
            self.app.stats.ghost[:] = self.samples
            self.app.stats.history.append(wpm)
            if self.spec.source == "book":
                books.finished_page(self.app, self.spec)
        result = TestResult(self.spec, wpm, raw, acc, elapsed, self.bad_keys,
                            self.best_combo, self.misses, self.failed, self.diff,
                            self.fail_reason, self.note, self.events, self.presses)
        result.quote = self.quote
        result.system = self.app.settings.wpm_system
        result.classic, result.active = classic, active
        result.active_secs = self.active_seconds(elapsed)
        result.pb_before = self.app.history.pb(result)
        result.counted = counted
        if counted:
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

    def paint(now=None):
        now = now or time.time()
        st = app.styles()
        head, marks = test.status(now)
        draw(st, app.settings, head, test.words, test.typed,
             test.wi, max(10, console.size()[0] - 4), test.footer(), marks, test.wrong,
             keyboard_lines(app, test), test.hidden(now),
             test.error_marks(), test.combo, now, test.last_error,
             test.typo_keys, test.tape(), *test.line_breaks())
    app.current_test = (test, paint)       # for ctrl-o: pause, settings, resume?
    from ..ui.lyrics_mode import follow_for     # the ui imports the engine
    test.follow = follow_for(spec)
    test.look_up_tempo()
    try:
        return _run(app, test, paint)
    finally:
        app.current_test = None
        if test.follow is not None:
            test.follow.stop()


def _next_song(test):
    """The test for the song spotify moved on to (its lyrics are fetched)."""
    from ..ui.lyrics_mode import song_at, spec_for
    song, now = test.follow.next
    return spec_for(song, song_at(now))


def pause(app, test, paint):
    """Esc in a test that's under way: the clock stops and the pause box
    asks whether to resume. True to carry on, False to leave the test."""
    from ..ui.anywhere import resume_dialog     # the ui imports the engine
    paused = time.time()
    if resume_dialog(app, paint, "Paused - resume?"):
        test.resume_after(time.time() - paused)
        return True
    return False


def _run(app, test, paint):
    last_draw = 0.0
    dirty = True
    while True:
        now = time.time()
        if test.abandoned:
            return MENU
        test.check_rules(now)
        if test.finished(now):
            break
        test.top_up()
        size = console.size()
        st = app.styles()
        every = REDRAW_ANIMATED if st.animated else REDRAW_EVERY
        if dirty or now - last_draw > every:
            paint(now)
            last_draw = now
            dirty = False

        if test.follow is not None and test.follow.next is not None:
            return _next_song(test)           # spotify moved on: type the new song
        if not keys.key_ready():
            time.sleep(0.002)
            dirty = dirty or console.size() != size
            continue

        key = keys.read_key(resize=False)
        dirty = True
        if key == keys.CTRL_P:                # pause the music, and the test with it
            media.play_pause()
            if test.start is None:
                continue
            if pause(app, test, paint):
                media.play_pause()            # carry on: the music too
                continue
            return MENU
        if key == keys.ESC and app.settings.esc_pause and test.start is not None:
            if pause(app, test, paint):
                continue
            return MENU
        nav = test.handle(key, time.time())
        if nav is not None:
            return nav
    return test.result()
