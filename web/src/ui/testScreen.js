// The typing screen (engine/runner.py's run_test for the browser). Keys are
// timed by the event's own timestamp, so a slow frame never lowers your speed;
// the screen redraws only what a key changed.

import { KEY, MENU, QUIT, LEARN_MIN_ACC, keystrokeAccuracy, newTest } from "../core/test.js";
import { LAYOUTS, ORDER } from "../core/config.js";
import { beep, h, keyTime, nowSecs, NAV } from "./dom.js";
import { WordsView } from "./wordsView.js";
import { Effects } from "../fx/effects.js";

const HUD_EVERY = 0.1;    // seconds between header updates

export const FOOTER = "esc menu   tab restart   ctrl-bksp word   ctrl-o settings";
export const ZEN_FOOTER = "enter finish   esc menu   ctrl-o settings";

/** The on-screen keyboard (engine/keyboard.py): the next key lit; in learn
 * mode keys coloured by confidence, otherwise your bad keys in red. */
export class KeyboardView {
  constructor(layout) {
    this.keys = new Map();
    this.el = h("div.kb");
    for (const [r, row] of (LAYOUTS[layout] ?? LAYOUTS.qwerty).entries()) {
      const rowEl = h("div.krow", { style: { marginLeft: `${r * 0.6}em` } });
      for (const c of row) {
        const k = h("div.k", c);
        this.keys.set(c, k);
        rowEl.append(k);
      }
      this.el.append(rowEl);
    }
    const space = h("div.k.space", "space");
    this.keys.set(" ", space);
    this.el.append(h("div.krow", space));
    this.lit = null;
  }

  next(c) {
    const k = this.keys.get(c ? c.toLowerCase() : null) ?? null;
    if (k === this.lit) return;
    this.lit?.classList.remove("next");
    k?.classList.add("next");
    this.lit = k;
  }

  colour(colours, under = []) {
    for (const [c, k] of this.keys) {
      k.style.color = colours[c] ?? "";
      k.style.borderColor = colours[c] ?? "";
      k.classList.toggle("under", under.includes(c));
    }
  }
}

export class TestScreen {
  constructor(ui, spec) {
    this.ui = ui;
    this.app = ui.app;
    this.navName = "menu";
    this.takesAllKeys = true;
    this.test = newTest(this.app, spec);
    this.hints = spec.kind === "zen" ? ZEN_FOOTER : FOOTER;
    this.test.onMiss = () => this.missed();
    this.ended = false;
    this.pausedAt = null;
    this.el = h("div.test", { tabindex: "-1" });
    this.build();
  }

  build() {
    const st = this.ui.restyle();
    const s = this.app.settings;
    this.view = new WordsView(st, s);
    this.hud = h("div.hud");
    this.hudParts = {
      label: h("span", this.test.spec.label),
      timer: h("span.big"),
      left: h("span"),
      progress: h("span"),
      wpm: h("span.wpm"),
      combo: h("span.combo"),
      note: h("span.note"),
    };
    this.hud.append(...Object.values(this.hudParts));
    const showKb = s.lowkey === "off" && (s.keyboard === "always" || (s.keyboard === "learn" && this.test.learning));
    this.kb = showKb ? new KeyboardView(s.layout) : null;
    this.el.replaceChildren(this.hud, this.view.root, ...(this.kb ? [this.kb.el] : []));
    this.effects?.destroy();
    this.effects = new Effects(this.ui, this.view, this);
    this.view.set(this.state());
    this.colourKeyboard();
    this.lastHud = 0;
    this.drawHud(nowSecs());
  }

  state(now = nowSecs()) {
    const t = this.test;
    return {
      words: t.words, typed: t.typed, wi: t.wi, errors: t.errMarks, typos: t.typoKeys,
      combo: t.combo, wrong: t.wrong, hidden: t.hidden(now),
    };
  }

  colourKeyboard() {
    if (!this.kb) return;
    const st = this.ui.st;
    if (this.test.learning) {
      const learn = this.app.learn;
      const colours = {};
      for (const c of ORDER.slice(0, learn.unlocked())) {
        const v = learn.conf(c);
        colours[c] = v === null ? st.accent : v >= 1 ? st.good : v >= 0.6 ? st.warn : st.error;
      }
      const foc = learn.focusKey();
      this.kb.colour(colours, foc ? [foc] : []);
    } else {
      this.kb.colour(Object.fromEntries(this.app.stats.badKeys().map((c) => [c, st.error])));
    }
    this.kb.next(this.test.nextChar());
  }

  missed() {
    if (this.app.settings.sound) beep();
    this.view.shake();
    this.effects.miss();
  }

  shown() {
    this.el.focus({ preventScroll: true });
    this.onMouse = () => document.getElementById("app").classList.remove("hidden-ui");
    window.addEventListener("mousemove", this.onMouse);
    this.onResize = () => this.view.relayout();
    window.addEventListener("resize", this.onResize);
  }

  destroy() {
    window.removeEventListener("mousemove", this.onMouse);
    window.removeEventListener("resize", this.onResize);
    document.getElementById("app").classList.remove("hidden-ui");
    this.effects?.destroy();
    if (!this.ended) this.sendKeystrokes();
  }

