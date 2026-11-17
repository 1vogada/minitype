// A new install picks a setup (ui/welcome.py): shown live as you move.

import { MENU } from "../core/test.js";
import { h } from "./dom.js";
import { RowList } from "./rows.js";

const SETUPS = [
  ["clean", "quiet and monochrome: just the words, a block caret, lowercase, forgiving punctuation"],
  ["art", "the summit theme: black and white, snow and code"],
];

export class WelcomeScreen {
  constructor(ui) {
    this.ui = ui;
    this.app = ui.app;
    this.navName = "";
    this.hints = "↑/↓ choose   enter use it   esc keep this one";
    this.list = new RowList(SETUPS.map(([name, help]) => ({ label: name, help, enter: () => this.use(name) })), {
      labelWidth: "8em",
      onSelect: (it) => { this.help.textContent = it.help; this.preview(it.label); },
    });
    this.help = h("p");
    this.el = h("div.welcome", h("h1", "minitype"),
      h("p", "a typing test, now in the browser. Pick a setup to start from; everything can be changed later in settings, and minitype's save.json and settings.json can be imported there (settings › data)."),
      this.list.el, this.help);
    this.help.textContent = SETUPS[0][1];
    this.preview("clean");
  }

  preview(name) {
    this.app.useSetup(name);
    this.ui.restyle();
  }

  use(name) {
    this.preview(name);
    this.app.firstRun = false;
    this.app.save();
    this.app.loadWords(this.app.settings.word_source).finally(() => this.ui.go(MENU));
  }

  onKey(key) {
    if (key === "ESC") return this.use(this.list.current().label);
    this.list.key(key);
  }
}
