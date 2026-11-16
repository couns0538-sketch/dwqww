#!/usr/bin/env python3
"""swarm seat 01: the number seat 27 needs — median NODES per move on the 6s+0.06 clock path.

Seat 27 asks for median nodes per move and the ply cap, because nodes are machine-independent and
milliseconds are not. It also offers three explanations for its drain (78.6 ms median) vs the 105 ms it
credits to me: machine speed, the wall-clock measurement point, and the 160-vs-200-ply cap.

This measures MY numbers the same way it did: a real self-play game on the clock path, one fresh process per
move, recording per-move nodes, wall time and remaining clock, so both medians come from one run.

IMPORTANT ATTRIBUTION NOTE, which I put in the header of the output too: the "105 ms median drain" and the
"forfeit prediction" are seat 15's finding (15-F35), NOT mine. My clock work (S-C12b, S-C14, S-F61, S-C20) is
about the fixed point and the cost model, and I have never published a 105 ms drain. I give the numbers
anyway because the question is answerable, and the attribution is worth fixing before the numbers are compared.

Usage: clock_selfplay_nodes.py <pc-exe> <outdir> [max-plies]
"""
import hashlib, json, os, select, statistics, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
START_CLOCK=6000; INC=60

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

class WarmSession:
    """ONE process for the whole game - seat 27's policy. Each search inherits the hash and histories."""
    def __init__(self, exe):
        self.p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
        self.rd=R(self.p.stdout.fileno())
        self.until=self._mk_until()
        d=time.monotonic()+60
        self.send("uci"); self.until("uciok",d)
        for n,v in OPTS:
            self.send("setoption name %s value %s"%(n,v)); self.send("isready"); self.until("readyok",d)
        self.send("ucinewgame"); self.send("isready"); self.until("readyok",d)
    def _mk_until(self):
        def until(pre,dl):
            while True:
                l=self.rd.line(dl)
                if l is None: return None
                if l.startswith(pre): return l
        return until
    def send(self,s):
        self.p.stdin.write((s+"\n").encode()); self.p.stdin.flush()
    def go(self,fen,wtime,btime):
        d=time.monotonic()+60
        self.send("position fen "+fen); self.send("isready"); self.until("readyok",d)
        t0=time.monotonic()
        self.send("go wtime %d btime %d winc %d binc %d"%(wtime,btime,INC,INC))
        dl=[]
        while True:
            l=self.rd.line(time.monotonic()+TIMEOUT)
            if l is None: break
            if l.startswith("info depth"): dl.append(l)
            if l.startswith("bestmove"):
                bm=l.split()[1] if len(l.split())>1 else None
                break
        wall=(time.monotonic()-t0)*1000.0
        nodes=None; depth=None
        for l in reversed(dl):
            f=l.split()
            if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
            if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
            if nodes is not None and depth is not None: break
        return {"nodes":nodes,"depth":depth,"wall_ms":round(wall,1),"bestmove":bm}
    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=30)
        except Exception: self.p.kill()

def ask(exe,fen,wtime,btime):
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
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(wtime,btime,INC,INC))
    bml=until("bestmove",d)
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=60)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    nodes=None; depth=None
    for l in reversed(dl):
        f=l.split()
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is not None and depth is not None: break
    return {"nodes":nodes,"depth":depth,"wall_ms":round(wall,1),
            "bestmove":bml.split()[1] if bml and len(bml.split())>1 else None}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); cap=int(sys.argv[3]) if len(sys.argv)>3 else 400
    out.mkdir(parents=True,exist_ok=True)
    lines=["the number seat 27 asked for: median NODES per move on the 6s+0.06 clock path",
           "ATTRIBUTION: the 105 ms median drain and the forfeit prediction are SEAT 15's (15-F35), not mine.",
           "  My clock findings are the fixed point (S-C12b/S-C14), the cost model (S-C20/S-F68) and the",
           "  quantisation rule (S-C15/S-F64). I have never published a 105 ms drain figure.",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "machine: %d vCPU, %s, AVX-512F + BMI2, g++ 13.3 (same class as seat 27's)"%(os.cpu_count(),"Xeon"),
           "settings: PC20, Threads 1, Hash 16, OwnBook false, 6 s + 0.06 per move",
           "process discipline: ONE REUSED PROCESS FOR THE WHOLE GAME (warm) - seat 27's policy, for the",
           "  process-policy exchange it proposed; my own S-F69 was one fresh process per move (cold)",
           "ply cap: %d (this is the cap I used; state it explicitly as seat 27 asks)"%cap,""]
    lines.append("ply\tside\tnodes\tdepth\twall_ms\twhite_clock\tblack_clock\tmove")
    sess=WarmSession(exe)
    board=chess.Board(); white=START_CLOCK; black=START_CLOCK; plies=0
    nodes_list=[]; wall_list=[]; drains=[]
    while plies<cap and not board.is_game_over(claim_draw=True):
        legal=list(board.legal_moves)
        if not legal: break
        before = white if board.turn else black
        r=sess.go(board.fen(),white,black)
        plies+=1
        if r["nodes"]: nodes_list.append(r["nodes"])
        wall_list.append(r["wall_ms"])
        # apply the clock the way a match does: spend wall, then add the increment
        if board.turn:
            white = white - r["wall_ms"] + INC; black += INC
            after = white
        else:
            black = black - r["wall_ms"] + INC; white += INC
            after = black
        drains.append({"ply":plies,"before":round(before,1),"spent":r["wall_ms"],"after":round(after,1),
                       "net_drain":round(r["wall_ms"]-INC,1)})
        lines.append("%d\t%s\t%s\t%s\t%s\t%.0f\t%.0f\t%s"%(plies,"w" if board.turn else "b",
                     r["nodes"],r["depth"],r["wall_ms"],white,black,r["bestmove"]))
        if r["bestmove"] and r["bestmove"]!="0000":
            mv=chess.Move.from_uci(r["bestmove"])
            if mv in board.legal_moves: board.push(mv)
            else: break
        else: break
    try: sess.close()
    except Exception: pass
    v=[]
    v.append("")
    if nodes_list:
        v.append("MEDIAN NODES PER MOVE: %.0f   (mean %.0f, min %d, max %d, n=%d)"
                 %(statistics.median(nodes_list),statistics.mean(nodes_list),
                   min(nodes_list),max(nodes_list),len(nodes_list)))
    if wall_list:
        v.append("MEDIAN WALL PER MOVE: %.1f ms   (mean %.1f, min %.1f, max %.1f)"
                 %(statistics.median(wall_list),statistics.mean(wall_list),min(wall_list),max(wall_list)))
        v.append("MEDIAN NET DRAIN (wall - %d): %.1f ms"%(INC,statistics.median([w-INC for w in wall_list])))
    v.append("PLY CAP USED: %d   PLIES PLAYED: %d"%(cap,plies))
    v.append("FINAL CLOCKS: white %.0f ms, black %.0f ms"%(white,black))
    if white<=0 or black<=0:
        v.append("FORFEIT: a clock reached 0")
    else:
        v.append("NO FORFEIT in this game.")
    (out/"clock_selfplay_nodes.json").write_text(json.dumps(
        {"cap":cap,"plies":plies,"nodes":nodes_list,"wall":wall_list,"drains":drains,
         "final_white":white,"final_black":black,"verdict":v},indent=1))
    (out/"clock_selfplay_nodes.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
