import sys; sys.path.insert(0,'/tmp')
from uci_drive import Engine
PINS={11:312866,13:862329,16:3024920}
for label,path in [("base(6b98f217)","/tmp/build/forge"),("band-repair","/tmp/build_fix/forge")]:
    e=Engine(path=path); out=[]
    for n,exp in PINS.items():
        e.send(f"bench {n}"); ls=e.read_until(lambda l:"bench depth" in l and f" {n} " in l,300)
        got=None
        for l in ls:
            if f"bench depth {n} " in l:
                p=l.split(); got=int(p[p.index("nodes")+1])
        out.append(f"bench {n} = {got} {'OK' if got==exp else 'MISMATCH'}")
    e.send("position startpos"); e.send("go perft 5")
    ls=e.read_until(lambda l:l.startswith("nodes "),300)
    pf=ls[-1].split()[1] if ls else "TIMEOUT"
    out.append(f"perft 5 = {pf} {'OK' if pf=='4865609' else 'MISMATCH'}")
    e.close()
    print(f"{label:18s} " + " | ".join(out))
