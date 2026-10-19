"""The system's play / pause, for ctrl-p in a test: it pauses whatever is
playing music - Spotify's app, a browser tab, anything that listens to the
media keys - without needing Spotify's own permission to control playback.

Windows: the play/pause media key, pressed through user32. macOS: Spotify,
then Music, through AppleScript. Linux: playerctl, if it's there.
"""

import os
import shutil
import subprocess
import sys

VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


def play_pause():
    """Toggle play / pause on the system; whether it could be sent."""
    try:
        if os.name == "nt":
            import ctypes
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            return True
        if sys.platform == "darwin":
            for app in ("Spotify", "Music"):
                script = (f'if application "{app}" is running then '
                          f'tell application "{app}" to playpause')
                if subprocess.run(["osascript", "-e", script], capture_output=True,
                                  timeout=3).returncode == 0:
                    return True
            return False
        if shutil.which("playerctl"):
            return subprocess.run(["playerctl", "play-pause"], capture_output=True,
                                  timeout=3).returncode == 0
    except (OSError, subprocess.SubprocessError, AttributeError):
        pass
    return False
