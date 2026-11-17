// A drawn, cartoon flame (motion-graphics style, not a simulation): ONE
// connected flame along a span (the combo's), or over a word with a tongue
// rising from each letter (the text's fire, textFire.js) - a shared base with tongues of different
// heights and widths growing out of it and merging, taller towards the end
// (the caret) - in flat colour bands (rim, middle, core) with a thick dark
// outline. It moves like hand-drawn animation: FRAMES drawings of the whole
// flame, each tongue at its own phase of a lick, shown one after another in a
// loop (on twos), plus a few flicks that pop off the tips. The drawings are
// remade only when the span changes; the loop itself is CSS, so a frame
// costs nothing.
//
// Its colours climb like the combo counter's: red, orange, yellow, white,
// blue, purple (heat 0..5, turning quickly at the end of each step).

const NS = "http://www.w3.org/2000/svg";
export const FRAMES = 6;           // drawings in the lick loop
export const LOOP = 0.6;           // seconds the loop takes
export const SPACING = [0.75, 1.5];    // em between neighbouring tongue tips
export const HEIGHT = 1.9;         // em: the tallest a tongue gets (before grow)
export const BASE = 0.2;           // em: the shared base's height
const OUTLINE = "#1b0f14";

// [rim, middle, core] per heat step
export const FLAME_BANDS = [
  ["#c4161c", "#ff4b24", "#ffb03b"],
  ["#d9480f", "#ff8c1a", "#ffd84a"],
  ["#f08c00", "#ffd43b", "#fff6c2"],
  ["#ffd54a", "#fff7d6", "#ffffff"],
  ["#1d4fd8", "#4dabf7", "#e3f4ff"],
  ["#6a1bd1", "#b46cff", "#f6edff"],
];
export const SHIFT = 0.08;         // the last share of a step where the colours turn to the next

const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (c) => "#" + c.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");

/** The three band colours at a heat (0..5): each step's own colours, turning
 * quickly to the next at the end of the step (a straight blend between, say,
 * yellow-white and blue would pass through grey). */
export function flameBands(heat) {
  const i = Math.max(0, Math.min(FLAME_BANDS.length - 1, Math.floor(heat)));
  const j = Math.min(FLAME_BANDS.length - 1, i + 1);
  const t = Math.max(0, Math.min(1, (heat - i - (1 - SHIFT)) / SHIFT));
  return FLAME_BANDS[i].map((a, k) => toHex(hex(a).map((v, c) => v + (hex(FLAME_BANDS[j][k])[c] - v) * t)));
}

