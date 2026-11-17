// The settings (ui/settings_menu.py + tree_menu.py, for the browser): every
// setting in one column, grouped by tab and page; a sidebar with the outline
// (tabs, their pages and sub-pages) jumps there and follows where you are as
// you scroll; the help on the right. ←/→ change a value, tab or [ ] jump a
// tab, / searches, esc goes back. On a narrow screen the sidebar folds into a
// "sections" button.

import { CHOICES, DEFAULTS, cycle } from "../core/settings.js";
import { WORD_SOURCES } from "../core/settings.js";
import { MENU } from "../core/test.js";
import { h, toast, NAV } from "./dom.js";
import { RowList } from "./rows.js";
import { TREE, flatten, outline } from "./settingsTree.js";

const RESTYLE = /^(theme|accent_text|untyped_lighten|fun_|effect_speed|flow_direction|smooth_caret|caret$|lowkey|fx_bg|fx_glass|fx_tiles)/;
const SEP = " › ";
const SPY_TOP = 120;      // px from the top of the window where "you are here" is read

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
    this.query = "";
    this.here = "";            // the section (its path joined by SEP) you're looking at
    this.open = new Set([TREE[0][0]]);   // tabs whose pages show in the sidebar
    this.outlineEls = new Map();         // path -> sidebar entry
    this.side = h("nav.side-tree");
    this.menuBtn = h("button.btn.sections-btn", { on: { click: () => this.el.classList.toggle("tree-open") } }, "☰ sections");
    this.search = h("input.search", {
      type: "search", placeholder: "/ search all settings",
      on: { input: () => { this.query = this.search.value.trim().toLowerCase(); this.drawRows(); } },
    });
    this.rowsBox = h("div.settings-rows");
    this.help = h("div.help");
    this.el = h("div.settings",
      h("div.side-col", this.side),
      h("div.main-col", h("div.settings-top", this.menuBtn, this.search), this.rowsBox),
      h("div.side", this.help));
    this.drawRows();
    this.drawSide();
    this.start = tab ? [tab] : this.app.cursors.settingsAt ?? null;
  }

  shown() {
    this.onScroll = () => {
      if (this.spyQueued) return;
      this.spyQueued = true;
      requestAnimationFrame(() => { this.spyQueued = false; this.spy(); });
    };
    window.addEventListener("scroll", this.onScroll, { passive: true });
    if (this.start) this.jump(this.start, false);
    else {
      window.scrollTo({ top: 0 });
      this.spy();
    }
  }

  resume() { this.shown(); }

  destroy() {
    window.removeEventListener("scroll", this.onScroll);
  }

  /** The sidebar: each tab, and under the open ones their pages and sub-pages. */
  drawSide() {
    this.outlineEls.clear();
    const entry = (node) => {
      const key = node.path.join(SEP);
      const isTab = node.depth === 0;
      const el = h(`a.tree-item.d${node.depth}`, {
        href: "#",
        on: {
          click: (e) => {
            e.preventDefault();
            if (isTab && this.open.has(node.name) && this.here.startsWith(key)) {
              this.open.delete(node.name);              // the tab you're in: fold it
              return this.drawSide();
            }
            this.jump(node.path);
            this.el.classList.remove("tree-open");
          },
        },
      }, isTab ? h("span.caret-ico", this.open.has(node.name) ? "▾" : "▸") : null, node.name);
      this.outlineEls.set(key, el);
      const kids = isTab && !this.open.has(node.name) ? [] : node.children.map(entry);
      return [el, ...kids];
    };
    this.side.replaceChildren(...outline().map(entry).flat(Infinity));
    this.mark();
  }

  /** Scroll to a group (its first section) and select its first row. */
  jump(path, smooth = true) {
    const key = path.join(SEP);
    if (this.query) {
      this.query = "";
      this.search.value = "";
      this.drawRows();
    }
    if (!this.open.has(path[0])) {
      this.open.add(path[0]);
      this.drawSide();
    }
    const title = [...this.rowsBox.querySelectorAll(".section-title")]
      .find((t) => t.dataset.section === key || t.dataset.section.startsWith(key + SEP));
    if (!title) return;
    const y = title.getBoundingClientRect().top + window.scrollY - 70;
    window.scrollTo({ top: Math.max(0, y), behavior: smooth ? "smooth" : "auto" });
    const i = this.list.items.findIndex((it) => it.section === title.dataset.section);
    if (i >= 0) this.list.select(i);
    this.setHere(title.dataset.section);
    this.pinned = performance.now() + (smooth ? 700 : 50);   // the smooth scroll doesn't move "here" on the way
  }

  /** Where you are: the last section heading above the reading line. */
  spy() {
    if (this.pinned && performance.now() < this.pinned) return;
    const titles = [...this.rowsBox.querySelectorAll(".section-title")];
    if (!titles.length) return;
    let here = titles[0].dataset.section;
    for (const t of titles) {
      if (t.getBoundingClientRect().top <= SPY_TOP) here = t.dataset.section;
      else break;
    }
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      here = titles[titles.length - 1].dataset.section;    // the bottom: the last section, however short
    }
    this.setHere(here);
  }

  setHere(here) {
    if (here === this.here) return;
    this.here = here;
    if (!this.query) this.app.cursors.settingsAt = here.split(SEP);
    const tab = here.split(SEP)[0];
    if (!this.open.has(tab) && !this.query) {
      this.open.add(tab);
      this.drawSide();
    } else this.mark();
  }

  /** Light up the sidebar entries for where you are: the tab, page and sub-page. */
  mark() {
    for (const [key, el] of this.outlineEls) {
      const on = this.here === key || this.here.startsWith(key + SEP);
      el.classList.toggle("on", on);
      el.classList.toggle("exact", this.here === key);
      if (this.here === key) el.scrollIntoView({ block: "nearest" });
    }
  }

  items() {
    const out = [];
    for (const { path, row } of flatten()) {
      const it = Array.isArray(row) ? this.settingItem(row) : this.actionItem(row);
      it.section = path.join(SEP);
      it.sectionLabel = h("span", ...path.slice(0, -1).map((p) => h("span.sub", p + SEP)), path[path.length - 1]);
      if (this.query && !`${it.label} ${it.help} ${path.join(" ")}`.toLowerCase().includes(this.query)) continue;
      out.push(it);
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
    const sel = this.list?.current()?.label;
    this.list = new RowList(items, {
      cursor: Math.max(0, items.findIndex((it) => it.label === sel)),
      labelWidth: "15em",
      onSelect: (it) => {
        this.help.textContent = it.help ?? "";
        if (!this.query && document.activeElement !== this.search) this.setHere(it.section);
      },
    });
    this.rowsBox.replaceChildren(this.list.el);
    if (!items.length) this.rowsBox.append(h("p.dim", "nothing found"));
    this.help.textContent = this.list.current()?.help ?? "";
    this.here = "";
    if (this.query) window.scrollTo({ top: 0 });
    requestAnimationFrame(() => this.spy());
  }

  /** The first row of the next (or previous) tab. */
  tabStep(step) {
    const tabs = TREE.map(([name]) => name);
    const cur = (this.list.current()?.section ?? this.here).split(SEP)[0];
    this.jump([tabs[(tabs.indexOf(cur) + step + tabs.length) % tabs.length]]);
  }

  fieldKey(key) {
    if (key === "ESC" && this.query) {
      this.query = "";
      this.search.value = "";
      this.drawRows();
    }
  }

  onKey(key) {
    if (key === "ESC") {
      if (this.el.classList.contains("tree-open")) return this.el.classList.remove("tree-open");
      return this.leave();
    }
    if (key === "/") return this.search.focus();
    if (key === "TAB" || key === "]") return this.tabStep(1);
    if (key === NAV.SHIFT_TAB || key === "[") return this.tabStep(-1);
    this.list.key(key);
  }

  leave() {
    if (this.over) return this.ui.back();
    this.ui.go(MENU);
  }
}
