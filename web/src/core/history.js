// Every finished test, kept across sessions (history.py). Runs and personal
// bests have the same shape as save.json's "history" and "pbs".

export const MAX_RUNS = 2000;

/** Local midnight (seconds) of the day `now` (seconds) is in. */
export function dayStart(now = Date.now() / 1000) {
  const d = new Date(now * 1000);
  d.setHours(0, 0, 0, 0);
  return d.getTime() / 1000;
}

/** "YYYY-MM-DD" of a local date. */
export function dayKey(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function daysBetween(a, b) {
  // whole local days from key a to key b (DST safe: noon to noon)
  const [ya, ma, da] = a.split("-").map(Number), [yb, mb, db] = b.split("-").map(Number);
  return Math.round((new Date(yb, mb - 1, db, 12) - new Date(ya, ma - 1, da, 12)) / 86400000);
}

const r1 = (x) => Math.round(x * 10) / 10;

export class History {
  constructor() {
    // {t, mode, wpm, acc, secs, failed[, awpm][, tag]}; tag "best": a best-words run
    this.runs = [];
    this.pbs = {};             // mode -> {wpm, acc, t[, awpm]}
    this.system = () => "classic";
    this.clock = () => Date.now() / 1000;
  }

  speed(r) {
    if (this.system() === "active") return r.awpm ?? r.wpm ?? 0;
    return r.wpm ?? 0;
  }

  /** What a run is compared against: its mode, plus the difficulty when not normal. */
  static mode(result) {
    const spec = result.spec;
    const m = ["learn", "book"].includes(spec.source) ? spec.source : spec.label;
    return result.difficulty === "normal" ? m : `${m} (${result.difficulty})`;
  }

  pb(result) {
    return this.speed(this.pbs[History.mode(result)] ?? {}) || 0;
  }

  /** Log a run. Returns true if it set a new personal best. */
  add(result) {
    const mode = History.mode(result);
    const now = Math.round(this.clock());
    const run = {
      t: now, mode,
      wpm: r1(result.classic || result.wpm),
      awpm: r1(result.active || result.wpm),
      acc: r1(result.acc),
      secs: r1(result.elapsed),
      failed: result.failed,
    };
    if (result.spec.source === "best") run.tag = "best";
    this.runs.push(run);
    if (this.runs.length > MAX_RUNS) this.runs.splice(0, this.runs.length - MAX_RUNS);
    if (result.failed) return false;
    const isNew = result.wpm > this.pb(result);
    const old = this.pbs[mode] ?? {};
    const classic = result.classic || result.wpm, active = result.active || result.wpm;
    const best = { ...old };
    if (classic > (old.wpm ?? 0)) Object.assign(best, { wpm: r1(classic), acc: r1(result.acc), t: now });
    if (active > (old.awpm ?? old.wpm ?? 0)) best.awpm = r1(active);
    best.acc ??= r1(result.acc);
    best.t ??= now;
    best.wpm ??= r1(classic);
    this.pbs[mode] = best;
    return isNew;
  }

  completed() { return this.runs.filter((r) => !r.failed); }
  normal() { return this.runs.filter((r) => r.tag !== "best"); }
  totalSeconds() { return this.runs.reduce((s, r) => s + r.secs, 0); }

  todaySeconds() {
    const start = dayStart(this.clock());
    return this.runs.filter((r) => r.t >= start).reduce((s, r) => s + r.secs, 0);
  }

  /** {"YYYY-MM-DD": seconds typed that day} */
  daySeconds() {
    const days = {};
    for (const r of this.runs) {
      const k = dayKey(new Date(r.t * 1000));
      days[k] = (days[k] ?? 0) + r.secs;
    }
    return days;
  }

  /** [days in a row you've typed, the longest run of days ever]. */
  streak(today = null) {
    const days = Object.keys(this.daySeconds()).sort();
    today = today ?? dayKey(new Date(this.clock() * 1000));
    let best = 0, run = 0, prev = null;
    for (const d of days) {
      run = prev !== null && daysBetween(prev, d) === 1 ? run + 1 : 1;
      best = Math.max(best, run);
      prev = d;
    }
    const last = days[days.length - 1];
    const current = last !== undefined && daysBetween(last, today) <= 1 ? run : 0;
    return [current, best];
  }

  bestByMode() {
    const best = {};
    for (const r of this.completed()) best[r.mode] = Math.max(best[r.mode] ?? 0, this.speed(r));
    return best;
  }

  apply(runs, pbs) {
    const need = ["t", "mode", "wpm", "acc", "secs", "failed"];
    if (Array.isArray(runs)) {
      this.runs = runs.filter((r) => r && typeof r === "object" && need.every((k) => k in r));
      if (this.runs.length > MAX_RUNS) this.runs.splice(0, this.runs.length - MAX_RUNS);
    }
    if (pbs && typeof pbs === "object") {
      this.pbs = Object.fromEntries(Object.entries(pbs)
        .filter(([, v]) => v && typeof v === "object" && typeof v.wpm === "number"));
    }
  }

  /** Another history's runs added to these (an import): no run twice, the
   * better personal best of each mode kept. */
  merge(runs, pbs) {
    const other = new History();
    other.apply(runs, pbs);
    const seen = new Set(this.runs.map((r) => `${r.t}|${r.mode}|${r.wpm}`));
    for (const r of other.runs) if (!seen.has(`${r.t}|${r.mode}|${r.wpm}`)) this.runs.push(r);
    this.runs.sort((a, b) => a.t - b.t);
    if (this.runs.length > MAX_RUNS) this.runs.splice(0, this.runs.length - MAX_RUNS);
    for (const [m, v] of Object.entries(other.pbs)) {
      const mine = this.pbs[m];
      if (!mine) { this.pbs[m] = v; continue; }
      const best = { ...mine };
      if (v.wpm > mine.wpm) Object.assign(best, { wpm: v.wpm, acc: v.acc, t: v.t });
      if ((v.awpm ?? v.wpm) > (mine.awpm ?? mine.wpm)) best.awpm = v.awpm ?? v.wpm;
      this.pbs[m] = best;
    }
  }
}
