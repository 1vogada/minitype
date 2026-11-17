// The test engine: word checking, wpm / accuracy, tab replays, the replay.

import { test } from "node:test";
import assert from "node:assert/strict";
import { KEY, MENU, REPLAY_BELOW, TypingTest, ZenTest, keystrokeAccuracy, makeSpec, newTest } from "../src/core/test.js";
import { activeSeconds, correctChars, score, speedSeries } from "../src/core/scoring.js";
import { makeApp, typeText } from "./helpers.js";

const words = (list, extra = {}) => makeSpec(`custom ${list.length} words`, "words", list.length, "custom", { words: list, ...extra });

test("correct chars count right letters and clean word spaces", () => {
  assert.equal(correctChars(["the", "cat"], ["the", "ca"], 1), 1 + 3 + 2);
  assert.equal(correctChars(["the", "cat"], ["thx", "c"], 1), 2 + 1);
});

test("score: 60 correct chars in 12 s is 60 wpm, accuracy from bad keys", () => {
  const w = ["aaaaa", "bbbbb", "ccccc", "ddddd", "eeeee", "fffff", "ggggg", "hhhhh", "iiiii", "jjjjj"];
  const [wpm, raw, acc] = score(w, w, 10, 60, 6, 12);
  assert.equal(wpm, 60 + 0 * raw);
  assert.equal(raw, 60);
  assert.equal(acc, 90);
});

test("typing a word test to the end finishes on its last letter", () => {
  const app = makeApp({ settings: { wpm_system: "classic" } });
  const t = new TypingTest(app, words(["hello", "world"]));
  typeText(t, "hello world", 100, 0.1);
  assert.equal(t.done, true);
  assert.equal(t.wi, 2);
  const r = t.result(200);
  assert.equal(r.acc, 100);
  assert.equal(r.errors, 0);
  // 12 chars (10 letters and a space for each finished word, as minitype counts) over 1.0 s
  assert.ok(Math.abs(r.elapsed - 1.0) < 1e-6);
  assert.ok(Math.abs(r.wpm - 12 / 5 / (1 / 60)) < 1e-6);
  assert.equal(app.history.runs.length, 1);
  assert.equal(app.history.runs[0].mode, "custom 2 words");
});

test("a wrong letter is a miss; backspace fixes it and it stays marked", () => {
  const app = makeApp();
  const t = new TypingTest(app, words(["cat", "dog"]));
  typeText(t, "cx", 10);
  assert.equal(t.typed[0], "cx");
  assert.equal(t.badKeys, 1);
  assert.equal(t.misses.a, 1);
  assert.equal(t.combo, 0);
  assert.ok(t.errMarks.has("0,1"));
  assert.equal(t.typoKeys["0,1"], "x");
  t.handle(KEY.BACKSPACE, 11);
  assert.equal(t.typed[0], "c");
  typeText(t, "at dog", 12);
  assert.equal(t.done, true);
  assert.equal(app.stats.errors.a, 1);
  assert.deepEqual(app.stats.wordClean.cat, [0, 1]);   // finished, but not clean
  assert.deepEqual(app.stats.wordClean.dog, [1, 1]);
});

test("a wrong word submitted with space counts once, backspace goes back into it", () => {
  const app = makeApp();
  const t = new TypingTest(app, words(["one", "two", "six"]));
  typeText(t, "onx ", 0);
  assert.equal(t.wi, 1);
  assert.equal(app.stats.missed.one, 1);
  t.handle(KEY.BACKSPACE, 2);
  assert.equal(t.wi, 0, "back into a wrong word");
  assert.equal(t.typed[0], "onx");
});

test("backspace doesn't go back into a correct word unless freedom", () => {
  const app = makeApp();
  const t = new TypingTest(app, words(["one", "two"]));
  typeText(t, "one ", 0);
  t.handle(KEY.BACKSPACE, 5);
  assert.equal(t.wi, 1);
  app.settings.backspace = "freedom";
  t.handle(KEY.BACKSPACE, 6);
  assert.equal(t.wi, 0);
});

test("stop on error letter: a wrong key never lands", () => {
  const app = makeApp({ settings: { stop_on_error: "letter" } });
  const t = new TypingTest(app, words(["cat"]));
  typeText(t, "cx", 0);
  assert.equal(t.typed[0], "c");
  assert.equal(t.wrong, true);
  typeText(t, "at", 1);
  assert.equal(t.done, true);
});

test("expert fails on a wrong word, master on a wrong key", () => {
  let app = makeApp({ settings: { difficulty: "expert" } });
  let t = new TypingTest(app, words(["cat", "dog"]));
  typeText(t, "cot ", 0);
  assert.equal(t.failed, true);
  assert.equal(t.failReason, "wrong word");
  app = makeApp({ settings: { difficulty: "master" } });
  t = new TypingTest(app, words(["cat", "dog"]));
  typeText(t, "cx", 0);
  assert.equal(t.failReason, "wrong key");
  const r = t.result(5);
  assert.equal(r.failed, true);
  assert.equal(app.history.runs[0].failed, true);
  assert.deepEqual(app.history.pbs, {});
});

test("punctuation forgive: left-out punctuation is typed for you", () => {
  const app = makeApp({ settings: { punctuation: "forgive" } });
  const t = new TypingTest(app, words(["hello,", "world."]));
  typeText(t, "hello world", 0);
  assert.equal(t.typed[0], "hello,");
  assert.equal(t.typed[1], "world.");
  assert.equal(t.badKeys, 0);
  assert.equal(t.done, true);
});

