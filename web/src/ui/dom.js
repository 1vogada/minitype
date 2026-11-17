// Small DOM helpers and the key names a KeyboardEvent stands for.

import { KEY } from "../core/test.js";

/** h("div.cls#id", {attrs, on: {click}}, ...children) */
export function h(tag, attrs = {}, ...children) {
  const [name, ...rest] = tag.split(/(?=[.#])/);
  const el = document.createElement(name || "div");
  for (const r of rest) {
    if (r[0] === ".") el.classList.add(r.slice(1));
    else if (r[0] === "#") el.id = r.slice(1);
  }
  if (attrs && (typeof attrs !== "object" || attrs instanceof Node || Array.isArray(attrs))) {
    children.unshift(attrs);
    attrs = {};
  }
  for (const [k, v] of Object.entries(attrs ?? {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "on") for (const [ev, fn] of Object.entries(v)) el.addEventListener(ev, fn);
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k === "class") el.className += " " + v;
    else if (k === "html") el.innerHTML = v;
    else if (k in el && typeof v !== "string") el[k] = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  append(el, children);
  return el;
}

function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

export const NAV = { UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT", PGUP: "PGUP", PGDN: "PGDN", HOME: "HOME", END: "END", CTRL_O: "CTRL_O", SHIFT_TAB: "SHIFT_TAB", DELETE: "DELETE" };

/** The key name (test.js KEY / NAV) or character a keydown stands for, or null. */
export function keyOf(e) {
  const k = e.key;
  const altGr = Boolean(e.getModifierState?.("AltGraph"));   // windows sends it as ctrl+alt
  const ctrl = (e.ctrlKey || e.metaKey) && !altGr;
  if (e.isComposing || k === "Dead" || k === "Process") return null;
  if (ctrl && (k === "o" || k === "O")) return NAV.CTRL_O;
  switch (k) {
    case "Escape": return KEY.ESC;
    case "Tab": return e.shiftKey ? NAV.SHIFT_TAB : KEY.TAB;
    case "Enter": return e.shiftKey ? KEY.SHIFT_ENTER : KEY.ENTER;
    case "Backspace": return ctrl || e.altKey ? KEY.CTRL_BACKSPACE : KEY.BACKSPACE;
    case "Delete": return NAV.DELETE;
    case "ArrowUp": return NAV.UP;
    case "ArrowDown": return NAV.DOWN;
    case "ArrowLeft": return NAV.LEFT;
    case "ArrowRight": return NAV.RIGHT;
    case "PageUp": return NAV.PGUP;
    case "PageDown": return NAV.PGDN;
    case "Home": return NAV.HOME;
    case "End": return NAV.END;
    default:
  }
  if (ctrl || (e.altKey && !altGr)) return null;
  return [...k].length === 1 ? k : null;
}

/** The time a key was pressed, in epoch seconds: the event's own stamp, not
 * when the page got round to it, so a slow frame never lowers your speed. */
export const keyTime = (e) => (performance.timeOrigin + e.timeStamp) / 1000;
export const nowSecs = () => (performance.timeOrigin + performance.now()) / 1000;

export function fmtTime(secs) {
  const m = Math.floor(secs / 60);
  return m >= 60 ? `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, "0")}m` : `${m}m ${String(Math.floor(secs % 60)).padStart(2, "0")}s`;
}

export function hints(text) {
  // "enter start   tab restart" -> kbd chips
  const el = document.getElementById("hints");
  el.replaceChildren();
  if (!text) return;
  for (const part of text.split(/ {3,}/)) {
    const [k, ...rest] = part.split(" ");
    el.append(h("kbd", k), " ", rest.join(" "), "   ");
  }
}

let toastTimer = null;
export function toast(text, ms = 2600) {
  document.querySelector(".toast")?.remove();
  const el = h("div.toast", text);
  document.body.append(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), ms);
}

/** A tiny beep for a wrong key (the sound setting). */
let audio = null;
export function beep() {
  try {
    audio ??= new AudioContext();
    const o = audio.createOscillator(), g = audio.createGain();
    o.frequency.value = 220;
    o.type = "square";
    g.gain.setValueAtTime(0.04, audio.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.08);
    o.connect(g).connect(audio.destination);
    o.start();
    o.stop(audio.currentTime + 0.09);
  } catch {
    // no audio: no beep
  }
}

/** An SVG element. */
export function svg(tag, attrs = {}, ...children) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  for (const c of children.flat()) if (c) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
