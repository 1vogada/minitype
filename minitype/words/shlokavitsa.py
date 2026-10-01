"""Bulgarian Cyrillic to шльокавица (shlokavitsa), Bulgarian written with
Latin letters and digits the way people type it in chats.

There's no single standard, so there are three styles:

    classic   the chat style: ч 4, ш 6, щ 6t, я q, ж j, ц c, ъ y, ю iu
    letters   the same idea without digits: ч ch, ш sh, щ sht, я ya, ж zh
    official  Bulgaria's 2009 transliteration law: ц ts, ъ a, й y, ю yu

Only the letters change, never the word boundaries, so a converted book
has exactly as many words as the original.
"""

BASE = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "з": "z",
    "и": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h",
    # letters that turn up in Bulgarian text from Russian or old spelling
    "ѝ": "i", "ѐ": "e", "ы": "y", "э": "e", "ё": "yo", "ѣ": "e", "ѫ": "a",
}

STYLES = {
    "classic": {"ж": "j", "й": "i", "ц": "c", "ч": "4", "ш": "6", "щ": "6t",
                "ъ": "y", "ь": "y", "ю": "iu", "я": "q"},
    "letters": {"ж": "zh", "й": "y", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sht",
                "ъ": "y", "ь": "y", "ю": "yu", "я": "ya"},
    "official": {"ж": "zh", "й": "y", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sht",
                 "ъ": "a", "ь": "y", "ю": "yu", "я": "ya"},
}
STYLE_NAMES = list(STYLES)


def is_cyrillic(c):
    return "Ѐ" <= c <= "ӿ"


def _table(style):
    return dict(BASE, **STYLES.get(style, STYLES["classic"]))


def convert_word(word, style="classic", table=None):
    table = table or _table(style)
    if not any(is_cyrillic(c) for c in word):
        return word
    shouting = len(word) > 1 and word.isupper()
    out = []
    for c in word:
        low = c.lower()
        if low not in table:
            out.append(c)
        elif c == low:
            out.append(table[low])
        else:
            t = table[low]
            out.append(t.upper() if shouting else t[:1].upper() + t[1:])
    return "".join(out)


def convert(words, style="classic"):
    table = _table(style)
    return [convert_word(w, style, table) for w in words]
