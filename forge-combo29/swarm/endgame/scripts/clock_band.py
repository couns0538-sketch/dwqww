#!/usr/bin/env python3
"""Pin the clock band where a WON ending's root score collapses, and its cost.

Observed first in play: after promoting, the engine shuffled kings while the clock
climbed, and depth-12 searches on a THREE-PIECE board took 2-16 s each. This script
sweeps the clock on one fixed board so the band and the cost are attributable.

Also runs the depth sweep: if the collapse is the leaf draw rule (a line that reaches
clock 100 inside the tree scores 0), then a SHALLOW search should be unaffected -- it
never reaches the horizon -- and the collapse should begin at depth ~100-hm.
"""
import json
import sys

sys.path.insert(0, "/tmp/fx")
import chess
from uci import Engine, parse_info

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/build/forge"
FEN = "8/8/8/8/8/2k5/8/KQ6 w - - {hm} 1"     # KQK, mate in 10 from clock 0

rows = []
e = Engine(EXE)
print("== clock sweep at depth 12 ==")
for hm in range(80, 100):
    e.set_position("position fen " + FEN.format(hm=hm))
    r = e.search("go depth 12")
    pi = parse_info(r["last"]) if r["last"] else {}
    rows.append({"hm": hm, "depth": 12, "score": pi.get("score"),
                 "kind": pi.get("score_kind"), "nodes": pi.get("nodes"),
                 "bestmove": r["bestmove"], "pv": pi.get("pv", [])[:6]})
    print(f"  hm={hm:3d} {pi.get('score_kind')} {pi.get('score'):>5} "
          f"nodes={pi.get('nodes'):>10} bm={r['bestmove']} "
          f"pv={' '.join(pi.get('pv',[])[:4])}", flush=True)

print("== depth sweep inside the collapse ==")
for hm in (85, 90, 95):
    for d in (4, 6, 8, 10, 12, 14):
        e.set_position("position fen " + FEN.format(hm=hm))
        r = e.search(f"go depth {d}")
        pi = parse_info(r["last"]) if r["last"] else {}
        rows.append({"hm": hm, "depth": d, "score": pi.get("score"),
                     "kind": pi.get("score_kind"), "nodes": pi.get("nodes"),
                     "bestmove": r["bestmove"]})
        print(f"  hm={hm:3d} depth={d:2d} {pi.get('score_kind')} {pi.get('score'):>5} "
              f"nodes={pi.get('nodes'):>10} bm={r['bestmove']}", flush=True)

print("== control: EvalRule50Damp on, same sweep ==")
e.quit()
e = Engine(EXE, {"EvalRule50Damp": "true"})
for hm in (85, 90, 95):
    e.set_position("position fen " + FEN.format(hm=hm))
    r = e.search("go depth 12")
    pi = parse_info(r["last"]) if r["last"] else {}
    rows.append({"hm": hm, "depth": 12, "damp": True, "score": pi.get("score"),
                 "kind": pi.get("score_kind"), "nodes": pi.get("nodes"),
                 "bestmove": r["bestmove"]})
    print(f"  DAMP hm={hm:3d} {pi.get('score_kind')} {pi.get('score'):>5} "
          f"nodes={pi.get('nodes'):>10} bm={r['bestmove']}", flush=True)
e.quit()
json.dump(rows, open("/tmp/fx/clock_band.json", "w"), indent=1)
