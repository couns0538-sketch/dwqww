"""Property 5: base vs band-repair, the exact table FINDINGS cites."""
import sys; sys.path.insert(0,'/tmp')
from uci_drive import Engine
F="6k1/8/5PPP/8/8/8/8/R6K b - - {} 40"
CTRL="6k1/5ppp/8/8/8/8/8/R5NK b - - {h} 40"
print("=== band fixture 6k1/8/5PPP/8/8/8/8/R6K b - - {h} 40, go depth 12 ===")
print(f"{'clock':>5s} {'base score':>11s} {'base nodes':>10s} {'repair score':>12s} {'repair nodes':>12s}")
rows={}
for h in (96,97,98,99,100):
    for label,path in (("base","/tmp/build/forge"),("repair","/tmp/build_fix/forge")):
        e=Engine(path=path,opts=[("OwnBook","false")])
        e.send("ucinewgame"); e.send(f"position fen {F.format(h)}"); e.drain(0.03)
        e.send("go depth 12"); ls=e.read_until(lambda l:l.startswith("bestmove"),90)
        info=[l for l in ls if l.startswith("info depth 12")]
        t=info[-1].split() if info else []
        sc=(t[t.index("score")+1]+t[t.index("score")+2]) if t else "NONE"
        nd=t[t.index("nodes")+1] if t else "-"
        rows.setdefault(h,{})[label]=(sc,nd)
        e.close()
for h in sorted(rows):
    b=rows[h]["base"]; r=rows[h]["repair"]
    print(f"{h:5d} {b[0]:>11s} {b[1]:>10s} {r[0]:>12s} {r[1]:>12s}")

print()
print("=== six-pawn control 6k1/5ppp/8/8/8/8/8/R5NK b - - {h} 40 (draw is CORRECT here) ===")
print(f"{'clock':>5s} {'base score':>11s} {'base nodes':>10s} {'repair score':>12s} {'repair nodes':>12s}")
for h in (96,97,98,99,100):
    out={}
    for label,path in (("base","/tmp/build/forge"),("repair","/tmp/build_fix/forge")):
        e=Engine(path=path,opts=[("OwnBook","false")])
        e.send("ucinewgame"); e.send(f"position fen {CTRL.format(h=h)}"); e.drain(0.03)
        e.send("go depth 12"); ls=e.read_until(lambda l:l.startswith("bestmove"),90)
        info=[l for l in ls if l.startswith("info depth 12")]
        t=info[-1].split() if info else []
        out[label]=((t[t.index("score")+1]+t[t.index("score")+2]) if t else "NONE",
                    t[t.index("nodes")+1] if t else "-")
        e.close()
    print(f"{h:5d} {out['base'][0]:>11s} {out['base'][1]:>10s} {out['repair'][0]:>12s} {out['repair'][1]:>12s}")
