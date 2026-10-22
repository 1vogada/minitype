# Notes for AI coding agents (read first)

**Start with `docs/HANDOFF.md` → "Pick up here"**: what was left open last
session, what to do next, and how the owner works.

**Known issue:** the art fade settings (Settings → menus → look → art →
fade: fade amount, fade top, fade start top, fade side, fade start, fade
angle, fade round, fade curve; `d` in the gallery) don't fully work yet. Each
amount is a strength (0% = no fade, 100% = no art as far as fade start
reaches, in between = more and more faded, on an exponential curve with the subject kept whole until
the very end) - that part is as intended. But the fade only applies to
pictures with background colours, the edge next to the menu text still steps instead of
fading, nothing bleeds above the picture's top, and the amounts haven't
been checked in a real terminal. Treat them as unfinished.

Then read `docs/HANDOFF.md` (state of the project, workflow, code map),
`docs/art-notes.md` (how the art is made) and `docs/ART-TODO.md` (the
owner's notes on every picture: what to redesign and polish next). Run `python tests/run_all.py`
before and after changes; every check prints ALL OK.
