#!/usr/bin/env python3
"""swarm seat 01: can a game ACTUALLY forfeit? Starting clocks below the fixed point.

My S-F76 saw a clock recover (673 -> 822 ms) because the hard limit falls below the increment at low clocks.
So the prediction is sharp and falsifiable:

  IF the fixed point is ~110 ms worst case / ~340-360 ms typical, THEN
    starting below it, the clock should RISE toward the fixed point, never empty;
    starting just above it, the clock should drift DOWN toward it and stop;
    a forfeit should be impossible from any starting clock, at this increment.

That is a testable claim, and testing it is the right way to close the forfeit question rather than arguing
about whose machine saw one. Four starting clocks, each played as far as the game goes on the clock, reporting
the clock trajectory and whether any clock reached 0.

The catch that makes this worth running: at a very low starting clock the engine may not have time to reach a
first completed iteration, so the "hard limit" branch and the emergency branch both matter. I record the depth
reached, which tells me which branch the engine was in.

Usage: check_low_clock_forfeit.py <pc-exe> <outdir> [max-plies]
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
INC=60
START_CLOCKS=[600, 300, 150, 100]

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
    send("go wtime %d btime %d winc %d binc %d"%(max(1,w),max(1,b),INC,INC))
    bm=None; depth=None; dl=[]
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    for l in reversed(dl):
        f=l.split()
        if "depth" in f: depth=int(f[f.index("depth")+1]); break
    return wall,bm,depth

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); cap=int(sys.argv[3]) if len(sys.argv)>3 else 120
    out.mkdir(parents=True,exist_ok=True)
    lines=["CAN A GAME FORFEIT? starting clocks below, at and above the predicted fixed point",
           "prediction (S-F76): below the fixed point the clock RISES; just above it drifts down and stops;",
           "a forfeit should be impossible from any starting clock at this 60 ms increment",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, winc=binc=60, cold (fresh process per move), startpos",""]
    results=[]
    for start in START_CLOCKS:
        board=chess.Board(); w=float(start); b=float(start); plies=0
        low=min(w,b); trajectory=[]; depths=[]
        forfeit=None
        while plies<cap and not board.is_game_over(claim_draw=True):
            if not list(board.legal_moves): break
            wall,bm,depth=ask(exe,board.fen(),w,b)
            plies+=1
            depths.append(depth)
            if board.turn: w=w-wall+INC; b+=INC
            else: b=b-wall+INC; w+=INC
            low=min(low,w,b)
            trajectory.append((plies,round(w,1),round(b,1)))
            if (w<=0 or b<=0) and forfeit is None: forfeit=plies
            if forfeit: break
            if bm and bm!="0000":
                mv=chess.Move.from_uci(bm)
                if mv in board.legal_moves: board.push(mv)
                else: break
            else: break
        results.append({"start":start,"plies":plies,"final_white":round(w,1),"final_black":round(b,1),
                        "lowest":round(low,1),"forfeit_ply":forfeit,
                        "median_depth":sorted([d for d in depths if d])[len(depths)//2] if any(depths) else None,
                        "first5":trajectory[:5],"last3":trajectory[-3:]})
        r=results[-1]
        print("start %-4d -> %d plies, final %.0f/%.0f, lowest %.0f, forfeit %s, med depth %s"
              %(start,plies,w,b,low,forfeit or "none",r["median_depth"]),flush=True)
        lines.append("start %d: %d plies, final w=%.0f b=%.0f, lowest=%.0f, forfeit=%s, median depth=%s"
                     %(start,plies,w,b,low,forfeit or "none",r["median_depth"]))
    v=[]
    v.append("")
    rose=[r for r in results if r["final_white"]>r["start"] and r["final_black"]>r["start"]]
    forfeits=[r for r in results if r["forfeit_ply"]]
    v.append("RESULTS: %d of %d starting clocks ended with BOTH clocks ABOVE their start; %d forfeits."
             %(len(rose),len(results),len(forfeits)))
    for r in results:
        v.append("  start %-4d: plies %-3d final w=%-6.0f b=%-6.0f lowest %-5.0f median depth %s"
                 %(r["start"],r["plies"],r["final_white"],r["final_black"],r["lowest"],r["median_depth"]))
    v.append("")
    if not forfeits and rose:
        v.append("VERDICT: the fixed point HOLDS as a live-game statement. Starting below it, the clock ROSE;")
        v.append("  no starting clock produced a forfeit. So a forfeit needs a run of hard-limit cuts at a")
        v.append("  clock that a normal game does not sustain, which is why its authors saw one on one machine")
        v.append("  and I do not here - position and machine specific, not a property of the control.")
    elif forfeits:
        v.append("VERDICT: a forfeit DID occur at start clocks %s, so the fixed point does not protect every"
                 %[r["start"] for r in forfeits])
        v.append("  starting clock; report the trajectory above, which is the useful part.")
    else:
        v.append("VERDICT: no clock rose, so the 'clock rises below the fixed point' prediction did not show")
        v.append("  here; report as is rather than claiming the fixed point is confirmed in play.")
    (out/"check_low_clock_forfeit.json").write_text(json.dumps({"results":results,"verdict":v},indent=1))
    (out/"check_low_clock_forfeit.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
