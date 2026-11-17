// One canvas over the page for every particle effect (fire on the line, the
// combo counter's flames, a shattering number). Drawn once a frame; nothing
// here runs on a key press, so typing never waits on it.

export const MAX_PARTICLES = 900;

// flame colours by heat, coolest first: red, orange, yellow, white, blue, purple
export const FLAME_TIERS = [
  ["#ff3b1f", "#b3100a"],
  ["#ff8a1f", "#e0420c"],
  ["#ffd84a", "#ff8a1f"],
  ["#fff6e0", "#ffd27a"],
  ["#7fc8ff", "#2f6bff"],
  ["#d58bff", "#7a2cff"],
];

function hexRgb(h) {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const TIER_RGB = FLAME_TIERS.map(([a, b]) => [hexRgb(a), hexRgb(b)]);

/** The flame colour pair at a heat (0..5, fractions blend between tiers). */
export function flameColour(heat, k = 0) {
  const i = Math.max(0, Math.min(TIER_RGB.length - 1, Math.floor(heat)));
  const j = Math.min(TIER_RGB.length - 1, i + 1);
  const t = Math.max(0, Math.min(1, heat - i));
  return TIER_RGB[i][k].map((v, c) => Math.round(v + (TIER_RGB[j][k][c] - v) * t));
}

export class ParticleLayer {
  constructor() {
    this.canvas = document.createElement("canvas");
    this.canvas.className = "fx-canvas";
    Object.assign(this.canvas.style, { position: "fixed", inset: "0", width: "100vw", height: "100vh", pointerEvents: "none", zIndex: "5" });
    document.body.append(this.canvas);
    this.ctx = this.canvas.getContext("2d");
    this.ps = [];
    this.cheap = false;
    this.resize = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      this.dpr = dpr;
      this.canvas.width = Math.round(innerWidth * dpr);
      this.canvas.height = Math.round(innerHeight * dpr);
    };
    this.resize();
    window.addEventListener("resize", this.resize);
  }

  /** A flame particle at x, y (css px): rises, flickers, shrinks. */
  flame(x, y, heat, size = 1) {
    if (this.ps.length >= MAX_PARTICLES * (this.cheap ? 0.4 : 1)) return;
    const h = heat + Math.random() * 0.5 - 0.25;
    this.ps.push({
      kind: "flame", x, y, vx: (Math.random() - 0.5) * 24 * size, vy: -(70 + Math.random() * 90) * size,
      life: 0, max: 0.35 + Math.random() * 0.4, r: (1.6 + Math.random() * 3) * size,
      hot: flameColour(h, 0), cool: flameColour(h, 1),
    });
  }

  /** A shard of a shattered number: flies out, spins, falls, fades. */
  shard(x, y, text, colour, font) {
    const a = Math.random() * Math.PI * 2, v = 160 + Math.random() * 320;
    this.ps.push({
      kind: "shard", x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 120, rot: 0, vr: (Math.random() - 0.5) * 14,
      life: 0, max: 0.9 + Math.random() * 0.5, text, colour, font,
    });
  }

  /** A spark: a fast short dot. */
  spark(x, y, colour) {
    if (this.ps.length >= MAX_PARTICLES) return;
    const a = Math.random() * Math.PI * 2, v = 60 + Math.random() * 220;
    this.ps.push({ kind: "spark", x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 0.3 + Math.random() * 0.4, colour });
  }

  get busy() { return this.ps.length > 0; }

  frame(dt) {
    const ctx = this.ctx, dpr = this.dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    if (!this.ps.length) return;
    const glow = !this.cheap;
    const alive = [];
    for (const p of this.ps) {
      p.life += dt;
      if (p.life >= p.max) continue;
      alive.push(p);
      const k = p.life / p.max;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.kind === "flame") {
        p.vx += (Math.random() - 0.5) * 260 * dt;
        p.vy *= 1 - dt * 0.6;
        // a tongue of flame: a hot core turning to its cooler colour, stretched by its speed
        const r = p.r * (1 - k * 0.75);
        const c = p.hot.map((v, i) => Math.round(v + (p.cool[i] - v) * Math.min(1, k * 1.6)));
        ctx.globalCompositeOperation = glow ? "lighter" : "source-over";
        ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},${(1 - k) * (glow ? 0.6 : 0.85)})`;
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, r, r * (1.8 + Math.min(2, -p.vy / 80)), 0, 0, Math.PI * 2);
        ctx.fill();
      } else if (p.kind === "spark") {
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = p.colour;
        ctx.globalAlpha = 1 - k;
        ctx.fillRect(p.x, p.y, 2, 2);
        ctx.globalAlpha = 1;
      } else {
        p.vy += 900 * dt;
        p.rot += p.vr * dt;
        ctx.globalCompositeOperation = "source-over";
        ctx.save();
        ctx.globalAlpha = 1 - k;
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.colour;
        ctx.font = p.font;
        ctx.fillText(p.text, 0, 0);
        ctx.restore();
      }
    }
    ctx.globalCompositeOperation = "source-over";
    this.ps = alive;
  }

  destroy() {
    window.removeEventListener("resize", this.resize);
    this.canvas.remove();
  }
}
