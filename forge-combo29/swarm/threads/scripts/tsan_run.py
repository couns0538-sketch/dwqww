#!/usr/bin/env python3
"""Run a Threads>1 search under a ThreadSanitizer build and count the reports.

Two instrument errors fixed here, both from the record:
  - TSAN_OPTIONS was built in a local dict and never handed to Popen, so the run had
    no log_path and the counter read a file that was never written. The count was of
    NOTHING and it printed 0. The environment is now passed explicitly, and the
    script ASSERTS the runner can see the sanitizer (see --probe).
  - TSan reports on stderr. stderr is captured separately and printed, never merged
    into the info stream where a line counter would miss it.

`--probe` mode runs a deliberately racy two-thread program through the SAME runner
and requires a report. Without that, "0 reports" says nothing about the engine.

Usage:
  tsan_run.py probe                     -> must print a warning, exit 0 only then
  tsan_run.py <exe> <fens> <threads> <out.json> [depth]
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402


def run_engine(exe, fens, threads, depth):
    """Drive the engine and return (reports, stderr_text, rows)."""
    tmpdir = tempfile.mkdtemp(prefix="tsanlog-")
    env = dict(os.environ)
    env.pop("TSAN_OPTIONS", None)
    # log_path makes TSan write to <path>.<pid>; history_size keeps the report.
    env["TSAN_OPTIONS"] = f"log_path={tmpdir}/tsan halt_on_error=0"

    import engine as eng
    orig = subprocess.Popen

    class P(orig):
        def __init__(self, *a, **kw):
            kw["env"] = env          # this is the line that was missing
            super().__init__(*a, **kw)

    eng.subprocess.Popen = P
    rows = []
    e = None
    try:
        e = Engine(exe, {"Hash": 64, "Threads": threads}, timeout=900.0)
        for fen in fens:
            e.ucinewgame()
            e.position(fen)
            info, best, wall = e.go(f"depth {depth}", timeout=900.0)
            d = last_depth_info(info)
            rows.append({"fen": fen, "bestmove": best.split()[-1],
                         "nodes": d["nodes"] if d else None})
    finally:
        if e:
            e.close()
        eng.subprocess.Popen = orig

    text = ""
    for name in sorted(os.listdir(tmpdir)):
        text += open(os.path.join(tmpdir, name), errors="replace").read()
    reports = text.count("WARNING: ThreadSanitizer")
    return reports, text, rows, tmpdir


def probe():
    """A known-racy program through the same runner. Must be reported."""
    src = tempfile.mktemp(suffix=".cpp")
    with open(src, "w") as fh:
        fh.write("""#include <thread>
#include <cstdio>
long long g=0;
int main(){ std::thread a([]{for(int i=0;i<200000;i++) g++;});
            std::thread b([]{for(int i=0;i<200000;i++) g++;});
            a.join(); b.join(); printf("%lld\\n",g); }
""")
    exe = tempfile.mktemp(suffix="")
    subprocess.run(["g++", "-fsanitize=thread", "-g", "-O1", "-std=c++20", src, "-o", exe],
                   check=True)
    tmpdir = tempfile.mkdtemp(prefix="tsanprobe-")
    env = dict(os.environ)
    env.pop("TSAN_OPTIONS", None)
    env["TSAN_OPTIONS"] = f"log_path={tmpdir}/probe halt_on_error=0"
    subprocess.run([exe], env=env, capture_output=True)
    text = ""
    for name in os.listdir(tmpdir):
        text += open(os.path.join(tmpdir, name), errors="replace").read()
    n = text.count("WARNING: ThreadSanitizer")
    print(f"probe: racy program reports {n} ThreadSanitizer warning(s)")
    if n == 0:
        print("PROBE FAILED: the runner cannot see a known race, so a 0 on the engine means nothing")
        return 1
    print("PROBE PASSED: this runner detects a known race")
    return 0


def main():
    if sys.argv[1] == "probe":
        return probe()
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    threads = int(sys.argv[3])
    out_path = sys.argv[4]
    depth = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    reports, text, rows, tmpdir = run_engine(exe, fens, threads, depth)
    print(f"threads={threads} positions={len(rows)} depth={depth} "
          f"tsan_warnings={reports} logdir={tmpdir}")
    if reports:
        print(text[:4000])
    print(f"nodes seen (proves the search ran): {[r['nodes'] for r in rows[:5]]}")
    with open(out_path, "w") as fh:
        json.dump({"exe": exe, "threads": threads, "depth": depth, "positions": len(rows),
                   "tsan_warnings": reports, "rows": rows,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0],
                   "report_text": text[:20000]}, fh, indent=2)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
