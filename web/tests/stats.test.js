// Best words, history and personal bests, learn, the generator, the save.

import { test } from "node:test";
import assert from "node:assert/strict";
import * as bestWords from "../src/core/bestWords.js";
import { History } from "../src/core/history.js";
import { SessionStats } from "../src/core/stats.js";
import { LearnProgress, lessonWords } from "../src/core/learn.js";
import { ORDER } from "../src/core/config.js";
import { Settings } from "../src/core/settings.js";
import { TypingTest, makeSpec } from "../src/core/test.js";
import { SAVE_KEY, SETTINGS_KEY, memoryStore } from "../src/core/app.js";
import { band } from "../src/core/words.js";
import { makeApp, seeded, typeText } from "./helpers.js";

function statsWith(n, { clean = true, typed = 5 } = {}) {
  const s = new SessionStats();
  for (let i = 0; i < n; i++) {
    const w = "w" + String.fromCharCode(97 + (i % 26)) + String.fromCharCode(97 + Math.floor(i / 26));
    s.wordSpeed[w] = [100 + i, 4];
    s.wordClean[w] = [clean ? typed : 0, typed];
  }
  return s;
}

test("best words: no pool under MIN_POOL, then the fastest first", () => {
  assert.deepEqual(bestWords.pool(statsWith(10)), []);
  assert.deepEqual(bestWords.progress(statsWith(10)), [10, 20]);
  const s = statsWith(30);
  const p = bestWords.pool(s);
  assert.equal(p.length, 30);
  assert.equal(p[0], "waa");
  assert.ok(s.wordSpeed[p[0]][0] <= s.wordSpeed[p[29]][0]);
});

test("best words: unclean words and rarely timed words are out", () => {
  const s = statsWith(25);
  s.wordClean.waa = [3, 5];              // 60% clean: out
  s.wordSpeed.wba[1] = 2;                // timed twice: out
  const p = bestWords.pool(s);
  assert.ok(!p.includes("waa"));
  assert.ok(!p.includes("wba"));
  assert.equal(p.length, 23);
});

test("best words: an estimate from key errors drops the least clean 40%", () => {
  const s = new SessionStats();
  for (let i = 0; i < 30; i++) s.wordSpeed["q" + "abcdefghijklmnopqrstuvwxyz"[i % 26] + i] = [100, 3];
  const keys = { q: [100, 100, 0], a: [100, 100, 50] };
  const all = bestWords.eligible(s, keys);
  assert.ok(all.length < 30);
});

test("best words: draws favour fast words, never the same twice in a row", () => {
  const s = statsWith(40);
  const w = bestWords.words(s, 300, seeded(3));
  assert.equal(w.length, 300);
  for (let i = 1; i < w.length; i++) assert.notEqual(w[i], w[i - 1]);
  const fast = w.filter((x) => s.wordSpeed[x][0] < 110).length;
  const slow = w.filter((x) => s.wordSpeed[x][0] >= 130).length;
  assert.ok(fast > slow / 2);
});

test("best words runs: their own mode, kept out of the word stats", () => {
  const app = makeApp();
  Object.assign(app.stats, statsWith(30));
  const before = JSON.stringify(app.stats.wordSpeed);
  const t = new TypingTest(app, makeSpec(bestWords.LABEL, "words", 5, bestWords.SOURCE));
  assert.ok(t.words.every((w) => app.stats.wordSpeed[w]));
  typeText(t, t.words.join(" "), 0, 0.1);
  const r = t.result(100);
  assert.equal(JSON.stringify(app.stats.wordSpeed), before);
  assert.equal(app.history.runs[0].tag, "best");
  assert.equal(app.history.runs[0].mode, "best words");
  assert.equal(app.history.normal().length, 0);
  assert.ok(bestWords.summary(app.history)[0] === 1);
  assert.ok(r.wpm > 0);
  assert.deepEqual(app.stats.history, [], "not in the session's normal speeds");
});

test("history: personal bests per mode and per wpm system", () => {
  const h = new History();
  h.clock = () => 1_800_000_000;
  const res = (wpm, extra = {}) => ({ spec: { label: "25 words", source: "words" }, wpm, classic: wpm, active: wpm + 5, acc: 97, elapsed: 20, failed: false, difficulty: "normal", ...extra });
  assert.equal(h.add(res(50)), true);
  assert.equal(h.add(res(40)), false);
  assert.equal(h.pbs["25 words"].wpm, 50);
  assert.equal(h.pbs["25 words"].awpm, 55);
  assert.equal(h.add(res(60, { difficulty: "expert" })), true);
  assert.ok("25 words (expert)" in h.pbs);
  assert.equal(h.add(res(90, { failed: true })), false);
  assert.equal(h.pbs["25 words"].wpm, 50);
  h.system = () => "active";
  assert.equal(h.pb(res(1)), 55);
});

