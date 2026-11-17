// A drawn, cartoon flame (motion-graphics style, not a simulation): a row of
// flat SVG tongues - a rim, a middle and a core band in solid colours, a
// thick dark outline - that lick (squash and stretch) in a smooth loop and
// "boil" through three hand-drawn frames, with little flicks popping off the
// tips. All the movement is CSS animation on a fixed handful of elements, so
// it costs next to nothing per frame; JS only sets its size and colours.
//
// Its colours climb with the combo like the counter's: red, orange, yellow,
// white, blue, purple (heat 0..5, blended in between).

const NS = "http://www.w3.org/2000/svg";
export const TONGUE_EM = 0.95;     // one tongue per this many em of burning line

// [rim, middle, core] per heat step
export const FLAME_BANDS = [
  ["#c4161c", "#ff4b24", "#ffb03b"],
  ["#d9480f", "#ff8c1a", "#ffd84a"],
  ["#f08c00", "#ffd43b", "#fff6c2"],
  ["#ffc21a", "#fff1b8", "#ffffff"],
  ["#1d4fd8", "#4dabf7", "#e3f4ff"],
  ["#6a1bd1", "#b46cff", "#f6edff"],
];
const OUTLINE = "#1b0f14";

const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (c) => "#" + c.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");

export const SHIFT = 0.15;         // the last share of a step where the colours turn to the next

/** The three band colours at a heat (0..5): each step's own colours, turning
 * quickly to the next at the end of the step (a straight blend between, say,
 * yellow-white and blue would pass through grey). */
export function flameBands(heat) {
  const i = Math.max(0, Math.min(FLAME_BANDS.length - 1, Math.floor(heat)));
  const j = Math.min(FLAME_BANDS.length - 1, i + 1);
  const t = Math.max(0, Math.min(1, (heat - i - (1 - SHIFT)) / SHIFT));
  return FLAME_BANDS[i].map((a, k) => toHex(hex(a).map((v, c) => v + (hex(FLAME_BANDS[j][k])[c] - v) * t)));
}

/** A tongue's outline in a 100 x 160 box, base centred at (50, 160). */
export function tonguePath(lean = 0, tip = 0, bulge = 0, curl = 0) {
  const tx = 50 + lean, ty = 4 + tip;
  return `M50 160 C ${18 - bulge} 160 ${4 - bulge} 128 ${10 - bulge} 102`
    + ` C ${16 - bulge} 74 ${30 + lean * 0.3} 62 ${34 + lean * 0.5 + curl} 34`
    + ` C ${38 + lean * 0.7} 20 ${tx - 6} ${ty + 8} ${tx} ${ty}`
    + ` C ${tx + 8 + curl} ${ty + 22} ${70 + lean * 0.4} 46 ${82 + bulge} 78`
    + ` C ${96 + bulge} 108 ${92 + bulge} 160 50 160 Z`;
}

/** A small detached flick (a teardrop) in a 20 x 30 box. */
const FLICK = "M10 30 C 2 30 0 20 4 13 C 7 8 9 4 10 0 C 12 6 18 11 18 19 C 18 26 15 30 10 30 Z";

function el(tag, attrs = {}) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

let seed = 1;
const rnd = () => {
  seed = (seed * 16807) % 2147483647;
  return seed / 2147483647;
};

/** One tongue: three boil frames, each three bands, in an svg that licks. */
function tongue(flicks) {
  const svg = el("svg", { viewBox: "-6 -6 112 172", class: "tongue", preserveAspectRatio: "xMidYMax meet" });
  const lean = (rnd() - 0.5) * 30;
  for (let f = 0; f < 3; f++) {
    const g = el("g", { class: `boil b${f}` });
    const d = tonguePath(lean + (rnd() - 0.5) * 14, rnd() * 14, (rnd() - 0.5) * 8, (rnd() - 0.5) * 10);
    g.append(
      el("path", { d, class: "rim" }),
      el("path", { d, class: "mid", transform: "translate(50 160) scale(0.74) translate(-50 -160)" }),
      el("path", { d, class: "core", transform: "translate(50 160) scale(0.46) translate(-50 -160)" }),
    );
    svg.append(g);
  }
  const wrap = document.createElement("span");
  wrap.className = "tongue-wrap";
  wrap.style.setProperty("--lick", `${0.55 + rnd() * 0.35}s`);
  wrap.style.setProperty("--lick-delay", `${-rnd()}s`);
  wrap.style.setProperty("--h", `${0.75 + rnd() * 0.5}`);
  wrap.append(svg);
  if (flicks && rnd() < 0.55) {
    const f = el("svg", { viewBox: "-3 -3 26 36", class: "flick" });
    f.append(el("path", { d: FLICK, class: "rim" }), el("path", { d: FLICK, class: "core", transform: "translate(10 30) scale(0.5) translate(-10 -30)" }));
    f.style.setProperty("--flick", `${0.8 + rnd() * 0.7}s`);
    f.style.setProperty("--flick-delay", `${-rnd() * 1.5}s`);
    f.style.setProperty("--flick-x", `${(rnd() - 0.5) * 1.2}em`);
    wrap.append(f);
  }
  return wrap;
}

/** A row of tongues along a span, sitting on a baseline. */
export class FlameRow {
  constructor(host, { flicks = true, className = "" } = {}) {
    this.el = document.createElement("div");
    this.el.className = `flame-row ${className}`.trim();
    host.append(this.el);
    this.flicks = flicks;
    this.count = 0;
    this.heat = -1;
    this.colours(0);
  }

  /** Burn from x0 to x1 (px), on the baseline y (px), tongues sized for an em of `em` px. */
  span(x0, x1, y, em) {
    const width = Math.max(0, x1 - x0);
    const want = width < em * 0.4 ? 0 : Math.max(1, Math.round(width / (em * TONGUE_EM)));
    while (this.count < want) {
      this.el.append(tongue(this.flicks));
      this.count++;
    }
    while (this.count > want) {
      this.el.lastChild.remove();
      this.count--;
    }
    const s = this.el.style;
    s.left = `${x0}px`;
    s.top = `${y}px`;
    s.width = `${width}px`;
    s.setProperty("--em", `${em}px`);
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
