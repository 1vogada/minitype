// Shared state handed to every screen (context.py's App): settings, stats,
// history, learn progress, the word sources, and the save. The save is the
// same shape as minitype's save.json and settings.json, kept in a store
// ({get, set, remove}: localStorage in the browser, a Map in the tests).

import { History } from "./history.js";
import { KeyboardApp } from "./keyboardApp.js";
import { LearnProgress } from "./learn.js";
import { SETUPS, Settings } from "./settings.js";
import { SessionStats } from "./stats.js";
import { QuoteBank, WordBank, WordGenerator } from "./words.js";
import { KEYS } from "./config.js";

export const SETTINGS_KEY = "minitype.settings";
export const SAVE_KEY = "minitype.save";
export const SAVING_KEY = "minitype.saving";

export function memoryStore(init = {}) {
  const m = new Map(Object.entries(init));
  return { get: (k) => (m.has(k) ? m.get(k) : null), set: (k, v) => m.set(k, String(v)), remove: (k) => m.delete(k), map: m };
}

export class App {
  constructor({ data, store = memoryStore(), fetchJson = null, fetchImpl, now, rng, proxy } = {}) {
    this.data = data;     // {words, quotes, code, themed, themes}
    this.store = store;
    this.settings = new Settings();
    this.stats = new SessionStats();
    this.history = new History();
    this.history.system = () => this.settings.wpm_system;
    this.now = now ?? (() => (performance.timeOrigin + performance.now()) / 1000);
    this.history.clock = () => this.now();
    this.rng = rng ?? Math.random;
    this.bank = new WordBank(data.words, data.themed, fetchJson);
    this.quotes = new QuoteBank(data.quotes, fetchJson);
    this.code = data.code;
    this.generator = new WordGenerator(this.settings, this.stats, this.bank, () => this.rng());
    this.learn = new LearnProgress();
    this.keyboard = new KeyboardApp({ fetchImpl, store, server: this.settings.keyboard_server, proxy });
    this.keyboardPairs = [];
    this.notice = "";
    this.firstRun = false;
    this.cursors = {};
  }

  themeNames() { return this.data.themes?.order ?? null; }

  // ---------------------------------------------------------------- disk

  /** What goes in save.json (history, bests, word timings, learn). */
  toDict() {
    return {
      learn: this.learn.config,
      stats: this.learn.stats,
      history: this.history.runs,
      pbs: this.history.pbs,
      word_speed: this.stats.wordSpeed,
      word_clean: this.stats.wordClean,
    };
  }

  /** What goes in settings.json: every setting, plus pinned / muted keys. */
  settingsDict() {
    return { ...this.settings.toDict(), key_state: this.stats.keyState, keyboard_pairs: this.keyboardPairs.map((p) => [...p]) };
  }

  saving() { return this.store.get(SAVING_KEY) !== "off"; }

  setSaving(on) {
    this.store.set(SAVING_KEY, on ? "on" : "off");
    if (on) this.save();
    else this.store.remove(SAVE_KEY);
  }

  saveSettings() {
    try { this.store.set(SETTINGS_KEY, JSON.stringify(this.settingsDict())); } catch { /* full */ }
    this.keyboard.server = this.settings.keyboard_server;
  }

  save() {
    this.saveSettings();
    if (this.saving()) {
      try { this.store.set(SAVE_KEY, JSON.stringify(this.toDict())); } catch { /* full */ }
    }
  }

  read(key) {
    try {
      const v = JSON.parse(this.store.get(key) ?? "null");
      return v && typeof v === "object" && !Array.isArray(v) ? v : null;
    } catch {
      return null;
    }
  }

  load() {
    let s = this.read(SETTINGS_KEY);
    const d = this.read(SAVE_KEY) ?? {};
    if (s === null) {
      s = { ...SETUPS.clean };
      this.firstRun = true;
    }
    this.applySettings(s);
    this.applySave(d);
  }

  applySettings(s) {
    this.settings.apply(s, this.themeNames());
    if (s.key_state && typeof s.key_state === "object") {
      for (const [c, v] of Object.entries(s.key_state)) {
        if ((v === "on" || v === "off") && KEYS.includes(c)) this.stats.keyState[c] = v;
      }
    }
    if (Array.isArray(s.keyboard_pairs)) {
      this.keyboardPairs = s.keyboard_pairs.filter((p) => Array.isArray(p) && p.length === 3
        && typeof p[0] === "string" && typeof p[1] === "string" && p[0].length === 1 && p[1].length === 1
        && Number.isInteger(p[2]) && p[2] > 0);
    }
    this.keyboard.server = this.settings.keyboard_server;
  }

  applySave(d, merge = false) {
    if (d.learn || d.stats) this.learn.apply(d);
    if (merge) this.history.merge(d.history, d.pbs);
    else this.history.apply(d.history, d.pbs);
    if (d.word_speed && typeof d.word_speed === "object") {
      for (const [w, v] of Object.entries(d.word_speed)) {
        if (Array.isArray(v) && v.length === 2) this.stats.wordSpeed[w] = [+v[0], v[1] | 0];
      }
    }
    if (d.word_clean && typeof d.word_clean === "object") {
      for (const [w, v] of Object.entries(d.word_clean)) {
        if (Array.isArray(v) && v.length === 2 && v.every((x) => Number.isInteger(x) && x >= 0) && v[0] <= v[1]) {
          this.stats.wordClean[w] = [v[0], v[1]];
        }
      }
    }
  }

  /** An imported file: minitype's save.json (merged into what's here) or
   * settings.json (replacing these). Returns what it was, or null. */
  importJson(obj) {
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return null;
    const isSave = ["history", "pbs", "word_speed", "learn", "stats"].some((k) => k in obj);
    const isSettings = ["theme", "difficulty", "word_source", "caret", "tape"].some((k) => k in obj);
    if (isSave) {
      this.applySave(obj, true);
      if (obj.settings && typeof obj.settings === "object") this.applySettings(obj.settings);
      this.save();
      return "save";
    }
    if (isSettings) {
      this.applySettings(obj);
      this.save();
      return "settings";
    }
    return null;
  }

  useSetup(name) {
    const fresh = new Settings();
    for (const k of Object.keys(fresh)) this.settings[k] = fresh[k];
    this.settings.apply(SETUPS[name] ?? {}, this.themeNames());
    this.saveSettings();
  }

  async loadWords(name) {
    const ok = await this.bank.load(name, this.settings.layout);
    this.settings.word_source = name;
    return ok;
  }
}
