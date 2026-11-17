// The typing screen's effects, so typing feels like an edit (phase 2), all in
// one drawn, motion-graphics style: flat colour bands, dark outlines, hard
// shadows, squash and stretch. Each has its own setting, all off by default:
//   fx_tilt    the words turn a little to the side and go 3D
//   fx_fire    a cartoon flame burns along the line (on a streak / at speed, or always)
//   fx_shine   a band of light sweeps the words now and then, a star twinkles
//   fx_combo   the combo counter escalates: flashes, shakes, burns (combo.js)
//   fx_popin   letters pop in with a squash and stretch on a right key
//   fx_camera  a small camera shake on a wrong key
// Key presses only note what happened; the drawing happens once a frame, so an
// effect never makes a key wait. When frames run slow (fx quality auto) they
// drop to cheap versions: no boil, no flicks, no outlines or extrusion.

import { ComboCounter, MILESTONES, comboHeat } from "./combo.js";
import { FlameRow } from "./flame.js";
import { ParticleLayer } from "./particles.js";
import { Shine } from "./shine.js";

export const FIRE_STREAK = 20;     // correct keys in a row that light the fire on a streak
const WPM_EVERY = 0.25;

let layer = null;                  // the shard canvas, shared by every test screen, made on first use
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
    this.grow = 0;          // the line's flame: how big it burns, eased
    this.bump = 0;          // ...a key's little pulse and a milestone's pop, decaying
    this.squash = 0;
    this.spanKey = "";
    if (s.fx_tilt) {
      view.root.classList.add("fx-tilt");
      view.root.style.setProperty("--tilt", `${s.fx_tilt_angle}deg`);
    }
    if (s.fx_popin) view.root.classList.add("fx-popin");
    this.fireRow = s.fx_fire !== "off" ? new FlameRow(view.words, { className: "line-flame" }) : null;
    if (this.fireRow) view.root.classList.add("fx-fire");
    this.shine = s.fx_shine ? new Shine(view) : null;
    this.counter = s.fx_combo ? new ComboCounter(screen.hud, particles, this.monitor) : null;
  }

  /** A typing key landed: ok when it was right. */
  key(ok, combo) {
    const before = this.combo;
    this.combo = combo;
    this.counter?.set(combo);
    if (ok) this.bump = Math.min(0.35, this.bump + 0.07);
    if (MILESTONES.some((m) => before < m && combo >= m)) {
      this.bump = 0.7;
      this.squash = 1;
    }
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
    this.bump = 0;
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

  /** The line's flame along the caret's line, from its start to the caret. */
  placeFire() {
    const v = this.view;
    const [w, l, i] = v.target();
    if (!w) return;
    const top = w.offsetTop;
    let first = i;
    while (first > 0 && v.wordEls[first - 1]?.offsetTop === top) first--;
    const x0 = v.wordEls[first].offsetLeft;
    const x1 = v.letterX(w, l);
    const key = `${x0}|${x1}|${top}|${v.lineH}`;
    if (key === this.spanKey) return;
    this.spanKey = key;
    const em = parseFloat(getComputedStyle(v.viewport).fontSize) || 28;
    this.fireRow.span(x0, x1, top + v.lineH * 0.76, em);   // the letters' baseline: the flame rises behind them
  }

  frame(now) {
    const dt = this.lastT === null ? 0 : Math.max(0, Math.min(0.05, now - this.lastT));
    this.lastT = now;
    const t = this.screen.test;
    if (t.start !== null && now - this.lastWpm > WPM_EVERY) {
      this.lastWpm = now;
      this.wpm = t.score(now - t.start)[0];
    }
    const cheap = this.monitor.cheap;
    this.view.root.classList.toggle("fx-cheap", cheap);
    this.counter?.el.classList.toggle("fx-cheap", cheap);
    if (layer) layer.cheap = cheap;
    this.shine?.frame(now);
    this.counter?.frame(dt);
    if (this.fireRow) {
      const burn = this.fire();
      const target = burn ? 0.55 + burn * 0.75 : 0;
      this.grow += (target - this.grow) * Math.min(1, dt * (target > this.grow ? 6 : 3));
      this.bump = Math.max(0, this.bump - dt * 1.6);
      this.squash = Math.max(0, this.squash - dt * 3);
      this.placeFire();
      this.fireRow.colours(Math.min(5, comboHeat(this.combo)));
      this.fireRow.size(this.grow * (1 + this.bump), this.squash);
    }
    if (layer?.busy) layer.frame(dt);
  }

  destroy() {
    this.shine?.destroy();
    this.counter?.destroy();
    this.fireRow?.destroy();
    // the chunks of a last break may still be flying: keep drawing them
    if (layer?.busy) {
      let last = performance.now();
      const run = (t) => {
        layer.frame(Math.min(0.05, (t - last) / 1000));
        last = t;
        if (layer.busy) requestAnimationFrame(run);
      };
      requestAnimationFrame(run);
    }
  }
}
