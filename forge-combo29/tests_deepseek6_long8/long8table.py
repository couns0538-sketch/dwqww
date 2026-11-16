#!/usr/bin/env python3
"""long8table.py -- the one command that prints the long-8 table.

Usage: long8table.py
Reads runs/<set>_{O,G}_{def,mov}.rows and prints a markdown table with the
default and moved node sums, the percent change, and the sanitizer count.
Also prints the two known-answer checks (defaults must equal long 7's
3,809,466 on O and 7,290,580 on G).
"""
import os
import sys

SETS = [
    ("LmrGiveCheck", "LmrGiveCheck=0"),
    ("LmrCutNode", "LmrCutNode=0"),
    ("LmrTtPv", "LmrTtPv=0"),
    ("SoundArms", "SoundPvArm=1"),
    ("SoundSteps", "SoundPvArm=1;SoundStepMask=0"),
    ("NodeLiterals", "NullStaticBase=360"),
    ("IirNoRoot", "IirRootExclude=1"),
]
BASE = {"O": 3809466, "G": 7290580}


def read(path):
    n = s = k = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 4:
                continue
            n += 1
            s += int(p[1])
            k += int(p[3])
    return n, s, k


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    runs = os.path.join(here, "runs")
    print("| set | moved value | O def | O mov | dO% | O san | G def | G mov | dG% | G san |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    total_san = 0
    total_pos = 0
    bad_default = []
    for name, moved in SETS:
        cells = []
        for st in ("O", "G"):
            nd, sd, kd = read(os.path.join(runs, "%s_%s_def.rows" % (name, st)))
            nm, sm, km = read(os.path.join(runs, "%s_%s_mov.rows" % (name, st)))
            total_san += kd + km
            total_pos += nd + nm
            if sd != BASE[st]:
                bad_default.append((name, st, sd))
            pct = 100.0 * (sm - sd) / sd if sd else 0.0
            cells.append((sd, sm, pct, kd + km))
        print("| %s | `%s` | %d | %d | %+.2f%% | %d | %d | %d | %+.2f%% | %d |"
              % (name, moved, cells[0][0], cells[0][1], cells[0][2], cells[0][3],
                 cells[1][0], cells[1][1], cells[1][2], cells[1][3]))
    print()
    print("known-answer check (defaults must equal the clean sanitizer baseline): %s"
          % ("ALL 14 MET (O 3809466, G 7290580)" if not bad_default else "FAILED %s" % bad_default))
    print("total sanitizer lines over all 28 settings (%d positions): %d"
          % (total_pos, total_san))
    return 0 if not bad_default and total_san == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
