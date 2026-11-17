// The effects' pure parts: the combo's heat steps, the flame's colours and shape.

import { test } from "node:test";
import assert from "node:assert/strict";
import { MILESTONES, comboHeat } from "../src/fx/combo.js";
import { FLAME_BANDS, FRAMES, flameBands, flamePath, seeded, tongues } from "../src/fx/flame.js";
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

test("the flame is one connected shape, taller towards the caret, licking", () => {
  const em = 30, width = 600, bottom = 80;
  const ts = tongues(width / em, seeded(5));
  assert.ok(ts.length >= 12, "tongues of their own along the line");
  const widths = new Set(ts.map((t) => t.w.toFixed(2)));
  assert.ok(widths.size > ts.length / 2, "of varied width");
  const d = flamePath(ts, width, em, bottom, 0);
  assert.equal((d.match(/M/g) || []).length, 1, "a single outline, not a row of separate shapes");
  assert.ok(d.endsWith("Z") && !/NaN|undefined/.test(d));
  // every point of the outline, as [x, height above the base]
  const points = (p) => {
    const out = [];
    for (const cmd of p.match(/[A-Z][^A-Z]*/g)) {
      const n = cmd.slice(1).trim().split(/\s+/).filter(Boolean).map(Number);
      for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], bottom - n[i + 1]]);
    }
    return out;
  };
  const pts = points(d);
  const top = (a, b) => Math.max(...pts.filter(([x]) => x >= a && x < b).map(([, y]) => y));
  const l = top(0, width / 3), r = top((2 * width) / 3, width);
  assert.ok(r > l, `taller at the caret end (${l.toFixed(0)} < ${r.toFixed(0)})`);
  assert.ok(pts.every(([, y]) => y >= 0), "nothing below its base");
  assert.notEqual(flamePath(ts, width, em, bottom, 1), d, "the frames of the lick differ");
  assert.equal(FRAMES, 6);
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
