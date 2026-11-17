// Watches the frame rate, so the effects can fall back to cheap versions
// when frames run slow (the fx quality setting: auto, full, cheap).

const SLOW_MS = 24;        // an average frame slower than this is slow (under ~42 fps)
const FAST_MS = 18;        // ...and faster than this is fine again
const SMOOTH = 0.05;

export class FxMonitor {
  constructor(app) {
    this.app = app;
    this.avg = 16.7;
    this.slow = false;
    this.slowFor = 0;
  }

  tick(dt) {
    if (!(dt > 0) || dt > 250) return;          // a hidden tab, a breakpoint: not a frame
    this.avg += SMOOTH * (dt - this.avg);
    if (!this.slow && this.avg > SLOW_MS) {
      this.slowFor += dt;
      if (this.slowFor > 600) this.slow = true;
    } else if (this.slow && this.avg < FAST_MS) {
      this.slowFor -= dt;
      if (this.slowFor < -2500) {
        this.slow = false;
        this.slowFor = 0;
      }
    } else if (!this.slow) this.slowFor = Math.max(0, this.slowFor - dt);
  }

  get fps() { return 1000 / this.avg; }

  /** Whether the effects should be their cheap selves now. */
  get cheap() {
    const q = this.app.settings.fx_quality;
    return q === "cheap" || (q === "auto" && this.slow);
  }
}
