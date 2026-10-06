"""Run every check script; each prints ALL OK when it passes.

    python tests/run_all.py            all of them
    python tests/run_all.py decor      the ones whose names contain "decor"

Run from anywhere; the repo root is put on the path for each.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# diagnostics that print a report rather than pass or fail
NOT_CHECKS = {"menu_look.py", "shows_check.py", "run_all.py"}


def main(args):
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, "*.py")))
    names = [n for n in names if n not in NOT_CHECKS and (not args or any(a in n for a in args))]
    env = dict(os.environ, PYTHONPATH=ROOT, PYTHONIOENCODING="utf-8")
    failed = []
    for n in names:
        r = subprocess.run([sys.executable, os.path.join(HERE, n)], cwd=ROOT, env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        last = (r.stdout.strip().splitlines() or [""])[-1] if r.returncode == 0 else \
            (r.stderr.strip().splitlines() or ["?"])[-1]
        ok = r.returncode == 0 and last == "ALL OK"
        print(f"{'ok  ' if ok else 'FAIL'} {n}: {last}")
        if not ok:
            failed.append(n)
    print(f"\n{len(names) - len(failed)} of {len(names)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
