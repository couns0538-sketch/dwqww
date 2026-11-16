#!/usr/bin/env python3
"""plant_verdict_job1.py — did the job 1 harness catch its two planted faults?

Z1 "200/200 ok, 0 NORESP"  -> the no-answer plant must produce NORESP (and hit the watchdog).
Z2 "0 over the movetime limit" -> the overrun plant must show wall_ms > 50.

Compares job1/outA/mt50.txt (real) with job2/out_plant_job1/{noanswer,overrun} (plants), all through
the same script (job1/timing.py).
"""
import os
import sys


def rows(path):
    with open(path) as fh:
        next(fh)
        return [line.rstrip("\n").split("\t") for line in fh]


def main() -> int:
    j1 = sys.argv[1]
    print("| plant | harness column | plant count | real count | the zero it must break | caught |")
    print("|---|---|---|---|---|---|")
    nb = rows(os.path.join(j1, "..", "job2", "out_plant_job1", "noanswer", "mt50.txt"))
    real = rows(os.path.join(j1, "outA", "mt50.txt"))
    p_n = sum(1 for r in nb if r[5] == "NORESP")
    r_n = sum(1 for r in real if r[5] == "NORESP")
    print(f"| no answer (fake never prints bestmove) | status == NORESP | {p_n}/{len(nb)} | {r_n}/{len(real)} "
          f"| 0 NORESP | {'YES' if p_n else 'NO'} |")

    ov = rows(os.path.join(j1, "..", "job2", "out_plant_job1", "overrun", "mt50.txt"))
    p_o = sum(1 for r in ov if float(r[2]) > 50.0)
    r_o = sum(1 for r in real if float(r[2]) > 50.0)
    print(f"| overrun (fake sleeps 300 ms) | wall_ms > 50 | {p_o}/{len(ov)} | {r_o}/{len(real)} "
          f"| 0 over movetime 50 | {'YES' if p_o else 'NO'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
