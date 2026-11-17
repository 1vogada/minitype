// Where the words come from: the word bank (words/bank.py), the generator
// with its bias settings (words/generator.py) and the funbox (words/funbox.py).
// The data (built-in list, themed lists) is handed in, so this runs in node too.

export const MONKEYTYPE = "https://raw.githubusercontent.com/monkeytypegame/monkeytype/master/frontend/static/";
const MT = MONKEYTYPE + "languages/";

export const SOURCES = {
  "built-in": null,
  "online 200": MT + "english.json",
  "online 1k": MT + "english_1k.json",
  "online 5k": MT + "english_5k.json",
  "online 10k": MT + "english_10k.json",
  "online 25k": MT + "english_25k.json",
  "online 450k": MT + "english_450k.json",
  "double letters": MT + "english_doubleletter.json",
  "misspelled": MT + "english_commonly_misspelled.json",
  "programming": "themed",
  "left hand": "themed",
  "right hand": "themed",
  "right heavy": "themed",
  "home row": "themed",
};
export const MIN_THEMED = 10;

/** A random index / choice helpers on an injectable rng. */
export const pick = (xs, rng = Math.random) => xs[Math.floor(rng() * xs.length)];
export const randint = (a, b, rng = Math.random) => a + Math.floor(rng() * (b - a + 1));
export function choices(items, weights, rng = Math.random) {
  const total = weights.reduce((a, b) => a + b, 0);
  let x = rng() * total;
  for (let i = 0; i < items.length; i++) {
    x -= weights[i];
    if (x < 0) return items[i];
  }
  return items[items.length - 1];
}

/** The active word list. `version` bumps on every load, for caches. */
export class WordBank {
  constructor(builtin, themed = {}, fetchJson = null) {
    this.builtin = builtin;
    this.themed = themed;          // name -> layout -> words
    this.fetchJson = fetchJson;    // url -> Promise<json>
    this.words = [...builtin];
    this.source = "built-in";
    this.note = "";
    this.version = 0;
    this.cache = {};
  }

  useBuiltin(note) {
    this.words = [...this.builtin];
    this.source = "built-in";
    this.note = note;
  }

  /** Swap in a word list; falls back to built-in with a note. Resolves true if it worked. */
  async load(name, layout = "qwerty") {
    this.version++;
    const url = SOURCES[name];
    if (!(name in SOURCES) || url === null) {
      this.useBuiltin(`${this.builtin.length} words, built-in`);
      return name === "built-in";
    }
    if (url === "themed") {
      const lists = this.themed[name] ?? {};
      const words = lists[layout] ?? lists.qwerty ?? [];
      const on = name === "programming" ? "" : ` on ${layout}`;
      if (words.length < MIN_THEMED) {
        this.useBuiltin(`only ${words.length} ${name} words${on} - using built-in`);
        return false;
      }
      this.words = words;
      this.source = name;
      this.note = `${words.length} words, ${name}${on}`;
      return true;
    }
    try {
      if (!this.cache[url]) {
        const data = await this.fetchJson(url);
        const words = (data?.words ?? []).filter((w) => w && !w.includes(" "));
        if (words.length < 50) throw new Error("list too short");
        this.cache[url] = words;
      }
      this.words = this.cache[url];
      this.source = name;
      this.note = `${this.words.length} words, ${name}`;
      this.version++;
      return true;
    } catch (e) {
      this.useBuiltin(`${name} failed (${e?.name ?? "error"}) - using built-in`);
      return false;
    }
  }
}

// ---- the generator

export const SHORT = 4, MEDIUM = 7;
export const BANDS = ["short", "medium", "long"];
export const NATURAL = { short: 45, medium: 45, long: 10 };
const WANTED = { short: ["short"], "short + medium": ["short", "medium"], medium: ["medium"], long: ["long"] };
export const MIN_LENGTH_WORDS = 20;

export const band = (w) => (w.length <= SHORT ? "short" : w.length <= MEDIUM ? "medium" : "long");

export class WordGenerator {
  constructor(settings, stats, bank, rng = Math.random) {
    this.settings = settings;
    this.stats = stats;
    this.bank = bank;
    this.rng = rng;
    this._poolKey = null;
    this._pool = [];
    this._bandsKey = null;
    this._bands = null;
  }

  bands() {
    if (this._bandsKey !== this.bank.version || !this._bands) {
      const out = { short: [], medium: [], long: [] };
      for (const w of this.bank.words) out[band(w)].push(w);
      this._bandsKey = this.bank.version;
      this._bands = out;
    }
    return this._bands;
  }

