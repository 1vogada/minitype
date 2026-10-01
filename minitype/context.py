from . import storage
from .history import History
from .learn.progress import LearnProgress
from .settings import Settings
from .stats import SessionStats
from .terminal.style import Styles
from .words.bank import WordBank
from .words.generator import WordGenerator


class App:
    """Shared state handed to every screen."""

    def __init__(self):
        self.settings = Settings()
        self.stats = SessionStats()
        self.history = History()
        self.bank = WordBank()
        self.generator = WordGenerator(self.settings, self.stats, self.bank)
        self.learn = LearnProgress()
        self.cursors = {}   # menu name -> selected row, kept between visits

    def styles(self):
        return Styles(self.settings.quiet)

    # ---------------------------------------------------------------- disk

    def to_dict(self):
        return {
            "learn": self.learn.config,
            "stats": self.learn.stats,
            "settings": self.settings.to_dict(),
            "history": self.history.runs,
            "key_state": self.stats.key_state,
        }

    def saving(self):
        return storage.enabled()

    def toggle_saving(self):
        storage.toggle(self.to_dict())

    def save(self):
        storage.write(self.to_dict())

    def load(self):
        d = storage.read()
        if d is None:
            return
        self.learn.apply(d)
        self.settings.apply(d.get("settings"))
        self.history.apply(d.get("history"))
        ks = d.get("key_state")
        if isinstance(ks, dict):
            self.stats.key_state.update(
                {c: v for c, v in ks.items() if v in ("on", "off")})
