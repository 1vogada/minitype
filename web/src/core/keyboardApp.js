// Learn as you type, for the MAX68HE magnetic keyboard (keyboard_app.py).
// POST {server}/api/learn/typing with {"action": "status" | "on" | "off" |
// "events", ...}. The app not running is normal. Nothing here throws, and
// nothing waits on it: a test's keystrokes go in the background, and the ones
// the app can't take (not running) wait in a queue (kept in storage) and go
// first the next time it answers.

export const SERVER = "http://127.0.0.1:6869";
export const PATH = "/api/learn/typing";
export const PROXY = "/kb";            // the dev server passes /kb/... to the app (vite.config.js)
export const TIMEOUT = 1000;           // ms
export const NOT_RUNNING = "app not running";
export const NEEDS_LOCAL = "needs the local app (npm run dev)";
export const MAX_EVENTS = 2000;        // keystrokes per events call
export const MAX_QUEUED = 20000;
export const QUEUE_KEY = "minitype.keyboard_queue";

export class Answer {
  constructor(state = null, error = null) {
    this.state = state;
    this.error = error;
  }
  get ok() { return this.state !== null; }
  get on() { return Boolean(this.ok && this.state.on); }

  line() {
    if (!this.ok) return `keyboard learn: ${this.error || NOT_RUNNING}`;
    const s = this.state;
    if (!s.on) return "keyboard learn: off";
    const count = (v) => (Number.isInteger(v) && v >= 0 ? v : 0);
    const tuned = count(s.tunedKeys), learning = count(s.learningKeys);
    const parts = ["on", `${tuned} key${tuned === 1 ? "" : "s"} tuned`];
    if (learning) parts.push(`${learning} learning`);
    if (typeof s.lastError === "string" && s.lastError) parts.push(short(s.lastError));
    return "keyboard learn: " + parts.join(" · ");
  }
}

export function short(text, n = 40) {
  text = String(text).split(/\s+/).filter(Boolean).join(" ");
  return text.length <= n ? text : text.slice(0, n - 1) + "…";
}

/** The server to ask, localhost as 127.0.0.1 (the app listens on IPv4 only). */
export function serverUrl(server) {
  let s = typeof server === "string" ? server.trim().replace(/\/+$/, "") : "";
  if (!/^https?:\/\/./.test(s)) s = SERVER;
  return s.replace(/^(https?:\/\/)localhost(?=[:/]|$)/, "$1127.0.0.1");
}

export const eventsBody = (events) => ({ action: "events", events: [...events] });

export function batches(events, n = MAX_EVENTS) {
  const out = [];
  for (let i = 0; i < events.length; i += n) out.push(events.slice(i, i + n));
  return out;
}

/** The client: `fetchImpl` and `store` ({get(key), set(key, value)}) are handed in. */
export class KeyboardApp {
  constructor({ fetchImpl = globalThis.fetch?.bind(globalThis), store = null, server = SERVER, proxy = PROXY, local = true } = {}) {
    this.fetch = fetchImpl;
    this.store = store;
    this.server = server;
    this.proxy = proxy;            // null: always straight to the server
    this.route = null;             // what worked last: "direct" or "proxy"
    // false on a page served over https from elsewhere (GitHub Pages): it can't
    // reach http://127.0.0.1 (mixed content) and has no proxy, so nothing is
    // tried and the keystrokes wait in the queue for the local version
    this.local = local;
    this.last = null;              // the last Answer
    this.patterns = null;          // what the app made of the last test's mistakes
    this.sending = Promise.resolve();
    this.listeners = new Set();
  }

