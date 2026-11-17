// A test played back as it was typed (engine/replay.py): each frame is what
// one key changed - [seconds in, word you're on, {word: typed}, {"w,l": wrong
// key}, combo, wrong] - and seeking applies frames from the start.

export class Recorder {
  constructor() {
    this.frames = [];
    this._typed = [];
    this._typos = {};
  }

  snap(test, now) {
    if (test.start === null) return;
    const typed = {};
    test.typed.forEach((t, i) => {
      if ((this._typed[i] ?? "") !== t) typed[i] = t;
    });
    const typos = {};
    for (const [k, v] of Object.entries(test.typoKeys)) if (this._typos[k] !== v) typos[k] = v;
    this._typed = [...test.typed];
    this._typos = { ...test.typoKeys };
    this.frames.push([Math.max(0, now - test.start), test.wi, typed, typos, test.combo, test.wrong]);
  }
}

export class Replay {
  constructor(words, frames, tape = "off") {
    this.words = [...words];
    this.frames = [...frames];
    this.tape = tape;
  }

  get length() {
    return this.frames.length ? this.frames[this.frames.length - 1][0] : 0;
  }

  /** The screen at t seconds in. */
  at(t) {
    let typed = new Array(this.words.length).fill("");
    const typos = {};
    let wi = 0, combo = 0, wrong = false, n = 0;
    for (const [el, wi2, changed, newTypos, combo2, wrong2] of this.frames) {
      if (el > t) break;
      for (const [i, text] of Object.entries(changed)) {
        while (typed.length <= +i) typed.push("");
        typed[+i] = text;
      }
      Object.assign(typos, newTypos);
      wi = wi2; combo = combo2; wrong = wrong2; n++;
    }
    return { typed, wi, errors: new Set(Object.keys(typos)), typos, combo, wrong, keys: n };
  }

  /** Correct words' letters (and their spaces) over the time so far. */
  wpm(typed, t) {
    if (t <= 0) return 0;
    let chars = 0;
    this.words.forEach((w, i) => {
      if (typed[i] && typed[i] === w) chars += w.length + 1;
    });
    return chars / 5 / (t / 60);
  }
}
