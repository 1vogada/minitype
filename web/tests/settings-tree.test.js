// Every setting can be reached from the settings sidebar's outline.

import { test } from "node:test";
import assert from "node:assert/strict";
import { DEFAULTS } from "../src/core/settings.js";
import { TREE, flatten, outline } from "../src/ui/settingsTree.js";

// set elsewhere, not rows: the main menu's mode options, favourites, and the
// terminal version's own (no use in the browser)
const NOT_ROWS = new Set(["time_amount", "word_amount", "quote_length", "fav_quotes", "keyboard_ask", "mouse"]);

test("every setting is in the tree, once", () => {
  const keys = flatten().filter(({ row }) => Array.isArray(row)).map(({ row }) => row[0]);
  assert.equal(new Set(keys).size, keys.length, "no setting twice");
  for (const k of keys) assert.ok(k in DEFAULTS, `${k} is a setting`);
  const missing = Object.keys(DEFAULTS).filter((k) => !NOT_ROWS.has(k) && !keys.includes(k));
  assert.deepEqual(missing, []);
});

test("every row sits in a page the sidebar lists", () => {
  const paths = new Set();
  const walk = (nodes) => nodes.forEach((n) => { paths.add(n.path.join("/")); walk(n.children); });
  walk(outline());
  for (const { path } of flatten()) assert.ok(paths.has(path.join("/")), path.join(" › "));
  assert.deepEqual(TREE.map(([t]) => t), ["in-game", "effects", "menus", "data"]);
  assert.ok(flatten().some(({ path, row }) => path[0] === "effects" && row[0] === "fx_combo"));
});
