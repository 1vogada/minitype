// Shared by the tests: an App on the real data, a fixed clock and a seeded rng.

import { readFileSync } from "node:fs";
import { App, memoryStore } from "../src/core/app.js";

const dataDir = new URL("../src/data/", import.meta.url);
const read = (name) => JSON.parse(readFileSync(new URL(name, dataDir), "utf8"));

export const DATA = {
  words: read("words.json"),
  quotes: read("quotes.json"),
  code: read("code.json"),
  themed: read("themed.json"),
  themes: read("themes.json"),
};

export function seeded(seed = 1) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeApp(opts = {}) {
  const clock = { t: 1_800_000_000 };
  const app = new App({
    data: DATA, store: opts.store ?? memoryStore(), now: () => clock.t, rng: seeded(opts.seed ?? 7),
    fetchImpl: opts.fetchImpl ?? (async () => { throw new TypeError("offline"); }), proxy: null,
  });
  app.clock = clock;
  if (opts.settings) Object.assign(app.settings, opts.settings);
  return app;
}

/** Type `text` into a test, one key every `gap` seconds from `start`. */
export function typeText(test, text, start, gap = 0.2) {
  let t = start;
  for (const ch of text) {
    test.handle(ch, t);
    test.recorder.snap(test, t);
    t += gap;
  }
  return t;
}
