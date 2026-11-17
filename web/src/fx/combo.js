// The combo counter, escalating like a video edit (the fx combo setting):
// it flashes harder, shakes and lunges at the edges of its box, and burns -
// a drawn cartoon flame (flame.js) going red, orange, yellow, white, blue,
// purple, getting bigger step by step at the milestones, with smooth ramps in
// between; each milestone pops a starburst. A break shatters the number and
// the flame dies down. It sits above the words and never covers the line.

import { FlameRow, flameBands } from "./flame.js";

export const MILESTONES = [10, 25, 50, 100, 200];
export const SHOW_FROM = 5;
const OUTLINE = "#1b0f14";

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

/** A starburst: flat rays and a ring, popping out and gone (a milestone). */
function burst(host, colour) {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "-50 -50 100 100");
  svg.setAttribute("class", "burst");
  const rays = 10;
  let d = "";
  for (let i = 0; i < rays * 2; i++) {
    const a = (i / (rays * 2)) * Math.PI * 2 - Math.PI / 2;
    const r = i % 2 ? 18 : 46;
    d += `${i ? "L" : "M"}${(Math.cos(a) * r).toFixed(1)} ${(Math.sin(a) * r).toFixed(1)} `;
  }
  const star = document.createElementNS(NS, "path");
  star.setAttribute("d", d + "Z");
  star.setAttribute("fill", colour);
  star.setAttribute("stroke", OUTLINE);
  star.setAttribute("stroke-width", "4");
  star.setAttribute("stroke-linejoin", "round");
  svg.append(star);
  host.append(svg);
  svg.animate([
    { transform: "scale(0) rotate(-30deg)", opacity: 1 },
    { transform: "scale(1.15) rotate(10deg)", opacity: 1, offset: 0.45 },
    { transform: "scale(1.35) rotate(20deg)", opacity: 0 },
  ], { duration: 520, easing: "cubic-bezier(.2,.9,.3,1.2)" }).onfinish = () => svg.remove();
}

export class ComboCounter {
  /** layer() gives the shard canvas (made only when something shatters). */
  constructor(host, layer, monitor) {
    this.layer = layer;
    this.monitor = monitor;
    this.el = document.createElement("div");
    this.el.className = "combo-fx";
    this.num = document.createElement("span");
    this.num.className = "combo-num";
    this.flame = new FlameRow(this.el, { flicks: 2, className: "combo-flame" });
    this.el.append(this.num);
    host.append(this.el);
    this.combo = 0;
    this.shown = false;
    this.heat = 0;           // eased towards the combo's heat
    this.punch = 0;          // a milestone's kick, decaying
    this.lunge = [0, 0];     // where a lunge pulls it
    this.pos = [0, 0];
    this.vel = [0, 0];
    this.t = 0;
    this.width = 0;
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
    if (!this.monitor.cheap) burst(this.el, flameBands(comboHeat(m))[1]);
  }

  /** A break: the number flies apart in outlined chunks, the flame dies down. */
  shatter() {
    if (!this.shown) return;
    const r = this.num.getBoundingClientRect();
    const cs = getComputedStyle(this.num);
    const font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const text = this.num.textContent;
    const step = r.width / Math.max(1, text.length);
    const pieces = this.monitor.cheap ? 1 : 2;
    const layer = this.layer();
    [...text].forEach((ch, i) => {
      for (let k = 0; k < pieces; k++) layer.shard(r.left + step * i, r.top + r.height * 0.8, ch, cs.color, font, OUTLINE);
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
    this.el.style.transform = `translate(${this.pos[0] + jx}px, ${this.pos[1] + jy}px) scale(${scale})`;
    const [, mid, core] = flameBands(heat);
    const strobe = heat > 3 && !cheap && Math.sin(this.t * 40) > 0;
    this.num.style.color = heat < 0.4 ? "" : strobe ? "#ffffff" : core;
    this.num.style.setProperty("--num-shadow", heat < 0.4 ? "var(--accent)" : mid);
    // the flame behind it: taller, wider and hotter step by step
    const w = this.num.offsetWidth;
    if (w !== this.width) {
      this.width = w;
      const em = parseFloat(getComputedStyle(this.num).fontSize) * 0.62;
      this.flame.span(-w * 0.1, w * 1.1, this.num.offsetHeight * 0.92, em);
    }
    this.flame.colours(Math.min(5, heat));
    this.flame.size(heat < 0.6 ? 0 : 0.6 + heat * 0.22 + this.punch * 0.5, this.punch);
  }

  destroy() {
    this.el.remove();
  }
}
