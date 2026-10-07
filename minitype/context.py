from . import storage
from .history import History
from .learn.progress import LearnProgress
from .settings import FADE_FIELDS, Settings
from .stats import SessionStats
from .terminal import console
from .terminal.art import THEME_ART
from .terminal.art import paint as paint_art
from .terminal.art import resolve as resolve_art
from .terminal.style import Styles, rgb_of_code, theme_art
from .words.bank import WordBank
from .words.generator import WordGenerator
from .words.quotes import QuoteBank
from .words.themed import LAYOUT_DEPENDENT


def _lum(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def _extremes(palette, background):
    """The theme's darkest and lightest colours (its art palette and its
    background), for flipping text over the art."""
    cols = [c for c in (rgb_of_code(v) for v in palette.values()) if c]
    cols.append(rgb_of_code(background, 48) or (18, 18, 22))
    return min(cols, key=_lum), max(cols, key=_lum)


class App:
    """Shared state handed to every screen."""

    def __init__(self):
        self.settings = Settings()
        self.stats = SessionStats()
        self.history = History()
        self.bank = WordBank()
        self.quotes = QuoteBank()
        self.generator = WordGenerator(self.settings, self.stats, self.bank)
        self.learn = LearnProgress()
        self.cursors = {}   # menu name -> selected row, kept between visits
        self.notice = ""    # one-off message for the next menu draw
        self.theme_draft = None   # the theme creator's work in progress
        self.current_test = None  # (test, redraw) while a test runs, for ctrl-o
        self.fade_picture = None  # the picture the fade settings are showing

    def styles(self, custom=None, art=None):
        """The current theme's colours, with every effect and fun-modifier
        setting applied. Every screen draws through this, so it's also where
        the theme's background, border and corner art are handed to the
        console. `custom` is a (palette, effects) pair to show instead and
        `art` its picture (the theme creator's draft)."""
        s = self.settings
        st = Styles(s.theme, s.lowkey, s.accent_text, lighten=s.text_lighten / 100,
                    background=s.theme_background, gradient=s.theme_gradient,
                    flow=s.theme_flow, heat=s.theme_heat,
                    text_style=s.theme_text_style,
                    modifiers={"bounce": s.fun_bounce, "shake": s.fun_shake,
                               "pop": s.fun_pop, "fade": s.fun_fade,
                               "caret_fx": s.fun_caret, "glitch": s.fun_glitch},
                    speed=s.effect_speed, reverse=s.flow_direction == "backward",
                    custom=custom)
        console.set_background(st.background)
        stealth = s.lowkey == "disguised"
        versions = theme_art(s.theme, s.art_style) if art is None else art
        shaded = s.art_colours == "shaded"
        palette = st.art_palette(shaded=shaded)
        if art is None and s.art_picture != "theme":
            # a remix: another theme's picture, in this theme's colours or
            # in its own theme's
            versions = resolve_art(s.art_picture, s.art_style) or versions
            home = next((t for t, n in THEME_ART.items() if n == s.art_picture), None)
            if s.art_recolour == "own" and home:
                palette = Styles(home).art_palette(shaded=shaded)
        if art is None:
            self.picture_fade(s.art_picture if s.art_picture != "theme"
                              else THEME_ART.get(s.theme) or f"theme {s.theme}")
        console.set_decor(
            border=None if stealth or s.border == "off" else s.border,
            border_style=st.title,
            art=None if stealth or s.art == "off" else
            [paint_art(piece, palette) for piece in versions],
            art_scope=s.art, behind=s.art_behind, panel=s.art_panel, shadow=st.dim,
            fade=(s.art_fade, s.fade_top, s.fade_side, s.fade_round, s.fade_start,
                  s.fade_start_top, s.fade_angle, s.fade_curve) if s.fade_on else None,
            text_fx=(s.text_contrast, s.text_bold) + _extremes(palette, st.background),
            see_through=s.see_through / 100)
        return st

    def picture_fade(self, picture):
        """The fade settings are per picture: coming to another picture
        brings its own back (the defaults for one never set), and whatever
        is set now is kept as the shown picture's. The first picture seen
        keeps the settings as they are (from before they were per picture)."""
        s = self.settings
        if picture != self.fade_picture:
            saved = s.fades.get(picture)
            if saved is not None or self.fade_picture is not None:
                default = Settings()
                for f in FADE_FIELDS:
                    setattr(s, f, (saved or {}).get(f, getattr(default, f)))
            self.fade_picture = picture
        s.fades[picture] = {f: getattr(s, f) for f in FADE_FIELDS}

    def load_words(self, name):
        """Switch word list and remember the choice. The choice is kept even
        when the list falls back to built-in (no internet, or too few words
        on this layout), so it comes back once it can."""
        ok = self.bank.load(name, layout=self.settings.layout)
        self.settings.word_source = name
        return ok

    def layout_changed(self):
        """One-hand and home-row lists depend on the layout: rebuild them."""
        if self.settings.word_source in LAYOUT_DEPENDENT:
            self.load_words(self.settings.word_source)

    # ---------------------------------------------------------------- disk

    def to_dict(self):
        """What goes in save.json (opt-in progress)."""
        return {
            "learn": self.learn.config,
            "stats": self.learn.stats,
            "history": self.history.runs,
            "pbs": self.history.pbs,
            "word_speed": self.stats.word_speed,
        }

    def settings_dict(self):
        """What goes in settings.json (always saved): every setting, plus
        which keys you pinned or muted in the bad-key editor."""
        return dict(self.settings.to_dict(), key_state=self.stats.key_state)

    def saving(self):
        return storage.enabled()

    def toggle_saving(self):
        storage.toggle(self.to_dict())

    def save_settings(self):
        storage.write_settings(self.settings_dict())

    def save(self):
        self.save_settings()
        storage.write(self.to_dict())

    def load(self):
        s = storage.read_settings()
        d = storage.read() or {}
        if s is None:
            s = dict(d.get("settings") or {}, key_state=d.get("key_state"))
        self.settings.apply(s)
        ks = s.get("key_state")
        if isinstance(ks, dict):
            self.stats.key_state.update(
                {c: v for c, v in ks.items() if v in ("on", "off")})
        self.learn.apply(d)
        self.history.apply(d.get("history"), d.get("pbs"))
        ws = d.get("word_speed")
        if isinstance(ws, dict):
            self.stats.word_speed.update(
                {w: [float(v[0]), int(v[1])] for w, v in ws.items()
                 if isinstance(v, list) and len(v) == 2})
