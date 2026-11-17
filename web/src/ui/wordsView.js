// The words on the typing screen (engine/render.py for the browser): every
// letter a span whose class says how it was typed, a caret that glides to the
// next letter, and lines that scroll smoothly instead of jumping. Used by the
// test and by the replay.
//
// The theme's fun modifiers only change looks, never what you type:
//   pop      the last few typed letters bright and bold
//   fade     typed letters far behind the caret go dim
//   glitch   untyped letters well ahead flicker to symbols now and then
//   bounce   letters bob (gentle: near the caret, wild: all of them)
//   shake    the text jolts sideways after a wrong key
//   caret    pulse blinks it, rainbow cycles its colour

import { h } from "./dom.js";
import { HEAT_STEP, typedColour } from "./theme.js";

export const POP_LEN = 3;
export const FADE_FROM = 12;
export const GLITCH_SAFE = 3;
export const GLITCH_ODDS = 45;
export const GLITCH_GLYPHS = "#%&@$*?!<>/\\=+";
export const BOB_RANGE = 8;
const NEAR = 6;            // words either side of the caret the effects look at

export class WordsView {
  constructor(st, settings, { tape = settings.tape } = {}) {
    this.st = st;
    this.s = settings;
    this.tapeMode = tape;
    this.typos = settings.blind ? "off" : settings.typos;
    this.root = h("div.wordsbox");
    this.words = h("div.words");
    this.caret = h("div.caret");
    this.caret.classList.add(settings.caret);
    this.marks = new Map();       // name -> element: the pace and ghost carets
    this.viewport = h("div.viewport", this.words);
    this.stage = h("div.stage", this.viewport);
    this.root.append(this.stage);
    const cls = this.root.classList;
    if (this.tapeMode !== "off") cls.add("tape");
    if (this.typos === "below" || this.typos === "both") cls.add("typos-below");
    if (settings.funbox === "mirror") cls.add("mirror");
    cls.add(`gap-${settings.word_gap}`);
    if (st.fx.bounce === "wild") cls.add("bounce-wild");
    if (st.fx.bold) cls.add("bold-text");
    if (st.fx.italic) cls.add("italic-text");
    if (st.fx.caret === "pulse") this.caret.classList.add("pulse");
    if (st.fx.caret === "rainbow") this.caret.classList.add("rainbow");
    this.wordEls = [];
    this.gapEls = [];
    this.state = null;
    this.flagged = new Set();     // letters wearing pop / faded / bob
    this.glitched = [];
    this.scrollY = 0;
    this.lastGlitch = 0;
    this.lastFlow = 0;
    this.lineH = 0;
  }

  /** The whole text from scratch. state: {words, typed, wi, errors, typos, combo, wrong, hidden} */
  set(state) {
    this.state = state;
    this.words.replaceChildren();
    this.wordEls = [];
    this.gapEls = [];
    this.flagged.clear();
    this.append(0);
    this.words.append(this.caret);
    this.place(true);
  }

  /** Words added at the end (a timed test topping up). */
  append(from) {
    const frag = document.createDocumentFragment();
    for (let i = from; i < this.state.words.length; i++) {
      const w = h("span.w"), g = h("span.g");
      this.wordEls[i] = w;
      this.gapEls[i] = g;
      this.renderWord(i, w);
      frag.append(w, g);
    }
    this.words.insertBefore(frag, this.caret.parentNode === this.words ? this.caret : null);
  }

  offsets() {
    const { words, typed } = this.state;
    const offs = [];
    let g = 0;
    for (let i = 0; i < words.length; i++) {
      offs.push(g);
      g += Math.max(words[i].length, (typed[i] ?? "").length) + 1;
    }
    return offs;
  }

