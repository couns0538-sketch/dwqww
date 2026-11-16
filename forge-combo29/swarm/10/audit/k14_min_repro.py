import sys; sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
def one(cmd,clear_first=False):
    d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
    d.opt("OwnBook","false"); d.opt("Threads","1"); d.opt("Hash","16"); d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    if clear_first:
        d.write("setoption name Clear Hash"); d.isready()
    n,b,l=d.go(cmd); d.quit()
    sc=None
    for x in reversed(l):
        if " score cp " in x: sc=int(x.split(" score cp ")[1].split()[0]); break
    return n,b,sc
print("MINIMAL REPRO: the move e2e4, scored at the root, depth N")
print("depth | unrestricted says | searchmoves e2e4 says | searchmoves e2e4 + ClearHash")
for dep in (8,10,12,14):
    u=one("go depth %d"%dep)
    r=one("go depth %d searchmoves e2e4"%dep)
    rc=one("go depth %d searchmoves e2e4"%dep, clear_first=True)
    # find what unrestricted scored e2e4: use multipv? just report root scores
    print("%5d | %5s %-5s nodes %-7s | %5s %-5s nodes %-7s | %5s nodes %-7s"%(
        dep,u[2],u[1],u[0],r[2],r[1],r[0],rc[2],rc[0]))
print()
print("determinism, depth 12, 3 reps of each:")
for rep in range(3):
    print("  rep",rep,"U",one("go depth 12"),"| R(e2e4)",one("go depth 12 searchmoves e2e4"))
