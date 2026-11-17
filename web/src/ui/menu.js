// The main menu (ui/main_menu.py): the modes, practice, and the notes under them.

import { CODE_LANGS, QUOTE_LENGTHS, TIMES, WORD_COUNTS } from "../core/config.js";
import { cycle } from "../core/settings.js";
import { MIN_SLOW_WORDS, makeSpec } from "../core/test.js";
import * as bestWords from "../core/bestWords.js";
import { statusLine } from "../core/keyboardApp.js";
import { h, fmtTime } from "./dom.js";
import { RowList } from "./rows.js";

const SMALL_LIST = 500;

export function goalLine(app) {
  const goal = app.settings.daily_goal;
  const today = app.history.todaySeconds();
  const [days] = app.history.streak();
  const streak = days > 1 ? `   ${days} day streak` : "";
  if (!goal) return today ? `today ${fmtTime(today)}${streak}` : "";
  const frac = Math.min(1, today / (goal * 60));
  const bar = 20, fill = Math.floor(frac * bar);
  return `today ${Math.floor(today / 60)}/${goal} min  ${"#".repeat(fill)}${".".repeat(bar - fill)}${frac >= 1 ? "  done!" : ""}${streak}`;
}

export class MenuScreen {
  constructor(ui) {
    this.ui = ui;
    this.app = ui.app;
    this.navName = "menu";
    this.hints = "enter start   ←/→ change   ↑/↓ choose   ctrl-o settings   ` theme";
    const s = this.app.settings;
    const app = this.app;
    const save = () => app.saveSettings();
    const mode = (key, label, value, seq, attr, start, help, section = "test") => ({
      key, label, section, help,
      value: () => value(),
      left: () => { s[attr] = cycle(seq, s[attr], -1); save(); },
      right: () => { s[attr] = cycle(seq, s[attr], 1); save(); },
      enter: () => ui.go(start()),
    });
    const ask = (fn) => () => fn().then((spec) => spec && ui.go(spec));
    const items = [
      mode("1", "time", () => `${s.time_amount}s`, TIMES, "time_amount",
        () => makeSpec(`${s.time_amount} seconds`, "time", s.time_amount), "type as many words as you can before the timer runs out"),
      mode("2", "words", () => `${s.word_amount}`, WORD_COUNTS, "word_amount",
        () => makeSpec(`${s.word_amount} words`, "words", s.word_amount), "a fixed number of words, as fast as you can"),
      mode("3", "quote", () => s.quote_length, QUOTE_LENGTHS, "quote_length",
        () => makeSpec("quote", "words", 0, "quote"), "type a real quote; choose genre, built-in or online quotes in settings"),
      { key: "4", label: "zen", section: "test", help: "no target text, type whatever you like; enter finishes",
        enter: () => ui.go(makeSpec("zen", "zen", 0, "zen")) },
      mode("5", "code", () => s.code_lang, CODE_LANGS, "code_lang",
        () => makeSpec(`code ${s.code_lang}`, "words", 0, "code"), "type a code snippet: symbols, brackets and keywords"),
      mode("6", "numbers", () => `${s.word_amount}`, WORD_COUNTS, "word_amount",
        () => makeSpec(`${s.word_amount} numbers`, "words", s.word_amount, "numbers"), "numbers only"),
      { key: "7", label: "custom length", section: "test", help: "any number of words, or any time like 45s", enter: ask(() => this.askLength()) },
      { key: "8", label: "custom text", section: "test", help: "paste some text, or open a .txt file", enter: ask(() => this.askText()) },
      { key: "9", label: "learn", section: "practice", value: () => `${app.learn.unlocked()}/26 letters`,
        warn: () => (app.bank.words.length < SMALL_LIST ? `small word list (${app.bank.words.length})` : ""),
        help: "keybr-style lessons that unlock letters as you get faster", enter: () => ui.go("learn") },
      { key: "0", label: "slow words", section: "practice", value: () => `${Object.keys(app.stats.wordSpeed).length} words timed`,
        help: "a test made of the words you type slowest", enter: () => this.slowDrill() },
      { key: "w", label: "best words", section: "practice",
        value: () => bestWords.progress(app.stats, app.learn.stats).join("/") + " words",
        help: "your fastest, cleanest words from your history (faster ones come up more), to push your top speed. Kept apart: its own bests and profile rows, not in your normal speed, accuracy, key or word stats, nor in keyboard learn",
        enter: () => this.bestDrill() },
      { key: "p", label: "profile", section: "you", help: "totals, speed chart, the days you typed and personal bests", enter: () => ui.go("profile") },
      { key: "s", label: "settings", section: "you", help: "rules, text, drills, theme, effects, keyboard learn, import and export", enter: () => ui.go("settings") },
    ];
    this.list = new RowList(items, {
      cursor: app.cursors.main ?? 0,
      onSelect: (it, i) => { app.cursors.main = i; this.showHelp(it); },
    });
    this.help = h("div.help");
    this.notes = h("div.notes");
    this.flags = h("div.flags");
    this.el = h("div.menu", h("div", this.list.el), h("div.side", this.help, this.flags, this.notes));
    this.showHelp(this.list.current());
    this.showNotes();
  }

