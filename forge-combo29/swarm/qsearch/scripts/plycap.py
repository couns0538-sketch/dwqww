import sys, json; sys.path.insert(0,'/tmp/probe')
from deadline import run_with_deadline
print("=== does removing the ply cap (m3) hang? ===")
for name,fen in [("queen_swap","3qk3/8/8/3q4/3Q4/8/8/3QK3 w - - 0 1"),
                 ("promo_fest","1n1q1b1r/1P1P1P1P/8/8/8/2K5/1p1p1p1p/R1BQ1B1k w - - 0 1"),
                 ("dense_mid","r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")]:
    for binp in ("p2_base","p2_m3_no_plycap"):
        for ply in (0,125,127):
            r=run_with_deadline([f"/tmp/probe/{binp}",fen,"-32001","32001","--ply",str(ply)],30)
            if r["status"]=="HANG":
                print(f"  {name:11s} {binp:18s} ply={ply:3d} ***HANG at {r['secs']}s***")
            else:
                d=json.loads(r["out"]) if r["out"].startswith("{") else {}
                print(f"  {name:11s} {binp:18s} ply={ply:3d} score={d.get('scores',['?'])[0]:>8} maxply={d.get('maxply','?'):>4} rc={r['rc']} {r['secs']:.2f}s")
