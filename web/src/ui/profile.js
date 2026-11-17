// Long-term progress (ui/profile.py): totals, a speed chart, the days you
// typed, personal bests, best words on their own rows, and the daily goal.

import * as bestWords from "../core/bestWords.js";
import { dayKey } from "../core/history.js";
import { MENU } from "../core/test.js";
import { fmtTime, h, svg, NAV } from "./dom.js";
import { goalLine } from "./menu.js";

const CHART_RUNS = 60;
const CAL_WEEKS = 26;

function sparkChart(values, width = 900, height = 110) {
  const lo = Math.min(...values), hi = Math.max(...values);
  const span = hi - lo || 1;
  const x = (i) => (i / (values.length - 1)) * width;
  const y = (v) => height - 8 - ((v - lo) / span) * (height - 16);
  const pts = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  return svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, preserveAspectRatio: "none", style: "height:110px" },
    svg("polyline", { class: "speed", points: pts }),
    ...values.map((v, i) => svg("circle", { cx: x(i), cy: y(v), r: 2.5, fill: "var(--accent)" })));
}

export function calendar(app, today = new Date()) {
  const days = app.history.daySeconds();
  const goal = app.settings.daily_goal * 60;
  const steps = goal ? [goal / 2, goal] : [5 * 60, 15 * 60];
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7) - 7 * (CAL_WEEKS - 1));
  const el = h("div.cal");
  const todayKey = dayKey(today);
  for (let w = 0; w < CAL_WEEKS; w++) {
    for (let d = 0; d < 7; d++) {
      const day = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + w * 7 + d);
      const key = dayKey(day);
      const secs = days[key] ?? 0;
      const level = !secs ? 0 : secs < steps[0] ? 1 : secs < steps[1] ? 2 : 3;
      el.append(h(`div${key > todayKey ? ".future" : level ? `.l${level}` : ""}`, { title: `${key}: ${fmtTime(secs)}` }));
    }
  }
  return el;
}

export class ProfileScreen {
  constructor(ui) {
    this.ui = ui;
    this.app = ui.app;
    this.navName = "profile";
    this.hints = "esc back   ↑/↓ scroll";
    this.el = h("div.profile");
    this.draw();
  }

  draw() {
    const app = this.app, hist = app.history;
    const normal = hist.normal();
    const runs = normal.filter((r) => !r.failed);
    const out = [];
    if (!hist.runs.length) out.push(h("p.dim", "no tests yet - type one, or import minitype's save.json in settings › data"));
    else {
      const wpms = runs.map((r) => hist.speed(r));
      const last = runs.slice(-10);
      const avg = last.length ? last.reduce((a, r) => a + hist.speed(r), 0) / last.length : 0;
      const acc = last.length ? last.reduce((a, r) => a + r.acc, 0) / last.length : 0;
      const [now, best] = hist.streak();
      const stats = [
        ["tests", normal.length],
        ["time typed", fmtTime(hist.totalSeconds())],
        ["top speed", `${(wpms.length ? Math.max(...wpms) : 0).toFixed(0)} wpm`],
        ["average (last 10)", `${avg.toFixed(0)} wpm`],
        ["accuracy (last 10)", `${acc.toFixed(1)}%`],
        ["failed", normal.length - runs.length],
        ["streak", best ? `${now} day${now === 1 ? "" : "s"}${best > now ? ` (best ${best})` : ""}` : "-"],
      ];
      const bw = bestWords.summary(hist);
      if (bw) {
        const [n, bavg, bacc, btop] = bw;
        stats.push(["best words", `${n} test${n === 1 ? "" : "s"}, top ${btop.toFixed(0)}`], ["best words average", `${bavg.toFixed(0)} wpm, ${bacc.toFixed(1)}%`]);
      }
      out.push(h("div.stat-grid", stats.map(([k, v]) => h("div.stat", h("div.label", k), h("div.val", v)))));
      const chart = runs.slice(-CHART_RUNS).map((r) => hist.speed(r));
      if (chart.length > 1) {
        out.push(h("h3", `speed, last ${chart.length} tests   ${Math.min(...chart).toFixed(0)}-${Math.max(...chart).toFixed(0)} wpm`), sparkChart(chart));
      }
      out.push(h("h3", "days typed"), calendar(app));
      const pbs = Object.entries(hist.pbs).sort((a, b) => hist.speed(b[1]) - hist.speed(a[1]));
      if (pbs.length) {
        out.push(h("h3", "personal bests"), h("table.pbs", pbs.map(([mode, pb]) =>
          h("tr", h("td", mode), h("td", `${hist.speed(pb).toFixed(0)} wpm`), h("td.dim", `${(pb.acc ?? 0).toFixed(0)}%`)))));
      }
    }
    const goal = goalLine(app);
    if (goal) out.push(h("h3", "today"), h("div", goal));
    if (!app.saving()) out.push(h("p.dim", "saving is off: history is kept for this session only"));
    this.el.replaceChildren(...out);
  }

  onKey(key) {
    if (key === "ESC" || key === "p" || key === "ENTER") return this.ui.go(MENU);
    if (key === NAV.DOWN) window.scrollBy({ top: 120, behavior: "smooth" });
    if (key === NAV.UP) window.scrollBy({ top: -120, behavior: "smooth" });
  }
}
