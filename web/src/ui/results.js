// The results screen (ui/results.py): the speed, personal best, a speed chart,
// the key heatmap, details, and what's next (tab restart, r replay, f favourite).

import { LAYOUTS } from "../core/config.js";
import { speedSeries } from "../core/scoring.js";
import { MENU } from "../core/test.js";
import { patternText, statusLine } from "../core/keyboardApp.js";
import { h, svg } from "./dom.js";
import { goalLine } from "./menu.js";
import { KeyboardView } from "./testScreen.js";

const HEAT_FALLBACK = ["#5fd75f", "#ffaf00", "#ff5f5f"];

export function isFav(app, r) {
  return app.settings.fav_quotes.some((q) => q.text === r.quote);
}

/** The speed through the test as a line, with a dot on every slice that had errors. */
export function speedChart(r, width = 900, height = 150) {
  if (r.elapsed < 1 || !r.events.length) return null;
  const buckets = Math.max(2, Math.min(Math.floor(r.elapsed), 60));
  const series = speedSeries(r.events, r.elapsed, buckets);
  const top = Math.max(10, ...series.map(([v]) => v)) * 1.1;
  const pad = 28;
  const x = (i) => pad + (i / (series.length - 1)) * (width - pad - 6);
  const y = (v) => height - 18 - (v / top) * (height - 30);
  const pts = series.map(([v], i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const el = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, preserveAspectRatio: "none" });
  for (const f of [0, 0.5, 1]) {
    const v = top * f / 1.1;
    el.append(svg("line", { class: "grid", x1: pad, x2: width, y1: y(v), y2: y(v) }), svg("text", { x: 0, y: y(v) + 4 }, v.toFixed(0)));
  }
  el.append(svg("path", { class: "area", d: `M${x(0)},${y(0)} L${pts.join(" L")} L${x(series.length - 1)},${y(0)} Z` }));
  el.append(svg("polyline", { class: "speed", points: pts.join(" ") }));
  series.forEach(([v, e], i) => { if (e) el.append(svg("circle", { class: "err", cx: x(i), cy: y(v), r: Math.min(5, 2 + e) })); });
  el.append(svg("text", { x: width - 4, y: height - 2, "text-anchor": "end" }, `${r.elapsed.toFixed(0)}s`));
  return el;
}

export class ResultsScreen {
  constructor(ui, r) {
    this.ui = ui;
    this.app = ui.app;
    this.r = r;
    this.navName = "menu";
    const s = this.app.settings;
    this.hints = `tab restart   r replay   enter next   esc menu${r.quote ? "   f favourite" : ""}`;
    this.el = h("div.results");
    if (s.fx_reveal && !ui.fx.cheap) this.el.classList.add("reveal");
    this.choices = [
      { key: "TAB", label: r.spec.replay ? "same words again" : "next test", act: () => ui.go(r.spec) },
      { key: "r", label: "replay", act: () => ui.go({ replayOf: r }) },
      { key: "m", label: "menu", act: () => ui.go(MENU) },
    ];
    if (r.quote) this.choices.push({ key: "f", label: isFav(this.app, r) ? "unfavourite" : "favourite", act: () => this.toggleFav() });
    this.draw();
  }

  shown() {
    this.off = this.app.keyboard.onChange(() => this.drawLearn());
  }

  destroy() { this.off?.(); }

  draw() {
    const r = this.r, app = this.app, s = app.settings;
    const parts = [];
    const top = h("div.res-top");
    if (r.failed) top.append(h("div.res-failed", "failed", h("div.dim", { style: { fontSize: "15px", fontWeight: 400 } }, r.failReason || r.difficulty)));
    else {
      const other = r.system === "active" ? ["classic", r.classic] : ["active", r.active];
      top.append(h("div.res-wpm", r.wpm.toFixed(1), h("small", "wpm"),
        other[1] && Math.abs(other[1] - r.wpm) >= 0.05 ? h("div.dim", { style: { fontSize: "14px", fontWeight: 400, marginTop: "6px" } }, `${other[1].toFixed(1)} ${other[0]}`) : null));
    }
    const time = r.system === "active" && r.activeSecs && r.elapsed - r.activeSecs >= 1
      ? `${r.elapsed.toFixed(1)}s (${r.activeSecs.toFixed(1)}s typing)` : `${r.elapsed.toFixed(1)}s`;
    top.append(h("div.res-stats", ...[["raw", r.raw.toFixed(1)], ["accuracy", `${r.acc.toFixed(1)}%`], ["time", time], ["errors", r.errors], ["combo", r.bestCombo]]
      .map(([k, v]) => h("div", h("b", v), k))));
    parts.push(top);
    const lines = h("div.res-line");
    if (r.note || r.quote) lines.append(h("div", r.quote && isFav(app, r) ? h("span.accent", "★ ") : "", r.note ? `- ${r.note}` : ""));
    for (const line of this.pbLines()) lines.append(line);
    parts.push(lines);
    if (s.res_chart) {
      const chart = speedChart(r);
      if (chart) parts.push(chart);
    }
    const grid = h("div.res-grid");
    if (s.res_heatmap && Object.keys(r.presses).length) grid.append(this.heatmap());
    const details = this.details();
    if (details.childNodes.length) grid.append(details);
    parts.push(grid);
    this.learnEl = h("div.res-line");
    parts.push(this.learnEl);
    this.choiceEls = this.choices.map((c, i) => h(`button.btn${i === 0 ? ".primary" : ""}`, { on: { click: () => c.act() } }, c.key === "TAB" ? "tab " : `${c.key} `, h("span.dim", c.label)));
    parts.push(h("div.choices", this.choiceEls));
    this.el.replaceChildren(...parts);
    this.drawLearn();
  }

