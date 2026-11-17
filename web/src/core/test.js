// One test's state and rules, independent of the screen (engine/runner.py:
// TypingTest and ZenTest). Times are seconds (epoch, with fractions); a key
// is a single character or one of the names in KEY.

import { MAX_EXTRA, ORDER, QUOTE_PUNCT, RULE_GRACE } from "./config.js";
import { Recorder, Replay } from "./replay.js";
import { activeSeconds, correctChars, score, wpmOver } from "./scoring.js";
import { History } from "./history.js";
import * as bestWords from "./bestWords.js";
import { lessonWords } from "./learn.js";
import { funbox, pick } from "./words.js";

export const KEY = {
  ESC: "ESC", TAB: "TAB", ENTER: "ENTER", SHIFT_ENTER: "SHIFT_ENTER", BACKSPACE: "BACKSPACE",
  CTRL_BACKSPACE: "CTRL_BACKSPACE", CTRL_C: "CTRL_C", OTHER: "OTHER",
};
export const MENU = "MENU";
export const QUIT = "QUIT";

export const REPLAY_BELOW = 90;   // % accuracy: a finished test under it replays on tab
export const SPACE_TYPO = "_";
export const SLOW_WORDS = 20;
export const MIN_SLOW_WORDS = 5;
export const LEARN_MIN_ACC = 60;  // % right keystrokes: under it a test isn't sent to keyboard learn

export const isChar = (key) => [...key].length === 1;
const posKey = (wi, j) => `${wi},${j}`;

/** A test to run (engine/spec.py). */
export function makeSpec(label, kind, amount, source = "words", extra = {}) {
  return { label, kind, amount, source, words: null, replay: null, ...extra };
}

function stripPunct(w) {
  let a = 0, b = w.length;
  while (a < b && QUOTE_PUNCT.includes(w[a])) a++;
  while (b > a && QUOTE_PUNCT.includes(w[b - 1])) b--;
  return w.slice(a, b);
}
const rstripPunct = (w) => {
  let b = w.length;
  while (b > 0 && QUOTE_PUNCT.includes(w[b - 1])) b--;
  return w.slice(0, b);
};
const isUpper = (c) => c !== c.toLowerCase() && c === c.toUpperCase();

export class TypingTest {
  constructor(app, spec) {
    this.app = app;
    this.spec = spec;
    const s = app.settings;
    this.diff = s.difficulty;
    this.stop = s.stop_on_error;
    this.learning = spec.source === "learn";
    this.best = spec.source === bestWords.SOURCE;
    this.note = "";
    this.quote = "";
    this.words = spec.replay ? [...spec.replay] : this.makeWords();
    this.typed = this.words.map(() => "");
    this.wi = this.keys = this.badKeys = 0;
    this.combo = this.bestCombo = 0;
    this.misses = {};
    this.presses = {};
    this.samples = [];
    this.events = [];
    this.recorder = new Recorder();
    this.keyTimes = [];
    this.start = null;
    this.lastKey = null;
    this.failed = false;
    this.failReason = "";
    this.done = false;
    this.wrong = false;
    this.errMarks = new Set();    // "w,l" positions that had a wrong key
    this.typoKeys = {};           // "w,l" -> the last wrong key pressed there
    this.missedWords = new Set();
    this.lastError = -1;
    this.prevT = null;
    this.wordStart = null;
    this.poppedHints = false;
    this.nBefore = this.learning ? app.learn.unlocked() : 0;
    this.keystrokes = s.keyboard_learn && !this.best ? [] : null;
    this.onMiss = null;           // the screen's: a beep, a shake
  }

  rng() { return this.app.rng ? this.app.rng() : Math.random(); }

  // ---------------------------------------------------------------- words

