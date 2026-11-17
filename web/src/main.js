// minitype in the browser: loads the app state and runs the screens
// (app.py's main loop: menu -> test -> results -> ...). One keydown listener
// for everything, one animation frame loop for whatever is on screen.

import words from "./data/words.json";
import quotes from "./data/quotes.json";
import code from "./data/code.json";
import themed from "./data/themed.json";
import themes from "./data/themes.json";
import { App } from "./core/app.js";
import { canReachLocal } from "./core/keyboardApp.js";
import { MENU, QUIT } from "./core/test.js";
import { keyOf, NAV, h, hints } from "./ui/dom.js";
import { applyTheme, styles } from "./ui/theme.js";
import { MenuScreen } from "./ui/menu.js";
import { TestScreen } from "./ui/testScreen.js";
import { ResultsScreen } from "./ui/results.js";
import { ProfileScreen } from "./ui/profile.js";
import { SettingsScreen } from "./ui/settings.js";
import { LearnScreen } from "./ui/learn.js";
import { ReplayScreen } from "./ui/replay.js";
import { WelcomeScreen } from "./ui/welcome.js";
import { FxMonitor } from "./fx/monitor.js";

const localStore = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode, full */ } },
  remove: (k) => { try { localStorage.removeItem(k); } catch { /* same */ } },
};

