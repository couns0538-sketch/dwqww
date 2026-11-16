import sys,os
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/audit')
from drv import Drv
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
d=Drv(os.path.expanduser("~/builds/release/forge")); d.uci(); d.isready()
d.opt("Threads","1"); d.opt("Hash","16")
for k,v in S14: d.opt(k,v)
d.isready(); d.write("ucinewgame"); d.isready()
d.pos("position startpos")
n,b,l=d.go("go depth 12")
sc=[x for x in reversed(l) if " score cp " in x]
print("CLEAN finished depth12: nodes",n,"best",b,"score",sc[0].split("score")[1].split("pv")[0].strip() if sc else None)
d.quit()
