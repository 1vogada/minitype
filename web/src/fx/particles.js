// One canvas over the page for the one effect that does fly apart: a combo
// that breaks shatters its number into outlined chunks (cartoon style, a dark
// line round each) that spin, fall and fade. Made only when something
// shatters; drawn once a frame while chunks are in the air.

export const MAX_SHARDS = 60;

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
      this.dpr = Math.min(2, window.devicePixelRatio || 1);
      this.canvas.width = Math.round(innerWidth * this.dpr);
      this.canvas.height = Math.round(innerHeight * this.dpr);
    };
    this.resize();
    window.addEventListener("resize", this.resize);
  }

  /** A chunk of a shattered number: flies out, spins, falls, fades. */
  shard(x, y, text, colour, font, outline = "#1b0f14") {
    if (this.ps.length >= MAX_SHARDS) return;
    const a = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.4, v = 220 + Math.random() * 300;
    this.ps.push({
      x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, rot: 0, vr: (Math.random() - 0.5) * 12,
      life: 0, max: 0.9 + Math.random() * 0.4, text, colour, font, outline, s: 0.6 + Math.random() * 0.6,
    });
  }

  get busy() { return this.ps.length > 0; }

  frame(dt) {
    const ctx = this.ctx;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    if (!this.ps.length) return;
    const alive = [];
    for (const p of this.ps) {
      p.life += dt;
      if (p.life >= p.max) continue;
      alive.push(p);
      const k = p.life / p.max;
      p.vy += 1100 * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.rot += p.vr * dt;
      ctx.save();
      ctx.globalAlpha = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;     // solid, then a quick fade: no mush
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.scale(p.s, p.s);
      ctx.font = p.font;
      ctx.lineJoin = "round";
      if (!this.cheap) {
        ctx.lineWidth = 6;
        ctx.strokeStyle = p.outline;
        ctx.strokeText(p.text, 0, 0);
      }
      ctx.fillStyle = p.colour;
      ctx.fillText(p.text, 0, 0);
      ctx.restore();
    }
    this.ps = alive;
  }

  destroy() {
    window.removeEventListener("resize", this.resize);
    this.canvas.remove();
  }
}
