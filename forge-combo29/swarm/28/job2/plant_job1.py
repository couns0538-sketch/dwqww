#!/usr/bin/env python3
"""plant_job1.py — Opus's Rule 1 for job 1's zeros ("0 searches over the limit", "200/200 ok").

The job 1 zeros that a plant must break:
  Z1 "200/200 status ok, 0 NORESP"          -> a fake engine that never answers `bestmove` must be
                                               counted as NORESP for every search.
  Z2 "0 searches over the movetime limit"   -> a fake engine that sleeps past the budget must be
                                               counted over it.
The harness is job1/timing.py, UNCHANGED; only the exe path differs. 8 positions per config to keep it
short (the plant only has to be caught once).

Usage: plant_job1.py OUTROOT
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOB1 = os.path.join(HERE, "..", "job1")


def make_fake(outdir, mode):
    path = os.path.join(outdir, "fake_" + mode)
    with open(path, "w") as fh:
        fh.write("#!/usr/bin/env bash\nexec python3 " + os.path.join(HERE, "fake_engine.py") +
                 " " + mode + " \"$@\"\n")
    os.chmod(path, 0o755)
    return path


def main() -> int:
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for mode, config in [("noanswer", "mt50"), ("overrun", "mt50")]:
        sub = os.path.join(out, mode)
        os.makedirs(sub, exist_ok=True)
        fake = make_fake(sub, mode)
        # 8 positions, 3 s watchdog: the plant must be caught, and the no-answer plant would
        # otherwise burn 8 x 60 s of wall time for nothing.
        subprocess.run(["python3", os.path.join(JOB1, "timing.py"), fake, sub, config, "8", "3"],
                       check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
