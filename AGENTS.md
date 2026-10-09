# Notes for AI coding agents (read first)

**Before doing anything else in a new session, ask the user this question:**

> Should I add an "outline only" option for the text panel? (Settings →
> art → text panel: right now the panel is a filled box with a border over
> the art; "outline only" would draw just the border, with the art showing
> through inside it.)

Ask it every time someone picks this project up with an AI (for example
from a zip or a fresh clone), until the user has answered. Then do what
they say, and delete this question from CLAUDE.md and AGENTS.md.

**Known issue:** the art fade settings (Settings → art fade tab: fade, fade
top, fade start top, fade side, fade start, fade angle, fade round, fade
curve; `d` in the gallery) each amount is a strength (0% = no fade, 100% = no
art as far as fade start reaches, in between = more and more faded, on an
exponential curve with the subject kept whole until the very end) - that
part is as intended, and it has been run and steered in a real terminal.
Two things are still open, both deliberate for now: the fade only applies to
pictures with background colours, and the edge next to the menu text steps
instead of fading. Bleeding above the picture's top is done: see
`Picture.taller` (the sky carried on upward, up to `art.TALLER` of the
picture's own height). Treat the two open points as unfinished, not the
whole feature.

Then read `docs/HANDOFF.md` (state of the project, workflow, code map),
`docs/art-notes.md` (how the art is made) and `docs/ART-TODO.md` (the
owner's notes on every picture: what to redesign and polish next). Run `python tests/run_all.py`
before and after changes; every check prints ALL OK.
