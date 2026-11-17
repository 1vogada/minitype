// The effects' pure parts: the combo's heat steps, the flame's colours and shape.

import { test } from "node:test";
import assert from "node:assert/strict";
import { MILESTONES, comboHeat } from "../src/fx/combo.js";
import { FLAME_BANDS, flameBands, tonguePath } from "../src/fx/flame.js";
import { FxMonitor } from "../src/fx/monitor.js";

test("combo heat: a step per milestone, smooth ramps between", () => {
  assert.equal(comboHeat(0), 0);
  assert.equal(comboHeat(5), 0.5);
  MILESTONES.forEach((m, i) => assert.equal(comboHeat(m), i + 1));
  assert.equal(comboHeat(75), 3.5);
  assert.equal(comboHeat(1000), MILESTONES.length);
  for (let c = 1; c < 260; c++) assert.ok(comboHeat(c) >= comboHeat(c - 1));
});

test("the flame's bands go red, orange, yellow, white, blue, purple", () => {
  assert.equal(FLAME_BANDS.length, 6);
  FLAME_BANDS.forEach((bands, i) => assert.deepEqual(flameBands(i), bands));
  const g = (h) => parseInt(h.slice(3, 5), 16);
  assert.deepEqual(flameBands(0.5), FLAME_BANDS[0], "a step keeps its colours");
  const mid = flameBands(0.93)[1];
  assert.ok(g(mid) > g(FLAME_BANDS[0][1]) && g(mid) < g(FLAME_BANDS[1][1]), "turns to the next at the end");
  assert.deepEqual(flameBands(9), FLAME_BANDS[5]);
});

test("a tongue is one closed path, standing on its base", () => {
  const d = tonguePath(10, 4, 2, -3);
  assert.ok(d.startsWith("M50 160"));
  assert.ok(d.endsWith("Z"));
  assert.ok(!/NaN|undefined/.test(d));
});

test("fx quality auto drops to cheap after slow frames, and comes back", () => {
  const app = { settings: { fx_quality: "auto" } };
  const m = new FxMonitor(app);
  for (let i = 0; i < 200; i++) m.tick(40);
  assert.equal(m.cheap, true);
  for (let i = 0; i < 400; i++) m.tick(16);
  assert.equal(m.cheap, false);
  app.settings.fx_quality = "cheap";
  assert.equal(m.cheap, true);
  app.settings.fx_quality = "full";
  for (let i = 0; i < 200; i++) m.tick(40);
  assert.equal(m.cheap, false);
});
