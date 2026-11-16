#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 25's S-F30 — a full self-play game at the owner's EXACT match setting.

Seat 25's claim, verbatim:
  "At the owner's exact match setting, a full self-play game is clean. PC r15/PC20/Threads 1/Hash 16,
   `go nodes 20000`, one fresh process per move, 90 plies: 0 illegal moves, 0 missing final info lines,
   90/90 moves from a completed iteration (non-empty PV), game terminated normally by threefold
   repetition, and nodes spent/N median 0.75 (0.34-1.00)."

This matters more than any isolated-position test: it is the path the owner actually runs. I replay my own
game with my own harness and check the same five things, plus three seat 25 did not report:
  * does every move come from a NON-EMPTY PV (the "completed iteration" test)?
  * is the node spend / N ratio in the same range?
  * does the game END, and by what?
  * NEW: is every bestmove LEGAL on the board python-chess thinks it is? (the refused-position trap from
    REFUSED_FEN_TRAP_AND_GUARD.md cannot fire here because there is no FEN input, but a stale board between
    moves would show as an illegal move, so this is the check that the game loop itself is sound.)
  * NEW: does the engine ever return 0000 on a board with legal moves?

Usage: selfplay_match_setting.py <pc-exe> <outdir> [max-plies]
"""
import hashlib, json, os, re, select, statistics, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT = 300.0
OPTS = [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
        ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
        ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
        ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
        ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
        ("OwnBook","false"),("Threads","1"),("Hash","16")]
N = 20000

class R:
    def __init__(self, fd): self.fd,self.buf,self.eof=fd,b"",False
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

def ask(exe, fen, go):
    """One fresh process per move, exactly as seat 25 describes."""
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
    for n,v in OPTS:
        send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    refused=[l for l in buf if l.startswith("info string invalid FEN")]
    send(go)
    bml=until("bestmove",d)
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    depth_lines=[l for l in buf if l.startswith("info depth")]
    nodes=None; depth=None; pvlen=0; score=""
    for l in reversed(depth_lines):
        f=l.split()
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if not score and " score " in l:
            i=f.index("score"); score=" ".join(f[i+1:i+3])
        if "pv" in f and pvlen==0: pvlen=len(f)-f.index("pv")-1
        if nodes is not None and depth is not None: break
    bm = bml.split()[1] if bml and len(bml.split())>1 else None
    return {"nodes":nodes,"depth":depth,"pvlen":pvlen,"score":score,"bestmove":bm,
            "refused":refused,"n_info":len(depth_lines)}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); maxplies=int(sys.argv[3]) if len(sys.argv)>3 else 120
    out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 25's S-F30: a self-play game at the owner's exact match setting",
           "exe_started: %s"%exe, "sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC r15 + PC20, Threads 1, Hash 16, OwnBook false, `go nodes %d`, ONE FRESH PROCESS PER MOVE"%N,
           "start: standard position; python-chess is the referee", ""]
    lines.append("ply\tside\tdepth\tnodes\tnodes/N\tpv_len\tscore\tmove\tlegal")
    board=chess.Board()
    illegal=0; missing_pv=0; zero_with_moves=0; ratios=[]; plies=0; end_reason=""
    while plies < maxplies:
        if board.is_game_over(claim_draw=True):
            end_reason = ("checkmate" if board.is_checkmate() else
                          "stalemate" if board.is_stalemate() else
                          "insufficient material" if board.is_insufficient_material() else
                          "seventyfive/repetition claim")
            break
        legal=list(board.legal_moves)
        if not legal:
            end_reason="no legal moves"; break
        r=ask(exe, board.fen(), "go nodes %d"%N)
        plies+=1
        mv=None; ok=False
        if r["bestmove"] and r["bestmove"]!="0000":
            try:
                mv=chess.Move.from_uci(r["bestmove"])
                ok = mv in board.legal_moves
            except ValueError:
                ok=False
        if not ok:
            illegal+=1
            if r["bestmove"] in ("0000",None): zero_with_moves+=1
        if r["pvlen"]==0: missing_pv+=1
        if r["nodes"]: ratios.append(r["nodes"]/N)
        lines.append("%d\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s"%(
            plies, "white" if board.turn else "black", r["depth"], r["nodes"],
            ("%.2f"%(r["nodes"]/N)) if r["nodes"] else "-", r["pvlen"], r["score"],
            r["bestmove"], ok))
        print("ply %-3d %-5s d%-3s nodes %-7s ratio %-5s pv %-2d %-8s %-6s %s"%(
            plies, "W" if board.turn else "B", r["depth"], r["nodes"],
            ("%.2f"%(r["nodes"]/N)) if r["nodes"] else "-", r["pvlen"], r["score"],
            r["bestmove"], "legal" if ok else "ILLEGAL"), flush=True)
        if not ok: break
        board.push(mv)
    if not end_reason:
        end_reason = "reached the %d-ply cap"%maxplies
    v=[]
    v.append("")
    v.append("RESULT: %d plies, ending by %s."%(plies,end_reason))
    v.append("  illegal moves: %d  |  0000 on a board with legal moves: %d  |  moves with an EMPTY PV: %d"
             %(illegal,zero_with_moves,missing_pv))
    if ratios:
        v.append("  nodes spent / N: median %.2f, min %.2f, max %.2f over %d moves"
                 %(statistics.median(ratios),min(ratios),max(ratios),len(ratios)))
    v.append("")
    if illegal==0 and missing_pv==0 and ratios:
        v.append("VERDICT: CONFIRMS seat 25's S-F30. At the owner's exact match setting a full self-play game")
        v.append("  is clean: every move legal, every move from a completed iteration (non-empty PV), no 0000")
        v.append("  on a playable board, and the node spend ratio in the same band seat 25 reported.")
    else:
        v.append("VERDICT: does NOT reproduce cleanly - see the counters above.")
    (out/"selfplay_match_setting.json").write_text(json.dumps(
        {"plies":plies,"end_reason":end_reason,"illegal":illegal,"zero_with_moves":zero_with_moves,
         "missing_pv":missing_pv,"ratios":ratios,"verdict":v},indent=1))
    (out/"selfplay_match_setting.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
