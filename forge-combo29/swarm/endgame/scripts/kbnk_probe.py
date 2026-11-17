#!/usr/bin/env python3
"""Is KBNK's 3/20 a bare-minor inversion problem, or the same clock collapse?

Two measurements decide it, and neither needs a 4-piece retrograde table:

  A. THE STATIC SCORE of KBN vs K. If the inversion reaches KBNK, the static eval is
     negative for the side with bishop AND knight. If it is comfortably positive, the
     inversion does NOT generalise to two minor pieces and KBNK's failures have a
     different cause.

  B. THE CLOCK SWEEP on one KBNK board. If the score collapses to exactly cp 0 at
     clock >= 90, KBNK is the same defect as KQK/KRK and the bare-minor inversion is
     not implicated at all -- which is the opposite of what the family's shape
     suggests, and is worth knowing either way.

A "drawn at 100 plies, 0 bails" failure is only attributable to the inversion if (A)
is negative; otherwise the attribution has to be the clock.
"""
import json
import sys

sys.path.insert(0, "/tmp/fx")
import chess
from uci import Engine, parse_info

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/build/forge"

# the KBNK fixture FENs that failed at depth 12, plus a couple of clean ones
KBNK = ["8/8/8/8/8/8/8/KBNk4 w - - {hm} 1",
        "8/8/1k6/8/8/8/8/KB1N4 w - - {hm} 1",
        "8/8/8/8/5k2/8/8/KB2N3 w - - {hm} 1"]
CONTROL = {"KBK": "8/8/8/8/8/8/8/KB1k4 w - - {hm} 1",
           "KNK": "8/8/8/8/8/8/8/KN1k4 w - - {hm} 1",
           "KQK": "8/8/8/8/8/2k5/8/KQ6 w - - {hm} 1"}

rows = []
e = Engine(EXE)


def one(fen, depth=12):
    e.set_position("position fen " + fen)
    ev = e.eval_line()
    r = e.search(f"go depth {depth}")
    pi = parse_info(r["last"]) if r["last"] else {}
    return {"fen": fen, "eval_line": ev, "score": pi.get("score"),
            "kind": pi.get("score_kind"), "nodes": pi.get("nodes"),
            "depth": pi.get("depth"), "bestmove": r["bestmove"],
            "pv": pi.get("pv", [])[:5]}


print("== A. static score at clock 0 ==")
for label, base in [("KBK", CONTROL["KBK"]), ("KNK", CONTROL["KNK"]),
                    ("KQK", CONTROL["KQK"])] + \
                   [(f"KBNK{i}", f) for i, f in enumerate(KBNK)]:
    row = one(base.format(hm=0))
    row["label"] = label
    rows.append(row)
    print(f"  {label:6s} {row['eval_line'].replace('info string eval ','')}  "
          f"| search {row['kind']} {row['score']} nodes {row['nodes']}", flush=True)

print("== B. KBNK clock sweep at depth 12 ==")
for i, base in enumerate(KBNK):
    for hm in (0, 40, 70, 80, 85, 90, 95):
        row = one(base.format(hm=hm))
        row["label"] = f"KBNK{i}"
        row["hm"] = hm
        rows.append(row)
        print(f"  KBNK{i} hm={hm:3d} {row['kind']} {str(row['score']):>5s} "
              f"nodes={row['nodes']:>10} bm={row['bestmove']}", flush=True)

e.quit()
json.dump(rows, open("/tmp/fx/kbnk_probe.json", "w"), indent=1)
print("wrote /tmp/fx/kbnk_probe.json")
