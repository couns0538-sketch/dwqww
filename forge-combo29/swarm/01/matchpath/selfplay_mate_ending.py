#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 25's S-F31 — the OTHER game ending, a forced mate, at the match setting.

Seat 25's claim, verbatim:
  "Both game endings are clean at the owner's match setting. A forced-mate self-play game (start
   `4k3/8/8/8/8/8/8/K1QR4 w`, PC r15/PC20/Threads 1/Hash 16, `go nodes 20000`, one fresh process per move) ends
   in CHECKMATE at ply 3 with 0 illegal moves, 0 missing info lines, 3/3 moves from a completed iteration,
   and 3 mate scores claimed of which 0 had a PV that fails to play out."

With my S-C16 (a 90-ply game ending by claim), that covers both endings. This replays the mate game with my own
harness and adds the check that matters for a PV claim: SLICE the engine's PV from its `info` line, play it out
with python-chess from the current board, and see whether it really ends in checkmate. A mate score with a PV
that does not mate is the kind of claim seat 05 chased all night.

Usage: selfplay_mate_ending.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
START="4k3/8/8/8/8/8/8/K1QR4 w - - 0 1"
N=20000

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

def ask(exe,fen,go):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno()); buf=[]
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            buf.append(l)
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+TIMEOUT
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    send(go)
    bml=until("bestmove",d)
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    score=""; pv=[]
    for l in reversed(dl):
        f=l.split()
        if " score " in l:
            i=f.index("score"); score=" ".join(f[i+1:i+3])
        if "pv" in f:
            pv=f[f.index("pv")+1:]
        if score: break
    return {"score":score,"pv":pv,"bestmove":bml.split()[1] if bml and len(bml.split())>1 else None,
            "n_info":len(dl)}

def play_out(board, pv):
    """Play the PV from `board` with python-chess. Returns (ended_in_checkmate, plies_played, reason)."""
    b=board.copy()
    for i,u in enumerate(pv):
        try: mv=chess.Move.from_uci(u)
        except ValueError: return False,i,"unparsable move %s"%u
        if mv not in b.legal_moves: return False,i,"illegal move %s at pv index %d"%(u,i)
        b.push(mv)
        if b.is_checkmate(): return True,i+1,"checkmate at pv ply %d"%(i+1)
    return False,len(pv),"pv ended without mate (is_checkmate=%s)"%b.is_checkmate()

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 25's S-F31: the forced-mate game ending at the match setting",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC r15 + PC20, Threads 1, Hash 16, OwnBook false, `go nodes %d`, one fresh process per move"%N,
           "start: "+START,"python-chess is the referee; PVs are SLICED from the info line and played out",""]
    lines.append("ply\tscore\tbestmove\tpv_len\tpv_mates?\tpv_note")
    board=chess.Board(START)
    mate_claims=0; bad_pv=0; illegal=0; plies=0; end=""
    while plies<20:
        if board.is_game_over(claim_draw=True):
            end=("checkmate" if board.is_checkmate() else "stalemate" if board.is_stalemate() else "other")
            break
        r=ask(exe,board.fen(),"go nodes %d"%N)
        plies+=1
        is_mate="mate" in r["score"]
        if is_mate: mate_claims+=1
        mates,played,note = play_out(board,r["pv"]) if r["pv"] else (False,0,"empty pv")
        if is_mate and not mates: bad_pv+=1
        mv=None
        try:
            mv=chess.Move.from_uci(r["bestmove"] or "")
        except ValueError:
            mv=None
        legal = mv is not None and mv in board.legal_moves
        if not legal: illegal+=1
        lines.append("%d\t%s\t%s\t%d\t%s\t%s"%(plies,r["score"],r["bestmove"],len(r["pv"]),
                     "yes" if mates else "no",note))
        print("ply %-2d %-8s %-6s pv %-2d pv_mates=%-5s %s"%(plies,r["score"],r["bestmove"],
              len(r["pv"]),"yes" if mates else "no",note),flush=True)
        if not legal: break
        board.push(mv)
    if not end:
        end="checkmate" if board.is_checkmate() else ("still going after %d plies"%plies)
    v=[]
    v.append("")
    v.append("RESULT: game ended by %s at ply %d; illegal moves %d; mate scores claimed %d of which %d had a"
             %(end,plies,illegal,mate_claims,bad_pv))
    v.append("  PV that does NOT play out to checkmate.")
    v.append("")
    if illegal==0 and bad_pv==0 and mate_claims>0:
        v.append("VERDICT: CONFIRMS seat 25's S-F31. The forced-mate ending is clean, and every mate score")
        v.append("  came with a PV that really plays out to checkmate when sliced and replayed.")
    elif illegal==0 and bad_pv==0:
        v.append("VERDICT: clean, but NO mate score was claimed in this game, so the PV-mates half of S-F31")
        v.append("  is untested here; reported as is.")
    else:
        v.append("VERDICT: does NOT reproduce - see the counters.")
    (out/"selfplay_mate_ending.json").write_text(json.dumps(
        {"plies":plies,"ended":end,"illegal":illegal,"mate_claims":mate_claims,"bad_pv":bad_pv,
         "verdict":v},indent=1))
    (out/"selfplay_mate_ending.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
