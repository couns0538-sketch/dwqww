"""Full property matrix with planted-fault controls for every check."""
import subprocess, json
P="/tmp/probe"
B=[("base","p2_base"),("standpat_incheck","p2_m1c_standpat_classic"),
   ("no_stalemate","p2_m2_no_stalemate"),("no_plycap","p2_m3_no_plycap"),
   ("tt_anybound","p2_m4_tt_no_bound"),("no_evasions","p2_m5_no_evasions")]
FIX=[
 ("P2 mate terminal",      "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"),
 ("P2 stalemate",          "7k/8/6QK/8/8/8/8/8 b - - 0 1"),
 ("P3 incheck nocap",      "1r4k1/8/8/8/8/8/8/1K6 w - - 0 1"),
 ("P3 incheck mate2",      "7k/5K2/8/4Q3/8/8/8/8 b - - 0 1"),
 ("P4 midgame",            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
 ("P5 clock99",            "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40"),
 ("P5 clock100",           "6k1/8/5PPP/8/8/8/8/R6K b - - 100 40"),
]
def run(binp,fen,extra=()):
    r=subprocess.run([f"{P}/{binp}",fen,"-32001","32001",*extra],capture_output=True,text=True,timeout=300)
    if r.returncode!=0: return None
    return json.loads(r.stdout)
w=22
print(f"{'fixture':22s} " + " ".join(f"{n:>13s}" for n,_ in B))
print("-"*(22+14*len(B)))
for name,fen in FIX:
    row=[]
    for n,b in B:
        d=run(b,fen)
        if d is None: row.append("  REFUSED")
        else:
            t=d["trace"]
            row.append(f"{d['scores'][0]:>7d}/{d['nodes']:>4d}")
    print(f"{name:22s} " + " ".join(f"{c:>13s}" for c in row))
print()
print("format = qsearch score / qsearch nodes from the root")