test("timed test ends at its time and tops up words", () => {
  const app = makeApp();
  const t = new TypingTest(app, makeSpec("15 seconds", "time", 15));
  assert.equal(t.words.length, 200);
  t.handle("x", 0);
  assert.equal(t.finished(14.9), false);
  assert.equal(t.finished(15), true);
  t.wi = 180;
  assert.equal(t.topUp(), true);
  assert.equal(t.words.length, 300);
  assert.equal(t.elapsed(40), 15);
});

test("min wpm fails after the grace time", () => {
  const app = makeApp({ settings: { min_wpm: 200 } });
  const t = new TypingTest(app, words(["slow", "words"]));
  t.handle("s", 0);
  t.checkRules(2);
  assert.equal(t.failed, false);
  t.checkRules(4);
  assert.equal(t.failed, true);
  assert.equal(t.failReason, "below 200 wpm");
});

test("tab replays: typed something -> same words; nothing typed -> new words", () => {
  const app = makeApp();
  const spec = makeSpec("10 words", "words", 10);
  const t = new TypingTest(app, spec);
  assert.deepEqual(t.handle(KEY.TAB, 0), spec, "nothing typed: the same spec, new words");
  t.handle(t.words[0][0], 1);
  const again = t.handle(KEY.TAB, 2);
  assert.deepEqual(again.replay, t.words);
  const t2 = new TypingTest(app, again);
  assert.deepEqual(t2.words, t.words, "the same words come back");
  const fresh = t2.handle(KEY.TAB, 3);
  assert.equal(fresh.replay, null, "a replayed test with nothing typed goes back to new words");
  app.settings.tab_same = false;
  const t3 = new TypingTest(app, spec);
  t3.handle("a", 0);
  assert.equal(t3.handle(KEY.TAB, 1), spec);
});

test("tab on the results: new words at 90%+, the same again below or failed", () => {
  const app = makeApp();
  const w = ["alpha", "beta"];
  let t = new TypingTest(app, words(w));
  typeText(t, "alpha beta", 0);
  let r = t.result(10);
  assert.ok(r.acc >= REPLAY_BELOW);
  assert.equal(r.spec.replay, null);
  t = new TypingTest(app, words(w));
  typeText(t, "axxxa bxxa", 0);
  r = t.result(10);
  assert.ok(r.acc < REPLAY_BELOW);
  assert.deepEqual(r.spec.replay, w);
  app.settings.tab_same = false;
  t = new TypingTest(app, words(w));
  typeText(t, "axxxa bxxa", 0);
  assert.equal(t.result(10).spec.replay, null);
});

test("nothing typed: the result is the menu, nothing recorded", () => {
  const app = makeApp();
  const t = new TypingTest(app, words(["a"]));
  assert.equal(t.result(5), MENU);
  assert.equal(app.history.runs.length, 0);
});

test("zen: whatever you type, enter finishes", () => {
  const app = makeApp();
  const t = newTest(app, makeSpec("zen", "zen", 0, "zen"));
  assert.ok(t instanceof ZenTest);
  typeText(t, "hi there", 0);
  assert.deepEqual(t.words, ["hi", "there"]);
  t.handle(KEY.ENTER, 5);
  assert.equal(t.finished(5), true);
});

test("hacker funbox: any key is right, and the run isn't kept", () => {
  const app = makeApp({ settings: { funbox: "hacker" } });
  const t = new TypingTest(app, words(["abc", "de"]));
  typeText(t, "zzzzzz", 0);
  assert.deepEqual(t.typed, ["abc", "de"]);
  const r = t.result(5);
  assert.equal(r.counted, false);
  assert.equal(app.history.runs.length, 0);
});

test("active wpm leaves long stops out", () => {
  const times = [0, 0.2, 0.4, 0.6, 30.6, 30.8];
  const secs = activeSeconds(times, 31);
  assert.ok(secs < 4, `${secs}`);
  assert.ok(secs > 1);
});

test("speed series buckets presses", () => {
  const s = speedSeries([[0.5, true], [1.5, false], [1.6, true]], 2, 2);
  assert.equal(s.length, 2);
  assert.equal(s[1][1], 1);
});

test("keystrokes for the keyboard app: expected char and accuracy", () => {
  const app = makeApp({ settings: { keyboard_learn: true } });
  const t = new TypingTest(app, words(["ab", "c"]));
  typeText(t, "ax", 0);
  t.handle(KEY.BACKSPACE, 1);
  assert.deepEqual(t.keystrokes.map((k) => [k.expected, k.typed]), [["a", "a"], ["b", "x"], [" ", ""]]);
  assert.equal(keystrokeAccuracy(t.keystrokes), 50);
  assert.equal(t.keystrokes[0].t, 0);
});

test("the replay rebuilds the screen at any moment", () => {
  const app = makeApp();
  const t = new TypingTest(app, words(["go", "up"]));
  typeText(t, "gx", 0, 1);
  t.handle(KEY.BACKSPACE, 2);
  t.recorder.snap(t, 2);
  typeText(t, "o up", 3, 1);
  const r = t.result(10);
  const rep = r.replay;
  assert.equal(rep.length, 6);
  assert.deepEqual(rep.at(1).typed, ["gx", ""]);
  assert.deepEqual(rep.at(2).typed, ["g", ""]);
  assert.ok(rep.at(2).errors.has("0,1"));
  const end = rep.at(99);
  assert.deepEqual(end.typed, ["go", "up"]);
  assert.equal(end.wi, 2);
  assert.ok(rep.wpm(end.typed, 6) > 0);
});
