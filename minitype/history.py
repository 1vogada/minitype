"""Every finished test, kept across sessions when saving is on. Feeds the
profile screen and the daily goal."""

import time

MAX_RUNS = 2000


def _day_start(now=None):
    t = time.localtime(now)
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, -1))


class History:
    def __init__(self):
        self.runs = []   # {"t", "mode", "wpm", "acc", "secs", "failed"}

    def add(self, result):
        spec = result.spec
        self.runs.append({
            "t": round(time.time()),
            "mode": "learn" if spec.source == "learn" else spec.label,
            "wpm": round(result.wpm, 1),
            "acc": round(result.acc, 1),
            "secs": round(result.elapsed, 1),
            "failed": result.failed,
        })
        del self.runs[:-MAX_RUNS]

    def completed(self):
        return [r for r in self.runs if not r["failed"]]

    def total_seconds(self):
        return sum(r["secs"] for r in self.runs)

    def today_seconds(self):
        start = _day_start()
        return sum(r["secs"] for r in self.runs if r["t"] >= start)

    def best_by_mode(self):
        best = {}
        for r in self.completed():
            best[r["mode"]] = max(best.get(r["mode"], 0), r["wpm"])
        return best

    def apply(self, runs):
        keys = {"t", "mode", "wpm", "acc", "secs", "failed"}
        if isinstance(runs, list):
            self.runs = [r for r in runs if isinstance(r, dict) and keys <= set(r)]
            del self.runs[:-MAX_RUNS]
