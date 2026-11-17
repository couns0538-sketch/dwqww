#!/usr/bin/env python3
"""refused_fen_guard.py -- does a refused FEN still answer readyok, and what catches it?

Seat 01's S-F94: a refused `position fen` still answers readyok, so "send isready, wait for readyok"
is satisfied while the position was rejected. The check that survives is `board_matches`: compare
`go perft 1` against python-chess for the INTENDED board.

Check the three quantities separately, because they are different claims:
  1. does the engine print a warning on refusal? (if yes, reading setup output catches it)
  2. does it still answer readyok? (if yes, the handshake lies)
  3. does `go perft 1` reveal the wrong board? (the guard that survives a lying handshake)

Cases: a VALID position (control that the guard passes when it should), an INVALID one
(king left in check -- the one that caught me), and a legal-but-refused-style one.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
VALID="r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"
INVALID_KING_IN_CHECK="7k/6Q1/6K1/8/8/8/8/8 w - - 100 1"   # the FEN that caught me
BAD_FIELDS="not a fen at all"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=60):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def probe(exe,fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    send("uci")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+PC20:
        send("setoption name "+o); send("isready")
        while True:
            l=r.get(30)
            if l is None or l.strip()=="readyok": break
    send("ucinewgame"); send("isready")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="readyok": break
    # the case: send a position that may be refused, then isready
    send("position fen "+fen); send("isready")
    setup_lines=[]; readyok=False
    while True:
        l=r.get(30)
        if l is None: break
        setup_lines.append(l.rstrip())
        if l.strip()=="readyok": readyok=True; break
    warned=any("invalid FEN" in x or "info string" in x for x in setup_lines)
    # the guard: perft 1 on whatever board the engine now holds
    send("go perft 1")
    perft=None
    while True:
        l=r.get(60)
        if l is None: break
        m=re.match(r"^nodes (\d+)$",l.strip())
        if m: perft=int(m.group(1)); break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return {"fen":fen,"setup_lines":setup_lines,"warned":warned,"readyok":readyok,"perft1":perft}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    print(f"{'case':22s} {'warned':>7} {'readyok':>8} {'perft1':>7} {'expected':>9} match")
    for name,fen in [("VALID_control",VALID),
                     ("INVALID_king_in_check",INVALID_KING_IN_CHECK),
                     ("INVALID_bad_fields",BAD_FIELDS)]:
        r=probe(exe,fen)
        # expected perft1 for the INTENDED board; python-chess is the oracle
        try:
            expected=chess.Board(fen).legal_moves.count()
        except ValueError:
            expected="(fen invalid)"
        match = (r["perft1"]==expected)
        rows.append({**r,"case":name,"expected":expected,"match":match})
        print(f"{name:22s} {str(r['warned']):>7} {str(r['readyok']):>8} {str(r['perft1']):>7} "
              f"{str(expected):>9} {match}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"refused_fen_guard.json"),"w"),indent=1)
    print()
    inv=[r for r in rows if r["case"].startswith("INVALID")]
    val=[r for r in rows if r["case"]=="VALID_control"][0]
    print(f"VALID control: perft1 {'matches' if val['match'] else 'MISMATCHES'} python-chess "
          f"({val['perft1']} vs {val['expected']}) -> the guard passes when it should")
    for r in inv:
        print(f"{r['case']}: readyok answered = {r['readyok']} (a lying handshake if True); "
              f"perft1 {r['perft1']} vs intended {r['expected']} -> "
              f"guard {'CATCHES it' if not r['match'] else 'MISSES it'}")

if __name__=="__main__": main()
