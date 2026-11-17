#!/usr/bin/env python3
"""e4_fix.py : the HANDOFF's E4 row prints a move list whose 8th ply is illegal. Verify the
corrected list gives the stated occurrence count and the stated BAIL, so the table's CLAIM
survives even though its reproduction step does not."""
import chess, subprocess, re
BASE="/home/ubuntu/build/forge"
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
def search(fen,moves,depth=10):
    p=subprocess.Popen([BASE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,text=True,bufsize=1)
    def send(s): p.stdin.write(s+"\n"); p.stdin.flush()
    send("uci")
    while p.stdout.readline().strip()!="uciok": pass
    for o in ("setoption name Threads value 1","setoption name Hash value 16","setoption name OwnBook value false"):
        send(o); send("isready")
        while p.stdout.readline().strip()!="readyok": pass
    send("ucinewgame")
    send("position fen %s moves %s"%(fen,moves) if moves else "position fen %s"%fen)
    send("isready")
    while p.stdout.readline().strip()!="readyok": pass
    send("go depth %d"%depth)
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: break
        m=INFO.match(l.strip())
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if l.strip().startswith("bestmove"):
            bm=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last,bm

def occ(fen,moves):
    b=chess.Board(fen); root=(b.board_fen(),b.turn,b.castling_rights); n=1
    for mv in moves.split():
        b.push(chess.Move.from_uci(mv))
        if (b.board_fen(),b.turn,b.castling_rights)==root: n+=1
    return n

FEN="7k/8/8/8/8/8/6PP/7K b - - 0 1"
DOC = "h8g8 h1g1 g8h8 g1h1 h8g8 h1g1 g8h8 h1g1"      # as printed
FIX = "h8g8 h1g1 g8h8 g1h1 h8g8 h1g1 g8h8 g1h1"      # 8th ply corrected
print("A. legality")
for name,mv in (("as printed",DOC),("corrected",FIX)):
    b=chess.Board(FEN); ok=True
    for i,m in enumerate(mv.split(),1):
        try: b.push(chess.Move.from_uci(m))
        except Exception: ok=False; print("  %-11s illegal at ply %d (%s)"%(name,i,m)); break
    if ok: print("  %-11s all 8 plies legal, ends %s"%(name,b.fen()))
print()
print("B. occurrence count under the table's stated key (placement+side+castling)")
print("  as printed: %s (n/a - list unplayable)"%("-",))
print("  corrected : %d  (table states 3)"%occ(FEN,FIX))
print()
print("C. does the corrected list still BAIL? (table states 0 nodes, cp 0, h8g7)")
last,bm=search(FEN,FIX)
print("  measured: score %s %d, nodes %d, bestmove %s"%(last[0],last[1],last[2],bm))
print("  table stated: cp 0, 0 nodes, h8g7 ->",
      "AGREES" if (last[1]==0 and last[2]==0 and bm=="h8g7") else "DISAGREES")
