"""Where every setting goes: the settings screen's pages, and pages inside
pages (see tree_menu). The rows themselves are built in settings_menu
(raw_items); this only files them.

The shape: a few general tabs (in-game, menus, data), each holding topic
pages, which hold the settings - or more pages, where a topic splits again
(lyrics › spotify, art › fade › top edge).

To add a setting: build its row in settings_menu.raw_items, then put its
key - (section, label) where it's built, with a new name as a third item if
it should show under another - in the page it belongs to below. To add a
page: (name, help, [rows and pages]) anywhere in a page's list, as deep as
it needs to go. To regroup: move keys. A row that isn't placed still shows,
in an "other" tab.
"""

from .tree_menu import Page

# Where every setting goes: pages of rows, and pages inside pages. A row is
# keyed by where it's built (section, label) - and its new name, if it has
# one; a page is (name, help, [rows and pages]). The top pages are the tabs.
# To add a setting, build its row in raw_items and put its key here; a row
# this doesn't place still shows, in an "other" tab, so nothing is lost.
TREE = [
    ("in-game", "everything about a test: its rules, what you type, and the typing screen", [
        ("test", "how a test plays: its rules, mistakes and challenges", [
            ("rules", "what a wrong key does, backspace, and pausing", [
                ("test", "difficulty"), ("test", "stop on error"), ("test", "backspace"),
                ("test", "pause on esc")]),
            ("mistakes", "how mistakes show, a beep on them, and typing blind", [
                ("test", "corrected letters"), ("test", "indicate typos"),
                ("look", "sound"), ("test", "blind", "blind mode")]),
            ("challenges", "a minimum speed or accuracy, typing from memory, the funbox", [
                ("challenges", "min speed"), ("challenges", "min accuracy"),
                ("challenges", "memory", "type from memory"), ("challenges", "funbox")]),
        ]),
        ("words", "what you type: the word list, punctuation, quotes, books and lyrics", [
            ("word list", "which words, and numbers and capitals in them", [
                ("words", "word list"), ("test", "numbers"), ("test", "all lowercase")]),
            ("punctuation", "punctuation and apostrophes in the words", [
                ("test", "punctuation"), ("test", "apostrophes visible")]),
            ("quotes", "where quotes come from and which kinds", [
                ("words", "quotes from"), ("words", "quote genre")]),
            ("books", "the book you type through, and its text", [
                ("words", "book page"), ("words", "book filter"),
                ("words", "bulgarian books"), ("words", "shlokavitsa style")]),
            ("lyrics", "the lyrics mode: search or spotify, karaoke, its own text, "
                       "linking spotify", [
                ("words", "lyrics from"), ("words", "karaoke"), ("words", "karaoke offset"),
                ("words", "song lines"),
                ("lyrics text", "the lyrics' own tape, punctuation and capitals", [
                    ("words", "lyrics tape"), ("words", "lyrics punctuation"),
                    ("words", "lyrics capitals")]),
                ("spotify", "linking to spotify, for what's playing", [
                    ("words", "spotify"), ("words", "spotify client id"),
                    ("words", "download liked songs"), ("words", "clear kept lyrics")]),
            ]),
        ]),
        ("practice", "extra practice on the keys and words you get wrong", [
            ("bad keys", "mixing in the keys you miss most", [
                ("drills", "bad keys"), ("drills", "bad key %"), ("drills", "edit keys")]),
            ("bad words", "mixing in the words you miss most", [
                ("drills", "bad words"), ("drills", "bad word %")]),
        ]),
        ("screen", "what you see and hear while you type", [
            ("caret", "the caret, its effect, and the carets you race", [
                ("look", "caret"), ("fun", "caret effect"), ("look", "pace caret"),
                ("look", "ghost")]),
            ("words line", "how the words are laid out", [
                ("look", "word gap"), ("look", "tape")]),
            ("hud", "the counters around the words", [
                ("header", "timer", "show timer"), ("header", "progress", "show progress"),
                ("header", "live wpm", "show live wpm"), ("header", "combo", "show combo"),
                ("header", "song wpm", "show song wpm"), ("header", "bpm", "show bpm")]),
            ("keyboard", "the on-screen keyboard and its layout", [
                ("look", "keyboard", "on-screen keyboard"),
                ("look", "layout", "keyboard layout")]),
            ("letter effects", "letters bouncing, shaking, popping and more - only looks, "
                               "never the words", [
                ("fun", "bounce"), ("fun", "shake"), ("fun", "pop"), ("fun", "fade"),
                ("fun", "glitch"), ("fun", "effect speed"), ("fun", "flow direction")]),
        ]),
    ]),
    ("menus", "the menus: their layout, help, the results screen, and the look", [
        ("layout", "how menus are laid out, the border, and hiding it all", [
            ("look", "ui style"), ("look", "sidebar tabs"), ("look", "border"),
            ("look", "lowkey")]),
        ("help", "the key hints and the help box", [
            ("look", "key hints"), ("look", "help box"), ("look", "help border")]),
        ("results screen", "how speed is counted, and what the results screen shows", [
            ("test", "wpm system"), ("results", "speed chart"), ("results", "key heatmap"),
            ("results", "personal best"), ("results", "worst keys"),
            ("results", "session keys"), ("results", "bad words"), ("results", "session")]),
        ("look", "the colours and the corner pictures", [
            ("colours", "the theme, the text's colour, and gradients", [
                ("theme", "the theme, its background and accent letters", [
                    ("look", "theme"), ("look", "theme creator"),
                    ("look", "theme background"), ("look", "accent letters")]),
                ("text", "how light the text is, and bold or italic", [
                    ("look", "lighter text"), ("look", "lighter untyped"),
                    ("look", "bold / italic")]),
                ("gradients", "colour running through the words, and heating up with a combo", [
                    ("look", "gradients"), ("look", "gradient flow"), ("look", "heat")]),
            ]),
            ("art", "the corner pictures", [
                ("picture", "whether art shows, and which picture in which style", [
                    ("look", "theme art", "show art"), ("fun", "art style"),
                    ("look", "picture"), ("look", "picture colours"),
                    ("fun", "art colours", "art shading")]),
                ("art and text", "how the text sits over the art: panel, behind, contrast", [
                    ("look", "text panel"), ("look", "art behind text"),
                    ("look", "see-through"), ("look", "text contrast"),
                    ("look", "bold text")]),
                ("fade", "the art dissolving into the screen at its edges", [
                    ("look", "fade on", "fade (all pictures)"),
                    ("look", "art fade", "fade amount"),
                    ("look", "fade round"), ("look", "fade curve"),
                    ("top edge", "the fade down from the picture's top", [
                        ("look", "fade top"), ("look", "fade start top")]),
                    ("side edge", "the fade in from the picture's left", [
                        ("look", "fade side"), ("look", "fade start"), ("look", "fade angle")]),
                ]),
            ]),
        ]),
    ]),
    ("data", "your goal, what's kept on disk, and starting over", [
        ("goal", "a daily goal to type towards", [("progress", "daily goal")]),
        ("saving", "what's kept on disk", [("progress", "save to disk")]),
        ("reset", "forgetting your bad words, or every setting", [
            ("progress", "reset", "reset bad words"), ("progress", "reset settings")]),
    ]),
]


