// The settings, as in minitype/settings.py: the same names and values, so a
// settings.json from the terminal minitype imports as it is (and exports
// back). Settings the browser has no use for (art, books, lyrics...) are kept
// as they came, in `extra`, and written back out with the rest.

import * as C from "./config.js";

export const DEFAULTS = {
  // ---- the test
  difficulty: "normal",
  stop_on_error: "off",
  tab_same: true,
  backspace: "normal",
  corrected: "marked",
  typos: "off",
  punctuation: "off",
  lowercase: false,
  apostrophes: true,
  numbers: false,
  blind: false,
  time_amount: 30,
  word_amount: 25,
  // ---- challenges
  min_wpm: 0,
  min_acc: 0,
  funbox: "off",
  memory: 0,
  // ---- practising weaknesses
  weak: false,
  weak_pct: 50,
  bad_words: false,
  bad_words_pct: 50,
  // ---- text sources
  word_source: "online 1k",
  word_length: "any",
  quote_length: "all",
  quote_source: "built-in",
  quote_genre: "all",
  wpm_system: "active",
  code_lang: "python",
  fav_quotes: [],
  // ---- look and feel
  theme: "default",
  accent_text: false,
  untyped_lighten: 0,
  esc_pause: true,
  theme_background: "theme",
  theme_gradient: true,
  theme_flow: true,
  theme_heat: true,
  theme_text_style: true,
  fun_bounce: "theme",
  fun_shake: "theme",
  fun_pop: "theme",
  fun_fade: "theme",
  fun_caret: "theme",
  fun_glitch: "theme",
  effect_speed: 1.0,
  flow_direction: "forward",
  lowkey: "off",
  tape: "off",
  caret: "underline",
  word_gap: "blank",
  keyboard: "learn",
  layout: "qwerty",
  ghost: false,
  pace: 0,
  sound: false,
  hints: true,
  mouse: true,
  // ---- the magnetic keyboard's app
  keyboard_learn: false,
  keyboard_ask: true,
  keyboard_server: "http://localhost:6869",
  // ---- header during a test
  show_timer: true,
  show_progress: true,
  show_wpm: true,
  show_combo: true,
  // ---- results screen sections
  res_chart: true,
  res_heatmap: true,
  res_pb: true,
  res_worst_keys: true,
  res_session_keys: true,
  res_bad_words: true,
  res_history: true,
  // ---- progress
  daily_goal: 0,
  // ---- the browser's own: effects (all off by default, for speed)
  fx_tilt: false,        // the words turn a little to the side, in 3D
  fx_tilt_angle: 14,
  fx_fire: "off",        // flames out of the typed words: off, on a streak / high speed, always
  fx_fire_wpm: 100,
  fx_shine: false,       // a band of light sweeps the words now and then, a star twinkles
  fx_combo: false,       // the combo counter escalates: flashes, shakes, burns
  fx_popin: false,       // letters pop in as you type them right
  fx_camera: false,      // a small camera shake on a wrong key
  fx_reveal: false,      // the results come in one by one
  fx_quality: "auto",    // auto drops to cheap effects when frames run slow
  smooth_caret: true,
};

export const CHOICES = {
  difficulty: C.DIFFICULTIES,
  stop_on_error: C.STOP_MODES,
  punctuation: C.PUNCTUATION_MODES,
  word_length: C.WORD_LENGTHS,
  backspace: C.BACKSPACE_MODES,
  min_wpm: C.MIN_WPMS,
  min_acc: C.MIN_ACCS,
  funbox: C.FUNBOXES,
  memory: C.MEMORY_SECS,
  quote_length: C.QUOTE_LENGTHS,
  quote_source: C.QUOTE_SOURCES,
  quote_genre: C.QUOTE_GENRES,
  code_lang: C.CODE_LANGS,
  pace: C.PACES,
  caret: C.CARETS,
  word_gap: C.WORD_GAPS,
  corrected: C.CORRECTED,
  typos: C.TYPOS,
  fun_bounce: C.FUN_BOUNCE,
  fun_shake: C.FUN_SWITCH,
  fun_pop: C.FUN_SWITCH,
  fun_fade: C.FUN_SWITCH,
  fun_caret: C.FUN_CARET,
  fun_glitch: C.FUN_SWITCH,
  effect_speed: C.EFFECT_SPEEDS,
  flow_direction: C.FLOW_DIRECTIONS,
  keyboard: C.KEYBOARD_MODES,
  layout: Object.keys(C.LAYOUTS),
  lowkey: C.LOWKEY_MODES,
  tape: C.TAPE_MODES,
  daily_goal: C.GOALS,
  wpm_system: C.WPM_SYSTEMS,
  theme_background: C.THEME_BACKGROUNDS,
  time_amount: C.TIMES,
  word_amount: C.WORD_COUNTS,
  weak_pct: C.PCTS,
  bad_words_pct: C.PCTS,
  untyped_lighten: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
  fx_quality: C.FX_QUALITY,
  fx_fire: C.FIRE_MODES,
  fx_tilt_angle: [6, 10, 14, 20, 26],
  fx_fire_wpm: [60, 80, 100, 120, 150],
};

// the word lists (words/bank.py); the theme list comes from the data
export const WORD_SOURCES = [
  "built-in", "online 200", "online 1k", "online 5k", "online 10k", "online 25k",
  "online 450k", "double letters", "misspelled", "programming", "left hand", "right hand",
  "right heavy", "home row",
];