  pbLines() {
    const r = this.r, app = this.app;
    if (!r.counted) return [h("div", `${app.settings.funbox} mode - just for fun, not kept`)];
    const out = [];
    if (r.spec.source === "best") out.push(h("div", "best words - kept apart from your normal stats"));
    if (!app.settings.res_pb || r.failed || r.spec.source === "zen") return out;
    if (r.wpm > r.pbBefore) {
      out.push(r.pbBefore ? h("div", h("span.pb", "new personal best! "), `+${(r.wpm - r.pbBefore).toFixed(1)} wpm`)
        : h("div", "first run of this mode: personal best set"));
    } else out.push(h("div", `personal best ${r.pbBefore.toFixed(1)} (${(r.wpm - r.pbBefore >= 0 ? "+" : "") + (r.wpm - r.pbBefore).toFixed(1)})`));
    return out;
  }

  heatmap() {
    const r = this.r, s = this.app.settings, st = this.ui.st;
    const [clean, some, many] = st.mono ? ["#d0d0d0", "#8a8a8a", "#ffffff"] : [st.good, st.warn, st.error].map((c, i) => c || HEAT_FALLBACK[i]);
    const keyset = new Set((LAYOUTS[s.layout] ?? LAYOUTS.qwerty).join(""));
    const colours = {};
    for (const [c0, n] of Object.entries(r.presses)) {
      const c = c0.toLowerCase();
      if (!keyset.has(c) || !n) continue;
      const rate = (r.misses[c] ?? 0) / n;
      colours[c] = rate === 0 ? clean : rate < 0.1 ? some : many;
    }
    const kb = new KeyboardView(s.layout);
    kb.el.classList.add("small");
    kb.el.style.marginTop = "6px";
    kb.el.lastChild.remove();
    kb.colour(colours);
    return h("div.res-block", h("h4", "keys"),
      h("div.legend", h("span", { style: { color: clean } }, "clean"), h("span", { style: { color: some } }, "some misses"), h("span", { style: { color: many } }, "many misses")), kb.el);
  }

  details() {
    const r = this.r, app = this.app, s = app.settings, stats = app.stats;
    const out = h("div.res-block");
    const add = (title, text) => out.append(h("h4", title), h("div", text));
    if (r.learnReport) add("learn", r.learnReport.join("  ·  "));
    if (s.res_worst_keys && Object.keys(r.misses).length) {
      add("worst keys", Object.entries(r.misses).sort((a, b) => b[1] - a[1]).slice(0, 5)
        .map(([k, v]) => `${k === " " ? "_" : k}×${v}`).join("   "));
    }
    const flagged = stats.badKeys();
    if (s.res_session_keys && flagged.length) {
      add("session keys", flagged.sort((a, b) => (stats.errors[b] ?? 0) - (stats.errors[a] ?? 0)).map((c) => `${c} - ${stats.errors[c] ?? 0}`).join("; "));
    }
    if (s.res_bad_words && Object.keys(stats.missed).length) {
      add("bad words", Object.entries(stats.missed).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([w, n]) => `${w}×${n}`).join("   "));
    }
    if (s.res_history && stats.history.length) {
      add("session", `${stats.history.slice(-5).map((v) => v.toFixed(0)).join("  ")}   best ${stats.best().toFixed(0)}`);
    }
    const goal = goalLine(app);
    if (goal) add("today", goal);
    return out;
  }

  drawLearn() {
    const line = statusLine(this.app);
    const pat = this.app.settings.keyboard_learn ? patternText(this.app.keyboard.patterns) : "";
    this.learnEl?.replaceChildren(...(line ? [h("div", line)] : []), ...(pat ? [h("div", pat)] : []));
  }

  toggleFav() {
    const app = this.app, r = this.r, favs = app.settings.fav_quotes;
    if (isFav(app, r)) app.settings.fav_quotes = favs.filter((q) => q.text !== r.quote);
    else favs.push({ text: r.quote, source: r.note });
    app.saveSettings();
    this.choices[this.choices.length - 1].label = isFav(app, r) ? "unfavourite" : "favourite";
    this.draw();
  }

  onKey(key) {
    if (key === "ESC" || key === "m" || key === "q") return this.ui.go(MENU);
    if (key === "TAB" || key === "ENTER" || key === " ") return this.ui.go(this.r.spec);
    const c = this.choices.find((x) => x.key === key);
    if (c) c.act();
  }
}
