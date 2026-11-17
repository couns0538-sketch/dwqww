"""Does the documented leaf-draw band fire on a NON-mate position where the
true value is ~-1000? Sweep the clock and watch where cp 0 appears."""
import subprocess, sys, json
sys.path.insert(0,'/tmp')
from uci_drive import Engine
FEN="4k3/8/8/8/8/8/8/Q3K2q w - - {} 60"
e=Engine(opts=[("OwnBook","false")])
print(f"{'clock':>5s} {'score':>8s} {'nodes':>8s} {'best':>7s}")
for h in range(90,101):
    f=FEN.format(h)
    e.send("ucinewgame"); e.send(f"position fen {f}"); e.drain(0.02)
    e.send("go depth 12")
    ls=e.read_until(lambda l:l.startswith("bestmove"),60)
    info=[l for l in ls if l.startswith("info depth 12")]
    if info:
        t=info[-1].split()
        sc=t[t.index("score")+1:t.index("score")+3]
        nd=t[t.index("nodes")+1]
        print(f"{h:5d} {sc[1]:>8s} {nd:>8s} {ls[-1].split()[1]:>7s}")
    else:
        print(f"{h:5d} {'NO INFO':>8s} {'-':>8s} {ls[-1].split()[1] if ls else 'TIMEOUT':>7s}")
e.close()
