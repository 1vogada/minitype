// The effects' pure parts: the combo's heat steps, the flame's colours and shape.

import { test } from "node:test";
import assert from "node:assert/strict";
import { MILESTONES, comboHeat } from "../src/fx/combo.js";
import { FLAME_BANDS, FRAMES, flameBands, flamePath, letterTongues, seeded, tongues } from "../src/fx/flame.js";
import { fireLook, fireTier } from "../src/fx/textFire.js";
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

test("the text's fire climbs in tiers: hue, size, speed, glow, layers, shake", () => {
  assert.equal(fireTier(0), 0);
  MILESTONES.forEach((m, i) => {
    assert.equal(fireTier(m - 1), i);
    assert.equal(fireTier(m), i + 1);
  });
  const looks = [0, ...MILESTONES].map((c) => fireLook(c));
  for (let i = 1; i < looks.length; i++) {
    const a = looks[i - 1], b = looks[i];
    assert.ok(b.size > a.size && b.lick < a.lick && b.glow > a.glow && b.shake > a.shake && b.halo > a.halo, `tier ${i} is fiercer`);
    assert.ok(b.flicks >= a.flicks);
    assert.ok(b.layers >= a.layers);
    assert.ok(b.heat > a.heat, "a new hue");
  }
  assert.equal(looks[0].layers, 1, "one layer to start");
  assert.ok(!looks[0].between && looks[5].between, "more tongues when hotter");
  assert.ok(looks[5].flicks > looks[0].flicks, "more embers when hotter");
  assert.ok(looks[5].layers >= 3, "several stacked at the top");
  assert.ok(fireLook(40).size > fireLook(25).size, "growing between tiers too");
  assert.ok(fireLook(30, 20).size > fireLook(30, 0).size, "and as the run gets longer");
});

test("a word's flame: a tongue per letter, layers behind bigger", () => {
  const em = 30, centres = [9, 27, 45, 63], width = 72, bottom = 100;
  const kept = [];
  const ts = letterTongues(centres, em, width / em, kept, seeded(3));
  assert.equal(ts.length, 4);
  ts.forEach((t, i) => assert.ok(Math.abs(t.x * em - centres[i]) < 0.2 * em, "over its letter"));
  const again = letterTongues(centres.concat([81]), em, 90 / em, kept, seeded(99));
  assert.deepEqual(again.slice(0, 4).map((t) => t.h), ts.map((t) => t.h), "keeps its shape as letters are typed");
  const tallest = (d) => Math.max(...d.match(/-?[\d.]+ -?[\d.]+/g).map((p) => bottom - Number(p.split(" ")[1])));
  const front = flamePath(ts, width, em, bottom, 0, 1, { ramp: false, height: 1.1 });
  const back = flamePath(ts, width, em, bottom, 0, 1, { ramp: false, height: 1.1, tall: 1.6, wide: 1.3 });
  assert.equal((front.match(/M/g) || []).length, 1, "one connected shape");
  assert.ok(tallest(back) > tallest(front), "the layer behind is taller");
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