/** A seeded random number source, so a flame keeps its shape as it grows. */
export function seeded(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

/** The tongues along a span: [{x (em), w (em), h (0..1), lean, phase}], from the left. */
export function tongues(widthEm, rng) {
  const out = [];
  let x = SPACING[0] * 0.4;
  while (x < widthEm - 0.15) {
    out.push({ x, w: 0.85 + rng() * 0.75, h: 0.5 + rng() * 0.5, lean: (rng() - 0.5) * 0.6, phase: rng() * Math.PI * 2 });
    x += SPACING[0] + rng() * (SPACING[1] - SPACING[0]);
  }
  return out;
}

/** The flame's outline in px (y up from the base at `bottom`): one closed path
 * over every tongue, valleys at the base's height between them. `scale` draws
 * the inner bands (the same flame, lower and narrower); `frame` picks the
 * moment of the lick loop. `ramp`: taller towards the right end (the caret);
 * `tall` / `wide` make a layer behind bigger; `height` is the tallest a tongue
 * gets, in em. */
export function flamePath(ts, widthPx, em, bottom, frame = 0, scale = 1, { ramp = true, tall = 1, wide = 1, height = HEIGHT } = {}) {
  if (!ts.length || widthPx <= 0) return "";
  const y = (h) => (bottom - h).toFixed(1);
  const base = BASE * em * scale;
  const inset = (1 - scale) * em * 0.35;
  const left = inset, right = widthPx - inset;
  let d = `M${left.toFixed(1)} ${bottom} L${left.toFixed(1)} ${y(base * 0.8)}`;
  let px = left;
  let first = true;
  ts.forEach((t) => {
    const cx = t.x * em;
    if (cx < left || cx > right) return;
    const r = ramp ? 0.5 + 0.5 * Math.pow(cx / Math.max(widthPx, 1), 0.7) : 1;
    const lick = 0.82 + 0.26 * Math.sin(t.phase + (frame / FRAMES) * Math.PI * 2);
    const h = Math.max(base * 1.4, t.h * height * em * r * lick * scale * tall);
    const half = (t.w * em * scale * wide) / 2;
    const lean = t.lean * em * (0.6 + 0.4 * Math.sin(t.phase * 2 + (frame / FRAMES) * Math.PI * 2));
    const tipX = cx + lean;
    const valleyX = (px + cx - half) / 2;
    const prevGap = cx - half - px;
    // down into the valley before this tongue (unless the tongues merge), up its left side, the tip, down its right side
    if (!first && prevGap > -half * 0.6) d += ` Q${valleyX.toFixed(1)} ${y(base * 0.85)} ${(cx - half).toFixed(1)} ${y(base * 1.15)}`;
    else d += ` L${(cx - half).toFixed(1)} ${y(base)}`;
    first = false;
    // round bellies, a pointed tip that curls with the lean: a drawn tongue, not a spike
    d += ` C${(cx - half * 1.15).toFixed(1)} ${y(h * 0.38)} ${(cx - half * 0.55 + lean * 0.4).toFixed(1)} ${y(h * 0.78)} ${tipX.toFixed(1)} ${y(h)}`;
    d += ` C${(tipX + half * 0.2).toFixed(1)} ${y(h * 0.8)} ${(cx + half * 1.2).toFixed(1)} ${y(h * 0.5)} ${(cx + half).toFixed(1)} ${y(base * 1.15)}`;
    px = cx + half;
  });
  d += ` Q${((px + right) / 2).toFixed(1)} ${y(base * 0.9)} ${right.toFixed(1)} ${y(base * 0.8)} L${right.toFixed(1)} ${bottom} Z`;
  return d;
}

/** One tongue per letter: centres in px from the span's left, the tongues'
 * own shapes from `kept` (grown with `rng` as letters are added, so a word's
 * flame keeps its shape while it is typed). A layer behind (`k` > 0) sits a
 * little off the letters, so its tongues show between the front ones. */
export function letterTongues(centres, em, widthEm, kept, rng, k = 0) {
  while (kept.length < centres.length) {
    kept.push({ w: 0.72 + rng() * 0.45, h: 0.55 + rng() * 0.45, lean: (rng() - 0.5) * 0.5, phase: rng() * Math.PI * 2, dx: (rng() - 0.5) * 0.2 });
  }
  const shift = k % 2 ? 0.22 : -0.12 * k;
  return centres.map((c, i) => ({ ...kept[i], x: Math.max(0.1, Math.min(widthEm - 0.1, c / em + kept[i].dx + shift)) }));
}

export const LAYER_TALL = 0.2;     // each layer behind is this much taller...
export const LAYER_WIDE = 0.12;    // ...and this much wider than the one in front

/** A small detached flick (a teardrop) in a 20 x 30 box. */
const FLICK = "M10 30 C 2 30 0 20 4 13 C 7 8 9 4 10 0 C 12 6 18 11 18 19 C 18 26 15 30 10 30 Z";

function el(tag, attrs = {}) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

let flameCount = 0;

/** One flame along a span, sitting on a baseline: one layer, or several
 * stacked (each behind bigger, with its own tongues and colours). */
export class FlameRow {
  constructor(host, { flicks = 4, className = "", seed = null, before = null, ramp = true, height = HEIGHT } = {}) {
    this.el = document.createElement("div");
    this.el.className = `flame-row ${className}`.trim();
    if (before) host.insertBefore(this.el, before);
    else host.prepend(this.el);                    // first: behind whatever it burns under
    this.svg = el("svg", { class: "flame-svg" });
    this.el.append(this.svg);
    this.opts = { ramp, height };
    this.seed = seed ?? 9301 + 4973 * ++flameCount;
    this.layers = [];
    this.shown = 1;
    this.lick = 0;
    this.addLayer();
    this.flicks = [];
    for (let i = 0; i < flicks; i++) {
      const f = el("svg", { viewBox: "-3 -3 26 36", class: "flick" });
      f.append(el("path", { d: FLICK, class: "rim" }), el("path", { d: FLICK, class: "core", transform: "translate(10 30) scale(0.5) translate(-10 -30)" }));
      f.style.setProperty("--flick", `${0.8 + i * 0.23}s`);
      f.style.setProperty("--flick-delay", `${-i * 0.37}s`);
      f.style.setProperty("--flick-x", `${(i % 2 ? 1 : -1) * (0.2 + i * 0.12)}em`);
      this.el.append(f);
      this.flicks.push(f);
    }
    this.args = null;
    this.key = "";
    this.heat = -1;
    this.colours(0);
  }

  addLayer() {
    const k = this.layers.length;
    const g = el("g", { class: "flame-layer" });
    const frames = [];
    for (let f = 0; f < FRAMES; f++) {
      const fg = el("g", { class: "lick-frame" });
      fg.style.setProperty("--fi", f);              // its place in the loop (the delay is in the CSS)
      const rim = el("path", { class: "rim" }), mid = el("path", { class: "mid" }), core = el("path", { class: "core" });
      fg.append(rim, mid, core);
      g.append(fg);
      frames.push([rim, mid, core]);
    }
    this.svg.prepend(g);                            // behind the layers made before it
    this.layers.push({ g, frames, ts: [], rng: seeded(this.seed + 7919 * k), heat: -1 });
  }

  /** How many layers burn: 1 is one flame; each more stacks behind, bigger. */
  setLayers(n) {
    n = Math.max(1, n);
    while (this.layers.length < n) this.addLayer();
    if (n === this.shown) return;
    this.shown = n;
    this.layers.forEach((L, k) => { L.g.style.display = k < n ? "" : "none"; });
    if (this.lick) this.speed(this.lick, true);
    this.key = "";
    if (this.args) this.span(...this.args);
  }

  /** Burn from x0 to x1 (px) on the baseline y (px), for letters `em` px big;
   * `centres` (px from x0) puts a tongue on each letter. */
  span(x0, x1, y, em, centres = null) {
    if (!(em > 0) || !Number.isFinite(x0 + x1 + y)) return;     // not laid out yet
    this.args = [x0, x1, y, em, centres];
    const width = Math.max(0, x1 - x0);
    const key = `${Math.round(width)}|${em}|${this.shown}|${centres ? centres.map(Math.round).join(",") : ""}`;
    const s = this.el.style;
    s.left = `${x0}px`;
    s.top = `${y}px`;
    s.setProperty("--em", `${em}px`);
    if (key === this.key) return;
    this.key = key;
    const widthEm = width / em;
    const { ramp, height } = this.opts;
    const top = height * em * 1.25 * (1 + LAYER_TALL * (this.shown - 1));   // room for the tallest tongue at full grow
    const pad = em * LAYER_WIDE * this.shown;                                // ...and for the wider layers' sides
    this.svgPad = pad;
    if (this.halo) this.halo.style.left = `${-pad}px`;
    this.svg.setAttribute("viewBox", `${(-pad).toFixed(1)} 0 ${Math.max(1, width + 2 * pad).toFixed(1)} ${top.toFixed(1)}`);
    this.svg.style.left = `${-pad}px`;
    this.svg.style.width = `${width + 2 * pad}px`;
    this.svg.style.height = `${top}px`;
    for (let k = 0; k < this.shown; k++) {
      const L = this.layers[k];
      let ts;
      if (centres) ts = letterTongues(centres, em, widthEm, L.ts, L.rng, k);
      else {
        // the tongues so far keep their shape; more grow at the end as the span grows
        while (!L.ts.length || L.ts[L.ts.length - 1].x < widthEm + 2) {
          const last = L.ts[L.ts.length - 1];
          L.ts.push(...tongues(SPACING[1] * 3, L.rng).map((t) => ({ ...t, x: t.x + (last ? last.x + SPACING[0] : 0) })));
        }
        ts = L.ts.filter((t) => t.x < widthEm);
      }
      const o = { ramp, height, tall: 1 + LAYER_TALL * k, wide: 1 + LAYER_WIDE * k };
      for (let f = 0; f < FRAMES; f++) {
        const [rim, mid, core] = L.frames[f];
        rim.setAttribute("d", flamePath(ts, width, em, top, f, 1, o));
        mid.setAttribute("d", flamePath(ts, width, em, top, f, 0.68, o));
        core.setAttribute("d", flamePath(ts, width, em, top, f, 0.38, o));
      }
    }
    this.flicks.forEach((f, i) => {
      f.style.left = `${((0.25 + 0.7 * ((i * 0.618) % 1)) * width).toFixed(0)}px`;
      f.style.display = width < em * 0.6 ? "none" : "";
    });
  }

  /** The letters themselves on fire: each letter's own shape drawn round it
   * in the flame's bands, a ring per layer (wider and further down the tiers
   * behind), under the real letters. `glyphs` [{ch, x}] (x from the span's
   * left), `baseline` px below the flame's base, `font` a CSS font, `radius`
   * px of the front ring. */
  glyphs(glyphs, baseline, font, radius) {
    const key = `${glyphs.map((g) => g.ch + Math.round(g.x)).join()}|${baseline.toFixed(1)}|${font}|${radius.toFixed(1)}|${this.shown}`;
    if (key === this.glyphKey) return;
    this.glyphKey = key;
    if (!this.halo) {
      this.halo = el("svg", { class: "halo-svg" });
      this.el.append(this.halo);
    }
    const pad = this.svgPad ?? 0;
    this.halo.style.font = font;
    const xs = glyphs.map((g) => (g.x + pad).toFixed(1)).join(" ");
    const text = glyphs.map((g) => g.ch).join("");
    const rings = [];
    for (let k = this.shown - 1; k >= 0; k--) {
      const L = this.layers[k];
      if (!L.ring) {
        L.ring = el("g", { class: "halo-layer" });
        if (L.ringVars) for (const [n, v] of L.ringVars) L.ring.style.setProperty(n, v);
      }
      L.ring.style.setProperty("--lick", L.g.style.getPropertyValue("--lick") || `${LOOP}s`);
      const r = radius * (1 + 0.38 * k);
      const band = (cls, width) => {
        const t = el("text", { class: cls, x: xs, y: baseline.toFixed(1), "text-anchor": "middle", "stroke-width": width.toFixed(1) });
        t.textContent = text;
        return t;
      };
      L.ring.replaceChildren(band("ring-line", 2 * r + 5), band("rim", 2 * r), band("mid", r));
      rings.push(L.ring);
    }
    this.halo.replaceChildren(...rings);
  }

  /** How many of the flicks (embers off the tips) show. */
  setFlicks(n) {
    this.flicks.forEach((f, i) => f.classList.toggle("off", i >= n));
  }

  /** The colours for a heat (0..5), of the front layer (k 0) or layer k
   * behind it; only touched when they change enough to see. */
  colours(heat, k = 0) {
    const L = this.layers[k];
    if (!L || Math.abs(heat - (k ? L.heat : this.heat)) < 0.04) return;
    if (k) L.heat = heat;
    else this.heat = heat;
    const [rim, mid, core] = flameBands(heat);
    const vars = [["--f-rim", rim], ["--f-mid", mid], ["--f-core", core]];
    if (!k) vars.push(["--f-line", OUTLINE]);
    else L.ringVars = vars;                         // the letters' ring for this layer wears them too
    for (const target of k ? [L.g, L.ring] : [this.el]) {
      if (target) for (const [n, v] of vars) target.style.setProperty(n, v);
    }
  }

  /** How long a lick loop takes (s): quicker is fiercer. The layers behind run a little slower. */
  speed(sec, force = false) {
    if (!force && Math.abs(sec - this.lick) < 0.01) return;
    this.lick = sec;
    this.layers.forEach((L, k) => {
      const v = `${(sec * (1 + 0.15 * k)).toFixed(3)}s`;
      L.g.style.setProperty("--lick", v);
      L.ring?.style.setProperty("--lick", v);
    });
  }

  /** How big it burns (1 = a normal flame), and a squash for punches. */
  size(grow, squash = 0) {
    const s = this.el.style;
    s.setProperty("--f-grow", grow.toFixed(3));
    s.setProperty("--f-squash", squash.toFixed(3));
    s.opacity = grow < 0.05 ? "0" : "1";
  }

  destroy() {
    this.el.remove();
  }
}
