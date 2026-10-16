from dataclasses import asdict, dataclass, field, fields

from .config import (BACKSPACE_MODES, BOOK_PAGES, BOOK_SCRIPTS, CARETS,
                     CODE_LANGS, DIFFICULTIES,
                     FUNBOXES, GOALS, KEYBOARD_MODES, LAYOUTS, LOWKEY_MODES,
                     MEMORY_SECS, MIN_ACCS, MIN_WPMS, PACES, QUOTE_LENGTHS,
                     QUOTE_SOURCES, QUOTE_GENRES, SIDEBAR_TABS, STOP_MODES,
                     TAPE_MODES, UI_STYLES,
                     WORD_GAPS, FUN_BOUNCE, FUN_SWITCH, FUN_CARET,
                     EFFECT_SPEEDS, FLOW_DIRECTIONS, CORRECTED, TYPOS,
                     PUNCTUATION_MODES,
                     BORDER_STYLES, ART_SCOPES, ART_STYLES, ART_COLOURS,
                     THEME_BACKGROUNDS,
                     ART_FADES, FADE_TOPS, FADE_SIDES, FADE_ROUNDS,
                     FADE_STARTS, FADE_ANGLES, FADE_CURVES, NUMBER_RANGES,
                     TEXT_CONTRASTS, SEE_THROUGH, HELP_POSITIONS, HELP_BORDERS)
from .terminal.style import theme_names
from .words.shlokavitsa import STYLE_NAMES as SHLOKAVITSA_STYLES

# fields whose value must be one of a set (a function when the set can
# change while the app runs, like themes from themes.json)
def _art_names():
    from .terminal.art import ART_NAMES
    return ART_NAMES


CHOICES = {
    "difficulty": DIFFICULTIES,
    "stop_on_error": STOP_MODES,
    "punctuation": PUNCTUATION_MODES,
    "backspace": BACKSPACE_MODES,
    "min_wpm": MIN_WPMS,
    "min_acc": MIN_ACCS,
    "funbox": FUNBOXES,
    "memory": MEMORY_SECS,
    "quote_length": QUOTE_LENGTHS,
    "quote_source": QUOTE_SOURCES,
    "quote_genre": QUOTE_GENRES,
    "code_lang": CODE_LANGS,
    "pace": PACES,
    "caret": CARETS,
    "word_gap": WORD_GAPS,
    "corrected": CORRECTED,
    "border": BORDER_STYLES,
    "art": ART_SCOPES,
    "art_picture": lambda: ["theme"] + _art_names(),
    "art_recolour": ["theme", "own"],
    "art_fade": ART_FADES,
    "fade_top": FADE_TOPS,
    "fade_side": FADE_SIDES,
    "fade_round": FADE_ROUNDS,
    "fade_start": FADE_STARTS,
    "text_contrast": TEXT_CONTRASTS,
    "see_through": SEE_THROUGH,
    "help_position": HELP_POSITIONS,
    "help_border": HELP_BORDERS,
    "text_lighten": SEE_THROUGH,
    "untyped_lighten": SEE_THROUGH,
    "fade_start_top": FADE_STARTS,
    "fade_angle": FADE_ANGLES,
    "fade_curve": FADE_CURVES,
    "art_style": ART_STYLES,
    "art_colours": ART_COLOURS,
    "theme_background": THEME_BACKGROUNDS,
    "typos": TYPOS,
    "fun_bounce": FUN_BOUNCE,
    "fun_shake": FUN_SWITCH,
    "fun_pop": FUN_SWITCH,
    "fun_fade": FUN_SWITCH,
    "fun_caret": FUN_CARET,
    "fun_glitch": FUN_SWITCH,
    "effect_speed": EFFECT_SPEEDS,
    "flow_direction": FLOW_DIRECTIONS,
    "keyboard": KEYBOARD_MODES,
    "layout": list(LAYOUTS),
    "theme": theme_names,
    "lowkey": LOWKEY_MODES,
    "tape": TAPE_MODES,
    "ui_style": UI_STYLES,
    "sidebar_tabs": SIDEBAR_TABS,
    "daily_goal": GOALS,
    "book_page": BOOK_PAGES,
    "book_script": BOOK_SCRIPTS,
    "shlokavitsa_style": SHLOKAVITSA_STYLES,
}


# the fade settings, kept per picture (see App.styles): the fields above
# hold the shown picture's, Settings.fades every picture's
FADE_FIELDS = ("art_fade", "fade_top", "fade_side", "fade_round", "fade_start",
               "fade_start_top", "fade_angle", "fade_curve")


