from . import storage
from .history import History
from .learn.progress import LearnProgress
from .settings import Settings
from .stats import SessionStats
from .terminal.style import Styles
from .words.bank import WordBank
from .words.generator import WordGenerator
from .words.quotes import QuoteBank


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

    def styles(self):
        return Styles(self.settings.theme, self.settings.lowkey)

    def load_words(self, name):
        """Switch word list and remember the choice."""
        ok = self.bank.load(name)
        self.settings.word_source = self.bank.source
        return ok

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
