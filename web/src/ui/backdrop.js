// The background scenes (the fx bg setting): drawn in the same flat,
// outlined style as the effects and coloured from the theme, in layers at
// different depths, so the whole scene tilts in 3D with the mouse and the
// near layers move more than the far ones (fx bg tilt).
//
// Each scene is a list of layers [{z, svg}], z in px towards the viewer
// (negative is far). The SVGs are made once per scene and theme; tilting only
// changes one transform, and stops when the scene has settled.

import { luminance, mix, saturation, turn } from "./colour.js";
import { seeded } from "../fx/flame.js";
import { BG_SCENES } from "../core/config.js";

export const SCENES = BG_SCENES.slice(2);
const W = 1600, H = 900;
const OUTLINE = "#1b0f14";

const AUTO = {
  synthwave: ["synthwave", "vaporwave", "party", "candy", "glitch", "rainbow", "bubbly"],
  aurora: ["aurora", "nord", "tundra", "midnight", "lavender", "catppuccin"],
  ocean: ["ocean", "deep sea", "reef", "coral"],
  mountains: ["default", "forest", "sunset", "moss", "pine", "autumn", "desert", "meadow", "jungle", "bamboo", "summit", "volcanic", "ember", "cherry", "blossom"],
  city: ["matrix", "phosphor", "amber", "dracula", "monokai", "gruvbox", "rose pine", "solarized"],
};

/** The scene for a setting and theme: "auto" picks one that suits the theme
 * (none for the high contrast and mono themes, which are about reading). */
export function sceneFor(setting, theme) {
  if (setting !== "auto") return SCENES.includes(setting) ? setting : null;
  if (theme.startsWith("high contrast") || theme === "mono" || theme === "paper") return null;
  for (const [scene, themes] of Object.entries(AUTO)) if (themes.includes(theme)) return scene;
  return "blobs";
}

/** A scene's colours from the theme: sky (top, horizon), and a ramp of hues. */
export function palette(st, raw = {}) {
  const bg = st.bg, light = luminance(bg) > 0.4;
  const far = light ? "#ffffff" : "#000000";
  // the theme's gradient, or its accent turned round the colour wheel a little (a grey accent: its other colours)
  const hues = raw.gradient?.length >= 2 ? pick(raw.gradient, 4)
    : saturation(st.accent) > 0.2 ? [st.accent, turn(st.accent, 28), turn(st.accent, -32), turn(st.accent, 60)]
      : [st.warn, st.good, st.accent, st.error];
  return {
    light,
    bg,
    skyTop: mix(bg, far, light ? 0.25 : 0.35),
    skyLow: mix(bg, hues[0], light ? 0.35 : 0.3),
    hues,
    // ground layers, far to near: hazy like the sky far away, deeper near
    ground: [0.3, 0.55, 0.8].map((t) => mix(mix(bg, hues[0], light ? 0.35 : 0.3), light ? mix(bg, hues[1], 0.6) : mix(mix(bg, hues[1], 0.2), "#000000", 0.45), t)),
    deep: light ? mix(bg, hues[1], 0.25) : mix(mix(bg, hues[1], 0.15), "#000000", 0.45),
    glow: hues[0],
    star: light ? mix(bg, "#000000", 0.25) : mix("#ffffff", hues[0], 0.25),
  };
}

function pick(list, n) {
  return Array.from({ length: n }, (_, i) => list[Math.floor((i * list.length) / n)]);
}

const svg = (body, defs = "", aspect = "xMidYMax slice") =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="${aspect}"><defs>${defs}</defs>${body}</svg>`;
const line = `stroke="${OUTLINE}" stroke-width="3" stroke-linejoin="round"`;

function sky(p, id = "sky") {
  return [`<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p.skyTop}"/><stop offset="1" stop-color="${p.skyLow}"/></linearGradient>`,
    `<rect width="${W}" height="${H}" fill="url(#${id})"/>`];
}

function stars(p, rng, n = 90, maxY = 0.6) {
  let s = "";
  for (let i = 0; i < n; i++) {
    const x = rng() * W, y = rng() * H * maxY, r = rng() < 0.12 ? 2.6 : 1.2 + rng();
    s += `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(1)}" fill="${p.star}" opacity="${(0.4 + rng() * 0.6).toFixed(2)}"/>`;
    if (r > 2.5) s += `<path d="M${x} ${y - 9} L${x + 1.6} ${y - 1.6} L${x + 9} ${y} L${x + 1.6} ${y + 1.6} L${x} ${y + 9} L${x - 1.6} ${y + 1.6} L${x - 9} ${y} L${x - 1.6} ${y - 1.6} Z" fill="${p.star}"/>`;
  }
  return s;
}