  showHelp(it) {
    this.help.textContent = it?.help ?? "";
  }

  showNotes() {
    const app = this.app;
    const notes = [];
    if (app.notice) {
      notes.push(h("div.warn", app.notice));
      app.notice = "";
    }
    if (app.bank.note) notes.push(h("div", app.bank.note));
    const best = app.stats.best();
    if (best !== null) notes.push(h("div", `best ${best.toFixed(0)} wpm this session`));
    const goal = goalLine(app);
    if (goal) notes.push(h("div", goal));
    const learn = statusLine(app);
    if (learn) notes.push(h("div", learn));
    this.notes.replaceChildren(...notes);
    this.flags.replaceChildren(...app.settings.flags().map((f) => h("span.flag", f)));
  }

  shown() {
    this.app.keyboard.onChange?.(() => this.showNotes());
  }

  slowDrill() {
    const n = Object.keys(this.app.stats.wordSpeed).length;
    if (n < MIN_SLOW_WORDS) {
      this.app.notice = `type a few tests first: ${n}/${MIN_SLOW_WORDS} words timed so far`;
      return this.showNotes();
    }
    this.ui.go(makeSpec("slow words", "words", this.app.settings.word_amount, "slow"));
  }

  bestDrill() {
    const s = this.app.settings;
    if (!bestWords.pool(this.app.stats, this.app.learn.stats).length) {
      const [have, need] = bestWords.progress(this.app.stats, this.app.learn.stats);
      this.app.notice = `best words needs more history (${have}/${need} words so far): a normal word test instead`;
      return this.ui.go(makeSpec(`${s.word_amount} words`, "words", s.word_amount));
    }
    this.ui.go(makeSpec(bestWords.LABEL, "words", s.word_amount, bestWords.SOURCE));
  }

  async askLength() {
    const input = h("input", { type: "text", placeholder: "50, or 45s" });
    setTimeout(() => input.focus(), 0);
    const ok = await this.ui.dialog("how long?", h("div", h("p", "a number of words, or seconds like 45s"), input),
      [{ label: "start", value: true }, { label: "cancel", value: false }], { cancel: false });
    const v = ok ? input.value.trim().toLowerCase() : "";
    if (/^\d+s$/.test(v)) {
      const n = Math.max(5, Math.min(3600, parseInt(v, 10)));
      return makeSpec(`${n} seconds`, "time", n);
    }
    if (/^\d+$/.test(v)) {
      const n = Math.max(1, Math.min(1000, parseInt(v, 10)));
      return makeSpec(`${n} words`, "words", n);
    }
    return null;
  }

  async askText() {
    const area = h("textarea", { placeholder: "paste some text here" });
    const file = h("input", { type: "file", accept: ".txt,text/plain", style: { marginTop: "10px" } });
    file.addEventListener("change", async () => {
      const f = file.files?.[0];
      if (f) area.value = await f.text();
    });
    setTimeout(() => area.focus(), 0);
    const ok = await this.ui.dialog("custom text", h("div", area, file),
      [{ label: "start", value: true }, { label: "cancel", value: false }], { cancel: false });
    const words = ok ? area.value.split(/\s+/).filter(Boolean) : [];
    if (!words.length) return null;
    return makeSpec(`custom ${words.length} words`, "words", words.length, "custom", { words });
  }

  onKey(key) {
    if (key === "`" || key === "~") {
      const names = this.ui.app.themeNames();
      const s = this.app.settings;
      s.theme = cycle(names, s.theme, key === "`" ? 1 : -1);
      this.app.saveSettings();
      this.ui.restyle();
      this.app.notice = `theme: ${s.theme}`;
      return this.showNotes();
    }
    if (key === "TAB") return this.list.moved((this.list.sel + 1) % this.list.items.length);
    const { handled } = this.list.key(key);
    if (handled) this.showNotes();
  }
}
