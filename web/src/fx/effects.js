// The typing screen's effects, so typing feels like an edit (phase 2). Each
// has its own setting, all off by default:
//   fx_tilt    the words turn a little to the side and go 3D
//   fx_fire    the line is set ablaze (on a streak / at speed, or always)
//   fx_shine   a band of light sweeps the words now and then, a star twinkles
//   fx_combo   the combo counter escalates: flashes, shakes, burns (combo.js)
//   fx_popin   letters pop in on a right key
//   fx_camera  a small camera shake on a wrong key
// Key presses only note what happened; the drawing happens once a frame, so
// an effect never makes a key wait. When frames run slow (fx quality auto)
// the effects drop to cheap versions: fewer particles, no glow, no extrusion.

import { ComboCounter, comboHeat } from "./combo.js";
import { ParticleLayer } from "./particles.js";
import { Shine } from "./shine.js";

export const FIRE_STREAK = 20;     // correct keys in a row that light the fire on a streak
const WPM_EVERY = 0.25;

let layer = null;                  // the particle canvas, shared by every test screen
function particles() {
  layer ??= new ParticleLayer();
  return layer;
}

export class Effects {
  constructor(ui, view, screen) {
    this.ui = ui;
    this.view = view;
    this.screen = screen;
    const s = ui.app.settings;
    this.s = s;
    this.monitor = ui.fx;
    this.combo = 0;
    this.wpm = 0;
    this.lastWpm = 0;
    this.lastT = null;
    this.emit = 0;
    const any = s.fx_fire !== "off" || s.fx_combo;
    this.layer = any ? particles() : null;
    if (s.fx_tilt) {
      view.root.classList.add("fx-tilt");
      view.root.style.setProperty("--tilt", `${s.fx_tilt_angle}deg`);
    }
    if (s.fx_popin) view.root.classList.add("fx-popin");
    this.shine = s.fx_shine ? new Shine(view) : null;
    this.counter = s.fx_combo ? new ComboCounter(screen.hud, this.layer, this.monitor) : null;
  }

  /** A typing key landed: ok when it was right. */
  key(ok, combo) {
    this.combo = combo;
    this.counter?.set(combo);
    if (ok && this.s.fx_popin) {
      const [w, l] = this.view.target();
      const typed = l ? l.previousElementSibling : w?.lastElementChild;
      if (typed && typed.classList.contains("ok")) {
        typed.classList.remove("popin");
        void typed.offsetWidth;
        typed.classList.add("popin");
      }
    }
  }

  miss() {
    this.combo = 0;
    this.counter?.set(0);
    if (this.s.fx_camera) {
      const k = this.monitor.cheap ? 2 : 4;
      document.getElementById("screen").animate([
        { translate: "0 0" }, { translate: `${k}px ${-k / 2}px` }, { translate: `${-k}px ${k / 2}px` },
        { translate: `${k / 2}px 0` }, { translate: "0 0" },
      ], { duration: 220, easing: "ease-out" });
    }
  }

  /** Whether the line burns now, and how hard (0..1). */
  fire() {
    const mode = this.s.fx_fire;
    if (mode === "off") return 0;
    const heat = Math.min(1, 0.25 + comboHeat(this.combo) / 5);
    if (mode === "always") return this.screen.test.start === null ? 0.25 : heat;
    const streak = this.combo >= FIRE_STREAK || (this.wpm >= this.s.fx_fire_wpm && this.combo >= 5);
    return streak ? heat : 0;
  }

  frame(now) {
    const dt = this.lastT === null ? 0 : Math.min(0.05, now - this.lastT);
    this.lastT = now;
    const t = this.screen.test;
    if (t.start !== null && now - this.lastWpm > WPM_EVERY) {
      this.lastWpm = now;
      this.wpm = t.score(now - t.start)[0];
    }
    const cheap = this.monitor.cheap;
    this.view.root.classList.toggle("fx-cheap", cheap);
    if (this.layer) this.layer.cheap = cheap;
    this.shine?.frame(now);
    this.counter?.frame(dt);
    const burn = this.fire();
    if (burn > 0 && this.layer) {
      const vp = this.view.viewport.getBoundingClientRect();
      const caret = this.view.caret.getBoundingClientRect();
      const left = vp.left, right = Math.max(left + 20, caret.left);
      this.emit += dt * (cheap ? 25 : 60 + burn * 160);
      const heat = comboHeat(this.combo);
      while (this.emit >= 1) {
        this.emit -= 1;
        const x = left + Math.random() * (right - left);
        // from the line's baseline up through its letters
        const base = this.s.caret === "underline" ? caret.top - caret.height * 0.1 : caret.bottom - caret.height * 0.12;
        this.layer.flame(x, base, Math.min(5, heat), 0.5 + burn * 0.7);
      }
    }
    if (this.layer && (this.layer.busy || burn)) this.layer.frame(dt);
  }

  destroy() {
    this.shine?.destroy();
    this.counter?.destroy();
    // the shards of a last break may still be flying: the layer keeps drawing them
    if (this.layer) {
      const l = this.layer;
      let last = performance.now();
      const run = (t) => {
        l.frame(Math.min(0.05, (t - last) / 1000));
        last = t;
        if (l.busy) requestAnimationFrame(run);
      };
      requestAnimationFrame(run);
    }
  }
}