  lengths() {
    const want = WANTED[this.settings.word_length];
    if (!want) return null;
    const b = this.bands();
    return want.reduce((n, k) => n + b[k].length, 0) >= MIN_LENGTH_WORDS ? want : null;
  }

  plain() {
    const words = this.bank.words;
    if (this.settings.word_length === "as listed" || !words.length) return pick(words, this.rng);
    const b = this.bands();
    let want = this.lengths();
    if (want === null) {
      if (b.long.length * 100 <= NATURAL.long * words.length) return pick(words, this.rng);
      want = BANDS;
    }
    want = want.filter((k) => b[k].length);
    return pick(b[choices(want, want.map((k) => NATURAL[k]), this.rng)], this.rng);
  }

  badPool() {
    const keys = new Set(this.stats.badKeys());
    const want = this.lengths();
    const key = `${this.bank.version}|${[...keys].sort().join("")}|${want}`;
    if (key === this._poolKey) return this._pool;
    let pool = [];
    for (const w of this.bank.words) {
      const hits = [...new Set(w)].filter((c) => keys.has(c)).length;
      for (let i = 0; i < Math.min(hits, 3); i++) pool.push(w);
    }
    if (want) {
      const fit = pool.filter((w) => want.includes(band(w)));
      if (fit.length) pool = fit;
    }
    this._poolKey = key;
    this._pool = pool;
    return pool;
  }

  missedPool() {
    const pool = [];
    for (const [w, n] of Object.entries(this.stats.missed)) for (let i = 0; i < Math.min(n, 3); i++) pool.push(w);
    return pool;
  }

  pickWord() {
    const s = this.settings;
    if (s.bad_words && this.rng() * 100 < s.bad_words_pct) {
      const pool = this.missedPool();
      if (pool.length) return pick(pool, this.rng);
    }
    if (s.weak && this.rng() * 100 < s.weak_pct) {
      const pool = this.badPool();
      if (pool.length) return pick(pool, this.rng);
    }
    return this.plain();
  }

  make(count, source = "words") {
    if (source === "numbers") {
      return Array.from({ length: count }, () => String(randint(0, 10 ** randint(1, 5, this.rng), this.rng)));
    }
    const out = [];
    for (let i = 0; i < count; i++) {
      if (this.settings.numbers && this.rng() < 0.05) out.push(String(randint(0, 9999, this.rng)));
      else out.push(this.pickWord());
    }
    return out;
  }
}

// ---- funbox: modifiers that change the words (mirror and the hackers don't)

export function funbox(words, mode, rng = Math.random) {
  if (mode === "reversed") return words.map((w) => [...w].reverse().join(""));
  if (mode === "caps") return words.map((w) => w.toUpperCase());
  if (mode === "random case") {
    return words.map((w) => [...w].map((c) => (rng() < 0.5 ? c.toUpperCase() : c.toLowerCase())).join(""));
  }
  return [...words];
}

// ---- quotes and code

export const QUOTE_SHORT = 100, QUOTE_MEDIUM = 300;
export const quoteBucket = (text) => (text.length <= QUOTE_SHORT ? "short" : text.length <= QUOTE_MEDIUM ? "medium" : "long");

export class QuoteBank {
  constructor(builtin, fetchJson = null) {
    this.builtin = builtin;        // [{text, source, genres}]
    this.fetchJson = fetchJson;
    this.online = null;
    this.note = "";
  }

  async loadOnline() {
    if (this.online !== null || !this.fetchJson) return;
    try {
      const data = await this.fetchJson(MONKEYTYPE + "quotes/english.json");
      this.online = (data?.quotes ?? []).filter((q) => q.text).map((q) => ({ text: q.text, source: q.source ?? "", genres: [] }));
      this.note = `${this.online.length} online quotes`;
    } catch (e) {
      this.online = [];
      this.note = `online quotes failed (${e?.name ?? "error"})`;
    }
  }

  pool(source) {
    return source === "online" && this.online?.length ? this.online : this.builtin;
  }

  /** {text, source} of the wanted length and genre, or any if none match. */
  pick(length = "all", source = "built-in", genre = "all", rng = Math.random) {
    const pool = this.pool(source);
    const byGenre = genre !== "all" ? pool.filter((q) => q.genres.includes(genre)) : pool;
    const active = byGenre.length ? byGenre : pool;
    const fits = active.filter((q) => length === "all" || quoteBucket(q.text) === length);
    return pick(fits.length ? fits : active, rng);
  }
}
