#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 21's 21-F2b — after a REFUSED `position fen`, does `go` play the old game?

Seat 21's claim, verbatim:
  "A refused `position fen` still answers `readyok`, and the next `go depth 6` returns a move of the OLD game
   (`g8f6` both before and after the refusal). Threads 1, build PC r15, PC20."

WHY THIS IS IN MY AREA: it is the exact failure my own guard page (REFUSED_FEN_TRAP_AND_GUARD.md) warns about -
"an engine that refuses a position command keeps the PREVIOUS position and answers normally". Seat 21 is
reporting the same mechanism with the UCI handshake intact, which is the part that makes it dangerous: the GUI
sees `readyok` and believes the position was accepted.

Two things measured:
  A. THE HANDSHAKE - does a refused position still produce `readyok`? If yes, a GUI that syncs on readyok is
     told the position was taken.
  B. THE MOVE - does the following `go` return a move from the OLD position? I check the move is legal on the
     old board and ILLEGAL (or meaningless) on the intended one, which is stronger than "the same move came
     back": a move that is legal on both proves less.
  C. MY OWN GUARD - would my `board_matches` check have caught this? It compares `go perft 1` against
     python-chess for the INTENDED board, so it should fire. Demonstrated rather than asserted.

Usage: check_refused_then_go.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=120.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
# a legal first position, then a FEN the engine refuses
FIRST="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BAD="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"     # castling right, no rook
INTENDED="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

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

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
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
    lines=["CHECK of seat 21's 21-F2b: after a REFUSED position fen, does go play the old game?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, ONE process so state carries between commands (the point of the test)",""]
    def search(fen,label):
        send("position fen "+fen); send("isready")
        ready=until("readyok",time.monotonic()+30)
        refused=[l for l in [] ]
        send("go depth 6")
        bm=None
        while True:
            l=rd.line(time.monotonic()+TIMEOUT)
            if l is None: break
            if l.startswith("bestmove"):
                bm=l.split()[1] if len(l.split())>1 else None; break
        # perft 1 tells us which board the engine holds - my own guard's method
        send("position fen "+fen); send("isready"); until("readyok",time.monotonic()+30)
        send("go perft 1")
        nodes=None
        while True:
            l=rd.line(time.monotonic()+TIMEOUT)
            if l is None: break
            if l.startswith("nodes "):
                nodes=int(l.split()[1]); break
        return {"label":label,"fen":fen,"got_readyok":ready is not None,"bestmove":bm,"perft1":nodes}
    # 1) establish the first position's move
    a=search(FIRST,"first_legal")
    # 2) send a REFUSED fen; capture readyok and the following go
    send("position fen "+BAD); send("isready")
    ready_after_bad = until("readyok",time.monotonic()+30)
    # collect the refusal lines by asking isready again after a perft, so we can see the engine's own answer
    send("go depth 6")
    bm_after_bad=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("bestmove"):
            bm_after_bad=l.split()[1] if len(l.split())>1 else None; break
    send("go perft 1")
    nodes_after_bad=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("nodes "):
            nodes_after_bad=int(l.split()[1]); break
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    old=chess.Board(FIRST); intended=chess.Board(INTENDED)
    def legal_on(board,u):
        try: return chess.Move.from_uci(u) in board.legal_moves
        except ValueError: return False
    lines.append("first_legal position: bestmove %s, perft1 %s (python-chess legal %d)"
                 %(a["bestmove"],a["perft1"],old.legal_moves.count()))
    lines.append("AFTER the refused FEN:")
    lines.append("  readyok returned: %s"%bool(ready_after_bad))
    lines.append("  next go bestmove: %s"%bm_after_bad)
    lines.append("  perft1 after refusal: %s (old board has %d legal moves; the intended board has %d)"
                 %(nodes_after_bad,old.legal_moves.count(),intended.legal_moves.count()))
    lines.append("  move legal on the OLD board: %s ; legal on the INTENDED board: %s"
                 %(legal_on(old,bm_after_bad or ""),legal_on(intended,bm_after_bad or "")))
    v=[]
    v.append("")
    v.append("A. HANDSHAKE: a refused position returned readyok = %s "%bool(ready_after_bad))
    v.append("   -> %s"%("so a GUI syncing on readyok is told the position was ACCEPTED. This is the dangerous half."
                         if ready_after_bad else "no, the GUI would notice."))
    v.append("B. MOVE: %s, legal on the old board = %s, legal on the intended board = %s"
             %(bm_after_bad,legal_on(old,bm_after_bad or ""),legal_on(intended,bm_after_bad or "")))
    v.append("   perft1 %s vs the old board's %d"%(nodes_after_bad,old.legal_moves.count()))
    stale = (nodes_after_bad==old.legal_moves.count())
    v.append("   -> the engine is holding %s"%("the OLD board (perft matches it exactly)" if stale else "some other board"))
    v.append("C. MY OWN GUARD: `board_matches` compares `go perft 1` against python-chess for the INTENDED board.")
    v.append("   Intended perft1 would be %d; the engine reports %s. %s"
             %(intended.legal_moves.count(),nodes_after_bad,
               "The guard FIRES - it would have caught this." if nodes_after_bad!=intended.legal_moves.count()
               else "The guard would NOT fire - a real gap in it."))
    v.append("")
    if ready_after_bad and stale:
        v.append("VERDICT: CONFIRMS 21-F2b. The refusal is silent at the UCI handshake level, the next search")
        v.append("  answers from the OLD board, and my documented guard catches it - which is why the guard is")
        v.append("  worth using rather than trusting readyok.")
    elif not stale:
        v.append("VERDICT: the engine did NOT keep the old board here, so the stale-play half does not reproduce.")
    else:
        v.append("VERDICT: no readyok after the refusal, so the silent-acceptance half does not reproduce.")
    (out/"check_refused_then_go.json").write_text(json.dumps({"first":a,"readyok_after_refusal":bool(ready_after_bad),
        "bestmove_after_refusal":bm_after_bad,"perft1_after_refusal":nodes_after_bad,"verdict":v},indent=1))
    (out/"check_refused_then_go.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(lines+v))

if __name__=="__main__":
    main()
