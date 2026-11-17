// The effects' pure parts: the combo's heat steps and the flame colours.

import { test } from "node:test";
import assert from "node:assert/strict";
import { MILESTONES, comboHeat } from "../src/fx/combo.js";
import { FLAME_TIERS, flameColour } from "../src/fx/particles.js";
import { FxMonitor } from "../src/fx/monitor.js";

test("combo heat: a step per milestone, smooth ramps between", () => {
  assert.equal(comboHeat(0), 0);
  assert.equal(comboHeat(5), 0.5);
  MILESTONES.forEach((m, i) => assert.equal(comboHeat(m), i + 1));
  assert.equal(comboHeat(75), 3.5);
  assert.equal(comboHeat(1000), MILESTONES.length);
  for (let c = 1; c < 260; c++) assert.ok(comboHeat(c) >= comboHeat(c - 1));
});

test("flames go red, orange, yellow, white, blue, purple", () => {
  const hex = (c) => "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
  FLAME_TIERS.forEach(([hot], i) => assert.equal(hex(flameColour(i, 0)), hot));
  const mid = flameColour(0.5, 0);
  assert.ok(mid[1] > flameColour(0, 0)[1] && mid[1] < flameColour(1, 0)[1], "blends between tiers");
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
