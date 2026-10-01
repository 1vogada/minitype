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
        self.pbs = {}    # mode -> {"wpm", "acc", "t"}

    @staticmethod
    def mode(result):
        """What a run is compared against: its mode, plus the difficulty
        when that isn't normal."""
        spec = result.spec
        m = spec.source if spec.source in ("learn", "book") else spec.label
        return m if result.difficulty == "normal" else f"{m} ({result.difficulty})"

    def pb(self, result):
        """The personal best for this run's mode, 0 if there's none yet."""
        return self.pbs.get(self.mode(result), {}).get("wpm", 0.0)

    def add(self, result):
        """Log a run. Returns True if it set a new personal best."""
        mode = self.mode(result)
        self.runs.append({
            "t": round(time.time()),
            "mode": mode,
            "wpm": round(result.wpm, 1),
            "acc": round(result.acc, 1),
            "secs": round(result.elapsed, 1),
            "failed": result.failed,
        })
        del self.runs[:-MAX_RUNS]
        if result.failed or result.wpm <= self.pb(result):
            return False
        self.pbs[mode] = {"wpm": round(result.wpm, 1), "acc": round(result.acc, 1),
                          "t": round(time.time())}
        return True

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

    def apply(self, runs, pbs=None):
        keys = {"t", "mode", "wpm", "acc", "secs", "failed"}
        if isinstance(runs, list):
            self.runs = [r for r in runs if isinstance(r, dict) and keys <= set(r)]
            del self.runs[:-MAX_RUNS]
        if isinstance(pbs, dict):
            self.pbs = {m: v for m, v in pbs.items()
                        if isinstance(v, dict) and isinstance(v.get("wpm"), (int, float))}
