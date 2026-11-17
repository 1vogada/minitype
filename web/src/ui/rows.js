// A list of rows to pick from (ui/menu.py's Menu, for the browser): up / down
// or the mouse pick one, its help shows; left / right change its value, enter
// (or a click) uses it; a row's own key jumps straight to it.

import { h, NAV } from "./dom.js";

export class RowList {
  /** items: [{key?, label, value?(), left?(), right?(), enter?(), help?, section?, warn?()}] */
  constructor(items, { cursor = 0, onChange = null, onSelect = null, labelWidth = null } = {}) {
    this.items = items;
    this.sel = Math.min(cursor, items.length - 1);
    this.onChange = onChange;        // after a value changed
    this.onSelect = onSelect;        // after the selection moved
    this.el = h("div.rows");
    this.labelWidth = labelWidth;
    this.render();
  }

  render() {
    this.el.replaceChildren();
    this.rowEls = [];
    let section = null;
    this.items.forEach((it, i) => {
      if (it.section && it.section !== section) {
        section = it.section;
        this.el.append(h("div.section-title", section));
      }
      const row = h("div.row", {
        on: {
          mouseenter: () => this.select(i),
          click: (e) => {
            if (e.target.closest(".arrow")) return;
            this.select(i);
            this.use(i);
          },
        },
      });
      this.fill(row, it);
      this.rowEls.push(row);
      this.el.append(row);
    });
    this.select(this.sel, false);
  }

  fill(row, it) {
    const val = it.value ? it.value() : "";
    const value = h("span.value");
    if (it.left || it.right) {
      value.append(
        h("span.arrow", { on: { click: () => this.change(row, it, -1) } }, "‹"),
        h("span.v", val),
        h("span.arrow", { on: { click: () => this.change(row, it, 1) } }, "›"),
      );
    } else if (val) value.append(h("span.v.dim", val));
    const warn = it.warn?.();
    if (warn) value.append(h("span.warn", " ", warn));
    row.replaceChildren(h("span.key", it.key && it.key.length === 1 ? it.key : ""), h("span.label", it.label), value);
    if (this.labelWidth) row.style.gridTemplateColumns = `2.2em ${this.labelWidth} 1fr`;
  }

  change(row, it, step) {
    const fn = step > 0 ? it.right : it.left;
    if (!fn) return;
    fn();
    this.fill(row, it);
    this.onChange?.(it);
  }

  refresh() {
    this.items.forEach((it, i) => this.fill(this.rowEls[i], it));
  }

  select(i, notify = true) {
    if (i < 0 || i >= this.items.length) return;
    this.sel = i;
    this.rowEls.forEach((r, k) => r.classList.toggle("sel", k === i));
    if (notify) this.onSelect?.(this.items[i], i);
  }

  current() { return this.items[this.sel]; }

  use(i = this.sel) {
    return this.items[i]?.enter?.();
  }

  /** A key for the list; returns {handled, result}. */
  key(key) {
    const n = this.items.length;
    if (key === NAV.UP) return this.moved((this.sel - 1 + n) % n);
    if (key === NAV.DOWN) return this.moved((this.sel + 1) % n);
    if (key === NAV.HOME) return this.moved(0);
    if (key === NAV.END) return this.moved(n - 1);
    const it = this.items[this.sel];
    if (key === NAV.LEFT && it?.left) { this.change(this.rowEls[this.sel], it, -1); return { handled: true }; }
    if (key === NAV.RIGHT && it?.right) { this.change(this.rowEls[this.sel], it, 1); return { handled: true }; }
    if (key === "ENTER" || (key === NAV.RIGHT && it?.enter && !it.right)) return { handled: true, result: this.use() };
    const k = this.items.findIndex((x) => x.key && x.key === key);
    if (k >= 0) {
      this.select(k);
      return { handled: true, result: this.use(k) };
    }
    return { handled: false };
  }

  moved(i) {
    this.select(i);
    this.rowEls[i]?.scrollIntoView({ block: "nearest" });
    return { handled: true };
  }
}
