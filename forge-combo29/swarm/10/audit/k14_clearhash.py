import sys; sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
def sess(plan,tag):
    d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
    d.opt("OwnBook","false"); d.opt("Threads","1"); d.opt("Hash","16"); d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    out=[]
    for s in plan:
        if s=='C': d.write("setoption name Clear Hash"); d.isready(); out.append(('C',))
        elif s=='N': d.write("ucinewgame"); d.isready(); out.append(('N',))
        else:
            n,b,l=d.go("go depth 12")
            sc=None
            for x in reversed(l):
                if " score cp " in x: sc=int(x.split(" score cp ")[1].split()[0]); break
            out.append(('U',n,sc,b))
    d.quit(); return out
print("Is Clear Hash a true cold-start control? (depth 12, startpos)")
for tag,plan in [("U only",['U']),("U,C,U",['U','C','U']),("U,C,C,U",['U','C','C','U']),
                 ("U,N,U",['U','N','U']),("U,N,C,U",['U','N','C','U'])]:
    print("  %-10s -> %s"%(tag,sess(plan,tag)))
print()
print("3 reps of U,C,U to confirm determinism:")
for r in range(3):
    print("   ",sess(['U','C','U'],'r'))
