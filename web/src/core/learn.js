// Learn mode (learn/progress.py and learn/wordgen.py): keybr-style lessons
// that unlock letters as every key in play reaches the target speed.

import { ORDER } from "./config.js";
import { choices, pick } from "./words.js";

export const TARGETS = [20, 25, 30, 35, 40, 50, 60, 80];
export const LENGTHS = [10, 15, 20, 30, 50];
export const START_LETTERS = 6;
export const CAL_SAMPLES = 5;
export const SMOOTH = 0.15;
export const MISS_FACTOR = 2.5;

export class LearnProgress {
  constructor() {
    this.config = { target: 35, letters: 6, words: 15, natural: true, capitals: false, punctuation: false, earned: 0 };
    this.stats = {};   // char -> [smoothed ms per press, presses, misses]
    this.note = "";
  }

  targetMs() { return 12000 / this.config.target; }

  hit(c, ms) {
    if (!ORDER.includes(c)) return;
    const s = (this.stats[c] ??= [0, 0, 0]);
    if (ms === null) {
      s[2]++;
      ms = this.targetMs() * MISS_FACTOR;
    }
    s[0] = s[1] === 0 ? ms : s[0] + SMOOTH * (ms - s[0]);
    s[1]++;
  }

  conf(c) {
    const s = this.stats[c];
    if (!s || s[1] < CAL_SAMPLES) return null;
    return Math.min(1, this.targetMs() / s[0]);
  }

  confident(c) {
    const v = this.conf(c);
    return v !== null && v >= 1;
  }

  unlocked() {
    let n = Math.max(START_LETTERS, this.config.earned);
    while (n < ORDER.length && [...ORDER.slice(0, n)].every((c) => this.confident(c))) n++;
    this.config.earned = n;
    return Math.max(this.config.letters, n);
  }

  focusKey() {
    const inc = ORDER.slice(0, this.unlocked());
    let bi = 0, best = null;
    for (let i = 0; i < inc.length; i++) {
      const v = this.conf(inc[i]);
      const rank = [v === null ? -1 : v, -i];
      if (best === null || rank[0] < best[0] || (rank[0] === best[0] && rank[1] < best[1])) {
        best = rank;
        bi = i;
      }
    }
    const v = this.conf(inc[bi]);
    return v !== null && v >= 1 ? null : inc[bi];
  }

  finish(nBefore) {
    const n = this.unlocked();
    this.note = n > nBefore ? ORDER.slice(nBefore, n) : "";
  }

  report() {
    const n = this.unlocked();
    const foc = this.focusKey();
    const lines = [`${n}/${ORDER.length} letters   target ${this.config.target} wpm`];
    if (this.note) lines.push("unlocked " + [...this.note].join(" "));
    if (foc) {
      const v = this.conf(foc);
      lines.push(`focus ${foc}   ` + (v === null ? "not enough presses yet" : `${Math.round(v * 100)}% of target`));
    } else lines.push("every key at target");
    return lines;
  }

  addLetters(delta) {
    this.config.letters = Math.max(START_LETTERS, Math.min(ORDER.length, this.config.letters + delta));
  }

  reset() {
    this.stats = {};
    this.config.earned = 0;
  }

  apply(d) {
    try {
      for (const [k, v] of Object.entries(d?.learn ?? {})) {
        if (k in this.config && typeof v === typeof this.config[k]) this.config[k] = v;
      }
      this.stats = {};
      for (const [c, v] of Object.entries(d?.stats ?? {})) {
        if (ORDER.includes(c) && Array.isArray(v) && v.length === 3) this.stats[c] = [+v[0], v[1] | 0, v[2] | 0];
      }
    } catch {
      // a bad save: what got in stays
    }
  }
}

// ---- lesson words

let modelCache = [null, null];

function bump(table, key, c) {
  const d = (table[key] ??= {});
  d[c] = (d[c] ?? 0) + 1;
}

function model(bank) {
  if (modelCache[0] === bank.version && modelCache[1]) return modelCache[1];
  const m2 = {}, m1 = {};
  for (const w of bank.words) {
    if (!/^[a-z]+$/.test(w)) continue;
    const s = "^^" + w + "$";
    for (let i = 2; i < s.length; i++) {
      bump(m2, s.slice(i - 2, i), s[i]);
      bump(m1, s[i - 1], s[i]);
    }
  }
  modelCache = [bank.version, [m2, m1]];
  return modelCache[1];
}

/** A made-up word from the allowed letters holding the focus key. */
export function pseudoWord(bank, allowed, focus, rng = Math.random) {
  const [m2, m1] = model(bank);
  const good = [];
  for (let k = 0; k < 40; k++) {
    let out = "", back = 0;
    while (out.length < 7) {
      const ctx = ("^^" + out).slice(-2);
      let opts = null;
      const levels = [[m2, ctx], [m1, ctx.slice(-1)]];
      for (let lvl = 0; lvl < levels.length; lvl++) {
        const [table, key] = levels[lvl];
        const cand = {};
        for (const [c, n] of Object.entries(table[key] ?? {})) {
          if (allowed.has(c) || (c === "$" && out.length >= 3)) {
            cand[c] = c === "$" ? n * (1 + Math.max(0, out.length - 3)) : n;
          }
        }
        if (Object.keys(cand).length) {
          opts = cand;
          back += lvl;
          break;
        }
      }
      if (!opts) break;
      const c = choices(Object.keys(opts), Object.values(opts), rng);
      if (c === "$") break;
      out += c;
    }
    if (out.length >= 3 && out.length <= 7 && (focus === null || out.includes(focus))) good.push([back, rng(), out]);
  }
  if (good.length) {
    good.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    return good[0][2];
  }
  const letters = [...allowed].sort();
  let w = Array.from({ length: 4 }, () => pick(letters, rng)).join("");
  if (focus && !w.includes(focus)) {
    const i = Math.floor(rng() * w.length);
    w = w.slice(0, i) + focus + w.slice(i + 1);
  }
  return w;
}

export function naturalPool(bank, allowed, focus) {
  return bank.words.filter((w) => w.length >= 3 && [...w].every((c) => allowed.has(c)) && (focus === null || w.includes(focus)));
}

const LESSON_PUNCT = ",,,..;:!?";

export function decorate(words, capitals, punctuation, rng = Math.random) {
  return words.map((w) => {
    if (capitals && rng() < 0.25) w = w[0].toUpperCase() + w.slice(1);
    if (punctuation && rng() < 0.2) w += pick(LESSON_PUNCT, rng);
    return w;
  });
}

export function lessonWords(progress, bank, n, rng = Math.random) {
  const cfg = progress.config;
  const allowed = new Set(ORDER.slice(0, progress.unlocked()));
  const foc = progress.focusKey();
  const nat = cfg.natural ? naturalPool(bank, allowed, foc) : [];
  const p = Math.min(1, nat.length / 20);
  const out = [];
  for (let i = 0; i < n; i++) {
    let w;
    for (let t = 0; t < 6; t++) {
      w = nat.length && rng() < p ? pick(nat, rng) : pseudoWord(bank, allowed, foc, rng);
      if (!out.length || w !== out[out.length - 1]) break;
    }
    out.push(w);
  }
  return decorate(out, cfg.capitals, cfg.punctuation, rng);
}
