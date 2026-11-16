#!/usr/bin/env python3
"""plant_test.py — Opus's Rule 1 applied to job 2's zeros.

Runs the SAME harness (lowtime.py, unchanged, same 10 clock configs) against a fake engine that plants
a fault, and checks the harness's own columns catch it:
  illegal  -> bestmove_legal must show False somewhere (job 2 reports "400/400 legal" = zero illegal)
  overrun  -> wall_ms must exceed the wtime sent (job 2 reports "0 over wtime" = zero time losses)

The harness is NOT modified for the plant; the fake engine speaks the same UCI.

Usage: plant_test.py OUTDIR
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


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
    for mode in ("illegal", "overrun"):
        sub = os.path.join(out, mode)
        os.makedirs(sub, exist_ok=True)
        fake = make_fake(sub, mode)
        subprocess.run(["python3", os.path.join(HERE, "lowtime.py"), fake, sub], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