async function fetchJson(url) {
  const r = await fetch(url, { cache: "force-cache" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

const app = new App({ data: { words, quotes, code, themed, themes }, store: localStore, fetchJson, local: canReachLocal(location) });
app.load();

const screenEl = document.getElementById("screen");
const nav = document.getElementById("nav");

class UI {
  constructor() {
    this.app = app;
    this.screen = null;
    this.stack = [];          // screens waiting under the one shown (settings over a test)
    this.fx = new FxMonitor(app);
    this.restyle();
  }

  restyle() {
    this.st = styles(app.settings);
    applyTheme(this.st);
    document.documentElement.style.setProperty("--fx-speed", Math.abs(this.st.fx.speed) || 1);
    document.documentElement.classList.toggle("no-smooth", !app.settings.smooth_caret);
    return this.st;
  }

  show(screen) {
    this.screen?.destroy?.();
    this.screen = screen;
    screenEl.replaceChildren(screen.el);
    hints(app.settings.hints ? screen.hints ?? "" : "");
    this.navOn(screen.navName);
    screen.shown?.();
  }

  /** Where the app goes next: MENU, QUIT, a test spec, a result, or a screen name. */
  go(state) {
    this.closeDialog();
    if (state === null || state === undefined) return;
    if (state === MENU || state === QUIT) return this.show(new MenuScreen(this));
    if (typeof state === "string") {
      const make = { profile: ProfileScreen, settings: SettingsScreen, learn: LearnScreen, welcome: WelcomeScreen }[state];
      return this.show(new make(this));
    }
    if (state.replayOf) return this.show(new ReplayScreen(this, state.replayOf));
    if (state.kind) return this.show(new TestScreen(this, state));
    if (state.spec) return this.show(new ResultsScreen(this, state));
    return this.show(new MenuScreen(this));
  }

  /** The settings over whatever is on screen (ctrl-o): back returns to it. */
  openSettings(tab = null) {
    if (this.screen instanceof SettingsScreen) return;
    const under = this.screen;
    under.pause?.();
    this.stack.push(under);
    under.el.remove();
    this.screen = new SettingsScreen(this, { tab, over: under });
    screenEl.replaceChildren(this.screen.el);
    hints(app.settings.hints ? this.screen.hints : "");
    this.navOn("settings");
  }

  back() {
    const under = this.stack.pop();
    if (!under) return this.go(MENU);
    this.screen?.destroy?.();
    this.restyle();
    this.screen = under;
    screenEl.replaceChildren(under.el);
    hints(app.settings.hints ? under.hints ?? "" : "");
    this.navOn(under.navName);
    under.resume?.();
  }

  navOn(name) {
    for (const b of nav.children) b.classList.toggle("on", b.dataset.name === name);
  }

  // ---- dialogs: one at a time, over the screen; keys go to them first

  dialog(title, body, buttons, { onKey = null, cancel = null } = {}) {
    const ov = document.getElementById("overlay");
    let sel = 0;
    const btns = buttons.map((b, i) => h("button.btn.choice", { on: { click: () => this.closeDialog(b.value), mouseenter: () => mark(i) } }, b.label));
    const mark = (i) => { sel = i; btns.forEach((b, k) => b.classList.toggle("sel", k === i)); };
    mark(0);
    ov.replaceChildren(h("div.dialog", h("h2", title), body ?? "", h("div.choices", btns)));
    ov.hidden = false;
    return new Promise((resolve) => {
      this._dialog = {
        resolve,
        key: (key) => {
          if (onKey && onKey(key) === true) return;
          if (key === NAV.LEFT || key === NAV.SHIFT_TAB) mark((sel - 1 + btns.length) % btns.length);
          else if (key === NAV.RIGHT || key === "TAB") mark((sel + 1) % btns.length);
          else if (key === "ENTER") this.closeDialog(buttons[sel].value);
          else if (key === "ESC") this.closeDialog(cancel);
          else {
            const b = buttons.find((x) => x.key === key);
            if (b) this.closeDialog(b.value);
          }
        },
      };
      ov.onclick = (e) => { if (e.target === ov) this.closeDialog(cancel); };
    });
  }

  closeDialog(value) {
    const d = this._dialog;
    this._dialog = null;
    const ov = document.getElementById("overlay");
    ov.hidden = true;
    ov.replaceChildren();
    d?.resolve(value);
  }
}

const ui = new UI();
window.minitype = ui;           // for poking at it from the console

for (const [name, label] of [["menu", "type"], ["learn", "learn"], ["profile", "profile"], ["settings", "settings"]]) {
  nav.append(h("button", { "data-name": name, on: { click: (e) => { e.currentTarget.blur(); ui.go(name === "menu" ? MENU : name); } } }, label));
}
document.querySelector(".logo").addEventListener("click", () => ui.go(MENU));

// keys the browser would act on itself: tab focus, space scrolling, quick find...
const KEEP = new Set(["TAB", "SHIFT_TAB", "BACKSPACE", "CTRL_BACKSPACE", NAV.CTRL_O, NAV.UP, NAV.DOWN, NAV.PGUP, NAV.PGDN, NAV.HOME, NAV.END, " ", "'", "/"]);

window.addEventListener("keydown", (e) => {
  const target = e.target;
  const typingInField = target instanceof HTMLElement && (target.matches("input, textarea") || target.isContentEditable);
  const key = keyOf(e);
  if (key === null) return;
  if (typingInField) {
    if (key === "ESC" || (key === "ENTER" && target.matches("input"))) {
      target.blur();
      ui._dialog?.key(key);
      ui.screen?.fieldKey?.(key, target);
      e.preventDefault();
    }
    return;
  }
  if (KEEP.has(key) || ui.screen?.takesAllKeys) e.preventDefault();
  if (ui._dialog) return ui._dialog.key(key);
  if (key === NAV.CTRL_O) return ui.openSettings();
  ui.screen?.onKey(key, e);
}, { capture: false });

let last = performance.now();
function frame(t) {
  ui.fx.tick(t - last);
  last = t;
  ui.screen?.frame?.(t);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// word list first (it may come from the network), then the first screen
const loading = h("div.dim", { style: { paddingTop: "20vh", textAlign: "center" } }, `loading ${app.settings.word_source}...`);
screenEl.replaceChildren(loading);
app.loadWords(app.settings.word_source).finally(() => {
  if (app.settings.quote_source === "online") app.quotes.loadOnline();
  ui.go(app.firstRun ? "welcome" : MENU);
});
