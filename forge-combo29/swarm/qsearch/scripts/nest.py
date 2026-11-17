import subprocess, json
FENS=[
 ("dense_w","r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
 ("dense_b","r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1"),
 ("p3","r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"),
 ("promo","1n1q1b1r/1P1P1P1P/8/8/8/2K5/1p1p1p1p/R1BQ1B1k w - - 0 1"),
 ("kqp","4k3/8/8/8/8/8/4q3/4K3 w - - 0 1"),
 ("kq2","6k1/8/8/8/8/8/1q6/K7 w - - 0 1"),
 ("queens","3qk3/8/8/3q4/3Q4/8/8/3QK3 w - - 0 1"),
 ("perppos","4k3/8/8/8/8/8/8/Q3K2q w - - 99 60"),
]
print(f"{'case':9s} {'nodes':>6s} {'inchk':>6s} {'nested':>7s} {'maxchkdepth':>12s} {'maxply':>7s}")
for n,f in FENS:
    r=subprocess.run(["/tmp/probe/p2_base",f,"-32001","32001"],capture_output=True,text=True)
    try:
        d=json.loads(r.stdout); t=d["trace"]
        print(f"{n:9s} {t['nodes']:6d} {t['in_check_nodes']:6d} {t['nested_inchk']:7d} {t.get('maxchkdepth','-'):>12} {d['maxply']:7d}")
    except Exception as e:
        print(f"{n:9s} ERR {r.returncode} {r.stdout[:70]}")
