// The typing screen's effects, so typing feels like an edit (phase 2), all in
// one drawn, motion-graphics style: flat colour bands, dark outlines, hard
// shadows, squash and stretch. Each has its own setting, all off by default:
//   fx_tilt    the words turn a little to the side and go 3D
//   fx_fire    the typed words give off cartoon flames, climbing in tiers (textFire.js)
//   fx_shine   a band of light sweeps the words now and then, a star twinkles
//   fx_combo   the combo counter escalates: flashes, shakes, burns (combo.js)
//   fx_popin   letters pop in with a squash and stretch on a right key
//   fx_camera  a small camera shake on a wrong key
// Key presses only note what happened; the drawing happens once a frame, so an
// effect never makes a key wait. When frames run slow (fx quality auto) they
// drop to cheap versions: no boil, no flicks, no outlines or extrusion.

import { ComboCounter, MILESTONES, comboHeat } from "./combo.js";
import { TextFire } from "./textFire.js";
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
    this.bump = 0;          // the fire's little pulse on a key and pop at a new tier, decaying
    this.squash = 0;
    this.tier = -1;         // the fire's tier, -1 out
    if (s.fx_tilt) {
      view.root.classList.add("fx-tilt");
      view.root.style.setProperty("--tilt", `${s.fx_tilt_angle}deg`);
    }
    if (s.fx_popin) view.root.classList.add("fx-popin");
    this.textFire = s.fx_fire !== "off" ? new TextFire(view) : null;
    if (this.textFire) view.root.classList.add("fx-fire");
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

  /** A shake of the screen, k px, ms long. */
  shake(k, ms) {
    document.getElementById("screen")?.animate([
      { translate: "0 0" }, { translate: `${k}px ${-k / 2}px` }, { translate: `${-k}px ${k / 2}px` },
      { translate: `${k / 2}px ${-k / 3}px` }, { translate: "0 0" },
    ], { duration: ms, easing: "ease-out" });
  }

  miss() {
    this.combo = 0;
    this.counter?.set(0);
    this.bump = 0;
    if (this.s.fx_camera) {
      this.shake(this.monitor.cheap ? 2 : 4, 220);
    }
  }

  /** Whether the text burns now, and how hard (0..1). */
  burn() {
    const mode = this.s.fx_fire;
    if (mode === "off") return 0;
    const heat = Math.min(1, 0.25 + comboHeat(this.combo) / 5);
    if (mode === "always") return this.screen.test.start === null ? 0.25 : heat;
    const streak = this.combo >= FIRE_STREAK || (this.wpm >= this.s.fx_fire_wpm && this.combo >= 5);
    return streak ? heat : 0;
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
    if (this.textFire) {
      const burn = this.burn();
      this.bump = Math.max(0, this.bump - dt * 1.6);
      this.squash = Math.max(0, this.squash - dt * 3);
      const look = this.textFire.frame(dt, { burn, combo: this.combo, bump: this.bump, squash: this.squash, cheap });
      // a new tier (or the fire lighting): the flames punch up and the screen shakes, harder the hotter
      const tier = burn && look ? look.tier : -1;
      if (tier > this.tier) {
        this.bump = 0.7;
        this.squash = 1;
        this.shake(look.shake * (cheap ? 0.5 : 1), 150 + 30 * tier);
      }
      this.tier = tier;
    }
    if (layer?.busy) layer.frame(dt);
  }

  destroy() {
    this.shine?.destroy();
    this.counter?.destroy();
    this.textFire?.destroy();
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
