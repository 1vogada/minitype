// Tilting cards (the fx tiles setting): the card under the mouse (a screen's
// glass card, a dialog) leans towards it in 3D, its thick edge showing on the
// side turned away, and settles flat again when the mouse leaves. Only CSS
// variables change; the transform and the edge are in style.css.

const MAX = 7;                 // degrees, at the card's edge
const CARDS = "#screen > *, .dialog";

export class Tiles {
  constructor(enabled) {
    this.enabled = enabled;
    this.card = null;
    this.frameAsked = false;
    this.last = null;
    document.addEventListener("pointermove", (e) => {
      if (!this.on()) return;
      this.last = e;
      if (!this.frameAsked) {
        this.frameAsked = true;
        requestAnimationFrame(() => this.update());
      }
    }, { passive: true });
    document.documentElement.addEventListener("pointerleave", () => this.rest());
  }

  on() {
    return this.enabled() && matchMedia("(min-width: 901px) and (hover: hover)").matches;
  }

  update() {
    this.frameAsked = false;
    const e = this.last;
    const card = e?.target instanceof Element ? e.target.closest(CARDS) : null;
    if (card !== this.card) {
      this.rest();
      this.card = card;
    }
    if (!card) return;
    const r = card.getBoundingClientRect();
    const x = Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1));
    const y = Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1));
    // a tall card leans less up and down, or its far end would swing a long way
    const tall = Math.min(1, 420 / Math.max(1, card.offsetHeight));
    const ry = x * MAX * Math.min(1, 900 / Math.max(1, card.offsetWidth));
    const rx = -y * MAX * tall;
    const s = card.style;
    s.setProperty("--rx", `${rx.toFixed(2)}deg`);
    s.setProperty("--ry", `${ry.toFixed(2)}deg`);
    // the edge shows on the side turned away from the mouse
    s.setProperty("--ex", (-ry / MAX).toFixed(3));
    s.setProperty("--ey", (rx / MAX).toFixed(3));
    s.setProperty("--shine-x", `${((x + 1) * 50).toFixed(1)}%`);
    s.setProperty("--shine-y", `${((y + 1) * 50).toFixed(1)}%`);
    card.classList.add("tilting");
  }

  rest() {
    const card = this.card;
    this.card = null;
    if (!card) return;
    for (const k of ["--rx", "--ry", "--ex", "--ey"]) card.style.removeProperty(k);
    card.classList.remove("tilting");
  }
}