def _clean_fade(entry):
    """A saved picture's fade settings with anything wrong left out."""
    s = Settings()
    s.apply({k: entry[k] for k in FADE_FIELDS if k in entry})
    return {k: getattr(s, k) for k in FADE_FIELDS if k in entry and entry[k] == getattr(s, k)}



# What a new install starts with (App.load, when there are no saved settings
# yet): the owner's own settings. The Settings defaults below stay the
# baseline the features are built and tested against; MINITYPE_FACTORY=1
# starts from that baseline instead.
STARTER = {
    'lowercase': True,
    'word_amount': 10,
    'weak_pct': 40,
    'bad_words_pct': 40,
    'word_source': 'online 200',
    'quote_length': 'short',
    'quote_source': 'online',
    'code_lang': 'javascript',
    'book_script': 'shlokavitsa',
    'shlokavitsa_style': 'letters',
    'book_filter': 'punct',
    'theme': 'summit',
    'border': 'off',
    'art': 'off',
    'art_style': 'upscaled',
    'art_behind': True,
    'art_panel': True,
    'text_contrast': 'nudge',
    'text_bold': True,
    'help_position': 'bottom left',
    'help_border': 'off',
    'fade_on': False,
    'art_recolour': 'own',
    'theme_background': 'off',
    'theme_gradient': False,
    'theme_flow': False,
    'theme_heat': False,
    'fun_bounce': 'off',
    'fun_shake': 'off',
    'fun_pop': 'off',
    'fun_fade': 'off',
    'fun_glitch': 'off',
    'keyboard': 'off',
    'res_worst_keys': False,
    'res_bad_words': False,
    'fades': {
        'island': {'art_fade': 'edges', 'fade_top': 50, 'fade_side': 90, 'fade_round': 0, 'fade_start': 60, 'fade_start_top': 20, 'fade_angle': 76, 'fade_curve': 0},
        'pines': {'art_fade': 'off', 'fade_top': 50, 'fade_side': 20, 'fade_round': 50, 'fade_start': 100, 'fade_start_top': 100, 'fade_angle': 0, 'fade_curve': 3},
        'sunset': {'art_fade': 'edges', 'fade_top': 0, 'fade_side': 0, 'fade_round': 50, 'fade_start': 100, 'fade_start_top': 30, 'fade_angle': 60, 'fade_curve': 3},
        'stones': {'art_fade': 'edges', 'fade_top': 20, 'fade_side': 90, 'fade_round': 50, 'fade_start': 40, 'fade_start_top': 10, 'fade_angle': 60, 'fade_curve': 3},
        'flowers': {'art_fade': 'off', 'fade_top': 50, 'fade_side': 20, 'fade_round': 50, 'fade_start': 100, 'fade_start_top': 100, 'fade_angle': 0, 'fade_curve': 3},
        'lollipop': {'art_fade': 'edges', 'fade_top': 0, 'fade_side': 0, 'fade_round': 50, 'fade_start': 100, 'fade_start_top': 100, 'fade_angle': 0, 'fade_curve': 3},
        'moon': {'art_fade': 'edges', 'fade_top': 0, 'fade_side': 20, 'fade_round': 50, 'fade_start': 100, 'fade_start_top': 100, 'fade_angle': 0, 'fade_curve': 3},
    },
}

