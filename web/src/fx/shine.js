// The shine (fx shine setting): every 4-20 s (random, so several texts never
// flash together) a narrow diagonal band of light sweeps the words left to
// right like light on a polished blade - about a quarter of the text's width,
// tilted ~20°, white at ~70% fading out both sides, 0.8-1.2 s ease-in-out,
// lighting only the letters. As it reaches the end a small four-point star
// twinkles once just past the last letter, a little above the baseline:
// scale 0 -> 1 turning 45°, a hold, then it shrinks and fades, ~0.6 s.

export const EVERY = [4, 20];         // seconds between sweeps
export const SWEEP = [0.8, 1.2];      // seconds a sweep takes
export const STAR_MS = 600;
export const BAND = 0.25;             // the band's share of the text's width

const rand = ([a, b]) => a + Math.random() * (b - a);

export class Shine {
  constructor(view) {
    this.view = view;
    this.next = performance.now() / 1000 + rand([1.5, 6]);
    this.layer = null;
    this.star = null;
  }

  frame(now) {
    if (now < this.next) return;
    this.next = now + rand(EVERY);
    this.sweep();
  }

  /** The line the caret is on: its right end, for the star. */
  lineEnd() {
    const v = this.view;
    const [w] = v.target();
    if (!w) return null;
    const top = w.offsetTop;
    let end = w;
    for (let i = v.wordEls.indexOf(w); i < v.wordEls.length; i++) {
      const x = v.wordEls[i];
      if (x.offsetTop !== top) break;
      end = x;
    }
    return { x: end.offsetLeft + end.offsetWidth, y: top };
  }

  sweep() {
    const v = this.view;
    this.layer?.remove();
    const layer = v.words.cloneNode(true);
    layer.className = "words shine-layer";
    layer.querySelectorAll(".caret, .mark, .shine-star").forEach((n) => n.remove());
    layer.style.transition = "none";
    v.viewport.append(layer);
    this.layer = layer;
    const width = v.viewport.clientWidth;
    const size = (width * BAND) / 0.2;               // the band is 20% (40%..60%) of the gradient
    layer.style.backgroundSize = `${size}px 100%`;
    const from = -size * 0.62, to = width - size * 0.38;
    const ms = rand(SWEEP) * 1000;
    const anim = layer.animate(
      [{ backgroundPosition: `${from}px 0` }, { backgroundPosition: `${to}px 0` }],
      { duration: ms, easing: "ease-in-out", fill: "forwards" });
    anim.onfinish = () => { if (this.layer === layer) { layer.remove(); this.layer = null; } };
    const end = this.lineEnd();
    if (end) this.twinkle(end, ms * 0.85);
  }

  twinkle(end, delay) {
    const v = this.view;
    this.star?.remove();
    const star = document.createElement("span");
    star.className = "shine-star";
    star.textContent = "✦";
    const lineH = v.lineH || 40;
    star.style.left = `${end.x + lineH * 0.06}px`;
    star.style.top = `${end.y + lineH * 0.08}px`;
    v.words.append(star);                      // in the words' own space: it scrolls with them
    this.star = star;
    const a = star.animate([
      { transform: "scale(0) rotate(0deg)", opacity: 1 },
      { transform: "scale(1) rotate(45deg)", opacity: 1, offset: 0.35 },
      { transform: "scale(1) rotate(45deg)", opacity: 1, offset: 0.6 },
      { transform: "scale(0) rotate(60deg)", opacity: 0 },
    ], { duration: STAR_MS, delay, easing: "ease-in-out", fill: "both" });
    a.onfinish = () => star.remove();
  }

  destroy() {
    this.layer?.remove();
    this.star?.remove();
  }
}
