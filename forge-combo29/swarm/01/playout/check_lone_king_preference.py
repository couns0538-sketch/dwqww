#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 06's S-F39 — a lone-king misevaluation, tested by GROUND-TRUTH PLAYOUT.

Seat 06's claim, verbatim: an independent play-out (both sides played BY THE ENGINE at depth 12, python-chess
adjudicating, scores never consulted) gives c6d6 = 22 plies survived and c6c7 = 20 plies, all ending in
checkmate, deterministic. So the engine's preference for c6c7 is WRONG by ground truth, and the error is its
SCORE for c6d6 (it rates it mate -8 when the move actually holds out 22 plies).

WHY THIS IS THE STRONGEST FORM OF TEST IN THE SWARM: it does not read the engine's score at all. It plays the
game out with the engine making every move and python-chess deciding checkmate, so a wrong score cannot hide the
consequence. A score is a claim; a playout is ground truth.

Method: for each first move, force it, then let BOTH SIDES be played by the engine (node-capped per move so the
measurement cannot hang - see my Trap 6), with python-chess adjudicating. Count plies survived. Repeat 3 times
to check determinism, as seat 06 did.

Safety, because I must not repeat the depth-20 hazard on my own work: every move is a NODE budget, never an
untimed depth, and the ply count is capped.

Usage: check_lone_king_preference.py <exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=60.0
import os
NODES = int(os.environ.get("PLAYOUT_NODES", "20000"))
# Seat 06 played its playout at DEPTH 12 with both sides moving; my default is a node budget. That choice can
# change the result, so it is a parameter rather than an assumption.
GO_LINE = os.environ.get("PLAYOUT_GO", "go nodes %d")
MAXPLIES=80
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
FEN="1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
FIRST_MOVES=["c6d6","c6c7"]

class R:
    def __init__(self,fd): self.fd,self.buf,self.eof=fd,b"",False
    def line(self,dl):
        while b"\n" not in self.buf:
            if self.eof: return None
            rem=dl-time.monotonic()
            if rem<=0: return None
            r,_,_=select.select([self.fd],[],[],rem)
            if not r: return None
            c=os.read(self.fd,65536)
            if not c: self.eof=True; return None
            self.buf+=c
        l,_,self.buf=self.buf.partition(b"\n")
        return l.decode("utf-8","replace")

def engine_move(rd,send,until,fen):
    d=time.monotonic()+30
    send("position fen "+fen); send("isready"); until("readyok",d)
    send(GO_LINE % NODES)
    d=time.monotonic()+TIMEOUT
    while True:
        l=rd.line(d)
        if l is None: return None
        if l.startswith("bestmove"):
            return l.split()[1] if len(l.split())>1 else None

def playout(exe, first):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno())
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+30
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    b=chess.Board(FEN)
    mv=chess.Move.from_uci(first)
    if mv not in b.legal_moves:
        send("quit"); p.wait(timeout=10)
        return {"plies":0,"reason":"first move illegal"}
    b.push(mv); plies=1
    reason=""
    while plies<MAXPLIES:
        if b.is_checkmate(): reason="checkmate"; break
        if b.is_game_over(claim_draw=True): reason="draw claim"; break
        m=engine_move(rd,send,until,b.fen())
        if m is None: reason="no bestmove"; break
        if m=="0000": reason="0000"; break
        try: emv=chess.Move.from_uci(m)
        except ValueError: reason="unparsable %s"%m; break
        if emv not in b.legal_moves: reason="illegal %s"%m; break
        b.push(emv); plies+=1
    if not reason: reason="ply cap"
    if b.is_checkmate(): reason="checkmate"
    send("quit")
    try: p.wait(timeout=15)
    except Exception: p.kill()
    return {"plies":plies,"reason":reason}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 06's S-F39: lone-king move preference, tested by GROUND-TRUTH PLAYOUT",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+FEN,
           "both sides played by the ENGINE at go nodes %d (a node budget, never an untimed depth);"%NODES,
           "python-chess adjudicates; scores never consulted; 3 runs per first move",""]
    lines.append("first_move\trun\tplies_survived\treason")
    rows=[]
    for fm in FIRST_MOVES:
        runs=[playout(exe,fm) for _ in range(3)]
        for i,r in enumerate(runs):
            print("%-9s run %d -> %d plies (%s)"%(fm,i+1,r["plies"],r["reason"]),flush=True)
            lines.append("%s\t%d\t%d\t%s"%(fm,i+1,r["plies"],r["reason"]))
        rows.append({"first":fm,"runs":runs,"plies":[r["plies"] for r in runs],
                     "deterministic": len({r["plies"] for r in runs})==1})
    v=[]
    v.append("")
    for r in rows:
        v.append("%s: plies survived %s%s"%(r["first"],r["plies"],
                 " (identical across 3 runs)" if r["deterministic"] else " (NOT deterministic)"))
    a,b_=rows[0],rows[1]
    if a["deterministic"] and b_["deterministic"]:
        diff=b_["plies"][0]-a["plies"][0]
        v.append("")
        v.append("GROUND TRUTH: %s survives %d plies, %s survives %d - a difference of %d plies."
                 %(a["first"],a["plies"][0],b_["first"],b_["plies"][0],diff))
        # MORE plies survived = BETTER (it delays the mate). Seat 06 claims c6c7 is WORSE.
        second_worse = diff < 0
        if second_worse:
            v.append("VERDICT: CONFIRMS seat 06's direction - %s (the second move) survives %d FEWER plies, so"
                     % (b_["first"], abs(diff)))
            v.append("  it is worse by ground truth. A playout cannot consult a score, so this is the engine's own")
            v.append("  play revealing a preference that loses sooner.")
        elif diff > 0:
            v.append("VERDICT: REFUTES seat 06's direction AT THIS SETTING - %s (the second move) survives %d MORE"
                     % (b_["first"], diff))
            v.append("  plies, so by ground truth it is BETTER there, not worse. Its claim was made at DEPTH 12 and")
            v.append("  mine at go nodes %d; the budget changes what the engine plays deeper in the playout, so" % NODES)
            v.append("  this is a SETTING difference to be resolved, not necessarily a contradiction.")
        else:
            v.append("VERDICT: both moves survived the same number of plies here, so the claim's difference did not")
            v.append("  reproduce at this node budget. Not a refutation of the direction, an absence of signal.")
    else:
        v.append("")
        v.append("VERDICT: playouts were not deterministic here, so no comparison is drawn.")
    (out/"check_lone_king_preference.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_lone_king_preference.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
