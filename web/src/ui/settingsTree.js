// Every setting the browser has, grouped like ui/settings_tree.py: tabs
// holding pages holding rows (a page can hold pages of its own). A node is
// [name, [children]]; a row is [setting, label, help] or {action, label, help}.

export const TREE = [
  ["in-game", [
    ["test", [
      ["rules", [
        ["difficulty", "difficulty", "expert: a wrong word ends the test. master: a wrong key ends it"],
        ["stop_on_error", "stop on error", "letter: a wrong key doesn't move the caret. word: you can't leave a wrong word"],
        ["backspace", "backspace", "off: no corrections at all. freedom: back into correct words too"],
        ["esc_pause", "pause on esc", "esc in a test that's under way pauses it (resume? yes / no) instead of leaving"],
        ["tab_same", "tab replays", "tab after typing something: the same words again; on the results, the same words below 90% accuracy, new ones at 90% or better"],
      ]],
      ["mistakes", [
        ["corrected", "corrected letters", "a letter you got wrong and fixed: marked (warn colour), normal, or red"],
        ["typos", "indicate typos", "show the wrong key you pressed: below the letter, in its place, or both"],
        ["sound", "sound", "a short beep on a wrong key"],
        ["blind", "blind mode", "no feedback at all until the results"],
      ]],
      ["challenges", [
        ["min_wpm", "min speed", "fail the test when your speed drops below this (after 3 seconds)"],
        ["min_acc", "min accuracy", "fail the test when your accuracy drops below this"],
        ["memory", "type from memory", "the words vanish this many seconds into the test"],
        ["funbox", "funbox", "reversed, caps, random case, mirror; hacker and god hacker type the right letters for you (not kept)"],
      ]],
    ]],
    ["words", [
      ["word list", [
        ["word_source", "word list", "the words a test draws from; the online lists come from monkeytype"],
        ["word_length", "word length", "any: a natural mix of short, medium and long words; or only some lengths"],
        ["numbers", "numbers", "sprinkle numbers into word tests"],
        ["lowercase", "all lowercase", "every word in lower case: quotes and custom text too"],
      ]],
      ["punctuation", [
        ["punctuation", "punctuation", "off: stripped from quotes. on: typed as is. forgive: any of it can be skipped"],
        ["apostrophes", "apostrophes visible", "off removes apostrophes altogether"],
      ]],
      ["quotes and code", [
        ["quote_source", "quotes from", "the built-in collection, or monkeytype's online quotes"],
        ["quote_genre", "quote genre", "for the built-in quotes"],
        ["code_lang", "code language", "the snippets the code mode draws from"],
      ]],
    ]],
    ["practice", [
      ["bad keys", [
        ["weak", "bad keys", "mix in words holding the keys you miss most"],
        ["weak_pct", "bad key %", "how often such a word is drawn"],
      ]],
      ["bad words", [
        ["bad_words", "bad words", "mix in the words you got wrong"],
        ["bad_words_pct", "bad word %", "how often one comes back"],
      ]],
    ]],
    ["screen", [
      ["caret", [
        ["caret", "caret", "underline, block, or a thin line"],
        ["smooth_caret", "smooth caret", "the caret glides from letter to letter, and lines scroll smoothly"],
        ["fun_caret", "caret effect", "theme, off, pulse (blinks) or rainbow"],
        ["pace", "pace caret", "a dim caret moving at this speed"],
        ["ghost", "ghost", "a caret replaying your last run, to race"],
      ]],
      ["words line", [
        ["word_gap", "word gap", "between words: blank, dots or underline"],
        ["tape", "tape", "one line that scrolls with the caret (from the left third, or from the middle)"],
      ]],
      ["hud", [
        ["show_timer", "timer", "the time in the header"],
        ["show_progress", "progress", "words done of the words in a word test"],
        ["show_wpm", "live wpm", "your speed as you type"],
        ["show_combo", "combo", "correct keys in a row"],
        ["lowkey", "lowkey", "minimal: just the words"],
      ]],
      ["keyboard", [
        ["keyboard", "on-screen keyboard", "off, in learn mode, or always"],
        ["layout", "keyboard layout", "for the on-screen keyboard and the one-hand word lists"],
      ]],
      ["magnetic keyboard", [
        ["keyboard_learn", "keyboard learn", "send each test's keystrokes to the MAX68HE keyboard app (on 127.0.0.1:6869), so it tunes each key's actuation to how you really press. minitype never switches the app's learning on or off and never changes the keyboard"],
        ["keyboard_server", "keyboard server", "where the keyboard app listens; localhost is used as 127.0.0.1"],
        { action: "keyboard_status", label: "check the app", help: "ask the keyboard app how learning is going (a status call, nothing changes)" },
      ]],
      ["letter effects", [
        ["fun_bounce", "bounce", "letters bob: gentle near the caret, wild everywhere"],
        ["fun_shake", "shake", "the text jolts after a wrong key"],
        ["fun_pop", "pop", "the last few typed letters flash bright"],
        ["fun_fade", "fade", "typed letters dim as they fall behind"],
        ["fun_glitch", "glitch", "letters ahead flicker to symbols"],
        ["effect_speed", "effect speed", "how fast gradients and effects move"],
        ["flow_direction", "flow direction", "which way gradients flow"],
      ]],
    ]],
  ]],
  ["effects", [
    ["background", [
      ["fx_bg", "background", "a drawn scene behind everything, in the theme's colours: auto picks one that suits the theme (none for the high contrast ones)"],
      ["fx_bg_tilt", "background tilt", "the scene tilts in 3D after the mouse, the near layers moving more than the far ones"],
      ["fx_glass", "glass cards", "a frosted glass card behind the text and the menus, so they read over the scene"],
      ["fx_tiles", "tilting cards", "the glass cards lean after the mouse when it's over them, a slab with its thick edge showing"],
    ]],
    ["3d and fire", [
      ["fx_tilt", "3d tilt", "the words turn a little to the side and go 3D"],
      ["fx_tilt_angle", "tilt angle", "how far they turn, in degrees"],
      ["fx_fire", "fire", "the typed words give off flames that climb with the combo (hue, size, layers), on a streak and at high speed, or always"],
      ["fx_fire_wpm", "fire from", "the speed (wpm) that lights the fire on a streak"],
    ]],
    ["shine", [
      ["fx_shine", "shine", "now and then a band of light sweeps the words like light on a blade, and a star twinkles past the last letter"],
    ]],
    ["combo", [
      ["fx_combo", "combo counter", "the combo flashes, shakes, burns and grows with every milestone (10, 25, 50, 100, 200); a break shatters it"],
    ]],
    ["feel", [
      ["fx_popin", "letters pop in", "each right key pops its letter in"],
      ["fx_camera", "camera shake", "a small shake of the whole screen on a wrong key"],
      ["fx_reveal", "results reveal", "the results come in one after another"],
    ]],
    ["quality", [
      ["fx_quality", "quality", "auto: cheaper effects whenever frames run slow; full; cheap"],
    ]],
  ]],
  ["menus", [
    ["results screen", [
      ["wpm_system", "wpm system", "active: over the time you were typing (long stops left out); classic: over the whole clock"],
      ["res_chart", "speed chart", "speed through the test"],
      ["res_heatmap", "key heatmap", "the keyboard coloured by misses"],
      ["res_pb", "personal best", "how the run compares with your best"],
      ["res_worst_keys", "worst keys", "this test's most missed keys"],
      ["res_session_keys", "session keys", "the keys the bad-key drill uses"],
      ["res_bad_words", "bad words", "the words you got wrong most"],
      ["res_history", "session", "your last few speeds this session"],
    ]],
    ["help", [
      ["hints", "key hints", "the keys at the bottom of each screen"],
    ]],
    ["look", [
      ["theme", [
        ["theme", "theme", "the colours, and the theme's own effects (` and ~ on the main menu flip through them)"],
        ["theme_background", "theme background", "theme: its own (or one made from its colours); off: plain"],
        ["accent_text", "accent letters", "typed letters in the theme's accent colour"],
        ["untyped_lighten", "lighter untyped", "the words not typed yet moved this % towards white"],
        ["theme_text_style", "bold / italic", "the theme's bold or italic letters"],
      ]],
      ["gradients", [
        ["theme_gradient", "gradients", "colour running through the typed words"],
        ["theme_flow", "gradient flow", "the gradient moves"],
        ["theme_heat", "heat", "text colour follows your combo"],
      ]],
    ]],
  ]],
  ["data", [
    ["goal", [
      ["daily_goal", "daily goal", "minutes of typing a day; the menu and results show how far you are"],
    ]],
    ["save", [
      { action: "saving", label: "save progress", help: "keep history, bests, word timings and learn progress in this browser" },
      { action: "import", label: "import", help: "minitype's save.json (merged with what's here) or settings.json (replaces these settings), from the terminal minitype's folder" },
      { action: "export_save", label: "export save.json", help: "your history and progress, in the terminal minitype's format" },
      { action: "export_settings", label: "export settings.json", help: "these settings, in the terminal minitype's format (its own settings kept)" },
    ]],
    ["reset", [
      { action: "reset_bad", label: "reset bad words", help: "forget the keys and words you missed" },
      { action: "reset_learn", label: "reset learn", help: "start learn mode over" },
      { action: "reset_settings", label: "reset settings", help: "every setting back to a setup (clean or art)" },
    ]],
  ]],
];

/** Whether an entry is a group ([name, [children]]) rather than a row. */
export const isNode = (x) => Array.isArray(x) && Array.isArray(x[1]);

/** Every row with the path of groups it's in: [{path: [tab, page, ...], row}]. */
export function flatten(tree = TREE, path = []) {
  const out = [];
  for (const x of tree) {
    if (isNode(x)) out.push(...flatten(x[1], [...path, x[0]]));
    else out.push({ path, row: x });
  }
  return out;
}

/** The groups as an outline for the sidebar: [{path, name, depth, children}]. */
export function outline(tree = TREE, path = []) {
  return tree.filter(isNode).map(([name, kids]) => ({
    name, path: [...path, name], depth: path.length, children: outline(kids, [...path, name]),
  }));
}