/** A jagged ridge across the scene, closed to the bottom: cartoon mountains. */
function ridge(rng, base, amp, step = 70) {
  let d = `M-40 ${H + 10} L-40 ${base}`;
  for (let x = -40; x <= W + 40; x += step * (0.6 + rng() * 0.8)) {
    d += ` L${x.toFixed(0)} ${(base - amp * (0.25 + 0.75 * rng())).toFixed(0)}`;
  }
  return `${d} L${W + 40} ${base} L${W + 40} ${H + 10} Z`;
}

/** A soft rolling line across the scene, closed to the bottom: hills,
 * waves (open: just the line, for foam). */
function wave(rng, base, amp, waves = 3, open = false, steps = 64) {
  const ph = [rng() * 6, rng() * 6], k = waves * Math.PI * 2 / W;
  let d = "";
  for (let i = 0; i <= steps; i++) {
    const x = -20 + (i / steps) * (W + 40);
    const y = base - amp * (0.6 * Math.sin(x * k + ph[0]) + 0.4 * Math.sin(x * k * 2.3 + ph[1]));
    d += `${i ? " L" : "M"}${x.toFixed(0)} ${y.toFixed(0)}`;
  }
  return open ? d : `M-20 ${H + 10} L${d.slice(1)} L${W + 20} ${H + 10} Z`;
}

