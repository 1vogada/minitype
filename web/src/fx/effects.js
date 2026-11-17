// The typing screen's effects (phase 2), all off by default. Filled in by
// the effect modules; the test screen calls key / miss / frame.

export class Effects {
  constructor(ui, view, screen) {
    this.ui = ui;
    this.view = view;
    this.screen = screen;
  }
  key() {}
  miss() {}
  frame() {}
  destroy() {}
}
