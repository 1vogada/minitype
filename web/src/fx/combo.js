// The combo counter, escalating like a video edit (the fx combo setting):
// it flashes harder, shakes and lunges at the edges of its box, and burns -
// flames going red, orange, yellow, white, blue, purple - getting bigger,
// brighter and hotter step by step at the milestones, with smooth ramps in
// between. A break shatters the number and the flames die out. It sits above
// the words and never covers the line you're typing.

import { flameColour } from "./particles.js";

export const MILESTONES = [10, 25, 50, 100, 200];
export const SHOW_FROM = 5;

/** The heat of a combo: 0 below the first milestone .. 5 at the last, ramping smoothly between. */
export function comboHeat(combo) {
  let lo = 0;
  for (let i = 0; i < MILESTONES.length; i++) {
    const hi = MILESTONES[i];
    if (combo < hi) return i + (combo - lo) / (hi - lo);
    lo = hi;
  }
  return MILESTONES.length;
}

export class ComboCounter {
  constructor(host, layer, monitor) {
    this.layer = layer;
    this.monitor = monitor;
    this.el = document.createElement("div");
    this.el.className = "combo-fx";
    this.num = document.createElement("span");
    this.el.append(this.num);
    host.append(this.el);
    this.combo = 0;
    this.shown = false;
    this.heat = 0;           // eased towards the combo's heat
    this.punch = 0;          // a milestone's kick, decaying
    this.lunge = [0, 0];     // where a lunge pulls it
    this.pos = [0, 0];
    this.vel = [0, 0];
    this.emit = 0;
    this.t = 0;
  }

  set(combo) {
    const before = this.combo;
    this.combo = combo;
    if (combo < before && before >= MILESTONES[0]) this.shatter();
    else if (combo < SHOW_FROM) this.hide();
    for (const m of MILESTONES) if (before < m && combo >= m) this.milestone(m);
    if (combo >= SHOW_FROM) {
      this.num.textContent = `x${combo}`;
      if (!this.shown) {
        this.shown = true;
        this.el.classList.remove("gone");
        this.el.style.opacity = "1";
      }
    }
  }

  hide() {
    if (!this.shown) return;
    this.shown = false;
    this.el.style.opacity = "0";
  }

  milestone(m) {
    this.punch = 1;
    this.lunge = [-(14 + m / 8), -(6 + m / 25)];       // out, away from the right edge, and up
    const r = this.el.getBoundingClientRect();
    const [cr, cg, cb] = flameColour(comboHeat(m), 0);
    for (let i = 0; i < (this.monitor.cheap ? 10 : 30); i++) this.layer.spark(r.left + r.width / 2, r.top + r.height / 2, `rgb(${cr},${cg},${cb})`);
  }

  /** A break: the number flies apart, the flames stop. */
  shatter() {
    if (!this.shown) return;
    const r = this.num.getBoundingClientRect();
    const cs = getComputedStyle(this.num);
    const font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const text = this.num.textContent;
    const step = r.width / Math.max(1, text.length);
    const pieces = this.monitor.cheap ? 1 : 3;
    [...text].forEach((ch, i) => {
      for (let k = 0; k < pieces; k++) this.layer.shard(r.left + step * i, r.top + r.height * 0.8, ch, cs.color, font);
    });
    this.shown = false;
    this.el.style.opacity = "0";
    this.el.classList.add("gone");
    this.heat = 0;
  }

  frame(dt) {
    this.t += dt;
    const target = this.shown ? comboHeat(this.combo) : 0;
    this.heat += (target - this.heat) * Math.min(1, dt * 4);
    if (!this.shown) return;
    const heat = this.heat, cheap = this.monitor.cheap;
    this.punch = Math.max(0, this.punch - dt * 2.5);
    // a lunge pulls it towards an edge now and then, more often when hotter; a spring brings it back
    if (heat > 1 && Math.random() < dt * 0.25 * heat) {
      const out = Math.random() < 0.7 ? -1 : 0.4;    // mostly out to the left: it sits at the right edge
      this.lunge = [out * (6 + heat * 7), -(Math.random() * (3 + heat * 3))];
    }
    for (let a = 0; a < 2; a++) {
      const force = (this.lunge[a] - this.pos[a]) * 160 - this.vel[a] * 14;
      this.vel[a] += force * dt;
      this.pos[a] += this.vel[a] * dt;
      this.lunge[a] *= Math.max(0, 1 - dt * 3);
    }
    const shake = heat < 0.5 ? 0 : (heat ** 1.5) * 0.9;
    const jx = (Math.random() - 0.5) * shake, jy = (Math.random() - 0.5) * shake;
    const beat = 1 + heat * 1.3;                           // pulses a second
    const pulse = Math.sin(this.t * Math.PI * 2 * beat) * (0.03 + heat * 0.025);
    const scale = 1 + heat * 0.13 + pulse + this.punch * 0.35;
    const skew = heat > 2.5 && !cheap ? Math.sin(this.t * 23) * (heat - 2.5) * 0.8 : 0;   // heat shimmer
    this.el.style.transform = `translate(${this.pos[0] + jx}px, ${this.pos[1] + jy}px) scale(${scale}) skewX(${skew}deg)`;
    const [r, g, b] = flameColour(heat, 0);
    const strobe = heat > 3 ? 0.85 + 0.4 * (Math.sin(this.t * 40) > 0 ? 1 : 0) : 1;
    this.num.style.color = heat < 0.4 ? "" : `rgb(${Math.min(255, r + 60)},${Math.min(255, g + 60)},${Math.min(255, b + 60)})`;
    this.num.style.textShadow = cheap ? "0 0 3px #000, 0 0 3px #000" : `0 0 3px #000, 0 0 3px #000, 0 0 ${4 + heat * 6}px rgba(${r},${g},${b},${0.5 + heat * 0.1}), 0 0 ${heat * 16}px rgba(${r},${g},${b},0.45)`;
    this.num.style.filter = heat > 3 && !cheap ? `brightness(${strobe})` : "";
    // flames from its base, more and taller step by step
    if (heat > 0.6) {
      const rect = this.num.getBoundingClientRect();
      this.emit += dt * (cheap ? 12 : 30 + heat * 55);
      while (this.emit >= 1) {
        this.emit -= 1;
        // from under the number and its sides, so the flames frame it and never hide it
        const side = Math.random() < 0.3;
        const x = side ? (Math.random() < 0.5 ? rect.left - 4 : rect.right + 4) : rect.left + Math.random() * rect.width;
        const y = side ? rect.top + rect.height * (0.4 + Math.random() * 0.5) : rect.bottom - rect.height * 0.08;
        this.layer.flame(x, y, Math.min(5, heat), 0.4 + heat * 0.14);
      }
    }
  }

  destroy() {
    this.el.remove();
  }
}