test("history: streaks over local days", () => {
  const h = new History();
  const day = (y, m, d) => new Date(y, m - 1, d, 12).getTime() / 1000;
  h.runs = [day(2026, 3, 1), day(2026, 3, 2), day(2026, 3, 3), day(2026, 3, 10)].map((t) => ({ t, mode: "x", wpm: 1, acc: 1, secs: 60, failed: false }));
  assert.deepEqual(h.streak("2026-03-11"), [1, 3]);
  assert.deepEqual(h.streak("2026-03-13"), [0, 3]);
});

test("history merge: no run twice, the better best kept", () => {
  const h = new History();
  h.runs = [{ t: 1, mode: "a", wpm: 10, acc: 90, secs: 5, failed: false }];
  h.pbs = { a: { wpm: 10, acc: 90, t: 1 } };
  h.merge([{ t: 1, mode: "a", wpm: 10, acc: 90, secs: 5, failed: false }, { t: 2, mode: "a", wpm: 30, acc: 95, secs: 5, failed: false }],
    { a: { wpm: 30, acc: 95, t: 2 }, b: { wpm: 5, acc: 50, t: 2 } });
  assert.equal(h.runs.length, 2);
  assert.equal(h.pbs.a.wpm, 30);
  assert.equal(h.pbs.b.wpm, 5);
});

test("learn: letters unlock once every key is at target", () => {
  const l = new LearnProgress();
  assert.equal(l.unlocked(), 6);
  for (const c of ORDER.slice(0, 6)) for (let i = 0; i < 6; i++) l.hit(c, 200);
  assert.equal(l.unlocked(), 7);
  assert.equal(l.focusKey(), ORDER[6]);
  l.hit("e", null);
  assert.equal(l.stats.e[2], 1);
  const words = lessonWords(l, { words: ["tear", "rate", "neat", "train", "eat"], version: 1 }, 10, seeded(1));
  assert.equal(words.length, 10);
  const allowed = new Set(ORDER.slice(0, 7));
  assert.ok(words.every((w) => [...w].every((c) => allowed.has(c))), words.join(" "));
});

test("generator: word length bands and bad keys", () => {
  const app = makeApp({ settings: { word_length: "short" } });
  const w = app.generator.make(200);
  assert.ok(w.every((x) => band(x) === "short"));
  app.settings.word_length = "any";
  app.stats.errors = { z: 50 };
  app.settings.weak = true;
  app.settings.weak_pct = 100;
  assert.ok(app.generator.make(50).every((x) => x.includes("z")));
  assert.ok(app.generator.make(30, "numbers").every((x) => /^\d+$/.test(x)));
});

test("settings: python settings.json applies, bad values skipped, extras kept", () => {
  const s = new Settings();
  s.apply({ theme: "summit", caret: "block", difficulty: "nope", time_amount: 45, punctuation: true,
    art: "everywhere", fades: { a: 1 }, tape: true, min_wpm: 999 }, ["summit", "default"]);
  assert.equal(s.theme, "summit");
  assert.equal(s.caret, "block");
  assert.equal(s.difficulty, "normal");
  assert.equal(s.time_amount, 45);
  assert.equal(s.punctuation, "on");
  assert.equal(s.tape, "on");
  assert.equal(s.min_wpm, 0);
  const out = s.toDict();
  assert.equal(out.art, "everywhere", "art settings travel back out");
  assert.deepEqual(out.fades, { a: 1 });
});

test("app: save, load and import of minitype's save.json", () => {
  const store = memoryStore();
  const app = makeApp({ store });
  app.load();
  assert.equal(app.firstRun, true);
  const t = new TypingTest(app, makeSpec("custom 2 words", "words", 2, "custom", { words: ["ok", "go"] }));
  typeText(t, "ok go", 0);
  t.result(10);
  const saved = JSON.parse(store.get(SAVE_KEY));
  assert.equal(saved.history.length, 1);
  assert.ok(JSON.parse(store.get(SETTINGS_KEY)).theme);

  const app2 = makeApp({ store });
  app2.load();
  assert.equal(app2.firstRun, false);
  assert.equal(app2.history.runs.length, 1);
  const kind = app2.importJson({
    history: [{ t: 5, mode: "30 seconds", wpm: 80, awpm: 85, acc: 96, secs: 30, failed: false }],
    pbs: { "30 seconds": { wpm: 80, acc: 96, t: 5, awpm: 85 } },
    word_speed: { hello: [120.5, 7] }, word_clean: { hello: [6, 7] },
    learn: { target: 40 }, stats: { e: [200, 30, 2] },
  });
  assert.equal(kind, "save");
  assert.equal(app2.history.runs.length, 2);
  assert.equal(app2.history.pbs["30 seconds"].wpm, 80);
  assert.deepEqual(app2.stats.wordSpeed.hello, [120.5, 7]);
  assert.equal(app2.learn.config.target, 40);
  assert.equal(app2.importJson({ theme: "summit", key_state: { q: "on" } }), "settings");
  assert.equal(app2.settings.theme, "summit");
  assert.equal(app2.stats.keyState.q, "on");
  assert.equal(app2.importJson([1, 2]), null);
});