  renderWord(i, el = this.wordEls[i]) {
    const { words, typed, wi, errors, typos, wrong, combo } = this.state;
    const w = words[i] ?? "", t = typed[i] ?? "";
    const blind = this.s.blind;
    const now = performance.now() / 1000;
    const n = Math.max(w.length, t.length);
    // letters are reused, not rebuilt: an effect running on one (pop-in) carries on
    while (el.children.length > n) el.lastChild.remove();
    for (let j = 0; j < n; j++) {
      const wc = j < w.length ? w[j] : undefined;
      const tc = j < t.length ? t[j] : undefined;
      let c = wc ?? tc;
      let cls = "";
      let below = null, belowDim = false;
      const key = `${i},${j}`;
      if (tc === undefined) {
        if (i < wi && !blind) cls = "missed";
        if (i === wi && j === t.length && wrong && (this.typos === "below" || this.typos === "both") && typos[key]) below = typos[key];
      } else if (blind) cls = "ok";
      else if (wc === undefined) cls = "extra";
      else if (tc === wc) {
        cls = "ok";
        if (errors.has(key)) {
          if (this.s.corrected === "red") cls = "bad";
          else if (this.s.corrected === "marked") cls = "fixed";
        }
      } else {
        cls = "bad";
        if (this.typos === "below") below = tc;
        else if (this.typos === "both") { below = wc; belowDim = true; }
        if (this.typos === "replace" || this.typos === "both") c = tc;
      }
      let l = el.children[j];
      if (!l) {
        l = document.createElement("span");
        l._base = null;
        el.append(l);
      }
      const base = cls + (belowDim ? " below-dim" : "");
      if (l._base !== base) {
        l.className = base ? `l ${base}` : "l";
        l._base = base;
        l.style.color = "";
      }
      if (l.dataset.real === undefined ? l.textContent !== c : l.dataset.real !== c) {
        l.textContent = c;
        delete l.dataset.real;
      }
      const b = below === null ? undefined : below === " " ? "_" : below;
      if (l.dataset.below !== b) {
        if (b === undefined) delete l.dataset.below;
        else l.dataset.below = b;
      }
      if (cls === "ok" && this.st.fx.gradient.length && !this.st.fx.heat.length) {
        l.style.color = typedColour(this.st, i * 6 + j, i, combo, now);
      }
    }
  }

  /** What a key changed: the words from..to (inclusive) and the caret. */
  update(state, from, to) {
    const grew = state.words.length > this.wordEls.length;
    this.state = state;
    if (grew) this.append(this.wordEls.length);
    for (let i = Math.max(0, from); i <= Math.min(to, state.words.length - 1); i++) this.renderWord(i);
    if (this.st.fx.heat.length) {
      const heat = this.st.fx.heat;
      this.words.style.setProperty("--ok", heat[Math.min(Math.floor(state.combo / HEAT_STEP), heat.length - 1)]);
    }
    this.caret.classList.toggle("wrong", Boolean(state.wrong) && !this.s.blind);
    this.root.classList.toggle("hide-untyped", Boolean(state.hidden));
    this.place();
    this.flourish();
  }

  /** The element the caret sits on: [word el, letter el or null, index]. */
  target() {
    const { words, typed, wi } = this.state;
    const i = Math.min(wi, words.length - 1);
    if (i < 0) return [null, null];
    const w = this.wordEls[i];
    const j = wi >= words.length ? Infinity : (typed[i] ?? "").length;
    return [w, w?.children[j] ?? null, i];
  }

  letterX(w, l) {
    if (!l) return w.offsetLeft + w.offsetWidth;
    if (this.s.funbox === "mirror") return w.offsetLeft + w.offsetWidth - l.offsetLeft - l.offsetWidth;
    return w.offsetLeft + l.offsetLeft;
  }

  /** Move the caret and the lines to where the typing is. */
  place(instant = false) {
    const [w, l] = this.target();
    if (!w) return;
    const x = this.letterX(w, l);
    const y = w.offsetTop;
    const width = l ? l.offsetWidth : (this.gapEls[0]?.offsetWidth || 10);
    this.lineH = w.offsetHeight || this.lineH;
    if (instant) {
      this.caret.style.transition = "none";
      this.words.style.transition = "none";
    }
    // a new line: the caret jumps there instead of gliding across the lines in between
    const jump = !instant && this.caretY !== undefined && y !== this.caretY;
    this.caretY = y;
    if (jump) this.caret.style.transition = "none";
    this.caret.style.transform = `translate(${x}px, ${y}px)`;
    if (jump) {
      void this.caret.offsetWidth;
      this.caret.style.transition = "";
    }
    this.caret.style.width = `${width}px`;
    this.caret.style.height = this.s.caret === "block" ? `${Math.round(this.lineH * 0.82)}px` : "";
    if (this.tapeMode !== "off") {
      const vw = this.viewport.clientWidth;
      const tx = this.tapeMode === "from middle" ? vw / 2 - x : Math.min(0, vw / 3 - x);
      this.words.style.transform = `translateX(${tx}px)`;
    } else {
      const last = this.wordEls[this.wordEls.length - 1];
      const total = last ? last.offsetTop + this.lineH : 0;
      const top = Math.max(0, Math.min(y - this.lineH, total - 3 * this.lineH));
      if (top !== this.scrollY || instant) {
        this.scrollY = top;
        this.words.style.transform = `translateY(${-top}px)`;
      }
    }
    if (instant) {
      void this.words.offsetWidth;
      this.caret.style.transition = "";
      this.words.style.transition = "";
    }
  }

