// The background scenes: picked for a theme, drawn as layers at depths.

import { test } from "node:test";
import assert from "node:assert/strict";
import { SCENES, buildScene, palette, sceneFor } from "../src/ui/backdrop.js";
import { readFileSync } from "node:fs";

const THEMES = JSON.parse(readFileSync(new URL("../src/data/themes.json", import.meta.url))).themes;
// the colours a scene uses, as styles() gives them
const styles = (name) => {
  const t = THEMES[name];
  return { bg: t.background ?? t.made_background ?? "#141517", accent: t.accent ?? "#ffffff", warn: t.warn ?? "#d7af5f", good: t.good ?? "#5fd75f", error: t.error ?? "#ff5f5f" };
};

test("auto picks a scene that suits the theme, none for the reading themes", () => {
  assert.equal(sceneFor("auto", "synthwave"), "synthwave");
  assert.equal(sceneFor("auto", "aurora"), "aurora");
  assert.equal(sceneFor("auto", "ocean"), "ocean");
  assert.equal(sceneFor("auto", "high contrast"), null);
  assert.equal(sceneFor("auto", "mono"), null);
  assert.equal(sceneFor("off", "synthwave"), null);
  assert.equal(sceneFor("city", "paper"), "city");
  for (const t of Object.keys(THEMES)) assert.ok(sceneFor("auto", t) === null || SCENES.includes(sceneFor("auto", t)), t);
});

test("every scene draws for every theme: layers far to near, no broken numbers", () => {
  for (const name of SCENES) {
    for (const theme of ["default", "synthwave", "paper", "ocean", "matrix"]) {
      const st = styles(theme);
      const layers = buildScene(name, st, THEMES[theme]);
      assert.ok(layers.length >= 3, `${name} has depth`);
      for (let i = 1; i < layers.length; i++) assert.ok(layers[i].z > layers[i - 1].z, `${name}: far to near`);
      for (const l of layers) {
        assert.ok(l.svg.startsWith("<svg") && l.svg.endsWith("</svg>"));
        assert.ok(!/NaN|undefined/.test(l.svg), `${name} in ${theme}`);
      }
    }
  }
  assert.equal(palette(styles("paper"), THEMES.paper).light, true);
});
