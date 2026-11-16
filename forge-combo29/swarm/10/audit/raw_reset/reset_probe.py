import sys; sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
G='1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1'
d=Drv('/home/ubuntu/builds/release/forge'); d.uci(); d.isready()
d.pos('position fen '+G)
d.write('eval'); print("after position fen G :", d._read_until(lambda l: l.startswith('info string eval'))[-1])
d.write('ucinewgame'); d.write('isready'); print("ucinewgame ->", d._read_until(lambda l: l=='readyok')[-1])
d.write('eval'); print("eval after ucinewgame:", d._read_until(lambda l: l.startswith('info string eval'))[-1])
d.write('go perft 1'); tot,lines=d.perft(1); print("perft1 after ucinewgame:",tot,"(startpos=20, G position has 38)")
d.quit()
