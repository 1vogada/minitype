// The text's fire (the fx fire setting): the typed words of a burning run
// burn themselves, on the caret's line. Each letter is wrapped in a flame of
// its own shape (rings of the flame's bands following the glyph, flickering)
// and gives off a drawn tongue rising from its top (flame.js). Nothing burns
// behind the text: the letters stay on top, heat-tinted and outlined.
//
// The fire climbs in tiers with the combo, at the combo counter's milestones:
// each tier a new hue (red, orange, yellow, white-hot, blue, purple), bigger
// flames, a quicker lick, more glow, and more layers: the front flame in the
// tier's hue, each layer behind it a little bigger in a tier below's hue.
// fireLook() is the whole recipe, so it can be tested.

import { FlameRow, flameBands } from "./flame.js";
import { MILESTONES, comboHeat } from "./combo.js";

export const FIRE_LAYERS = [1, 1, 2, 3, 3, 4];   // flame layers per tier
export const MAX_WORDS = 12;                      // words burning at once, back from the caret
export const WORD_HEIGHT = 1.3;                   // em: a letter's tallest tongue at size 1

/** The tier of a combo: 0 below the first milestone .. 5 from the last. */
export function fireTier(combo) {
  return MILESTONES.filter((m) => combo >= m).length;
}

/** How the fire looks at a combo, `run` words into the burning run. */
export function fireLook(combo, run = 0) {
  const tier = fireTier(combo);
  const within = Math.max(0, Math.min(1, comboHeat(combo) - tier));      // on the way to the next tier
  return {
    tier,
    heat: Math.min(5, comboHeat(combo)),
    layers: FIRE_LAYERS[tier],
    size: (0.7 + 0.16 * tier + 0.12 * within) * (1 + Math.min(0.3, run * 0.02)),
    lick: 0.6 - 0.05 * tier,      // seconds a lick loop takes: quicker when hotter
    glow: 2.5 * tier,             // px of glow around the flames and the letters
    bright: 1 + 0.05 * tier,
    shake: 1.5 + 1.3 * tier,      // px: the screen shake when this tier lands
    halo: 0.065 + 0.02 * tier,    // em: the letter-shaped ring round each letter
    between: tier >= 3,           // tongues between the letters too
    flicks: 1 + Math.floor(tier / 2),
  };
}

const ascents = new Map();
/** Where a font's baseline sits in a line `lineH` px tall, from the line's top. */
function baselineIn(font, lineH) {
  if (!ascents.has(font)) {
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = font;
    const m = ctx.measureText("Hg");
    ascents.set(font, [m.fontBoundingBoxAscent, m.fontBoundingBoxDescent]);
  }
  const [up, down] = ascents.get(font);
  return (lineH - up - down) / 2 + up;
}

export class TextFire {
  constructor(view) {
    this.view = view;
    this.box = document.createElement("div");
    this.box.className = "text-fire";
    this.rows = new Map();        // word index -> FlameRow
    this.lit = new Set();         // word elements wearing .burning
    this.runStart = null;         // the word the run lit on
    this.grow = 0;
    this.sig = "";
    this.aboveY = null;
    this.em = 0;
    this.vars = "";
  }

  /** A frame: burn is 0 (out) .. 1, combo the combo now. Returns the look. */
  frame(dt, { burn, combo, bump = 0, squash = 0, cheap = false }) {
    const v = this.view, st = v.state;
    if (this.box.parentNode !== v.words) v.words.prepend(this.box);       // a new text clears the words
    if (!st) return null;
    this.hideAbove();
    const wi = Math.min(st.wi, st.words.length - 1);
    if (!burn) this.runStart = null;
    else if (this.runStart === null || this.runStart > wi) this.runStart = wi;
    const look = fireLook(combo, this.runStart === null ? 0 : wi - this.runStart);
    const target = burn ? look.size : 0;
    this.grow += (target - this.grow) * Math.min(1, dt * (target > this.grow ? 6 : 3));
    if (!burn && this.grow < 0.03) {
      if (this.rows.size) this.clear();
      return look;
    }
    const layers = cheap ? 1 : look.layers;
    if (burn) {
      // what moves the flames: a key, the line, the layout (a font arriving, a resize), a new tier
      const cw = v.wordEls[wi];
      const sig = `${wi}|${(st.typed[wi] ?? "").length}|${this.runStart}|${cw?.offsetLeft},${cw?.offsetTop}|${v.lineH}|${v.viewport.clientWidth}|${layers}|${look.tier}`;
      if (sig !== this.sig) {
        this.sig = sig;
        this.place(wi, layers, look);
      }
    }
    const vars = `${cheap ? 0 : look.glow}px|${look.bright.toFixed(2)}|${flameBands(look.heat)[1]}`;
    if (vars !== this.vars) {
      this.vars = vars;
      const [glow, bright, tint] = vars.split("|");
      const s = v.words.style;
      s.setProperty("--fire-glow", glow);
      s.setProperty("--fire-bright", bright);
      s.setProperty("--fire-tint", tint);
    }
    for (const row of this.rows.values()) {
      // the front flame wears the tier's hue; each layer behind it, a little bigger, a tier below's
      for (let k = 0; k < row.shown; k++) row.colours(Math.max(0, look.heat - k), k);
      row.speed(look.lick);
      row.size(this.grow * row.recency * (1 + bump), squash);
    }
    return look;
  }

