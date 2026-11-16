#!/usr/bin/env python3
"""long8addtable.py -- the one command that prints the long-8 addendum table.

Usage: long8addtable.py
Reads runs/<set>_{O,G}_<movetag>.rows for the addendum's 13 settings and prints a
markdown table with the node sum, the percent change against that set's DEFAULTS
run, and the sanitizer count. One committed command, as the brief requires.
"""
import os
import sys

MOVES = [
    ("SoundArms", "SoundInCheckArm=1", "ic1"),
    ("SoundArms", "SoundMateAlphaArm=1", "ma1"),
    ("SoundSteps", "SoundPvArm=1;SoundStepMask=8", "mask8"),
    ("SoundSteps", "SoundPvArm=1;SoundStepMask=1", "mask1"),
    ("SoundSteps", "SoundRegretCount=true", "rc"),
    ("SoundSteps", "SoundRegretProbe=true", "rp"),
    ("NodeLiterals", "NullStaticSlope=48", "nss48"),
    ("NodeLiterals", "NullEvalRedMax=0", "nerm0"),
    ("NodeLiterals", "NullVerifyDepth=1", "nvd1"),
    ("NodeLiterals", "ProbcutImproving=0", "pci0"),
    ("NodeLiterals", "ProbcutReduction=6", "pcr6"),
    ("NodeLiterals", "ProbcutTtSlack=1", "pts1"),
    ("NodeLiterals", "ProbcutStoreReduction=1", "psr1"),
]


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
    print("| set | moved value | O def | O mov | dO% | G def | G mov | dG% | san |")
    print("|---|---|---|---|---|---|---|---|---|")
    total_san = 0
    total_pos = 0
    unchanged = []
    for name, moved, tag in MOVES:
        cd_, sd, kd = read(os.path.join(runs, "%s_O_def.rows" % name))
        cm, sm, km = read(os.path.join(runs, "%s_O_mov.rows" % name))   # original addendum run
        co, so, ko = read(os.path.join(runs, "%s_O_%s.rows" % (name, tag)))
        cdg, sdg, kdg = read(os.path.join(runs, "%s_G_def.rows" % name))
        cog, sog, kog = read(os.path.join(runs, "%s_G_%s.rows" % (name, tag)))
        san = ko + kog
        total_san += san
        total_pos += co + cog
        if so == sd:
            unchanged.append((name, moved, "O"))
        if sog == sdg:
            unchanged.append((name, moved, "G"))
        print("| %s | `%s` | %d | %d | %+.2f%% | %d | %d | %+.2f%% | %d |"
              % (name, moved, sd, so, 100.0 * (so - sd) / sd,
                 sdg, sog, 100.0 * (sog - sdg) / sdg, san))
    print()
    print("settings %d, positions %d, total sanitizer lines %d" % (len(MOVES), total_pos, total_san))
    print("moved values that did NOT change the tree: %s" % (unchanged or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