@dataclass
class Settings:
    # ---- the test
    difficulty: str = "normal"   # expert: a wrong word ends it. master: a wrong key ends it.
    stop_on_error: str = "off"   # letter: wrong keys don't move the cursor. word: can't leave a wrong word
    backspace: str = "normal"    # off: no corrections at all. freedom: back into correct words too
    corrected: str = "marked"    # fixed letters: marked (warn colour), normal, or red
    typos: str = "off"           # show the wrong key: off, below, replace, both
    punctuation: str = "off"     # off: stripped from quotes, none added. on: typed as is. forgive: all of it can be skipped
    lowercase: bool = False      # every word in lower case: quotes, books, custom text too
    apostrophes: bool = True     # apostrophes visible; off removes them altogether from quotes and text
    numbers: bool = False        # sprinkle numbers into normal word tests
    blind: bool = False          # no feedback until the results screen
    time_amount: int = 30        # seconds, for the time mode
    word_amount: int = 25        # words, for the words and numbers modes

    # ---- challenges
    min_wpm: int = 0             # fail when live speed drops below this
    min_acc: int = 0             # fail when accuracy drops below this
    funbox: str = "off"          # reversed / caps / random case / mirror
    memory: int = 0              # hide the words this many seconds in

    # ---- practising weaknesses
    weak: bool = False           # bias words toward the keys you keep missing
    weak_pct: int = 50           # how often a biased word is drawn
    bad_words: bool = False      # replay whole words you got wrong
    bad_words_pct: int = 50

    # ---- text sources
    word_source: str = "online 1k"
    quote_length: str = "all"
    quote_source: str = "built-in"
    quote_genre: str = "all"
    code_lang: str = "python"
    book_page: int = 50          # words per page in book mode
    book_script: str = "cyrillic"            # Bulgarian books: cyrillic or shlokavitsa
    shlokavitsa_style: str = "classic"       # classic / letters / official
    book_filter: str = ""        # characters removed from books; "punct" for all punctuation
    book_marks: dict = field(default_factory=dict)   # book title -> word position

    # ---- look and feel
    theme: str = "default"
    accent_text: bool = False    # typed letters in the theme's accent colour
    text_lighten: int = 0        # menu text moved this % towards white
    untyped_lighten: int = 0     # the typing screen's untyped words moved this % towards white
    border: str = "rounded"      # frame around the screen: off, ascii, line, rounded, double, heavy
    art: str = "menus"           # the theme's corner picture: off, menus, everywhere
    art_style: str = "revamp"    # revamp / blocks / detailed / og / combined
    art_colours: str = "shaded"  # shaded (softer shades and hues) / flat
    art_behind: bool = False     # art always full size, text drawn over it
    art_panel: bool = False      # art full size, the text in a bordered panel over it
    text_contrast: str = "off"   # letters over the art: off, nudge (until they read), flip
    text_bold: bool = False      # letters over the art in bold
    help_position: str = "inline"   # the help box: under the selected row, or in a corner
    help_border: str = "auto"       # the help box's border: auto, frame, a border style, off
    see_through: int = 40        # how much of the art shows through boxes (help, panel, dialogs), %
    fade_on: bool = True         # the art fade at all (every picture's own fade settings kept)
    art_fade: str = "edges"      # how the art dissolves at its edges: edges / corner / off
    fade_top: int = 50           # edges, from the top: 0 no fade .. 100 no art
    fade_side: int = 20          # edges, from the left: 0 no fade .. 100 no art
    fade_round: int = 50         # corner, towards the bottom right: 0 no fade .. 100 no art
    fade_start: int = 100        # how far in the side / corner fade reaches, % of the picture
    fade_start_top: int = 100    # how far down the top fade reaches, % of the picture
    fade_angle: int = 0          # the side fade's edge tilted, degrees (+ leans in at the top)
    fade_curve: int = 3          # how sharp the fade's exponential is: 0 straight .. 10
    fades: dict = field(default_factory=dict)   # picture -> its own fade settings (FADE_FIELDS)
    fav_quotes: list = field(default_factory=list)   # favourite quotes: [{"text", "source"}]
    esc_pause: bool = True       # esc in a test pauses it (resume? yes / no) instead of leaving
    art_picture: str = "theme"   # the theme's own picture, or any picture's name (a remix)
    art_recolour: str = "theme"  # a remixed picture in the theme's colours, or its own theme's
    # a theme's effects, each of which can be switched off
    theme_background: str = "theme"   # theme / always / off
    theme_gradient: bool = True
    theme_flow: bool = True      # gradients move
    theme_heat: bool = True      # text colour follows the combo
    theme_text_style: bool = True   # bold / italic letters
    # fun modifiers: "theme" follows the theme, or force them
    fun_bounce: str = "theme"    # theme / off / gentle / wild
    fun_shake: str = "theme"     # theme / off / on, and the same below
    fun_pop: str = "theme"
    fun_fade: str = "theme"
    fun_caret: str = "theme"     # theme / off / pulse / rainbow
    fun_glitch: str = "theme"
    effect_speed: float = 1.0    # how fast gradients and modifiers move
    flow_direction: str = "forward"
    lowkey: str = "off"          # minimal: just the words. disguised: looks like a plain prompt
    ui_style: str = "sidebar"    # how menus are laid out
    sidebar_tabs: str = "left"   # sidebar style: tab bar on top, or section buttons on the left
    tape: str = "off"            # off / on (from left) / from middle
    caret: str = "underline"     # underline: the letter to type is underlined. block: inverted
    word_gap: str = "blank"      # between words: blank, dots or underline
    keyboard: str = "learn"      # on-screen keyboard: off, in learn mode, or always
    layout: str = "qwerty"       # for the on-screen keyboard
    ghost: bool = False          # dim caret replaying your last run
    pace: int = 0                # dim caret moving at a fixed wpm
    sound: bool = False          # bell on a wrong key
    hints: bool = True           # key hints at the bottom of each screen

    # ---- header during a test
    show_timer: bool = True
    show_progress: bool = True
    show_wpm: bool = True
    show_combo: bool = True

    # ---- results screen sections
    res_chart: bool = True
    res_heatmap: bool = True
    res_pb: bool = True
    res_worst_keys: bool = True
    res_session_keys: bool = True
    res_bad_words: bool = True
    res_history: bool = True

    # ---- progress
    daily_goal: int = 0          # minutes of typing a day, 0 for none

    @property
    def quiet(self):
        return self.theme == "mono" or self.lowkey == "disguised"

    def flags(self):
        """Short labels for every non-default rule, for the main menu."""
        flags = []
        if self.difficulty != "normal":
            flags.append(self.difficulty)
        if self.stop_on_error != "off":
            flags.append(f"stop-{self.stop_on_error}")
        if self.backspace != "normal":
            flags.append("no-bksp" if self.backspace == "off" else "freedom")
        if self.punctuation != "off":
            flags.append("punct" if self.punctuation == "on" else "punct-skip")
        for on, name in ((self.lowercase, "lower"),
                         (self.numbers, "num"),
                         (self.blind, "blind"), (self.ghost, "ghost")):
            if on:
                flags.append(name)
        if self.tape not in (False, "off"):
            flags.append("tape" if self.tape == "on" else f"tape-{self.tape.replace(' ', '-')}")
        if self.funbox != "off":
            flags.append(self.funbox)
        if self.memory:
            flags.append(f"memory{self.memory}s")
        if self.min_wpm:
            flags.append(f"min{self.min_wpm}wpm")
        if self.min_acc:
            flags.append(f"min{self.min_acc}%")
        if self.weak:
            flags.append(f"keys{self.weak_pct}%")
        if self.bad_words:
            flags.append(f"words{self.bad_words_pct}%")
        if self.pace:
            flags.append(f"pace{self.pace}")
        return flags

    def __setattr__(self, name, value):
        if name == "tape" and isinstance(value, bool):
            value = "on" if value else "off"
        super().__setattr__(name, value)

    def to_dict(self):
        return asdict(self)

    def apply(self, d):
        """Take saved values, skipping any of the wrong type or out of range."""
        if not isinstance(d, dict):
            return
        if d.get("quiet") is True and "theme" not in d:
            self.theme = "mono"          # from before themes existed
        if d.get("show_spaces") is True and "word_gap" not in d:
            self.word_gap = "dots"       # from before word gap had choices
        if d.get("keep_errors") is True and "corrected" not in d:
            self.corrected = "marked"    # keep errors became corrected letters
        if isinstance(d.get("theme_background"), bool):
            # it was on/off before "always" came along
            d = dict(d, theme_background="theme" if d["theme_background"] else "off")
        if isinstance(d.get("punctuation"), bool) or (
                d.get("forgive_apostrophe") is True and "apostrophes" not in d):
            # punctuation was on/off, with separate apostrophe toggles
            d = dict(d, punctuation="forgive" if d.get("forgive_apostrophe")
                     else "on" if d.get("punctuation") is True else "off")
        if d.get("remove_apostrophe") is True and "apostrophes" not in d:
            d = dict(d, apostrophes=False)
        if isinstance(d.get("tape"), bool):
            d = dict(d, tape="on" if d["tape"] else "off")
        for f in fields(self):
            v = d.get(f.name)
            if type(v) is not type(getattr(self, f.name)):
                continue
            allowed = CHOICES.get(f.name)
            if callable(allowed):
                allowed = allowed()
            if f.name in NUMBER_RANGES:          # any number in its range
                lo, hi = NUMBER_RANGES[f.name]
                if not lo <= v <= hi:
                    continue
            elif allowed is not None and v not in allowed:
                continue
            if f.name in ("time_amount", "word_amount") and not 0 < v <= 3600:
                continue
            if f.name == "book_marks":
                v = {k: n for k, n in v.items()
                     if isinstance(k, str) and type(n) is int and n >= 0}
            if f.name == "fades":
                v = {k: _clean_fade(e) for k, e in v.items()
                     if isinstance(k, str) and isinstance(e, dict)}
            if f.name == "fav_quotes":
                v = [{"text": q["text"], "source": str(q.get("source", ""))}
                     for q in v if isinstance(q, dict) and isinstance(q.get("text"), str)]
            setattr(self, f.name, v)
