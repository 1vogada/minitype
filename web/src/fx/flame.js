// A drawn, cartoon flame (motion-graphics style, not a simulation): ONE
// connected flame along a span - a shared base with tongues of different
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
  ["#ffc21a", "#fff1b8", "#ffffff"],
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
 * moment of the lick loop. Taller towards the right end. */
export function flamePath(ts, widthPx, em, bottom, frame = 0, scale = 1) {
  if (!ts.length || widthPx <= 0) return "";
  const y = (h) => (bottom - h).toFixed(1);
  const base = BASE * em * scale;
  const inset = (1 - scale) * em * 0.35;
  const left = inset, right = widthPx - inset;
  let d = `M${left.toFixed(1)} ${bottom} L${left.toFixed(1)} ${y(base * 0.8)}`;
  let px = left;
  ts.forEach((t, i) => {
    const cx = t.x * em;
    if (cx < left || cx > right) return;
    const ramp = 0.5 + 0.5 * Math.pow(cx / Math.max(widthPx, 1), 0.7);      // taller towards the caret
    const lick = 0.82 + 0.26 * Math.sin(t.phase + (frame / FRAMES) * Math.PI * 2);
    const h = Math.max(base * 1.4, t.h * HEIGHT * em * ramp * lick * scale);
    const half = (t.w * em * scale) / 2;
    const lean = t.lean * em * (0.6 + 0.4 * Math.sin(t.phase * 2 + (frame / FRAMES) * Math.PI * 2));
    const tipX = cx + lean;
    const valleyX = (px + cx - half) / 2;
    const prevGap = cx - half - px;
    // down into the valley before this tongue (unless the tongues merge), up its left side, the tip, down its right side
    if (i > 0 && prevGap > -half * 0.6) d += ` Q${valleyX.toFixed(1)} ${y(base * 0.85)} ${(cx - half).toFixed(1)} ${y(base * 1.15)}`;
    else d += ` L${(cx - half).toFixed(1)} ${y(base)}`;
    // round bellies, a pointed tip that curls with the lean: a drawn tongue, not a spike
    d += ` C${(cx - half * 1.15).toFixed(1)} ${y(h * 0.38)} ${(cx - half * 0.55 + lean * 0.4).toFixed(1)} ${y(h * 0.78)} ${tipX.toFixed(1)} ${y(h)}`;
    d += ` C${(tipX + half * 0.2).toFixed(1)} ${y(h * 0.8)} ${(cx + half * 1.2).toFixed(1)} ${y(h * 0.5)} ${(cx + half).toFixed(1)} ${y(base * 1.15)}`;
    px = cx + half;
  });
  d += ` Q${((px + right) / 2).toFixed(1)} ${y(base * 0.9)} ${right.toFixed(1)} ${y(base * 0.8)} L${right.toFixed(1)} ${bottom} Z`;
  return d;
}

/** A small detached flick (a teardrop) in a 20 x 30 box. */
const FLICK = "M10 30 C 2 30 0 20 4 13 C 7 8 9 4 10 0 C 12 6 18 11 18 19 C 18 26 15 30 10 30 Z";

function el(tag, attrs = {}) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

let flameCount = 0;

/** One flame along a span, sitting on a baseline. */
export class FlameRow {
  constructor(host, { flicks = 4, className = "", seed = null, before = null } = {}) {
    this.el = document.createElement("div");
    this.el.className = `flame-row ${className}`.trim();
    if (before) host.insertBefore(this.el, before);
    else host.prepend(this.el);                    // first: behind whatever it burns under
    this.svg = el("svg", { class: "flame-svg" });
    this.el.append(this.svg);
    this.frames = [];
    for (let f = 0; f < FRAMES; f++) {
      const g = el("g", { class: "lick-frame" });
      g.style.animationDelay = `${-(f * LOOP) / FRAMES}s`;
      const rim = el("path", { class: "rim" }), mid = el("path", { class: "mid" }), core = el("path", { class: "core" });
      g.append(rim, mid, core);
      this.svg.append(g);
      this.frames.push([rim, mid, core]);
    }
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
    this.rng = seeded(seed ?? 9301 + 4973 * ++flameCount);
    this.ts = [];
    this.key = "";
    this.heat = -1;
    this.colours(0);
  }

  /** Burn from x0 to x1 (px) on the baseline y (px), for letters `em` px big. */
  span(x0, x1, y, em) {
    const width = Math.max(0, x1 - x0);
    const key = `${Math.round(width)}|${em}`;
    const s = this.el.style;
    s.left = `${x0}px`;
    s.top = `${y}px`;
    s.setProperty("--em", `${em}px`);
    if (key === this.key) return;
    this.key = key;
    const widthEm = width / em;
    // the tongues so far keep their shape; more grow at the end as the span grows
    while (!this.ts.length || this.ts[this.ts.length - 1].x < widthEm + 2) {
      const last = this.ts[this.ts.length - 1];
      const more = tongues(SPACING[1] * 3, this.rng).map((t) => ({ ...t, x: t.x + (last ? last.x + SPACING[0] : 0) }));
      this.ts.push(...more);
    }
    const top = HEIGHT * em * 1.25;             // room above the base for the tallest tongue at full grow
    this.svg.setAttribute("viewBox", `0 0 ${Math.max(1, width).toFixed(1)} ${top.toFixed(1)}`);
    this.svg.style.width = `${width}px`;
    this.svg.style.height = `${top}px`;
    const ts = this.ts.filter((t) => t.x < widthEm);
    for (let f = 0; f < FRAMES; f++) {
      const [rim, mid, core] = this.frames[f];
      rim.setAttribute("d", flamePath(ts, width, em, top, f, 1));
      mid.setAttribute("d", flamePath(ts, width, em, top, f, 0.68));
      core.setAttribute("d", flamePath(ts, width, em, top, f, 0.38));
    }
    this.flicks.forEach((f, i) => {
      f.style.left = `${((0.25 + 0.7 * ((i * 0.618) % 1)) * width).toFixed(0)}px`;
      f.style.display = width < em * 0.6 ? "none" : "";
    });
  }

  /** The colours for a heat (0..5); only touched when they change enough to see. */
  colours(heat) {
    if (Math.abs(heat - this.heat) < 0.04) return;
    this.heat = heat;
    const [rim, mid, core] = flameBands(heat);
    const s = this.el.style;
    s.setProperty("--f-rim", rim);
    s.setProperty("--f-mid", mid);
    s.setProperty("--f-core", core);
    s.setProperty("--f-line", OUTLINE);
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
