"""Where every setting goes: the settings screen's pages, and pages inside
pages (see tree_menu). The rows themselves are built in settings_menu
(raw_items); this only files them.

To add a setting: build its row in settings_menu.raw_items, then put its
key - (section, label) where it's built, with a new name as a third item if
it should show under another - in the page it belongs to below. To add a
page: (name, help, [rows and pages]) anywhere in a page's list, as deep as
it needs to go; give it a fourth item, one of its rows' keys, to make that
row its switch (a HUD element: on/off right there, enter for the rest). To
regroup: move keys. A row that isn't placed still shows, in an "other" tab.
"""

from .tree_menu import Page

# Where every setting goes: pages of rows, and pages inside pages. A row is
# keyed by where it's built (section, label) - and its new name, if it has
# one; a page is (name, help, [rows and pages]), or (name, help, [...], key)
# with the key of its main setting: then its row is that setting's switch as
# well as the way in ("keyboard  on ›"). The top pages are the tabs.
# To add a setting, build its row in raw_items and put its key here; a row
# this doesn't place still shows, in an "other" tab, so nothing is lost.
TREE = [
    ("gameplay", "how a test plays: its rules, mistakes, challenges and drills", [
        ("test", "difficulty"),
        ("rules", "what a wrong key does, backspace, and pausing", [
            ("test", "stop on error"), ("test", "backspace"), ("test", "pause on esc")]),
        ("mistakes", "how mistakes show, and typing blind", [
            ("test", "corrected letters"), ("test", "indicate typos"), ("test", "blind")]),
        ("challenges", "a minimum speed or accuracy, typing from memory, the funbox", [
            ("challenges", "min speed"), ("challenges", "min accuracy"),
            ("challenges", "memory"), ("challenges", "funbox")]),
        ("drills", "extra practice on the keys and words you get wrong", [
            ("bad keys", "mixing in the keys you miss most", [
                ("drills", "bad keys"), ("drills", "bad key %"), ("drills", "edit keys")],
             ("drills", "bad keys")),
            ("bad words", "mixing in the words you miss most", [
                ("drills", "bad words"), ("drills", "bad word %")],
             ("drills", "bad words")),
        ]),
    ]),
    ("words", "what you type: the word list, quotes and books", [
        ("words", "word list"), ("test", "numbers"), ("test", "all lowercase"),
        ("punctuation", "punctuation and apostrophes in the words", [
            ("test", "punctuation"), ("test", "apostrophes visible")],
         ("test", "punctuation")),
        ("quotes", "where quotes come from and which kinds", [
            ("words", "quotes from"), ("words", "quote genre")]),
        ("lyrics", "the lyrics mode: search or spotify, karaoke, its own tape and "
                   "punctuation, linking spotify", [
            ("words", "lyrics from"), ("words", "karaoke"), ("words", "karaoke offset"),
            ("words", "song lines"),
            ("words", "lyrics tape"), ("words", "lyrics punctuation"),
            ("words", "lyrics capitals"),
            ("spotify", "linking to spotify, for what's playing", [
                ("words", "spotify"), ("words", "spotify client id"),
                ("words", "download liked songs"), ("words", "clear kept lyrics")]),
        ], ("words", "lyrics from")),
        ("books", "the book you type through, and its text", [
            ("words", "book page"), ("words", "book filter"),
            ("words", "bulgarian books"), ("words", "shlokavitsa style")]),
    ]),
    ("typing screen", "what you see and hear while you type", [
        ("hud", "what shows around the words: counters and the keyboard", [
            ("header", "timer", "show timer"), ("header", "progress", "show progress"),
            ("header", "live wpm", "show live wpm"), ("header", "combo", "show combo"),
            ("keyboard", "the on-screen keyboard and its layout", [
                ("look", "keyboard", "on-screen keyboard"), ("look", "layout", "keyboard layout")],
             ("look", "keyboard")),
        ]),
        ("caret", "the caret, its effect, and the carets you race", [
            ("look", "caret"), ("fun", "caret effect"), ("look", "pace caret"), ("look", "ghost"),
        ], ("look", "caret")),
        ("words line", "how the words are laid out", [
            ("look", "word gap"), ("look", "tape")]),
        ("look", "sound"),
    ]),
    ("theme", "the colours: the theme, its background and the text", [
        ("look", "theme"), ("look", "theme creator"),
        ("background", "the theme's background and its accent letters", [
            ("look", "theme background"), ("look", "accent letters")],
         ("look", "theme background")),
        ("text colour", "how light the text is, and bold or italic", [
            ("look", "lighter text"), ("look", "lighter untyped"), ("look", "bold / italic")]),
        ("gradients", "colour running through the words, and heating up with a combo", [
            ("look", "gradients"), ("look", "gradient flow"), ("look", "heat")],
         ("look", "gradients")),
    ]),
    ("effects", "letters bouncing, shaking, popping and more - only looks, never the words", [
        ("letters", "what the letters do as you type them", [
            ("fun", "bounce"), ("fun", "shake"), ("fun", "pop"), ("fun", "fade"), ("fun", "glitch")]),
        ("motion", "how fast effects run, and which way", [
            ("fun", "effect speed"), ("fun", "flow direction")]),
    ]),
    ("art", "the corner pictures", [
        ("look", "theme art", "show art"),
        ("picture", "which picture, in which style and colours", [
            ("fun", "art style"), ("look", "picture"), ("look", "picture colours"),
            ("fun", "art colours", "art shading")]),
        ("art and text", "how the text sits over the art: panel, behind, contrast", [
            ("look", "text panel"), ("look", "art behind text"),
            ("text over art", "letters drawn over the art: contrast and bold", [
                ("look", "text contrast"), ("look", "bold text")]),
            ("look", "see-through")]),
        ("fade", "the art dissolving into the screen at its edges", [
            ("look", "fade on", "fade (all pictures)"), ("look", "art fade", "fade"),
            ("look", "fade round"), ("look", "fade curve"),
            ("top edge", "the fade down from the picture's top", [
                ("look", "fade top"), ("look", "fade start top")], ("look", "fade top")),
            ("side edge", "the fade in from the picture's left", [
                ("look", "fade side"), ("look", "fade start"), ("look", "fade angle")],
             ("look", "fade side")),
        ], ("look", "fade on")),
    ]),
    ("interface", "menus: their layout, border, help, and hiding it all", [
        ("layout", "how menus are laid out, and the border", [
            ("look", "ui style"), ("look", "sidebar tabs"), ("look", "border")],
         ("look", "ui style")),
        ("help", "the key hints and the help box", [
            ("look", "key hints"), ("look", "help box"), ("look", "help border")]),
        ("look", "lowkey"),
    ]),
    ("results", "what the results screen shows", [
        ("charts", "the speed chart and the key heatmap", [
            ("results", "speed chart"), ("results", "key heatmap")]),
        ("lists", "personal best, worst keys and words, the session", [
            ("results", "personal best"), ("results", "worst keys"),
            ("results", "session keys"), ("results", "bad words"), ("results", "session")]),
    ]),
    ("progress", "your goal, what's kept on disk, and starting over", [
        ("progress", "daily goal"), ("progress", "save to disk"), ("progress", "reset"),
        ("progress", "reset settings")]),
]


