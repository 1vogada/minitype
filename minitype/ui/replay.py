"""Watch a finished test again, at its own pace: pause, seek and speed up."""

import time

from ..engine.render import draw
from ..terminal import console, keys

SPEEDS = [0.5, 1, 2, 4]
SEEK = 3.0              # seconds left / right moves
HINTS = "space pause   left/right seek   up/down speed   tab from the start   esc back"


def replay_screen(app, replay):
    """Play the replay until esc. Returns None."""
    t, speed, playing = 0.0, 1, True
    last = time.time()
    while True:
        now = time.time()
        if playing:
            t = min(replay.length, t + (now - last) * speed)
        last = now
        at_end = t >= replay.length
        typed, wi, errors, typos, combo, wrong, n = replay.at(t)
        parts = ["replay", f"{t:.1f}s / {replay.length:.1f}s",
                 f"{replay.wpm(typed, t):.0f} wpm", f"{speed:g}x"]
        if at_end:
            parts.append("end - space plays again")
        elif not playing:
            parts.append("paused")
        draw(app.styles(), app.settings, "   ".join(parts), replay.words, typed, wi,
             max(10, console.size()[0] - 4), HINTS, (), wrong, (), False, errors,
             combo, now, -1.0, typos, replay.tape, replay.breaks, replay.split)
        if not keys.key_ready():
            time.sleep(0.01)
            continue
        key = keys.read_key(resize=False)
        if key in (keys.ESC, keys.CTRL_C, "r"):
            return None
        if key == " ":
            if at_end:
                t = 0.0
            playing = at_end or not playing
        elif key in (keys.LEFT, keys.RIGHT):
            t = max(0.0, min(replay.length, t + (SEEK if key == keys.RIGHT else -SEEK)))
        elif key in (keys.UP, keys.DOWN):
            i = SPEEDS.index(speed) + (1 if key == keys.UP else -1)
            speed = SPEEDS[max(0, min(len(SPEEDS) - 1, i))]
        elif key in (keys.TAB, keys.HOME):
            t, playing = 0.0, True
