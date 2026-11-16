#!/usr/bin/env python3
"""swarm seat 01: does the start-2 opening really forfeit on the clock, in my own harness?

Seat 27 reports the forfeit reproduces in BOTH process policies on start 2
`rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b` at 144-178 plies, which makes it a property of that
opening at this control rather than of warm-vs-cold policy.

That is a deterministic recipe for a failure, so it deserves independent confirmation: if it reproduces, a match
harness has a findable worst case; if it does not, the claim is machine-dependent and should be scoped.

Method: play a self-play game from that FEN on the clock, one fresh process per move (cold, the stricter
policy for this purpose since it cannot benefit from a warm table), decrementing a real clock by measured wall
time and adding the 60 ms increment. Record where each clock goes and report the ply of the first non-positive
clock, if any.

Usage: check_start2_forfeit.py <pc-exe> <outdir> [max-plies]
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
START="rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b - - 0 1"
CLOCK=6000; INC=60

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

def ask(exe,fen,w,b):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno())
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+60
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(w,b,INC,INC))
    bm=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    return wall,bm

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); cap=int(sys.argv[3]) if len(sys.argv)>3 else 400
    out.mkdir(parents=True,exist_ok=True)
    lines=["does start 2 forfeit on the clock? independent check of seat 27's claim",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "start: "+START,"PC20, Threads 1, Hash 16, 6 s + 0.06, COLD (fresh process per move)",""]
    board=chess.Board(START); w=CLOCK; b=CLOCK; plies=0; forfeit_ply=None
    lines.append("ply\tside\twall_ms\twhite_ms\tblack_ms\tmove")
    while plies<cap and not board.is_game_over(claim_draw=True):
        if not list(board.legal_moves): break
        wall,bm=ask(exe,board.fen(),w,b)
        plies+=1
        if board.turn:
            w = w - wall + INC; b += INC
            if w<=0 and forfeit_ply is None: forfeit_ply=plies
        else:
            b = b - wall + INC; w += INC
            if b<=0 and forfeit_ply is None: forfeit_ply=plies
        lines.append("%d\t%s\t%.1f\t%.0f\t%.0f\t%s"%(plies,"w" if board.turn else "b",wall,w,b,bm))
        if plies%20==0 or plies<6:
            print("ply %-3d %s wall %-7.1f w %-6.0f b %-6.0f %s"%(plies,"w" if board.turn else "b",wall,w,b,bm),flush=True)
        if forfeit_ply: break
        if bm and bm!="0000":
            mv=chess.Move.from_uci(bm)
            if mv in board.legal_moves: board.push(mv)
            else: break
        else: break
    v=[]
    v.append("")
    v.append("RESULT: %d plies; final clocks white %.0f ms, black %.0f ms."%(plies,w,b))
    if forfeit_ply:
        v.append("FORFEIT at ply %d (%s) - CONFIRMS seat 27's claim on this build and harness."
                 %(forfeit_ply,"white" if w<=0 else "black"))
    elif plies < 144:
        # the crucial distinction: a game that ENDED EARLY cannot test a claim about plies 144-178
        reason=("threefold repetition claim" if board.can_claim_threefold_repetition() else
                "fifty-move claim" if board.can_claim_fifty_moves() else
                "checkmate" if board.is_checkmate() else
                "stalemate" if board.is_stalemate() else
                "insufficient material" if board.is_insufficient_material() else "other")
        v.append("INCONCLUSIVE, NOT A REFUTATION. The game ended at ply %d by %s - BEFORE seat 27's")
        v.append("  144-178 forfeit window - so this run did not reach the plies the claim is about and tests")
        v.append("  nothing about it. To test it I would have to keep the game alive past 144 plies, which a")
        v.append("  threefold claim stops by rule. Stated as inconclusive rather than as a failed reproduction.")
    else:
        v.append("NO FORFEIT in a game that ran %d plies (>144), so the claim did not reproduce here; report"%plies)
        v.append("  as machine- or mixture-dependent rather than as a property of the opening alone.")
    (out/"check_start2_forfeit.json").write_text(json.dumps(
        {"start":START,"plies":plies,"final_white":w,"final_black":b,"forfeit_ply":forfeit_ply,
         "verdict":v},indent=1))
    (out/"check_start2_forfeit.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
