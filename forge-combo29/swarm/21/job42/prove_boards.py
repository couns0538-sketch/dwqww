import sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/21/job6')
from safe_engine import SafeEngine, bestmove_of, last_info
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),
("IirDepth","2"),("NonPawnCorrection","true")]
PC20=[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
# MY board (rook e1) and SEAT 20's board (rook d1), each with its own mating move named
CASES=[('6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60','e1e8','MY board, rook e1'),
       ('6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 100 60','d1d8','SEAT 20 board, rook d1')]
for fen,mv,label in CASES:
    for tag,exe,use in (('base','/home/ubuntu/b/release/forge',[]),('pc20','/home/ubuntu/b/pc/forge',S14+PC20)):
        e=SafeEngine(exe,'/tmp/p12_%s_%s.txt'%(tag,mv),hash_mb=16,threads=1)
        for k,v in use:
            e.send("setoption name %s value %s"%(k,v)); e.send("isready"); e.wait_for("readyok")
        if use: e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
        e.position('position fen '+fen)
        l=e.go('go searchmoves %s depth 4'%mv, timeout=60)
        info=last_info(l)
        print('%-9s %-26s %-6s %-6s %s' % (tag,label,mv,bestmove_of(l),info[-34:]))
        e.close()
