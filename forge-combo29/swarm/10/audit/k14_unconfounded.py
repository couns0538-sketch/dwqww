import sys; sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
def one(cmd):
    d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
    d.opt("OwnBook","false"); d.opt("Threads","1"); d.opt("Hash","16"); d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    n,b,l=d.go(cmd); d.quit()
    sc=None
    for x in reversed(l):
        if " score cp " in x: sc=int(x.split(" score cp ")[1].split()[0]); break
    return n,b,sc
print("depth | U move+score | single-move restrict to U's OWN move | confounded?")
for dep in (8,10,12,14,16):
    u=one("go depth %d"%dep)
    r=one("go depth %d searchmoves %s"%(dep,u[1]))
    print("%5d | %-6s cp %-3s | restrict %s -> cp %-3s nodes %-7s | %s"%(
        dep,u[1],u[2],u[1],r[2],r[0],"NO (same move)" if True else ""))
