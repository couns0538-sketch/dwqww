"""Sweep the band: for each fixture (known p) and each clock H, the oracle says
FOUND or MISSED, and we compare all three builds against it.

Band cells are separated from root-guard cells by NODE COUNT: a real band cell
searches (>0 nodes); a root-guard cell returns 0 nodes. Mixing them is the trap.
"""
import sys, json
sys.path.insert(0,'.')
from family_lib import ask
from oracle_claim_model import solve, show

MATE = 10**5
FIX = [
  ("p2 mate-in-1", "6k1/8/5PPP/8/8/8/8/R6K b - - {h} 40", 2),
  ("p4 mate-in-2", "6k1/8/6K1/8/8/8/8/R7 b - - {h} 40", 4),
]
import os
builds = {"base": os.environ.get("BASE_EXE",""), "composed": os.environ.get("COMPOSED_EXE",""),
          "fixed": os.environ.get("FIXED_EXE","")}
rows=[]
for label, tmpl, p in FIX:
    print(f"\n=== {label} (mating move at ply {p})")
    print(f"{'H':>4} {'oracle':>10} {'truth':>7} | " + " | ".join(f"{k:>22}" for k in builds))
    for h in range(94, 101):
        fen = tmpl.format(h=h)
        v = solve(fen, max_ply=p+3)
        # exact: convert the solver's ply value to the engine's "mate N" string.
        # v<0 means the side to move is mated in (MATE+v) plies -> N = ceil(plies/2).
        if v < -MATE//2:
            plies = MATE + v; truth = f"mate -{(plies + 1)//2}"
        elif v > MATE//2:
            plies = MATE - v; truth = f"mate {(plies + 1)//2}"
        else:
            truth = "cp 0"
        # what SHOULD the engine report?  mate if truth is a mate, else draw
        row={"label":label,"p":p,"h":h,"fen":fen,"truth":truth}
        cells=[]
        for k,exe in builds.items():
            r = ask(exe, f"position fen {fen}", depth=12)
            ok = (r["score"]==truth) if truth!="draw" else (r["score"]=="cp 0")
            row[k]={"score":r["score"],"nodes":r["nodes"],"bestmove":r["bestmove"],"ok":ok}
            cells.append(f"{str(r['score']):>9} n={str(r['nodes']):>6} {'OK' if ok else 'WRONG'}")
        rows.append(row)
        print(f"{h:>4} {truth:>10} {'':>7} | " + " | ".join(cells))

out = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence", "band_sweep.json"))
json.dump(rows, open(out, "w"), indent=1)
print("\n--- totals (band cells only: nodes>0 in base, i.e. not the root guard)")
for k in builds:
    band = [r for r in rows if r[k]["nodes"] not in (None,0)]
    print(f"  {k:9} correct {sum(1 for r in rows if r[k]['ok'])}/{len(rows)}  "
          f"(searched {len(band)} cells)")