def _origin(it):
    """Where a row was built: (section, label), kept through renaming."""
    if not hasattr(it, "origin"):
        it.origin = (it.section, it.label)
    return it.origin


def build_tree(items):
    """The rows as TREE's pages (see tree_menu.Page), each row renamed as
    TREE says and tagged with its old section, its label and every page it
    sits in, so #look, #fade and the like still find it. Rows TREE doesn't
    place go in an "other" tab at the end."""
    by_key = {_origin(it): it for it in items}
    placed = set()

    def page(name, help, specs, trail):
        children = []
        for spec in specs:
            if isinstance(spec[2] if len(spec) > 2 else None, list):
                children.append(page(spec[0], spec[1], spec[2], trail + (spec[0],)))
                continue
            it = by_key.get(spec[:2])
            if it is None:
                continue
            placed.add(id(it))
            it.label = spec[2] if len(spec) > 2 else spec[1]
            it.tags = tuple(dict.fromkeys(tuple(it.tags) + spec[:2] + trail))
            children.append(it)
        return Page(name, children, help)

    pages = [page(name, help, specs, (name,)) for name, help, specs in TREE]
    rest = [it for it in items if id(it) not in placed]
    if rest:
        pages.append(Page("other", rest, "settings not filed anywhere else yet"))
    return pages


def arrange(items):
    """The rows in TREE's order, flat: every setting with its top page as
    its section (for tests and anything that wants one list)."""
    out = []
    for top in build_tree(items):
        for it in top.leaves():
            it.section = top.name
            out.append(it)
    return out
