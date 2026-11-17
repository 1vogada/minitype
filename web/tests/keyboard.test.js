// The keyboard app client: 127.0.0.1, never throws, queues while the app is down.

import { test } from "node:test";
import assert from "node:assert/strict";
import { KeyboardApp, MAX_EVENTS, NEEDS_LOCAL, NOT_RUNNING, QUEUE_KEY, batches, canReachLocal, serverUrl } from "../src/core/keyboardApp.js";
import { memoryStore } from "../src/core/app.js";

test("server url: localhost becomes 127.0.0.1", () => {
  assert.equal(serverUrl("http://localhost:6869/"), "http://127.0.0.1:6869");
  assert.equal(serverUrl("nonsense"), "http://127.0.0.1:6869");
  assert.equal(serverUrl("http://10.0.0.2:6869"), "http://10.0.0.2:6869");
});

test("batches of MAX_EVENTS", () => {
  const ev = Array.from({ length: MAX_EVENTS * 2 + 1 }, (_, i) => ({ t: i }));
  assert.deepEqual(batches(ev).map((b) => b.length), [MAX_EVENTS, MAX_EVENTS, 1]);
});

test("down: keystrokes wait in the queue, then go first once it answers", async () => {
  const store = memoryStore();
  let up = false;
  const calls = [];
  const fetchImpl = async (url, opts) => {
    if (!up) throw new TypeError("refused");
    const body = JSON.parse(opts.body);
    calls.push([url, body]);
    return { ok: true, status: 200, json: async () => ({ on: true, tunedKeys: 3, patterns: { keys: [] } }) };
  };
  const kb = new KeyboardApp({ fetchImpl, store, proxy: null });
  const a = await kb.postEvents([{ t: 1, expected: "a", typed: "a" }]);
  assert.equal(a.ok, false);
  assert.equal(a.error, NOT_RUNNING);
  assert.equal(kb.queuedCount(), 1);
  up = true;
  const b = await kb.postEvents([{ t: 2, expected: "b", typed: "b" }]);
  assert.equal(b.ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], "http://127.0.0.1:6869/api/learn/typing");
  assert.equal(calls[0][1].action, "events");
  assert.deepEqual(calls[0][1].events.map((e) => e.t), [1, 2]);
  assert.equal(store.get(QUEUE_KEY), null);
  assert.equal(kb.line?.call, undefined);
  assert.equal(kb.last.line(), "keyboard learn: on · 3 keys tuned");
});

test("a refused direct call falls back to the dev server's proxy", async () => {
  const urls = [];
  const fetchImpl = async (url) => {
    urls.push(url);
    if (url.startsWith("http")) throw new TypeError("cors");
    return { ok: true, status: 200, json: async () => ({ on: false }) };
  };
  const kb = new KeyboardApp({ fetchImpl, store: memoryStore() });
  const a = await kb.call("status");
  assert.equal(a.ok, true);
  assert.deepEqual(urls, ["http://127.0.0.1:6869/api/learn/typing", "/kb/api/learn/typing"]);
  await kb.call("status");
  assert.equal(urls[2], "/kb/api/learn/typing", "the way that worked goes first");
});

test("an error answer is kept as its message, not queued", async () => {
  const store = memoryStore();
  const fetchImpl = async () => ({ ok: false, status: 400, json: async () => ({ error: "bad events" }) });
  const kb = new KeyboardApp({ fetchImpl, store, proxy: null });
  const a = await kb.postEvents([{ t: 1, expected: "a", typed: "a" }]);
  assert.equal(a.error, "bad events");
  assert.equal(kb.queuedCount(), 0);
});

test("never throws, even when fetch itself is missing", async () => {
  const kb = new KeyboardApp({ fetchImpl: () => { throw new Error("boom"); }, store: memoryStore(), proxy: null });
  const a = await kb.call("status");
  assert.equal(a.ok, false);
  assert.equal(await kb.postEvents([]), null);
});

test("an https page from elsewhere (GitHub Pages) doesn't try, and keeps the keystrokes", async () => {
  assert.equal(canReachLocal({ protocol: "https:", hostname: "1vogada.github.io" }), false);
  assert.equal(canReachLocal({ protocol: "http:", hostname: "localhost" }), true);
  assert.equal(canReachLocal({ protocol: "https:", hostname: "localhost" }), true);
  let called = 0;
  const kb = new KeyboardApp({ fetchImpl: async () => { called++; throw new Error("no"); }, store: memoryStore(), local: false });
  const a = await kb.postEvents([{ t: 1, expected: "a", typed: "a" }]);
  assert.equal(called, 0);
  assert.equal(a.error, NEEDS_LOCAL);
  assert.equal(a.line(), "keyboard learn: needs the local app (npm run dev)");
  assert.equal(kb.queuedCount(), 1);
});
