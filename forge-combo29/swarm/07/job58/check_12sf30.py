#!/usr/bin/env python3
"""check_12sf30.py -- does kiwipete discriminate where startpos cannot?

Seat 12's S-F30: the two plausible "first legal move" orders (engine generation order vs alphabetical)
AGREE on startpos (both a2a3) and DIFFER on kiwipete (engine a2a3 vs alphabetical a1b1). So a check
that only uses startpos cannot tell a real bestmove from a fabricated first-in-alphabetical-order move,
and adding kiwipete makes it discriminating.

Check with python-chess, no engine needed for the core claim:
  1. startpos: is the engine's first-generated legal move the same as the alphabetically-first legal move?
  2. kiwipete: same question.
  3. and confirm with the engine what its FIRST legal move actually is on each (via `go searchmoves`
     on a fresh process is not needed: `position` + `go depth 1` gives its pick, but generation order is
     what matters -- so read it from legal_moves() ordering AND from the engine's own a2a3-style answer
     with a node budget too small to search).

The point is harness design: which positions let you distinguish a fabricated move from a real one.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

START="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
KIWI="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=300):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def tiny_search(exe,fen):
    """1-node search: the engine's answer must be its own first move (07-F1's path)."""
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def drain():
        while True:
            l=r.get()
            if l is None: raise RuntimeError("no readyok")
            if l.strip()=="readyok": return
    send("uci")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send("go nodes 1")
    best=None
    while True:
        l=r.get(300)
        if l is None: break
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return best

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    for name,fen in [("startpos",START),("kiwipete",KIWI)]:
        b=chess.Board(fen)
        legal=[m.uci() for m in b.legal_moves]
        alpha=sorted(legal)
        eng=tiny_search(exe,fen)
        # The claim compares the ENGINE's answer with the ALPHABETICAL first move, because a
        # fabricated move in seat 12's planted probe is the alphabetical first. My first version
        # compared python-chess's generation order with alphabetical, which is a different question
        # and reported "does not reproduce" while the raw numbers actually confirmed the claim.
        rows.append({"pos":name,"n_legal":len(legal),
                     "pythonchess_first":legal[0],
                     "first_alphabetical":alpha[0],
                     "engine_1node":eng,
                     "engine_equals_alphabetical_first": eng==alpha[0]})
        print(f"{name}: {len(legal)} legal moves")
        print(f"   first alphabetically             : {alpha[0]}")
        print(f"   engine, go nodes 1               : {eng}")
        print(f"   a fabricated alphabetical move is : "
              f"{'INDISTINGUISHABLE' if eng==alpha[0] else 'distinguishable'} here")
    json.dump(rows,open(os.path.join(outdir,"check_12sf30.json"),"w"),indent=1)
    print()
    s=[r for r in rows if r["pos"]=="startpos"][0]
    k=[r for r in rows if r["pos"]=="kiwipete"][0]
    print(f"startpos: engine == alphabetical first? {s['engine_equals_alphabetical_first']}")
    print(f"kiwipete: engine == alphabetical first? {k['engine_equals_alphabetical_first']}")
    if s['engine_equals_alphabetical_first'] and not k['engine_equals_alphabetical_first']:
        print("=> seat 12's S-F30 CONFIRMED: a fabricated alphabetical move is invisible on startpos")
        print("   and visible on kiwipete, so kiwipete makes the check discriminating.")
    else:
        print("=> does NOT reproduce as stated.")

if __name__=="__main__": main()