const BUILD = {
  synthwave(p, rng) {
    const [sd, sb] = sky(p);
    const sunTop = p.hues[2], sunLow = p.hues[0];
    let gaps = "";
    for (let i = 0; i < 7; i++) gaps += `<rect x="0" y="${330 + i * 30 + i * i * 2}" width="${W}" height="${3 + i * 2.4}" fill="#000"/>`;
    const sun = `<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sunTop}"/><stop offset="1" stop-color="${sunLow}"/></linearGradient>
      <mask id="sunmask"><rect width="${W}" height="${H}" fill="#fff"/>${gaps}</mask>`;
    let grid = `<rect y="600" width="${W}" height="300" fill="${p.deep}"/>`;
    for (let i = 0; i < 9; i++) {
      const y = 600 + 300 * ((i + 1) / 9) ** 2;
      grid += `<line x1="0" x2="${W}" y1="${y.toFixed(0)}" y2="${y.toFixed(0)}" stroke="${p.glow}" stroke-width="${1.5 + i * 0.4}" opacity="0.8"/>`;
    }
    for (let i = -14; i <= 14; i++) grid += `<line x1="${W / 2 + i * 30}" y1="600" x2="${W / 2 + i * 260}" y2="${H}" stroke="${p.glow}" stroke-width="2" opacity="0.8"/>`;
    return [
      { z: -420, svg: svg(sb + stars(p, rng, 70, 0.45), sd) },
      { z: -300, svg: svg(`<circle cx="${W / 2}" cy="420" r="210" fill="url(#sun)" mask="url(#sunmask)" ${line}/>`, sun) },
      { z: -160, svg: svg(`<path d="${ridge(rng, 610, 170, 110)}" fill="${p.ground[0]}" ${line}/>`) },
      { z: 0, svg: svg(grid) },
    ];
  },

  mountains(p, rng) {
    const [sd, sb] = sky(p);
    const moon = `<circle cx="1220" cy="170" r="52" fill="${mix(p.star, p.skyLow, 0.2)}" ${line}/><circle cx="1204" cy="158" r="10" fill="${mix(p.star, p.bg, 0.3)}"/><circle cx="1238" cy="188" r="7" fill="${mix(p.star, p.bg, 0.3)}"/>`;
    return [
      { z: -420, svg: svg(sb + stars(p, rng), sd) },
      { z: -330, svg: svg(moon) },
      { z: -220, svg: svg(`<path d="${ridge(rng, 560, 260, 120)}" fill="${p.ground[0]}" ${line}/>`) },
      { z: -110, svg: svg(`<path d="${ridge(rng, 700, 220, 90)}" fill="${p.ground[1]}" ${line}/>`) },
      { z: 0, svg: svg(`<path d="${wave(rng, 820, 40, 2)}" fill="${p.ground[2]}" ${line}/>`) },
    ];
  },

  aurora(p, rng) {
    const [sd, sb] = sky(p);
    let ribbons = "";
    const defs = `<filter id="soft" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>` +
      p.hues.map((c, i) => `<linearGradient id="rib${i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${c}" stop-opacity="0"/><stop offset="0.3" stop-color="${c}"/><stop offset="0.7" stop-color="${p.hues[(i + 1) % 4]}"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></linearGradient>`).join("");
    for (let i = 0; i < 3; i++) {
      const y = 170 + i * 90, a = 70 + rng() * 60;
      ribbons += `<path d="M-100 ${y} C 300 ${y - a}, 600 ${y + a}, 900 ${y} S 1400 ${y - a}, 1700 ${y + 20}" fill="none" stroke="url(#rib${i})" stroke-width="${110 - i * 25}" opacity="0.55" filter="url(#soft)"/>`;
    }
    let pines = "";
    for (let x = -30; x < W + 40; x += 34 + rng() * 40) {
      const h = 110 + rng() * 150, b = 900;
      pines += `<path d="M${x} ${b - h} L${x + h * 0.22} ${b - h * 0.55} L${x + h * 0.12} ${b - h * 0.55} L${x + h * 0.3} ${b - h * 0.2} L${x - h * 0.3} ${b - h * 0.2} L${x - h * 0.12} ${b - h * 0.55} L${x - h * 0.22} ${b - h * 0.55} Z" fill="${p.ground[2]}" ${line}/>`;
    }
    return [
      { z: -420, svg: svg(sb + stars(p, rng, 110, 0.7), sd) },
      { z: -300, svg: svg(ribbons, defs) },
      { z: -150, svg: svg(`<path d="${wave(rng, 800, 50, 1.5)}" fill="${p.ground[1]}" ${line}/>`) },
      { z: 0, svg: svg(pines) },
    ];
  },

  ocean(p, rng) {
    const [sd, sb] = sky(p);
    const sun = `<circle cx="${W * 0.62}" cy="560" r="120" fill="${p.hues[2]}" ${line}/>`;
    const layers = [{ z: -420, svg: svg(sb + stars(p, rng, 40, 0.35), sd) }, { z: -340, svg: svg(sun) }];
    const blues = [0.1, 0.3, 0.5, 0.7].map((t) => mix(mix(p.hues[1], p.hues[3], 0.3), p.deep, t));
    blues.forEach((c, i) => {
      const base = 600 + i * 75;
      const foam = i ? `<path d="${wave(rng, base + 16, 10 + i * 4, 4 + i, true)}" fill="none" stroke="${mix(c, "#ffffff", 0.4)}" stroke-width="3" stroke-linecap="round" stroke-dasharray="46 34" opacity="0.6"/>` : "";
      layers.push({ z: -260 + i * 85, svg: svg(`<path d="${wave(rng, base, 14 + i * 6, 4 + i)}" fill="${c}" ${line}/>${foam}`) });
    });
    return layers;
  },

  city(p, rng) {
    const [sd, sb] = sky(p);
    const moon = `<circle cx="1260" cy="150" r="44" fill="${mix(p.star, "#ffffff", 0.5)}" ${line}/>`;
    const skyline = (base, maxH, colour, lit) => {
      let s = "";
      for (let x = -20; x < W + 20;) {
        const w = 50 + rng() * 90, h = maxH * (0.35 + rng() * 0.65);
        s += `<rect x="${x.toFixed(0)}" y="${(base - h).toFixed(0)}" width="${w.toFixed(0)}" height="${(h + 40).toFixed(0)}" fill="${colour}" ${line}/>`;
        if (lit) {
          for (let wy = base - h + 14; wy < base - 12; wy += 22) {
            for (let wx = x + 10; wx < x + w - 14; wx += 18) {
              if (rng() < 0.3) s += `<rect x="${wx.toFixed(0)}" y="${wy.toFixed(0)}" width="8" height="11" fill="${rng() < 0.7 ? p.hues[2] : p.glow}"/>`;
            }
          }
        }
        x += w + rng() * 8;
      }
      return s;
    };
    return [
      { z: -420, svg: svg(sb + stars(p, rng, 50, 0.4), sd) },
      { z: -330, svg: svg(moon) },
      { z: -220, svg: svg(skyline(720, 380, p.ground[0], false)) },
      { z: -110, svg: svg(skyline(820, 320, p.ground[1], true)) },
      { z: 0, svg: svg(skyline(930, 200, p.ground[2], true)) },
    ];
  },

  blobs(p, rng) {
    const defs = `<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>`;
    const blob = (i) => `<circle cx="${(rng() * W).toFixed(0)}" cy="${(rng() * H).toFixed(0)}" r="${(180 + rng() * 200).toFixed(0)}" fill="${p.hues[i % 4]}" opacity="${p.light ? 0.45 : 0.55}" filter="url(#blur)"/>`;
    let dots = "";
    for (let x = 40; x < W; x += 48) for (let y = 40; y < H; y += 48) dots += `<circle cx="${x}" cy="${y}" r="1.6" fill="${p.star}" opacity="0.35"/>`;
    return [
      { z: -420, svg: svg(`<rect width="${W}" height="${H}" fill="${p.bg}"/>${blob(0)}${blob(1)}`, defs, "xMidYMid slice") },
      { z: -240, svg: svg(`${blob(2)}${blob(3)}${blob(1)}`, defs, "xMidYMid slice") },
      { z: -60, svg: svg(dots, "", "xMidYMid slice") },
    ];
  },
};