# Every switch for how the app looks, gathered in one "ui" tab (they stay in
# their own pages too), by where they're built: a quick-access tab at the end.
UI_TAB = [("look", "ui style"), ("look", "sidebar tabs"), ("look", "border"),
          ("look", "key hints"), ("look", "help box"), ("look", "help border"),
          ("look", "theme background"), ("look", "theme art"),
          ("look", "art behind text"), ("look", "text panel"), ("look", "text contrast"),
          ("look", "bold text"), ("look", "see-through"), ("look", "lighter text"),
          ("look", "lighter untyped"), ("look", "fade on"),
          ("header", "timer"), ("header", "progress"), ("header", "live wpm"),
          ("header", "combo"), ("look", "keyboard"), ("look", "lowkey")]


def _origin(it):
    """Where a row was built: (section, label), kept through renaming."""
    if not hasattr(it, "origin"):
        it.origin = (it.section, it.label)
    return it.origin


def build_tree(items):
    """The rows as TREE's pages (see tree_menu.Page), each row renamed as
    TREE says and tagged with its old section, its label and every page it
    sits in, so #look, #fade and the like still find it. The ui tab goes
    at the end; rows TREE doesn't place go in an "other" tab after it."""
    import copy
    items = [it for it in items if not getattr(it, "ui_copy", False)]
    by_key = {_origin(it): it for it in items}
    placed = set()

    def page(name, help, specs, trail, main=None):
        children = []
        for spec in specs:
            if isinstance(spec[2] if len(spec) > 2 else None, list):
                children.append(page(spec[0], spec[1], spec[2], trail + (spec[0],),
                                     spec[3] if len(spec) > 3 else None))
                continue
            it = by_key.get(spec[:2])
            if it is None:
                continue
            placed.add(id(it))
            it.label = spec[2] if len(spec) > 2 else spec[1]
            it.tags = tuple(dict.fromkeys(tuple(it.tags) + spec[:2] + trail))
            children.append(it)
        # the page's main setting: its row is a switch as well as the way in
        lead = next((c for c in children if getattr(c, "origin", None) == main), None) if main else None
        return Page(name, children, help, lead)

    pages = [page(name, help, specs, (name,)) for name, help, specs in TREE]
    ui = []
    for key in UI_TAB:
        it = by_key.get(key)
        if it is not None:
            dup = copy.copy(it)
            dup.tags = tuple(it.tags) + ("ui",)
            dup.ui_copy = True            # placed already; arranging again skips it
            ui.append(dup)
    pages.append(Page("ui", ui, "every switch for how the app looks, in one place"))
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
