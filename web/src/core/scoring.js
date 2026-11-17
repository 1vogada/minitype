// Speed and accuracy (engine/scoring.py and engine/speed.py).

/** The letters typed right, and a space for each word finished cleanly. */
export function correctChars(words, typed, wi) {
  let chars = 0;
  for (let i = 0; i < Math.min(wi, words.length); i++) if (typed[i] === words[i]) chars++;
  for (let i = 0; i < Math.min(wi + 1, words.length); i++) {
    const w = words[i], t = typed[i] ?? "";
    for (let j = 0; j < t.length; j++) if (j < w.length && t[j] === w[j]) chars++;
  }
  return chars;
}

/** [wpm, raw wpm, accuracy %] - classic: over the whole clock. */
export function score(words, typed, wi, keys, badKeys, elapsed) {
  const chars = correctChars(words, typed, wi);
  const mins = elapsed / 60;
  const wpm = mins ? chars / 5 / mins : 0;
  const raw = mins ? keys / 5 / mins : 0;
  const acc = keys ? (100 * (keys - badKeys)) / keys : 0;
  return [wpm, raw, acc];
}

/** The test cut into `buckets` slices: [wpm, errors] for each. */
export function speedSeries(events, elapsed, buckets) {
  if (elapsed <= 0 || buckets <= 0) return [];
  const size = elapsed / buckets;
  const ok = new Array(buckets).fill(0), bad = new Array(buckets).fill(0);
  for (const [t, good] of events) {
    const b = Math.min(buckets - 1, Math.floor(t / size));
    if (good) ok[b]++; else bad[b]++;
  }
  return ok.map((n, i) => [n / 5 / (size / 60), bad[i]]);
}

// ---- active wpm: words a minute over the time you were actually typing

export const IDLE_MIN = 1.0;   // seconds: a gap below this always counts in full
export const IDLE_MAX = 3.0;   // ...and no gap counts for more than this
export const IDLE_MULT = 4.0;  // the cap, in your own typical gaps
export const TYPICAL = 0.25;   // a typical gap before there are any to go by

export function gaps(times, end) {
  const out = [];
  for (let i = 1; i < times.length; i++) out.push(times[i] - times[i - 1]);
  if (times.length) out.push(Math.max(0, end - times[times.length - 1]));
  return out;
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

export function typical(between) {
  const seen = between.filter((g) => g > 0);
  return seen.length ? Math.max(median(seen), 0.05) : TYPICAL;
}

export function cap(typ) {
  return Math.min(Math.max(IDLE_MULT * typ, IDLE_MIN), IDLE_MAX);
}

/** Seconds of typing in a test whose presses came at `times` up to `end`. */
export function activeSeconds(times, end) {
  if (!times.length) return 0;
  const g = gaps(times, end);
  const typ = typical(g.slice(0, -1));
  const top = cap(typ);
  return g.reduce((sum, gap) => sum + Math.min(gap, top), 0);
}

/** [wpm, raw] for correct letters and all presses over secs. */
export function wpmOver(chars, keys, secs) {
  const mins = secs / 60;
  return mins ? [chars / 5 / mins, keys / 5 / mins] : [0, 0];
}
