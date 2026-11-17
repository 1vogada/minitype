// Everything remembered about your typing (stats.py).

import { BAD_KEYS_TRACKED, KEYS, KEY_STATES } from "./config.js";

const PUNCT_STRIP = ".,;:!?'\"()";
export const WORD_SMOOTH = 0.4;   // weight of the newest timing of a word
export const MAX_WORDS = 1500;    // word timings kept

function strip(w, chars) {
  let a = 0, b = w.length;
  while (a < b && chars.includes(w[a])) a++;
  while (b > a && chars.includes(w[b - 1])) b--;
  return w.slice(a, b);
}

function isAlpha(w) {
  return /^\p{L}+$/u.test(w);
}

/** Forget the least seen entries of a {word: [x, times]} map past `max`. */
function trim(map, max, timesIndex) {
  const keys = Object.keys(map);
  if (keys.length <= max) return;
  keys.sort((a, b) => map[a][timesIndex] - map[b][timesIndex])
    .slice(0, keys.length - max).forEach((k) => delete map[k]);
}

export class SessionStats {
  constructor() {
    this.errors = {};      // char -> times missed, drives weak-key bias
    this.missed = {};      // word -> times you submitted it wrong
    this.keyState = {};    // char -> "on" / "off"; absent means auto
    this.history = [];     // wpm of runs completed this session
    this.ghost = [];       // [elapsed, chars] samples from the last completed run
    this.wordSpeed = {};   // word -> [smoothed ms per char, times typed]
    this.wordClean = {};   // word -> [times finished with no wrong key, times finished]
  }

  missKey(c) { this.errors[c] = (this.errors[c] ?? 0) + 1; }
  missWord(w) { this.missed[w] = (this.missed[w] ?? 0) + 1; }

  /** A word as it's stored: bare and lowercase; null if too short or not letters. */
  static bare(word) {
    const w = strip(word, PUNCT_STRIP).toLowerCase();
    return w.length >= 2 && isAlpha(w) ? w : null;
  }

  wordDone(word, clean) {
    const w = SessionStats.bare(word);
    if (w === null) return;
    const c = (this.wordClean[w] ??= [0, 0]);
    c[0] += clean ? 1 : 0;
    c[1] += 1;
    trim(this.wordClean, MAX_WORDS, 1);
  }

  wordTime(word, msPerChar) {
    const w = SessionStats.bare(word);
    if (w === null) return;
    const s = this.wordSpeed[w];
    if (!s) this.wordSpeed[w] = [msPerChar, 1];
    else {
      s[0] += WORD_SMOOTH * (msPerChar - s[0]);
      s[1] += 1;
    }
    trim(this.wordSpeed, MAX_WORDS, 1);
  }

  slowest(n) {
    return Object.entries(this.wordSpeed).sort((a, b) => b[1][0] - a[1][0])
      .slice(0, n).map(([w]) => w);
  }

  resetErrors() { this.errors = {}; this.missed = {}; }

  best() { return this.history.length ? Math.max(...this.history) : null; }

  autoKeys() {
    return Object.entries(this.errors)
      .filter(([c]) => /^[\p{L}\p{N}]$/u.test(c) && (this.keyState[c] ?? "auto") === "auto")
      .sort((a, b) => b[1] - a[1]).slice(0, BAD_KEYS_TRACKED).map(([c]) => c);
  }

  badKeys() {
    const pinned = [...KEYS].filter((c) => this.keyState[c] === "on");
    return pinned.concat(this.autoKeys().filter((c) => !pinned.includes(c)));
  }

  cycleKey(c) {
    const st = this.keyState[c] ?? "auto";
    const nxt = KEY_STATES[(KEY_STATES.indexOf(st) + 1) % KEY_STATES.length];
    if (nxt === "auto") delete this.keyState[c]; else this.keyState[c] = nxt;
  }

  ghostChars(elapsed) {
    let n = 0;
    for (const [t, c] of this.ghost) {
      if (t > elapsed) break;
      n = c;
    }
    return n;
  }
}