  // ctrl-o: the settings over the test; the clock stops meanwhile
  pause() { this.pausedAt = nowSecs(); }

  resume() {
    if (this.pausedAt !== null && this.test.start !== null) this.test.resumeAfter(nowSecs() - this.pausedAt);
    this.pausedAt = null;
    this.build();
    this.shown();
  }

  async onKey(key, e) {
    if (this.ended || this.pausing) return;
    const t = this.test;
    const s = this.app.settings;
    const at = keyTime(e);
    if (key === KEY.ESC && s.esc_pause && t.start !== null) return this.pauseDialog();
    if (key === NAV.SHIFT_TAB) key = KEY.TAB;
    if ([NAV.UP, NAV.DOWN, NAV.LEFT, NAV.RIGHT, NAV.PGUP, NAV.PGDN, NAV.HOME, NAV.END, NAV.DELETE].includes(key)) key = "OTHER";
    const before = t.wi, beforeCombo = t.combo, beforeLen = t.words.length;
    const nav = t.handle(key, at);
    t.recorder.snap(t, at);
    if (nav !== null) return this.leave(nav);
    if (t.start !== null && key.length === 1) document.getElementById("app").classList.add("hidden-ui");
    t.topUp();
    const from = Math.min(before, t.wi), to = Math.max(before, t.wi);
    this.view.update(this.state(at), from - (t.words.length !== beforeLen ? 0 : 0), to);
    if (this.kb) this.kb.next(t.nextChar());
    if (key.length === 1) this.effects.key(t.combo > beforeCombo, t.combo);
    if (t.finished(nowSecs())) this.finish();
  }

  async pauseDialog() {
    this.pausing = true;
    const paused = nowSecs();
    const yes = await this.ui.dialog("Paused - resume?", null,
      [{ label: "yes", value: true, key: "y" }, { label: "no", value: false, key: "n" }], { cancel: false });
    this.pausing = false;
    if (yes) {
      this.test.resumeAfter(nowSecs() - paused);
      return;
    }
    this.leave(MENU);
  }

  leave(nav) {
    this.ended = true;
    this.sendKeystrokes();
    this.ui.go(nav === QUIT ? MENU : nav);
  }

  finish() {
    if (this.ended) return;
    this.ended = true;
    const result = this.test.result(nowSecs());
    this.sendKeystrokes();
    this.ui.go(result);
  }

  /** The test's keystrokes to the keyboard app, in the background. */
  sendKeystrokes() {
    const t = this.test;
    if (!t.keystrokes?.length || !this.app.settings.keyboard_learn) return;
    const events = t.keystrokes;
    t.keystrokes = [];
    if (keystrokeAccuracy(events) < LEARN_MIN_ACC) return;   // mashing, wrong layout: not learnt from
    this.app.keyboard.postEvents(events);
  }

  drawHud(now) {
    const t = this.test, s = this.app.settings, p = this.hudParts;
    const started = t.start !== null;
    const el = started ? now - t.start : 0;
    p.timer.textContent = started && s.show_timer ? (t.spec.kind === "time" ? `${Math.max(0, Math.ceil(t.spec.amount - el))}` : `${el.toFixed(1)}s`) : "";
    p.left.textContent = "";
    p.progress.textContent = s.show_progress && t.spec.kind === "words" ? `${t.wi}/${t.words.length}` : "";
    p.wpm.textContent = started && s.show_wpm ? `${t.score(el)[0].toFixed(0)} wpm` : "";
    const racing = s.ghost && this.app.stats.ghost.length;
    p.combo.textContent = started && s.show_combo && t.combo > 4 && !racing && !s.fx_combo ? `x${t.combo}` : "";
    const flags = [t.diff !== "normal" ? t.diff : "", t.stop !== "off" ? `stop ${t.stop}` : "", s.blind ? "blind" : "", s.funbox !== "off" ? s.funbox : ""].filter(Boolean);
    p.note.textContent = flags.length ? `[${flags.join(" ")}]` : t.note ? t.note : "";
    if (s.lowkey === "minimal") this.hud.style.visibility = "hidden";
    // the pace and ghost carets
    this.view.mark("pace", started && s.pace ? Math.floor((s.pace * 5 / 60) * el) : null);
    this.view.mark("ghost", started && racing ? this.app.stats.ghostChars(el) : null);
    this.view.caret.classList.toggle("idle", !started);
  }

  frame() {
    if (this.ended || this.pausedAt !== null) return;
    const now = nowSecs();
    const t = this.test;
    if (!this.pausing) {
      t.checkRules(now);
      if (t.finished(now)) return this.finish();
    }
    if (now - this.lastHud >= HUD_EVERY) {
      this.lastHud = now;
      this.drawHud(now);
      const hidden = t.hidden(now);
      if (hidden !== this.view.root.classList.contains("hide-untyped")) this.view.root.classList.toggle("hide-untyped", hidden);
    }
    this.view.frame(now);
    this.effects.frame(now);
  }
}
