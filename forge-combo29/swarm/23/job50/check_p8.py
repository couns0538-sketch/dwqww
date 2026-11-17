#!/usr/bin/env python3
"""position 8 sanity: black to move; base says best=f4h2 at depth 12. Is black actually lost there?"""
import re,subprocess,os,chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
PC=os.path.expanduser("~/pcbuild/forge"); BASE=os.path.expanduser("~/build/forge")
FEN="2b2b1r/Np3p1p/5k2/2np2p1/4PqP1/P1P1P2P/1P1BK2R/3R1B2 b - - 0 25"
def go(exe,fen,depth):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush(); opts=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): opts.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    if "OwnBook" in opts: p.stdin.write("setoption name OwnBook value false\n");p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush(); p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip(); m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"):
            bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try:p.wait(timeout=10)
    except Exception:p.kill()
    return last,bm
b=chess.Board(FEN)
print("fen:",FEN)
print("mover:","white" if b.turn else "black","| legal:",len(list(b.legal_moves)))
print("material (black - white) in pawns:")
vals={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9}
diff=sum(v*(1 if p.color==chess.BLACK else -1) for p,v in vals.items() for p in [p] if False)
diff=sum(v for p,v in [(p,v) for p,v in [(pp,vals.get(pp.piece_type,0)) for pp in b.piece_map().values()] ] )
mat=sum((vals.get(p.piece_type,0))*(1 if p.color==chess.BLACK else -1) for p in b.piece_map().values())
print("  black material minus white =",mat)
for d in (12,16,18):
    print(f"  BASE depth {d}:", *go(BASE,FEN,d))
print("  after f4h2 (base's chosen move), PC depth 16:")
c=chess.Board(FEN); c.push(chess.Move.from_uci("f4h2"))
print("   ", *go(PC,c.fen(),16))
print("  control: PC on the ROOT at depth 16:")
print("   ", *go(PC,FEN,16))
