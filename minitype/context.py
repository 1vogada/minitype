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
        self.bank = WordBank()
        self.generator = WordGenerator(self.settings, self.stats, self.bank)
        self.learn = LearnProgress()
        self.cursors = {}   # menu name -> selected row, kept between visits

    def styles(self):
        return Styles(self.settings.quiet)
