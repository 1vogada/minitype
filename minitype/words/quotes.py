"""Quotes to type. A small built-in set from public-domain writers, or
Monkeytype's English quote collection online."""

import random

from .bank import MONKEYTYPE, fetch_json

ONLINE_URL = MONKEYTYPE + "quotes/english.json"
SHORT, MEDIUM = 100, 300          # character limits for the length buckets

BUILTIN_QUOTES = [
    ("Well done is better than well said.", "Benjamin Franklin"),
    ("Lost time is never found again.", "Benjamin Franklin"),
    ("An investment in knowledge pays the best interest.", "Benjamin Franklin"),
    ("Energy and persistence conquer all things.", "Benjamin Franklin"),
    ("Brevity is the soul of wit.", "William Shakespeare"),
    ("The course of true love never did run smooth.", "William Shakespeare"),
    ("We know what we are, but know not what we may be.", "William Shakespeare"),
    ("All the world's a stage, and all the men and women merely players.",
     "William Shakespeare"),
    ("Go confidently in the direction of your dreams. Live the life you have "
     "imagined.", "Henry David Thoreau"),
    ("Our life is frittered away by detail. Simplify, simplify.",
     "Henry David Thoreau"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Twenty years from now you will be more disappointed by the things that "
     "you didn't do than by the ones you did do.", "Mark Twain"),
    ("Kindness is the language which the deaf can hear and the blind can see.",
     "Mark Twain"),
    ("It is a truth universally acknowledged, that a single man in possession "
     "of a good fortune, must be in want of a wife.", "Jane Austen"),
    ("There is no charm equal to tenderness of heart.", "Jane Austen"),
    ("It was the best of times, it was the worst of times, it was the age of "
     "wisdom, it was the age of foolishness, it was the epoch of belief, it "
     "was the epoch of incredulity.", "Charles Dickens"),
    ("No one is useless in this world who lightens the burdens of another.",
     "Charles Dickens"),
    ("Not all those who wander are lost.", "proverb"),
    ("Do not go where the path may lead, go instead where there is no path "
     "and leave a trail.", "Ralph Waldo Emerson"),
    ("What lies behind us and what lies before us are tiny matters compared "
     "to what lies within us.", "Ralph Waldo Emerson"),
    ("The only person you are destined to become is the person you decide "
     "to be.", "Ralph Waldo Emerson"),
    ("Hope is the thing with feathers that perches in the soul, and sings the "
     "tune without the words, and never stops at all.", "Emily Dickinson"),
    ("Whatever you are, be a good one.", "Abraham Lincoln"),
    ("Four score and seven years ago our fathers brought forth on this "
     "continent, a new nation, conceived in Liberty, and dedicated to the "
     "proposition that all men are created equal.", "Abraham Lincoln"),
    ("I have not failed. I've just found ten thousand ways that won't work.",
     "Thomas Edison"),
    ("Genius is one percent inspiration and ninety-nine percent perspiration.",
     "Thomas Edison"),
    ("Life is really simple, but we insist on making it complicated.",
     "Confucius"),
    ("It does not matter how slowly you go as long as you do not stop.",
     "Confucius"),
    ("The journey of a thousand miles begins with one step.", "Lao Tzu"),
    ("Knowing others is intelligence; knowing yourself is true wisdom. "
     "Mastering others is strength; mastering yourself is true power.",
     "Lao Tzu"),
    ("The unexamined life is not worth living.", "Socrates"),
    ("Happiness depends upon ourselves.", "Aristotle"),
    ("You have power over your mind, not outside events. Realize this, and "
     "you will find strength.", "Marcus Aurelius"),
    ("The happiness of your life depends upon the quality of your thoughts: "
     "therefore, guard accordingly, and take care that you entertain no "
     "notions unsuitable to virtue and reasonable nature.", "Marcus Aurelius"),
    ("Waste no more time arguing about what a good man should be. Be one.",
     "Marcus Aurelius"),
    ("It is not that we have a short time to live, but that we waste a lot "
     "of it. Life is long enough, and a sufficiently generous amount has been "
     "given to us for the highest achievements if it were all well invested.",
     "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("I wandered lonely as a cloud that floats on high over vales and hills, "
     "when all at once I saw a crowd, a host, of golden daffodils.",
     "William Wordsworth"),
    ("Two roads diverged in a wood, and I took the one less traveled by, and "
     "that has made all the difference.", "Robert Frost"),
    ("Call me Ishmael. Some years ago, never mind how long precisely, having "
     "little or no money in my purse, and nothing particular to interest me "
     "on shore, I thought I would sail about a little and see the watery part "
     "of the world.", "Herman Melville"),
    ("Happy families are all alike; every unhappy family is unhappy in its "
     "own way.", "Leo Tolstoy"),
    ("If you want to be happy, be.", "Leo Tolstoy"),
    ("The man who moves a mountain begins by carrying away small stones.",
     "proverb"),
    ("A smooth sea never made a skilled sailor.", "proverb"),
    ("Fall seven times, stand up eight.", "proverb"),
]


def bucket(text):
    n = len(text)
    return "short" if n <= SHORT else "medium" if n <= MEDIUM else "long"


class QuoteBank:
    def __init__(self):
        self.online = None    # [(text, source)] once fetched
        self.note = ""

    def _pool(self, source):
        if source == "online":
            if self.online is None:
                try:
                    data = fetch_json(ONLINE_URL, timeout=10)
                    self.online = [(q["text"], q.get("source", ""))
                                   for q in data.get("quotes", []) if q.get("text")]
                    self.note = f"{len(self.online)} online quotes"
                except Exception as e:
                    self.online = []
                    self.note = f"online quotes failed ({type(e).__name__})"
            if self.online:
                return self.online
        return BUILTIN_QUOTES

    def pick(self, length="all", source="built-in"):
        """A (text, source) pair of the wanted length, or any length if
        none match."""
        pool = self._pool(source)
        fits = [q for q in pool if length == "all" or bucket(q[0]) == length]
        return random.choice(fits or pool)