/** The layers of a scene for a theme: [{z, svg}]. */
export function buildScene(name, st, raw) {
  const make = BUILD[name];
  if (!make) return [];
  return make(palette(st, raw), seeded(SCENES.indexOf(name) * 7907 + 101));
}

const PERSPECTIVE = 900;
const MAX_TILT = [5, 8];     // degrees: up/down, left/right

/** The scene behind the app, tilting after the mouse. */
export class Backdrop {
  constructor() {
    this.el = document.createElement("div");
    this.el.id = "backdrop";
    this.el.setAttribute("aria-hidden", "true");
    this.tiltEl = document.createElement("div");
    this.tiltEl.className = "bd-tilt";
    this.el.append(this.tiltEl);
    document.body.prepend(this.el);
    this.key = "";
    this.tilt = true;
    this.target = [0, 0];
    this.cur = [0, 0];
    this.running = false;
    window.addEventListener("pointermove", (e) => {
      this.aim((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1);
    }, { passive: true });
    document.documentElement.addEventListener("pointerleave", () => this.aim(0, 0));
    window.addEventListener("blur", () => this.aim(0, 0));
  }

  /** The scene for these settings and theme (made again only when they change). */
  apply(settings, st, raw, themeName) {
    const name = sceneFor(settings.fx_bg ?? "auto", themeName);
    this.tilt = settings.fx_bg_tilt !== false;
    if (!this.tilt) this.aim(0, 0, true);
    document.documentElement.classList.toggle("has-bg", Boolean(name));
    const key = `${name}|${st.bg}|${st.accent}|${(raw.gradient ?? []).join()}`;
    if (key === this.key) return;
    this.key = key;
    this.tiltEl.replaceChildren(...(name ? buildScene(name, st, raw) : []).map(({ z, svg: s }) => {
      const layer = document.createElement("div");
      layer.className = "bd-layer";
      // pushed back and scaled up again, so every layer fills the screen at any depth
      layer.style.transform = `translateZ(${z}px) scale(${(1 - z / PERSPECTIVE).toFixed(3)})`;
      layer.innerHTML = s;
      return layer;
    }));
    this.el.dataset.scene = name ?? "";
  }

  aim(x, y, now = false) {
    this.target = this.tilt ? [x, y] : [0, 0];
    if (now) this.cur = [...this.target];
    if (!this.running) {
      this.running = true;
      requestAnimationFrame(() => this.step());
    }
  }

  step() {
    const [tx, ty] = this.target;
    this.cur[0] += (tx - this.cur[0]) * 0.08;
    this.cur[1] += (ty - this.cur[1]) * 0.08;
    const [x, y] = this.cur;
    this.tiltEl.style.transform = `rotateX(${(-y * MAX_TILT[0]).toFixed(3)}deg) rotateY(${(x * MAX_TILT[1]).toFixed(3)}deg)`;
    if (Math.abs(tx - x) + Math.abs(ty - y) < 0.002) {
      this.running = false;
      return;
    }
    requestAnimationFrame(() => this.step());
  }
}