  /** The burning words: from where the run lit (at most MAX_WORDS back) to the caret, on the caret's line. */
  place(wi, layers, look) {
    const v = this.view, st = v.state;
    const caretWord = v.wordEls[wi];
    if (!caretWord) return;
    const top = caretWord.offsetTop;
    this.em = parseFloat(getComputedStyle(v.viewport).fontSize) || 28;
    const em = this.em;
    const y = top + v.lineH / 2 - 0.12 * em;               // about the top of the small letters
    let font = null, baseline = 0;
    const mirror = v.s.funbox === "mirror";
    const want = new Set();
    const lit = new Set();
    for (let i = wi, j = 0; i >= Math.max(0, this.runStart ?? wi) && j < MAX_WORDS; i--, j++) {
      const w = v.wordEls[i];
      if (!w || w.offsetTop !== top) break;
      // the letters typed right so far
      const spans = [];
      const n = i === wi ? (st.typed[i] ?? "").length : w.children.length;
      for (let c = 0; c < Math.min(n, w.children.length); c++) {
        const l = w.children[c];
        if (!l.classList.contains("ok")) continue;
        const left = mirror ? w.offsetWidth - l.offsetLeft - l.offsetWidth : l.offsetLeft;
        spans.push([left, left + l.offsetWidth, l.textContent]);
        if (!font) {
          const cs = getComputedStyle(l);
          font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
          baseline = top + baselineIn(font, v.lineH) - y;
        }
      }
      if (!spans.length) continue;
      const a = Math.min(...spans.map((p) => p[0])), b = Math.max(...spans.map((p) => p[1]));
      let row = this.rows.get(i);
      if (!row) {
        row = new FlameRow(this.box, { flicks: 3, ramp: false, height: WORD_HEIGHT, className: "word-flame", seed: 4241 + i * 977 });
        this.rows.set(i, row);
      }
      row.recency = 1 - Math.min(0.3, j * 0.06);           // taller towards the caret
      row.setLayers(layers);
      const centres = spans.map((p) => (p[0] + p[1]) / 2 - a);
      // hotter: more tongues, between the letters too
      const tongueAt = look.between ? centres.flatMap((c, k) => (k ? [(centres[k - 1] + c) / 2, c] : [c])) : centres;
      row.span(w.offsetLeft + a, w.offsetLeft + b, y, em, tongueAt);
      row.glyphs(spans.map((p, k) => ({ ch: p[2], x: centres[k] })), baseline, font, look.halo * em);
      row.setFlicks(look.flicks);
      want.add(i);
      lit.add(w);
    }
    for (const [i, row] of this.rows) {
      if (want.has(i)) continue;
      this.rows.delete(i);
      row.el.classList.add("out");
      setTimeout(() => row.destroy(), 260);
    }
    for (const w of this.lit) if (!lit.has(w)) w.classList.remove("burning");
    for (const w of lit) w.classList.add("burning");
    this.lit = lit;
  }

  /** The lines scrolled off the top stay hidden: the flames have room above the box, those lines don't. */
  hideAbove() {
    const v = this.view;
    const key = `${v.scrollY}|${v.viewport.clientWidth}|${v.wordEls.length}|${v.lineH}`;
    if (v.tapeMode !== "off" || key === this.aboveY) return;
    this.aboveY = key;
    const wi = Math.min(v.state.wi, v.wordEls.length - 1);
    for (let i = Math.max(0, wi - 120); i <= wi + 1 && i < v.wordEls.length; i++) {
      const up = v.wordEls[i].offsetTop < v.scrollY - 1;
      v.wordEls[i].classList.toggle("above", up);
      v.gapEls[i]?.classList.toggle("above", up);
    }
  }

  clear() {
    for (const row of this.rows.values()) row.destroy();
    this.rows.clear();
    for (const w of this.lit) w.classList.remove("burning");
    this.lit.clear();
    this.sig = "";
  }

  destroy() {
    this.clear();
    this.box.remove();
  }
}