// The setups a new install picks from (welcome screen), as in settings.py
// without the art: "clean" is quiet and monochrome, "art" the summit theme.
const SHARED_SETUP = {
  typos: "below", punctuation: "forgive", lowercase: true, word_amount: 10,
  weak_pct: 40, bad_words_pct: 40, word_source: "online 200", quote_length: "short",
  quote_source: "online", code_lang: "javascript", esc_pause: false,
  theme_background: "always", fun_bounce: "off", fun_shake: "off", fun_fade: "off",
  effect_speed: 1.5, caret: "block", keyboard: "off", sound: true,
  res_worst_keys: false, res_session_keys: false, res_bad_words: false,
};
export const SETUPS = {
  clean: { ...SHARED_SETUP, theme: "mono", theme_flow: false, theme_heat: false,
    fun_pop: "off", fun_glitch: "off", hints: false },
  art: { ...SHARED_SETUP, theme: "summit", untyped_lighten: 10 },
};

export function sameType(a, b) {
  if (Array.isArray(a)) return Array.isArray(b);
  if (a === null || b === null) return a === b;
  if (typeof a === "number") return typeof b === "number" && Number.isFinite(b)
    && (Number.isInteger(a) ? Number.isInteger(b) : true);
  return typeof a === typeof b;
}

export class Settings {
  constructor() {
    Object.assign(this, structuredClone(DEFAULTS));
    // what came in an import that this version has no use for, kept to write back
    Object.defineProperty(this, "extra", { value: {}, writable: true, enumerable: false });
  }

  /** Take saved values, skipping any of the wrong type or out of range
   * (settings.py apply, with its migrations from older versions). */
  apply(d, themeNames = null) {
    if (!d || typeof d !== "object" || Array.isArray(d)) return;
    d = { ...d };
    if (d.quiet === true && !("theme" in d)) d.theme = "mono";
    if (d.show_spaces === true && !("word_gap" in d)) d.word_gap = "dots";
    if (typeof d.theme_background === "boolean") d.theme_background = d.theme_background ? "theme" : "off";
    if (typeof d.punctuation === "boolean" || (d.forgive_apostrophe === true && !("apostrophes" in d))) {
      d.punctuation = d.forgive_apostrophe ? "forgive" : d.punctuation === true ? "on" : "off";
    }
    if (d.remove_apostrophe === true && !("apostrophes" in d)) d.apostrophes = false;
    if (typeof d.tape === "boolean") d.tape = d.tape ? "on" : "off";
    if (d.lowkey === "disguised") d.lowkey = "minimal";
    for (const [k, v] of Object.entries(d)) {
      if (!(k in DEFAULTS)) {
        if (!["key_state", "keyboard_pairs"].includes(k)) this.extra[k] = v;
        continue;
      }
      if (!sameType(DEFAULTS[k], v)) continue;
      const range = C.NUMBER_RANGES[k];
      let allowed = CHOICES[k];
      if (k === "theme" && themeNames) allowed = themeNames;
      if (k === "word_source") allowed = WORD_SOURCES;
      if (range) {
        if (!(range[0] <= v && v <= range[1])) continue;
      } else if (allowed && !["time_amount", "word_amount"].includes(k) && !allowed.includes(v)) {
        continue;
      }
      if ((k === "time_amount" || k === "word_amount") && !(v > 0 && v <= 3600)) continue;
      if (k === "fav_quotes") {
        this[k] = v.filter((q) => q && typeof q.text === "string")
          .map((q) => ({ text: q.text, source: String(q.source ?? "") }));
        continue;
      }
      this[k] = v;
    }
  }

  toDict() {
    return { ...structuredClone(this.extra), ...structuredClone({ ...this }) };
  }

  /** Short labels for every non-default rule, for the main menu. */
  flags() {
    const f = [];
    if (this.difficulty !== "normal") f.push(this.difficulty);
    if (this.stop_on_error !== "off") f.push(`stop-${this.stop_on_error}`);
    if (this.backspace !== "normal") f.push(this.backspace === "off" ? "no-bksp" : "freedom");
    if (this.punctuation !== "off") f.push(this.punctuation === "on" ? "punct" : "punct-skip");
    if (this.lowercase) f.push("lower");
    if (this.numbers) f.push("num");
    if (this.blind) f.push("blind");
    if (this.ghost) f.push("ghost");
    if (this.tape !== "off") f.push(this.tape === "on" ? "tape" : "tape-from-middle");
    if (this.funbox !== "off") f.push(this.funbox);
    if (this.memory) f.push(`memory${this.memory}s`);
    if (this.min_wpm) f.push(`min${this.min_wpm}wpm`);
    if (this.min_acc) f.push(`min${this.min_acc}%`);
    if (this.weak) f.push(`keys${this.weak_pct}%`);
    if (this.bad_words) f.push(`words${this.bad_words_pct}%`);
    if (this.pace) f.push(`pace${this.pace}`);
    return f;
  }
}

/** The next value in a list (wrapping), like util.cycle. */
export function cycle(seq, value, step = 1) {
  const i = seq.indexOf(value);
  if (i < 0) return seq[0];
  return seq[(i + step + seq.length) % seq.length];
}
