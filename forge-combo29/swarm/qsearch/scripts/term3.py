"""Property 1: termination. Every probe deadline-bounded (SIGKILL at 45s).
A HANG is a result. Also reports the MaxPly clamp as the mechanism."""
import subprocess, json, sys
sys.path.insert(0,'/tmp/probe')
from deadline import run_with_deadline
CASES=[
 ("promo_fest",  "1n1q1b1r/1P1P1P1P/8/8/8/2K5/1p1p1p1p/R1BQ1B1k w - - 0 1"),
 ("queen_swap",  "3qk3/8/8/3q4/3Q4/8/8/3QK3 w - - 0 1"),
 ("knights",     "1n1n1n1n/1n1n1n1n/8/8/8/8/1N1N1N1N/2K3kN w - - 0 1"),
 ("rooks_open",  "r1r1r1r1/1r1r1r1r/8/8/8/8/1R1R1R1R/2K3kR w - - 0 1"),
 ("dense_mid",   "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
 ("dense_mid_b", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1"),
 ("perpetual",   "8/8/8/8/8/2k5/8/1K1Q4 b - - 0 1"),
 ("kp_only",     "8/8/8/8/8/4k3/4p3/4K3 w - - 0 1"),
]
print(f"{'case':12s} {'ply':>4s} {'score':>8s} {'nodes':>6s} {'maxply':>7s} {'secs':>6s} status")
for name,fen in CASES:
    for ply in (0,100,124,125,127):
        r=run_with_deadline(["/tmp/probe/p2_base",fen,"-32001","32001","--ply",str(ply)],45)
        if r["status"]=="HANG":
            print(f"{name:12s} {ply:4d} {'':>8s} {'':>6s} {'':>7s} {r['secs']:6.2f} ***HANG***")
        else:
            try:
                d=json.loads(r["out"]); t=d["trace"]
                print(f"{name:12s} {ply:4d} {d['scores'][0]:8d} {d['nodes']:6d} {d['maxply']:7d} {r['secs']:6.2f} returned")
            except Exception:
                print(f"{name:12s} {ply:4d} rc={r['rc']} out={r['out'][:80]}")
