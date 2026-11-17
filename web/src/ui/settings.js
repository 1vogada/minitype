// The settings (ui/settings_menu.py + tree_menu.py, for the browser): tabs on
// the left, each tab's pages as headings with their rows, the help on the
// right. ←/→ change a value, tab or [ ] switch tabs, / searches, esc goes back.

import { CHOICES, DEFAULTS, cycle } from "../core/settings.js";
import { WORD_SOURCES } from "../core/settings.js";
import { MENU } from "../core/test.js";
import { h, toast, NAV } from "./dom.js";
import { RowList } from "./rows.js";
import { TREE } from "./settingsTree.js";

const RESTYLE = /^(theme|accent_text|untyped_lighten|fun_|effect_speed|flow_direction|smooth_caret|caret$|lowkey)/;

function download(name, obj) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 1)], { type: "application/json" }));
  const a = h("a", { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export class SettingsScreen {
  constructor(ui, { tab = null, over = null } = {}) {
    this.ui = ui;
    this.app = ui.app;
    this.over = over;          // the screen under it (ctrl-o), or null
    this.navName = "settings";
    this.hints = "←/→ change   ↑/↓ choose   tab next tab   / search   esc back";
    this.tab = Math.max(0, TREE.findIndex(([name]) => name === tab));
    if (tab === null) this.tab = this.app.cursors.settingsTab ?? 0;
    this.query = "";
    this.tabsEl = h("div.tabs");
    this.search = h("input.search", { type: "search", placeholder: "/ search", on: { input: () => { this.query = this.search.value.trim().toLowerCase(); this.drawRows(); } } });
    this.rowsBox = h("div");
    this.help = h("div.help");
    this.el = h("div.settings", this.tabsEl, h("div", this.search, this.rowsBox), h("div.side", this.help));
    this.drawTabs();
    this.drawRows();
  }

  drawTabs() {
    this.tabsEl.replaceChildren(...TREE.map(([name], i) => h(`div.tab${i === this.tab && !this.query ? ".on" : ""}`,
      { on: { click: () => { this.query = ""; this.search.value = ""; this.setTab(i); } } }, name)));
  }

  setTab(i) {
    this.tab = (i + TREE.length) % TREE.length;
    this.app.cursors.settingsTab = this.tab;
    this.drawTabs();
    this.drawRows();
  }

  items() {
    const out = [];
    const tabs = this.query ? TREE : [TREE[this.tab]];
    for (const [tabName, pages] of tabs) {
      for (const [page, rows] of pages) {
        for (const row of rows) {
          const it = Array.isArray(row) ? this.settingItem(row) : this.actionItem(row);
          it.section = this.query ? `${tabName} › ${page}` : page;
          if (this.query && !`${it.label} ${it.help} ${page}`.toLowerCase().includes(this.query)) continue;
          out.push(it);
        }
      }
    }
    return out;
  }

  values(key) {
    if (key === "theme") return this.app.themeNames();
    if (key === "word_source") return WORD_SOURCES;
    if (typeof DEFAULTS[key] === "boolean") return [false, true];
    return CHOICES[key] ?? null;
  }

  show(key, v) {
    if (typeof v === "boolean") return v ? "on" : "off";
    if (key === "pace") return v ? `${v} wpm` : "off";
    if (["min_wpm", "fx_fire_wpm"].includes(key)) return v ? `${v} wpm` : "off";
    if (key === "min_acc") return v ? `${v}%` : "off";
    if (["weak_pct", "bad_words_pct", "untyped_lighten"].includes(key)) return `${v}%`;
    if (key === "memory") return v ? `${v}s` : "off";
    if (key === "daily_goal") return v ? `${v} min` : "off";
    if (key === "effect_speed") return `${v}×`;
    if (key === "fx_tilt_angle") return `${v}°`;
    return String(v);
  }

  settingItem([key, label, help]) {
    const s = this.app.settings;
    const seq = this.values(key);
    const it = { label, help, value: () => this.show(key, s[key]) };
    if (seq) {
      it.left = () => this.set(key, cycle(seq, s[key], -1));
      it.right = () => this.set(key, cycle(seq, s[key], 1));
      it.enter = it.right;
    } else {
      it.enter = () => this.editText(key, label);
    }
    return it;
  }

  actionItem(a) {
    const app = this.app;
    const acts = {
      saving: { value: () => (app.saving() ? "on" : "off"), enter: () => { app.setSaving(!app.saving()); this.list.refresh(); } },
      import: { enter: () => this.importFile() },
      export_save: { enter: () => download("save.json", app.toDict()) },
      export_settings: { enter: () => download("settings.json", app.settingsDict()) },
      reset_bad: { enter: () => this.confirm("forget the keys and words you missed?", () => { app.stats.resetErrors(); app.save(); }) },
      reset_learn: { enter: () => this.confirm("start learn mode over?", () => { app.learn.reset(); app.save(); }) },
      reset_settings: { enter: () => this.confirm("every setting back to a setup?", () => this.ui.go("welcome")) },
      keyboard_status: {
        value: () => app.keyboard.last?.line().replace(/^keyboard learn: /, "") ?? "",
        enter: () => app.keyboard.call("status").then(() => this.list.refresh()),
      },
    };
    return { label: a.label, help: a.help, ...acts[a.action] };
  }

  set(key, v) {
    const app = this.app;
    app.settings[key] = v;
    app.saveSettings();
    if (key === "word_source" || (key === "layout" && /hand|home|heavy/.test(app.settings.word_source))) {
      app.loadWords(app.settings.word_source).then(() => toast(app.bank.note));
    }
    if (key === "quote_source" && v === "online") app.quotes.loadOnline().then(() => app.quotes.note && toast(app.quotes.note));
    if (key === "keyboard_learn" && v) app.keyboard.call("status").then(() => this.list.refresh());
    if (RESTYLE.test(key) || key.startsWith("theme_")) this.ui.restyle();
  }

  async editText(key, label) {
    const input = h("input", { type: "text", value: this.app.settings[key] });
    setTimeout(() => { input.focus(); input.select(); }, 0);
    const ok = await this.ui.dialog(label, input, [{ label: "save", value: true }, { label: "cancel", value: false }], { cancel: false });
    if (ok) this.set(key, input.value.trim() || DEFAULTS[key]);
    this.list.refresh();
  }

  async confirm(question, act) {
    const yes = await this.ui.dialog(question, null, [{ label: "yes", value: true, key: "y" }, { label: "no", value: false, key: "n" }], { cancel: false });
    if (yes) {
      act();
      toast("done");
      this.list.refresh();
    }
  }

  importFile() {
    const input = h("input", { type: "file", accept: ".json,application/json", multiple: true });
    input.addEventListener("change", async () => {
      for (const f of input.files ?? []) {
        let kind = null;
        try {
          kind = this.app.importJson(JSON.parse(await f.text()));
        } catch {
          kind = null;
        }
        toast(kind ? `${f.name}: ${kind} imported` : `${f.name}: not a minitype save or settings file`);
      }
      this.ui.restyle();
      this.app.loadWords(this.app.settings.word_source);
      this.drawRows();
    });
    input.click();
  }

  drawRows() {
    const items = this.items();
    this.list = new RowList(items, {
      cursor: 0,
      labelWidth: "15em",
      onSelect: (it) => { this.help.textContent = it.help ?? ""; },
    });
    this.rowsBox.replaceChildren(this.list.el);
    this.help.textContent = items[0]?.help ?? (this.query ? "nothing found" : "");
    this.drawTabs();
  }

  fieldKey(key) {
    if (key === "ESC" && this.query) {
      this.query = "";
      this.search.value = "";
      this.drawRows();
    }
  }

  onKey(key) {
    if (key === "ESC") return this.leave();
    if (key === "/") return this.search.focus();
    if (key === "TAB" || key === "]") return this.setTab(this.tab + 1);
    if (key === NAV.SHIFT_TAB || key === "[") return this.setTab(this.tab - 1);
    this.list.key(key);
  }

  leave() {
    if (this.over) return this.ui.back();
    this.ui.go(MENU);
  }

  destroy() {}
}
