import sys; sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
import chess
ALL=" ".join(m.uci() for m in chess.Board().legal_moves)
def one(cmd,iir=None):
    d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
    d.opt("OwnBook","false"); d.opt("Threads","1"); d.opt("Hash","16")
    if iir is not None: d.opt("IirDepth",str(iir))
    d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    n,b,l=d.go(cmd); d.quit()
    sc=None
    for x in reversed(l):
        if " score cp " in x: sc=int(x.split(" score cp ")[1].split()[0]); break
    return n,b,sc
print("Does IIR explain the residual? depth 12, IirDepth 20 = IIR cannot fire")
for iir in (None,20):
    u=one("go depth 12",iir); s=one("go depth 12 searchmoves e2e4",iir); a=one("go depth 12 searchmoves "+ALL,iir)
    print(" IirDepth=%s | U %s cp%s n%s | single %s cp%s n%s | all20 %s cp%s n%s"%(
        iir,u[1],u[2],u[0],s[1],s[2],s[0],a[1],a[2],a[0]))
print()
print("contamination, IirDepth 20 (unrestricted after restricted vs control):")
def sess(plan,iir=20):
    d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
    d.opt("OwnBook","false"); d.opt("Threads","1"); d.opt("Hash","16"); d.opt("IirDepth",str(iir)); d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    out=[]
    for k in plan:
        n,b,l=d.go("go depth 12 searchmoves "+ALL if k=='R' else "go depth 12")
        sc=None
        for x in reversed(l):
            if " score cp " in x: sc=int(x.split(" score cp ")[1].split()[0]); break
        out.append((k,n,b,sc))
    d.quit(); return out
print("  R,U ->",sess(['R','U']))
print("  U,U ->",sess(['U','U']))
