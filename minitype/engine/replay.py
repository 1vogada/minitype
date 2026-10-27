"""A test played back as it was typed: every key's effect on the screen,
recorded while you type, and rebuilt at any moment for the replay screen.

Each frame is what one key changed - (seconds in, the word you're on,
{word: its typed text}, {(word, letter): wrong key}, combo, wrong) - so a
long test stays small, and seeking just applies frames from the start."""


class Recorder:
    def __init__(self):
        self.frames = []
        self._typed = []
        self._typos = {}

    def snap(self, test, now):
        """Record what the last key changed; nothing before the first key."""
        if test.start is None:
            return
        typed = {i: t for i, t in enumerate(test.typed)
                 if (self._typed[i] if i < len(self._typed) else "") != t}
        typos = {k: v for k, v in test.typo_keys.items() if self._typos.get(k) != v}
        self._typed = list(test.typed)
        self._typos = dict(test.typo_keys)
        self.frames.append((max(0.0, now - test.start), test.wi, typed, typos,
                            test.combo, test.wrong))


class Replay:
    """A recorded test: its words, its frames and how it was drawn."""

    def __init__(self, words, frames, tape=None, breaks=(), split="off"):
        self.words = list(words)
        self.frames = list(frames)
        self.tape, self.breaks, self.split = tape, breaks, split

    @property
    def length(self):
        return self.frames[-1][0] if self.frames else 0.0

    def at(self, t):
        """The screen at t seconds in: (typed, wi, errors, typos, combo,
        wrong, keys so far)."""
        typed = [""] * len(self.words)
        typos, wi, combo, wrong, n = {}, 0, 0, False, 0
        for el, wi_, changed, new_typos, combo_, wrong_ in self.frames:
            if el > t:
                break
            for i, text in changed.items():
                if i >= len(typed):
                    typed += [""] * (i + 1 - len(typed))
                typed[i] = text
            typos.update(new_typos)
            wi, combo, wrong, n = wi_, combo_, wrong_, n + 1
        return typed, wi, set(typos), typos, combo, wrong, n

    def wpm(self, typed, t):
        """Correct words' letters (and their spaces) over the time so far."""
        if t <= 0:
            return 0.0
        chars = sum(len(w) + 1 for w, got in zip(self.words, typed) if got and got == w)
        return chars / 5 / (t / 60)
