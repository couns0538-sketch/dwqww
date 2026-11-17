"""Property 1, the real risk: qsearch at an in-check node generates ALL evasions
(quiet ones included). If the evasion gives check back, the child is in check again,
so qsearch recurses on NON-CAPTURES. A perpetual-check chain is therefore bounded
only by the ply cap. Measure how deep it actually goes."""
import sys, json; sys.path.insert(0,'/tmp/probe')
from deadline import run_with_deadline
CASES=[
 ("perpetual_1","8/8/8/8/8/2k5/8/1K1Q4 b - - 0 1"),
 ("perpetual_2","6k1/8/8/8/8/8/6q1/6K1 w - - 0 1"),
 ("perpetual_3","7k/8/8/8/8/8/5q2/7K w - - 0 1"),
 ("perp_queens","3qk3/8/8/8/8/8/8/3QK3 w - - 0 1"),
 ("perp_rooks","r3k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
]
print(f"{'case':13s} {'score':>8s} {'nodes':>7s} {'maxply':>7s} {'incheck':>8s} {'secs':>6s}")
for name,fen in CASES:
    r=run_with_deadline(["/tmp/probe/p2_base",fen,"-32001","32001"],45)
    if r["status"]=="HANG":
        print(f"{name:13s} ***HANG at {r['secs']}s***")
    else:
        d=json.loads(r["out"]); t=d["trace"]
        print(f"{name:13s} {d['scores'][0]:8d} {d['nodes']:7d} {d['maxply']:7d} {t['in_check_nodes']:8d} {r['secs']:6.2f}")
