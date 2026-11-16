#!/usr/bin/env python3
"""Sign check on the ACTUAL reported board: score all four White moves separately and see whether
the engine's free choice is the move with the LARGEST |mate N| (i.e. the longest resistance)."""
import subprocess

FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
MOVES = ["c6c5", "c6c7", "c6d6", "c6d7"]

def run(exe, depth, sm=None, mode="PC20"):
    S14 = [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
           ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
           ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
           ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
    PC20 = S14 + [("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
                  ("MateAlphaGuard","true"),("OwnBook","false")]
    opts = PC20 if mode=="PC20" else S14
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    def w(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def r():
        l=p.stdout.readline()
        if l=="": raise RuntimeError("died")
        return l
    def rd():
        while True:
            if r().strip()=="readyok": return
    w("uci")
    while r().strip()!="uciok": pass
    for n,v in [("Threads","1"),("Hash","16")]+opts:
        w("setoption name %s value %s"%(n,v)); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen "+FEN); w("isready"); rd()
    w(("go depth %d searchmoves %s"%(depth,sm)) if sm else ("go depth %d"%depth))
    last=None; bm=None
    while True:
        l=r().strip()
        if " pv " in l and l.startswith("info"): last=l.split()
        if l.startswith("bestmove"): bm=l.split()[1]; break
    p.kill()
    if last is None: return None
    return {"kind":last[last.index("score")+1],"score":int(last[last.index("score")+2]),
            "seldepth":int(last[last.index("seldepth")+1]),
            "nodes":int(last[last.index("nodes")+1]),"bm":bm}

for depth in (18,20):
    print("=== depth %d ===" % depth)
    print("| what | score | seldepth | nodes | move |")
    print("|---|---|---|---|---|")
    f = run("/tmp/bld/pc/forge", depth)
    print("| FREE CHOICE | %s %d | %d | %d | %s |" % (f["kind"],f["score"],f["seldepth"],f["nodes"],f["bm"]))
    for mv in MOVES:
        d = run("/tmp/bld/pc/forge", depth, mv)
        print("| searchmoves %s | %s %d | %d | %d | %s |" % (mv,d["kind"],d["score"],d["seldepth"],d["nodes"],d["bm"]))
    print()
