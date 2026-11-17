// The theme's colours as CSS variables, and its effects with the fun-modifier
// settings on top (terminal/style.py's Styles, for the browser).

import themesData from "../data/themes.json";

export const THEMES = themesData.themes;
export const THEME_ORDER = themesData.order;
export const RAINBOW = themesData.rainbow;
export const GRADIENT_STEPS = 24;
export const HEAT_STEP = 5;

// the default theme is the terminal's 16 colours: shown as a terminal shows them
const DEFAULT_FIX = { error: "#ff5f5f", extra: "#d75f5f", good: "#5fd75f", warn: "#d7af5f", dim: "#7c7c7c", text: "#e8e8e8" };
const MONO = { dim: "#6f6f6f", text: "#e4e4e4", error: "#e4e4e4", extra: "#8a8a8a", accent: "#ffffff", good: "#cfcfcf", warn: "#bdbdbd" };
const FALLBACK_BG = "#141517";

import { hexToRgb, rgbToHex, mix, luminance } from "./colour.js";

export { hexToRgb, rgbToHex, mix, luminance };

/** `steps` colours running evenly through the stops and back to the first. */
export function blend(stops, steps = GRADIENT_STEPS) {
  const pts = [...stops, stops[0]].map(hexToRgb);
  const out = [];
  for (let k = 0; k < steps; k++) {
    const x = (k / steps) * (pts.length - 1);
    const i = Math.floor(x), t = x - i;
    const a = pts[i], b = pts[Math.min(i + 1, pts.length - 1)];
    out.push(rgbToHex(a.map((v, c) => v + (b[c] - v) * t)));
  }
  return out;
}

/** The theme in use: colours, background and effects, from the settings. */
export function styles(s) {
  const raw = THEMES[s.theme] ?? THEMES.default;
  const mono = raw.mono;
  const c = { ...raw };
  if (mono) Object.assign(c, MONO);
  if (s.theme === "default") Object.assign(c, DEFAULT_FIX);
  for (const k of ["dim", "text", "error", "extra", "accent", "good", "warn"]) c[k] = c[k] ?? MONO[k];
  let bg = raw.background;
  if (s.theme_background === "off") bg = null;
  if (!bg) bg = s.theme_background === "off" ? null : raw.made_background;
  const light = luminance(c.text) < 0.35;
  if (!bg) bg = light ? "#f6f6f3" : FALLBACK_BG;
  if (s.accent_text) c.text = c.accent;
  const untyped = s.untyped_lighten ? mix(c.dim, light ? "#000000" : "#ffffff", s.untyped_lighten / 100) : c.dim;
  const pick = (setting, own) => (setting === "theme" ? own : setting);
  const sw = (setting, own) => (setting === "theme" ? own : setting === "on");
  const fx = {
    gradient: s.theme_gradient && raw.gradient?.length ? blend(raw.gradient) : [],
    by: raw.by,
    flow: s.theme_flow ? raw.flow : 0,
    heat: s.theme_heat ? raw.heat ?? [] : [],
    bold: s.theme_text_style && raw.bold,
    italic: s.theme_text_style && raw.italic,
    bounce: pick(s.fun_bounce, raw.bounce),
    shake: sw(s.fun_shake, raw.shake),
    pop: sw(s.fun_pop, raw.pop) && !mono,
    fade: sw(s.fun_fade, raw.fade),
    caret: pick(s.fun_caret, raw.caret),
    glitch: sw(s.fun_glitch, raw.glitch),
    speed: (s.effect_speed || 1) * (s.flow_direction === "backward" ? -1 : 1),
  };
  if (mono && fx.caret === "rainbow") fx.caret = "off";
  if (s.lowkey !== "off") Object.assign(fx, { bounce: "off", shake: false, pop: false, glitch: false, gradient: [], heat: [] });
  return { ...c, bg, untyped, light, mono, fx };
}

/** Put a theme's colours on the page. */
export function applyTheme(st, root = document.documentElement) {
  const set = (k, v) => root.style.setProperty(k, v);
  set("--bg", st.bg);
  set("--dim", st.dim);
  set("--text", st.text);
  set("--untyped", st.untyped);
  set("--error", st.error);
  set("--extra", st.extra);
  set("--accent", st.accent);
  set("--good", st.good);
  set("--warn", st.warn);
  set("--panel", mix(st.bg, st.light ? "#000000" : "#ffffff", 0.045));
  set("--panel-2", mix(st.bg, st.light ? "#000000" : "#ffffff", 0.09));
  set("--line", mix(st.bg, st.dim, 0.45));
  root.classList.toggle("mono", st.mono);
  root.classList.toggle("light", st.light);
  root.style.colorScheme = st.light ? "light" : "dark";
}

/** The colour of a correctly typed letter: heat by combo, a gradient, or the text colour. */
export function typedColour(st, off, word, combo, now) {
  const fx = st.fx;
  if (fx.heat.length) return fx.heat[Math.min(Math.floor(combo / HEAT_STEP), fx.heat.length - 1)];
  if (fx.gradient.length) {
    const k = fx.by === "letter" ? off : word;
    const shift = Math.floor(now * fx.flow * fx.speed);
    const n = fx.gradient.length;
    return fx.gradient[(((k + shift) % n) + n) % n];
  }
  return null;
}

export function caretColour(now, speed = 1) {
  return RAINBOW[Math.floor(now * 6 * Math.abs(speed)) % RAINBOW.length];
}
