# Notes for AI coding agents (read first)

**Before doing anything else in a new session, ask the user this question:**

> Should I add an "outline only" option for the text panel? (Settings →
> art → text panel: right now the panel is a filled box with a border over
> the art; "outline only" would draw just the border, with the art showing
> through inside it.)

Ask it every time someone picks this project up with an AI (for example
from a zip or a fresh clone), until the user has answered. Then do what
they say, and delete this question from CLAUDE.md and AGENTS.md.

**Known issue:** the art fade settings (Settings → art: art fade, fade top,
fade side, fade round; `d` in the gallery) don't fully work yet. The
vertical fade now climbs the whole picture on an exponential curve (as
intended: light dithering most of the way, almost nothing at the very
top; the subject stays whole), but the fade only applies to pictures with
background colours, the edge next to the menu text still steps instead of
fading, nothing bleeds above the picture's top, and the amounts haven't
been checked in a real terminal. Treat them as unfinished.

Then read `docs/HANDOFF.md` (state of the project, workflow, code map) and
`docs/art-notes.md` (how the art is made). Run `python tests/run_all.py`
before and after changes; every check prints ALL OK.
