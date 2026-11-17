// Best words (words/best_words.py): a test made only of the words you type
// fastest and cleanest, to push your top speed. Its runs are their own mode,
// kept out of the normal stats, word timings, bad keys and keyboard learn.

export const SOURCE = "best";
export const LABEL = "best words";
export const TAG = "best";
export const MIN_TYPED = 5;        // finishes before word_clean is trusted over the estimate
export const MIN_CLEAN = 0.9;      // measured share with no wrong key
export const DROP = 0.4;           // estimated: the least clean 40% are out
export const MIN_KEY_PRESSES = 30; // a key's error rate counts once it has this many presses
export const MIN_TIMED = 3;        // times it was timed (typed correctly)
export const MIN_POOL = 20;
export const MAX_POOL = 150;
export const BIAS = 2;             // how strongly faster words are drawn more often

function keyErrors(keys) {
  const out = {};
  for (const [c, v] of Object.entries(keys ?? {})) {
    if (Array.isArray(v) && v.length >= 3 && v[1] >= MIN_KEY_PRESSES) out[c] = v[2] / v[1];
  }
  return out;
}

function estimate(word, err) {
  let p = 1;
  for (const c of word) p *= 1 - (err[c] ?? 0);
  return p;
}

/** [[ms per char, word]] for the words fast and clean enough, fastest first. */
export function eligible(stats, keys = null) {
  const err = keyErrors(keys);
  const hasErr = Object.keys(err).length > 0;
  const measured = [];
  let guessed = [];
  for (const [w, speed] of Object.entries(stats.wordSpeed)) {
    if (!speed || speed[1] < MIN_TIMED) continue;
    const [clean, typed] = stats.wordClean[w] ?? [0, 0];
    if (typed >= MIN_TYPED) {
      if (clean >= MIN_CLEAN * typed) measured.push([speed[0], w]);
    } else {
      guessed.push([speed[0], w, estimate(w, err)]);
    }
  }
  if (guessed.length && hasErr) {
    const cut = guessed.map((g) => g[2]).sort((a, b) => a - b)[Math.floor(guessed.length * DROP)];
    guessed = guessed.filter((g) => g[2] >= cut);
  }
  return measured.concat(guessed.map(([ms, w]) => [ms, w]))
    .sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
}

export function pool(stats, keys = null) {
  const best = eligible(stats, keys).slice(0, MAX_POOL).map(([, w]) => w);
  return best.length >= MIN_POOL ? best : [];
}

export function progress(stats, keys = null) {
  return [Math.min(eligible(stats, keys).length, MAX_POOL), MIN_POOL];
}

function choose(items, weights, rng) {
  const total = weights.reduce((a, b) => a + b, 0);
  let x = rng() * total;
  for (let i = 0; i < items.length; i++) {
    x -= weights[i];
    if (x < 0) return items[i];
  }
  return items[items.length - 1];
}

/** n words from the pool, faster ones more often, no word twice in a row. */
export function words(stats, n, rng = Math.random, keys = null) {
  const p = pool(stats, keys);
  if (!p.length) return [];
  const slowest = stats.wordSpeed[p[p.length - 1]][0];
  const weight = p.map((w) => (slowest / Math.max(stats.wordSpeed[w][0], 1)) ** BIAS);
  const out = [];
  for (let i = 0; i < n; i++) {
    let w = choose(p, weight, rng);
    while (out.length && w === out[out.length - 1] && p.length > 1) w = choose(p, weight, rng);
    out.push(w);
  }
  return out;
}

export const isBest = (run) => run.tag === TAG;

/** [tests, average speed, average accuracy, top speed] of completed best-words runs, or null. */
export function summary(history) {
  const runs = history.runs.filter((r) => isBest(r) && !r.failed);
  if (!runs.length) return null;
  const sp = runs.map((r) => history.speed(r));
  return [runs.length, sp.reduce((a, b) => a + b, 0) / sp.length,
    runs.reduce((a, r) => a + r.acc, 0) / runs.length, Math.max(...sp)];
}
