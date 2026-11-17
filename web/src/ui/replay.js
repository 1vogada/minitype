// Watch a finished test again (ui/replay.py): it plays back as it was typed,
// space pauses, ←/→ seek a second, esc goes back to the results.

import { h, NAV } from "./dom.js";
import { WordsView } from "./wordsView.js";

export class ReplayScreen {
  constructor(ui, result) {
    this.ui = ui;
    this.app = ui.app;
    this.r = result;
    this.rep = result.replay;
    this.navName = "menu";
    this.hints = "space pause   ←/→ seek   home start   esc back";
    this.t = 0;
    this.playing = true;
    this.lastFrame = null;
    this.view = new WordsView(ui.st, this.app.settings, { tape: this.rep.tape });
    this.info = h("span");
    this.slider = h("input", { type: "range", min: 0, max: Math.max(0.01, this.rep.length), step: 0.01, value: 0,
      on: { input: () => { this.t = +this.slider.value; this.draw(); } } });
    this.playBtn = h("button.btn", { on: { click: () => this.toggle() } }, "pause");
    this.el = h("div.test", h("div.hud", h("span", `replay · ${result.spec.label}`), this.info), this.view.root,
      h("div.replay-bar", this.playBtn, this.slider, h("button.btn", { on: { click: () => this.ui.go(this.r) } }, "back")));
    this.view.set(this.stateAt(0));
  }

  stateAt(t) {
    const s = this.rep.at(t);
    return { words: this.rep.words, typed: s.typed, wi: s.wi, errors: s.errors, typos: s.typos, combo: s.combo, wrong: s.wrong, hidden: false, keys: s.keys };
  }

  draw() {
    const st = this.stateAt(this.t);
    this.view.update(st, 0, this.rep.words.length - 1);
    this.slider.value = this.t;
    this.info.textContent = `${this.t.toFixed(1)}s / ${this.rep.length.toFixed(1)}s   ${this.rep.wpm(st.typed, this.t).toFixed(0)} wpm   ${st.keys} keys`;
    this.keysShown = st.keys;
  }

  toggle() {
    if (!this.playing && this.t >= this.rep.length) this.t = 0;
    this.playing = !this.playing;
    this.playBtn.textContent = this.playing ? "pause" : "play";
  }

  onKey(key) {
    if (key === "ESC" || key === "r") return this.ui.go(this.r);
    if (key === " " || key === "ENTER") return this.toggle();
    if (key === NAV.LEFT) this.t = Math.max(0, this.t - 1);
    if (key === NAV.RIGHT) this.t = Math.min(this.rep.length, this.t + 1);
    if (key === NAV.HOME) this.t = 0;
    this.draw();
  }

  frame(now) {
    const dt = this.lastFrame === null ? 0 : (now - this.lastFrame) / 1000;
    this.lastFrame = now;
    if (!this.playing) return;
    const before = this.rep.at(this.t).keys;
    this.t = Math.min(this.rep.length, this.t + dt);
    if (this.rep.at(this.t).keys !== before || Math.floor(this.t * 10) !== Math.floor((this.t - dt) * 10)) this.draw();
    if (this.t >= this.rep.length) this.toggle();
  }
}