  /** A dim caret at a char offset (pace, ghost); null hides it. */
  mark(name, off) {
    let el = this.marks.get(name);
    if (off === null || off === undefined) {
      if (el) el.hidden = true;
      return;
    }
    if (!el) {
      el = h("div.mark");
      if (name === "ghost") el.classList.add("ghost");
      this.marks.set(name, el);
      this.words.append(el);
    }
    const offs = this.offsets();
    let i = offs.length - 1;
    while (i > 0 && offs[i] > off) i--;
    const w = this.wordEls[i];
    if (!w) return;
    const j = off - offs[i];
    const l = w.children[j] ?? null;
    el.hidden = false;
    el.style.transform = `translate(${this.letterX(w, l)}px, ${w.offsetTop}px)`;
    el.style.width = `${l ? l.offsetWidth : 10}px`;
  }

  shake() {
    if (!this.st.fx.shake) return;
    this.root.classList.remove("shake-text");
    void this.root.offsetWidth;
    this.root.classList.add("shake-text");
  }

  /** pop, fade and gentle bounce around the caret. */
  flourish() {
    const fx = this.st.fx;
    if (!fx.pop && !fx.fade && fx.bounce !== "gentle") return;
    for (const l of this.flagged) l.classList.remove("pop", "bob");
    this.flagged.clear();
    const { wi, typed, words } = this.state;
    const offs = this.offsets();
    const caret = wi < words.length ? offs[wi] + (typed[wi] ?? "").length : Infinity;
    for (let i = Math.max(0, wi - NEAR); i <= Math.min(words.length - 1, wi + 2); i++) {
      const w = this.wordEls[i];
      if (!w) continue;
      for (let j = 0; j < w.children.length; j++) {
        const l = w.children[j];
        const d = caret - (offs[i] + j);
        const ok = l.classList.contains("ok");
        if (ok && fx.pop && d > 0 && d <= POP_LEN) { l.classList.add("pop"); this.flagged.add(l); }
        if (fx.fade) l.classList.toggle("faded", ok && d > FADE_FROM);
        if (fx.bounce === "gentle" && Math.abs(d) <= BOB_RANGE) {
          l.style.setProperty("--i", offs[i] + j);
          l.classList.add("bob");
          this.flagged.add(l);
        }
      }
    }
  }

  /** Per-frame bits: glitch flickers, a flowing gradient. */
  frame(now) {
    const fx = this.st.fx;
    if (!this.state) return;
    if (fx.glitch && now - this.lastGlitch > 0.125) {
      this.lastGlitch = now;
      for (const l of this.glitched) {
        if (l.dataset.real !== undefined) l.textContent = l.dataset.real;
        delete l.dataset.real;
        l.classList.remove("glitch");
      }
      this.glitched = [];
      const { wi, typed, words } = this.state;
      for (let i = wi; i < Math.min(words.length, wi + 12); i++) {
        const w = this.wordEls[i];
        const from = i === wi ? (typed[i] ?? "").length + GLITCH_SAFE : 0;
        for (let j = from; j < (w?.children.length ?? 0); j++) {
          if (Math.random() * GLITCH_ODDS < 1) {
            const l = w.children[j];
            if (l.className !== "l") continue;
            l.dataset.real = l.textContent;
            l.textContent = GLITCH_GLYPHS[Math.floor(Math.random() * GLITCH_GLYPHS.length)];
            l.classList.add("glitch");
            this.glitched.push(l);
          }
        }
      }
    }
    if (fx.gradient.length && fx.flow && !fx.heat.length && now - this.lastFlow > 1 / Math.min(12, Math.abs(fx.flow * fx.speed) * 2 || 1)) {
      this.lastFlow = now;
      const { wi, combo } = this.state;
      for (let i = Math.max(0, wi - 40); i <= Math.min(wi, this.wordEls.length - 1); i++) {
        const w = this.wordEls[i];
        for (let j = 0; j < w.children.length; j++) {
          const l = w.children[j];
          if (l.classList.contains("ok")) l.style.color = typedColour(this.st, i * 6 + j, i, combo, now);
        }
      }
    }
  }

  /** Re-measure (the window changed size). */
  relayout() {
    if (this.state) this.place(true);
  }
}
