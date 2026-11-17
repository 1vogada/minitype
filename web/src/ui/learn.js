// Learn mode's menu (ui/learn_menu.py): the letters and how close each is to
// the target, the focus key, the lesson's options, and starting a lesson.

import { ORDER } from "../core/config.js";
import { LENGTHS, START_LETTERS, TARGETS } from "../core/learn.js";
import { cycle } from "../core/settings.js";
import { MENU, makeSpec } from "../core/test.js";
import { h } from "./dom.js";
import { RowList } from "./rows.js";

export class LearnScreen {
  constructor(ui) {
    this.ui = ui;
    this.app = ui.app;
    this.navName = "learn";
    this.hints = "enter start a lesson   ←/→ change   esc back";
    const learn = this.app.learn, cfg = learn.config;
    const save = () => this.app.save();
    const flag = (name, label, help) => ({
      label, help, value: () => (cfg[name] ? "on" : "off"),
      left: () => { cfg[name] = !cfg[name]; save(); }, right: () => { cfg[name] = !cfg[name]; save(); },
    });
    this.list = new RowList([
      { key: "ENTER", label: "start a lesson", help: "words from the letters you have, every one holding the focus key",
        value: () => `${cfg.words} words`, enter: () => this.ui.go(makeSpec("learn", "words", cfg.words, "learn")) },
      { label: "target speed", help: "every key must reach this before the next letter unlocks", value: () => `${cfg.target} wpm`,
        left: () => { cfg.target = cycle(TARGETS, cfg.target, -1); save(); this.drawLetters(); },
        right: () => { cfg.target = cycle(TARGETS, cfg.target, 1); save(); this.drawLetters(); } },
      { label: "lesson length", help: "words in a lesson", value: () => `${cfg.words}`,
        left: () => { cfg.words = cycle(LENGTHS, cfg.words, -1); save(); }, right: () => { cfg.words = cycle(LENGTHS, cfg.words, 1); save(); } },
      { label: "letters at least", help: `play with more letters than you've earned (never fewer than ${START_LETTERS})`, value: () => `${cfg.letters}`,
        left: () => { learn.addLetters(-1); save(); this.drawLetters(); }, right: () => { learn.addLetters(1); save(); this.drawLetters(); } },
      flag("natural", "real words", "real words where enough fit the letters, made-up ones otherwise"),
      flag("capitals", "capitals", "capitalise some words"),
      flag("punctuation", "punctuation", "end some words with punctuation"),
    ], { labelWidth: "13em", onSelect: (it) => { this.help.textContent = it.help ?? ""; } });
    this.letters = h("div.letters");
    this.report = h("div.dim");
    this.help = h("div.help");
    this.el = h("div.menu", h("div", h("div.section-title", "letters"), this.letters, this.report, h("div.section-title", "lesson"), this.list.el), h("div.side", this.help));
    this.help.textContent = this.list.current().help;
    this.drawLetters();
  }

  drawLetters() {
    const learn = this.app.learn;
    const n = learn.unlocked(), foc = learn.focusKey();
    this.letters.replaceChildren(...[...ORDER].map((c, i) => {
      const v = learn.conf(c);
      const cls = i >= n ? "" : v === null ? ".in" : v >= 1 ? ".in.c2" : v >= 0.6 ? ".in.c1" : ".in.c0";
      return h(`span${cls}${c === foc ? ".focus" : ""}`, { title: v === null ? "not enough presses yet" : `${Math.round(v * 100)}% of target` }, c);
    }));
    this.report.replaceChildren(...learn.report().map((l) => h("div", l)));
  }

  onKey(key) {
    if (key === "ESC") return this.ui.go(MENU);
    this.list.key(key);
  }
}