  onChange(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emit() { for (const fn of this.listeners) try { fn(this); } catch { /* a screen's problem */ } }

  urls() {
    const direct = serverUrl(this.server) + PATH;
    const proxied = this.proxy !== null ? this.proxy + PATH : null;
    const all = [["direct", direct], ...(proxied ? [["proxy", proxied]] : [])];
    return this.route === "proxy" ? all.reverse() : all;
  }

  async post(body) {
    if (!this.local) return new Answer(null, NEEDS_LOCAL);
    let lastError = NOT_RUNNING;
    for (const [route, url] of this.urls()) {
      const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
      const timer = ctl ? setTimeout(() => ctl.abort(), TIMEOUT) : null;
      try {
        const r = await this.fetch(url, {
          method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(body), signal: ctl?.signal,
        });
        let reply = null;
        try { reply = await r.json(); } catch { reply = null; }
        if (!r.ok) {
          // the proxy with nothing behind it answers 5xx / 404: the app isn't there
          if (route === "proxy" && (r.status >= 500 || r.status === 404) && !reply?.error) continue;
          this.route = route;
          const why = reply && typeof reply.error === "string" && reply.error ? short(reply.error) : `error ${r.status}`;
          return new Answer(null, why);
        }
        if (!reply || typeof reply.on !== "boolean") return new Answer(null, "odd answer from the app");
        this.route = route;
        return new Answer(reply);
      } catch {
        lastError = NOT_RUNNING;      // refused, timed out, blocked (CORS): try the next way
      } finally {
        if (timer) clearTimeout(timer);
      }
    }
    return new Answer(null, lastError);
  }

  async call(action) {
    if (!["status", "on", "off"].includes(action)) return new Answer(null, `unknown action '${action}'`);
    const a = await this.post({ action });
    this.last = a;
    if (a.ok && a.state.patterns) this.patterns = a.state.patterns;
    this.emit();
    return a;
  }

  queued() {
    try {
      const data = JSON.parse(this.store?.get(QUEUE_KEY) ?? "[]");
      return Array.isArray(data) ? data.filter((e) => e && typeof e === "object") : [];
    } catch {
      return [];
    }
  }

  writeQueue(events) {
    try {
      if (!events.length) this.store?.remove?.(QUEUE_KEY);
      else this.store?.set(QUEUE_KEY, JSON.stringify(events.slice(-MAX_QUEUED)));
    } catch {
      // storage full or off: nothing kept, nothing breaks
    }
  }

  /** The waiting events first, then these; what the app can't take because
   * it isn't running is kept for next time. The last Answer (null: nothing sent). */
  async sendQueued(events) {
    const waiting = this.queued();
    const all = waiting.concat(events);
    let answer = null, sent = 0;
    for (const part of batches(all)) {
      answer = await this.post(eventsBody(part));
      if (!answer.ok) break;
      sent += part.length;
    }
    if (answer && !answer.ok && (answer.error === NOT_RUNNING || answer.error === NEEDS_LOCAL)) this.writeQueue(all.slice(sent));
    else if (sent || waiting.length) this.writeQueue([]);
    return answer;
  }

  /** A test's keystrokes, in the background (chained, so they go in order).
   * Resolves with the last Answer; never rejects. */
  postEvents(events) {
    events = [...events];
    if (!events.length) return Promise.resolve(null);
    this.patterns = null;
    const run = this.sending.then(() => this.sendQueued(events)).then((a) => {
      if (a) {
        this.last = a;
        if (a.ok) this.patterns = a.state.patterns ?? null;
        this.emit();
      }
      return a;
    }, () => null);
    this.sending = run.catch(() => null);
    return run;
  }

  queuedCount() { return this.queued().length; }
}

/** The short line the results and menu show, or "" when learn is off. */
export function statusLine(app) {
  if (!app.settings.keyboard_learn) return "";
  const kb = app.keyboard;
  const waiting = kb.queuedCount();
  const base = kb.last ? kb.last.line() : `keyboard learn: ${kb.local ? "on" : NEEDS_LOCAL}`;
  return waiting ? `${base} · ${waiting} keystrokes waiting` : base;
}

/** worst key · most mixed-up pair, from the app's patterns (keyboard_learn.pattern_text, short). */
export function patternText(patterns) {
  if (!patterns || typeof patterns !== "object") return "";
  const parts = [];
  const keys = Array.isArray(patterns.keys) ? patterns.keys : [];
  let worst = null, worstN = 0;
  for (const k of keys) {
    const n = (k.misses | 0) + (k.ghosts | 0) + (k.doubles | 0);
    if (n > worstN) { worst = k; worstN = n; }
  }
  if (worst && worstN >= 2) parts.push(`worst key ${worst.key} (${worstN})`);
  const pairs = Array.isArray(patterns.pairs) ? patterns.pairs : [];
  const top = pairs.filter((p) => (p.count | 0) >= 2).sort((a, b) => b.count - a.count)[0];
  if (top) parts.push(`${top.expected ?? top.a}/${top.typed ?? top.b} mixed up ${top.count}x`);
  if (typeof patterns.fastShare === "number" && patterns.fastShare >= 0.6) parts.push("most when typing fast");
  return parts.join(" · ");
}

/** Whether a page at `location` can reach the local keyboard app: served
 * from this machine (the dev server or preview, with their /kb proxy), or
 * over plain http. An https page from elsewhere (GitHub Pages) can't. */
export function canReachLocal(loc) {
  if (!loc) return true;
  const host = loc.hostname;
  return loc.protocol === "http:" || host === "localhost" || host === "127.0.0.1" || host === "[::1]" || host.endsWith(".localhost");
}