  makeWords() {
    const app = this.app, spec = this.spec, s = app.settings, rng = () => this.rng();
    const src = spec.source;
    let words;
    if (src === "custom") words = [...spec.words];
    else if (src === "learn") return lessonWords(app.learn, app.bank, spec.amount, rng);
    else if (src === "quote") {
      const q = app.quotes.pick(s.quote_length, s.quote_source, s.quote_genre, rng);
      this.note = q.source;
      this.quote = q.text;
      let text = q.text;
      if (s.punctuation === "off") {
        text = text.replaceAll("—", " ").replaceAll("--", " ");
        words = text.split(/\s+/).map((w) => stripPunct(w).replaceAll(",", "")).filter(Boolean);
      } else words = text.split(/\s+/).filter(Boolean);
    } else if (src === "code") {
      const snippets = app.code[s.code_lang] ?? app.code.python;
      const sn = pick(snippets, rng);
      this.note = sn.name;
      words = sn.text.split(/\s+/).filter(Boolean);
    } else if (src === "slow") words = slowWords(app, spec.amount, rng);
    else if (src === bestWords.SOURCE) {
      const n = spec.kind === "words" ? spec.amount : 200;
      words = bestWords.words(app.stats, n, rng, app.learn.stats);
      if (!words.length) words = app.generator.make(n);
    } else words = app.generator.make(spec.kind === "words" ? spec.amount : 200, src);
    if (!s.apostrophes) words = words.map((w) => w.replace(/['’‘]/g, "")).filter(Boolean);
    words = funbox(words, s.funbox, rng);
    if (s.lowercase) words = words.map((w) => w.toLowerCase());
    return words;
  }

  // ---------------------------------------------------------------- flow

  /** Carry on after `pause` seconds away: every clock moves on by that much. */
  resumeAfter(pause) {
    this.start += pause;
    for (const k of ["prevT", "wordStart", "lastKey"]) if (this[k] !== null) this[k] += pause;
    if (this.lastError >= 0) this.lastError += pause;
  }

  finished(now) {
    if (this.done) return true;
    if (this.spec.kind === "words" && this.wi >= this.words.length) return true;
    return Boolean(this.start !== null && this.spec.kind === "time" && now - this.start >= this.spec.amount);
  }

  elapsed(now) {
    const el = now - this.start;
    if (this.spec.kind === "time") return Math.min(el, this.spec.amount);
    if (this.spec.kind === "words" && this.wi >= this.words.length && this.lastKey) return this.lastKey - this.start;
    return el;
  }

  checkRules(now) {
    const s = this.app.settings;
    if (this.start === null || !(s.min_wpm || s.min_acc)) return;
    const el = now - this.start;
    if (el < RULE_GRACE) return;
    const [wpm, , acc] = this.score(el);
    if (s.min_wpm && wpm < s.min_wpm) this.fail(`below ${s.min_wpm} wpm`);
    else if (s.min_acc && acc < s.min_acc) this.fail(`below ${s.min_acc}% accuracy`);
  }

  /** Timed tests get more words as you near the end of the list. */
  topUp() {
    if (this.spec.kind === "time" && ["words", "numbers"].includes(this.spec.source) && this.wi > this.words.length - 30) {
      const more = funbox(this.app.generator.make(100, this.spec.source), this.app.settings.funbox, () => this.rng());
      const lower = this.app.settings.lowercase ? more.map((w) => w.toLowerCase()) : more;
      this.words.push(...lower);
      this.typed.push(...lower.map(() => ""));
      return true;
    }
    return false;
  }

  score(elapsed) {
    return this.app.settings.wpm_system === "classic" ? this.classic(elapsed) : this.active(elapsed);
  }

  classic(elapsed) {
    return score(this.words, this.typed, this.wi, this.keys, this.badKeys, elapsed);
  }

  active(elapsed) {
    const [, , acc] = this.classic(elapsed);
    const secs = this.activeSeconds(elapsed);
    if (secs < 0.05) return this.classic(elapsed);
    const [wpm, raw] = wpmOver(correctChars(this.words, this.typed, this.wi), this.keys, secs);
    return [wpm, raw, acc];
  }

  activeSeconds(elapsed) { return activeSeconds(this.keyTimes, elapsed); }

  noteActive(now) {
    if (this.start !== null) this.keyTimes.push(now - this.start);
  }

  /** The key you should press next, " " for space, null at the end. */
  nextChar() {
    if (this.wi >= this.words.length) return null;
    const w = this.words[this.wi], t = this.typed[this.wi];
    return t.length < w.length ? w[t.length] : " ";
  }

  hidden(now) {
    const m = this.app.settings.memory;
    return Boolean(m && this.start !== null && now - this.start >= m);
  }

  // ---------------------------------------------------------------- input

  /** Apply one key press at `now`. Returns MENU / QUIT / a spec to leave, else null. */
  handle(key, now) {
    const dt = this.prevT === null ? null : now - this.prevT;
    this.prevT = now;
    if (key === KEY.ESC) return MENU;
    if (key === KEY.TAB) {
      if (this.app.settings.tab_same && (this.wi || (this.wi < this.typed.length && this.typed[this.wi]))) {
        return { ...this.spec, replay: [...this.words] };   // typed something: the same words again
      }
      return this.spec.replay ? { ...this.spec, replay: null } : this.spec;   // nothing typed: new words
    }
    if (key === KEY.CTRL_C) return QUIT;
    if (key === KEY.BACKSPACE) {
      this.log(now, "");
      if (this.canBackspace()) {
        this.backspace();
        this.noteActive(now);
      }
      return null;
    }
    if (key === KEY.CTRL_BACKSPACE) {
      if (this.canBackspace()) {
        this.wipeWord();
        this.noteActive(now);
      }
      return null;
    }
    if ((key === KEY.ENTER || key === KEY.SHIFT_ENTER) && this.spec.kind === "zen") {
      this.done = true;
      return null;
    }
    if (!isChar(key)) {
      this.poppedHints = true;
      return null;
    }
    this.poppedHints = false;
    if (this.start === null) this.start = now;
    if (this.spec.kind === "time" && now - this.start >= this.spec.amount) {
      this.done = true;
      return null;
    }
    this.log(now, key);
    const el = now - this.start;
    this.lastKey = now;
    this.noteActive(now);
    if (this.hacker()) this.hack(el);
    else if (key === " ") this.space(el, now);
    else this.char(key, el, dt, now);
    return null;
  }

  log(now, typed) {
    if (this.keystrokes !== null) {
      this.keystrokes.push({ t: Math.round(now * 1000), expected: this.expected(typed), typed });
    }
  }

  /** The char key `typed` is compared with, before it lands. */
  expected(typed) {
    if (this.wi >= this.words.length || this.hacker()) return null;
    const word = this.words[this.wi];
    let j = this.typed[this.wi].length;
    if (this.forgive() && typed !== "") {
      if (typed === " " && this.typed[this.wi] === rstripPunct(word)) return " ";
      while (j < word.length && QUOTE_PUNCT.includes(word[j]) && j + 1 < word.length
        && typed !== word[j] && this.same(typed, word[j + 1])) j++;
    }
    if (j < word.length) return word[j];
    return this.wi === this.words.length - 1 && this.spec.kind !== "time" ? null : " ";
  }

  hacker() {
    return ["hacker", "god hacker"].includes(this.app.settings.funbox) && this.spec.kind !== "zen";
  }

  hack(el) {
    if (this.wi >= this.words.length) return;
    const word = this.words[this.wi], typed = this.typed[this.wi];
    const rest = this.app.settings.funbox === "god hacker" || typed.length >= word.length
      ? word.slice(typed.length) + " " : word[typed.length];
    for (let i = 0; i < rest.length; i++) {
      this.press(el, true);
      this.hit();
    }
    this.typed[this.wi] = (typed + rest).replace(/ +$/, "");
    const last = this.spec.kind === "words" && this.wi === this.words.length - 1;
    if (rest.endsWith(" ") || (last && this.typed[this.wi] === word)) {
      this.wi++;
      this.wordStart = null;
      if (this.spec.kind === "words" && this.wi >= this.words.length) this.done = true;
    }
  }

  canBackspace() {
    const s = this.app.settings, t = this.typed[this.wi] ?? "";
    if (this.stop === "word" && t && t !== this.words[this.wi].slice(0, t.length)) return true;
    return this.diff === "normal" && s.backspace !== "off";
  }

  backOk(i) {
    return this.app.settings.backspace === "freedom" || this.typed[i] !== this.words[i];
  }

  backspace() {
    this.wrong = false;
    if (this.typed[this.wi]) this.typed[this.wi] = this.typed[this.wi].slice(0, -1);
    else if (this.wi > 0 && this.backOk(this.wi - 1)) this.wi--;
  }

  wipeWord() {
    this.wrong = false;
    if (this.typed[this.wi]) this.typed[this.wi] = "";
    else if (this.wi > 0 && this.backOk(this.wi - 1)) {
      this.wi--;
      this.typed[this.wi] = "";
    }
  }

  press(el, ok) {
    this.keys++;
    this.samples.push([el, this.keys]);
    this.events.push([el, ok]);
  }

  due(c) { this.presses[c] = (this.presses[c] ?? 0) + 1; }

  miss(want, now) {
    this.badKeys++;
    this.combo = 0;
    this.missedWords.add(this.wi);
    this.lastError = now;
    this.misses[want] = (this.misses[want] ?? 0) + 1;
    if (!this.best) this.app.stats.missKey(want);
    this.onMiss?.();
  }

  hit() {
    this.wrong = false;
    this.combo++;
    this.bestCombo = Math.max(this.bestCombo, this.combo);
  }

  fail(reason) {
    this.failed = this.done = true;
    this.failReason = reason;
  }

  forgive() { return this.app.settings.punctuation === "forgive"; }
  same(ch, want) { return ch === want; }
  tape() { return this.app.settings.tape; }
  tracked() { return !this.learning && !this.best; }

  wordDone(word, clean) {
    if (this.tracked()) this.app.stats.wordDone(word, clean);
  }

  timeWord(word, el) {
    if (this.wordStart !== null && this.tracked()) {
      this.app.stats.wordTime(word, ((el - this.wordStart) * 1000) / word.length);
    }
  }

  space(el, now) {
    const word = this.words[this.wi];
    let typed = this.typed[this.wi];
    if (!typed) return;                              // leading spaces are ignored
    if (this.forgive() && typed === rstripPunct(word) && typed !== word) typed = this.typed[this.wi] = word;
    this.due(" ");
    if (typed !== word && this.stop !== "off" && this.diff !== "master") {
      // stop on error: the space is a wrong key and the cursor stays put
      this.press(el, false);
      const j = typed.length;
      this.miss(this.stop === "letter" && j < word.length ? word[j] : " ", now);
      if (j < word.length) {
        this.errMarks.add(posKey(this.wi, j));
        this.typoKeys[posKey(this.wi, j)] = SPACE_TYPO;
      }
      this.wrong = true;
      return;
    }
    this.press(el, typed === word);
    if (typed !== word) {
      if (!this.missedWords.has(this.wi)) this.badKeys++;
      this.combo = 0;
      if (this.tracked()) this.app.stats.missWord(word);
      this.wordDone(word, false);
      if (this.diff === "expert" || this.diff === "master") {
        this.fail("wrong word");
        return;
      }
    } else {
      this.hit();
      this.timeWord(word, el);
      this.wordDone(word, !this.missedWords.has(this.wi));
    }
    this.wi++;
    this.wordStart = null;
  }

  char(ch, el, dt, now) {
    const word = this.words[this.wi];
    if (this.typed[this.wi].length >= word.length + MAX_EXTRA) return;
    let j = this.typed[this.wi].length;
    if (this.forgive()) {
      // punctuation you leave out is typed for you
      while (j < word.length && QUOTE_PUNCT.includes(word[j]) && j + 1 < word.length
        && ch !== word[j] && this.same(ch, word[j + 1])) {
        this.typed[this.wi] += word[j];
        j++;
      }
    }
    const want = j < word.length ? word[j] : "+";
    this.due(want);
    const ok = j < word.length && (this.same(ch, word[j])
      || (this.forgive() && "'’‘".includes(ch) && "'’‘".includes(word[j])));
    if (ok && ch !== word[j]) ch = word[j];
    this.press(el, ok);
    if (j === 0) this.wordStart = el;
    if (this.learning && j < word.length) {
      if (ok) {
        if (dt !== null && dt > 0.03 && dt < 2.0) this.app.learn.hit(ch, dt * 1000);
      } else this.app.learn.hit(word[j], null);
    }
    if (!ok) {
      this.miss(want, now);
      if (j < word.length) {
        this.errMarks.add(posKey(this.wi, j));
        this.typoKeys[posKey(this.wi, j)] = ch;
      }
      if (this.diff === "master") {
        this.fail("wrong key");
        return;
      }
      if (this.stop === "letter") {
        this.wrong = true;
        return;                                      // the key never lands
      }
    } else this.hit();
    this.typed[this.wi] += ch;
    if (this.forgive() && this.spec.kind === "words" && this.wi === this.words.length - 1) {
      const t = this.typed[this.wi];
      if (t.length < word.length && word.startsWith(t) && !stripPunct(word.slice(t.length))) this.typed[this.wi] = word;
    }
    // the last word of a word test ends as soon as it's long enough
    if (this.spec.kind === "words" && this.wi === this.words.length - 1 && this.typed[this.wi].length >= word.length) {
      if (this.typed[this.wi] !== word) {
        if (this.stop === "word") return;
        if (!this.missedWords.has(this.wi)) this.badKeys++;
        if (this.tracked()) this.app.stats.missWord(word);
        this.wordDone(word, false);
      } else {
        this.timeWord(word, el);
        this.wordDone(word, !this.missedWords.has(this.wi));
      }
      this.wi++;
      this.done = true;
    }
  }

  // ---------------------------------------------------------------- end

  /** Wrap up: record the run and return its result, or MENU if nothing was typed. */
  result(now) {
    if (this.start === null) return MENU;
    const elapsed = this.elapsed(now);
    const [wpm, raw, acc] = this.score(elapsed);
    const classic = this.classic(elapsed)[0], active = this.active(elapsed)[0];
    if (this.learning) this.app.learn.finish(this.nBefore);
    const counted = !this.hacker();
    if (!this.failed && counted && !this.best) {
      this.app.stats.ghost = [...this.samples];
      this.app.stats.history.push(wpm);
    }
    // tab on the results: new words once it went well; below REPLAY_BELOW (or
    // failed), with tab replays on, the same words again
    const retry = this.app.settings.tab_same && (this.failed || acc < REPLAY_BELOW);
    const again = { ...this.spec, replay: retry ? [...this.words] : null };
    const result = {
      spec: again, wpm, raw, acc, elapsed, errors: this.badKeys, bestCombo: this.bestCombo,
      misses: this.misses, failed: this.failed, difficulty: this.diff, failReason: this.failReason,
      note: this.note, events: this.events, presses: this.presses, quote: this.quote,
      system: this.app.settings.wpm_system, classic, active,
      activeSecs: this.activeSeconds(elapsed), counted,
      replay: new Replay(this.words, this.recorder.frames, this.tape()),
      words: this.words.length, learnReport: this.learning ? this.app.learn.report() : null,
    };
    result.pbBefore = this.app.history.pb(result);
    if (counted) {
      result.newPb = this.app.history.add(result);
      this.app.save?.();
    }
    return result;
  }
}

/** No target text: whatever you type is the text. Enter finishes. */
export class ZenTest extends TypingTest {
  makeWords() { return [""]; }
  expected() { return null; }
  finished() { return this.done; }
  checkRules() {}
  canBackspace() { return true; }

  backspace() {
    if (this.typed[this.wi]) this.typed[this.wi] = this.words[this.wi] = this.typed[this.wi].slice(0, -1);
    else if (this.wi > 0) {
      this.words.pop();
      this.typed.pop();
      this.wi--;
    }
  }

  wipeWord() {
    if (this.typed[this.wi]) this.typed[this.wi] = this.words[this.wi] = "";
    else this.backspace();
  }

  space(el) {
    if (!this.typed[this.wi]) return;
    this.press(el, true);
    this.hit();
    this.wi++;
    this.words.push("");
    this.typed.push("");
  }

  char(ch, el) {
    this.press(el, true);
    this.due(ch);
    this.hit();
    this.typed[this.wi] += ch;
    this.words[this.wi] = this.typed[this.wi];
  }
}

export function newTest(app, spec) {
  return spec.kind === "zen" ? new ZenTest(app, spec) : new TypingTest(app, spec);
}

export function slowWords(app, n, rng = Math.random) {
  const pool = app.stats.slowest(SLOW_WORDS);
  if (!pool.length) return app.generator.make(n);
  return Array.from({ length: n }, () => pick(pool, rng));
}

/** % of keystrokes that typed what the text wanted; 100 with none to judge. */
export function keystrokeAccuracy(events) {
  const judged = events.filter((e) => e.expected !== null && e.expected !== undefined && e.typed);
  if (!judged.length) return 100;
  return (100 * judged.filter((e) => e.typed === e.expected).length) / judged.length;
}

export { History, ORDER };
