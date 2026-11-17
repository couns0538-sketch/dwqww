#!/usr/bin/env python3
"""hang_check.py : was the piece already lost BEFORE the bail's move?
Scores each candidate alone at fixed depth on the PC build, and separately reports
whether the piece was already attacked at the root (a static python-chess question)."""
import re, subprocess, sys
import chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())

def score(fen,moves,depth=16):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm)
        p.stdin.write(line+"\n");p.stdin.flush();p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    cmd="go depth %d"%depth
    if moves: cmd+=" searchmoves "+" ".join(moves)
    p.stdin.write(cmd+"\n");p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last

BOARDS=[("B1 (23-F60/F61)",  "rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16","e6e5","b6b4",chess.B6),
        ("B2 (23-F60 second)","5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35","c6c5","e4b1",chess.E4)]
print("depth 16, each candidate scored ALONE on the PC build; root material (black - white)")
for name,fen,base_mv,pc_mv,sq in BOARDS:
    b=chess.Board(fen)
    pc=b.piece_at(sq)
    atk=b.is_attacked_by(chess.WHITE,sq)
    print("\n%s  %s to move; piece on %s = %s"%(name,"black" if b.turn==chess.BLACK else "white",
          chess.square_name(sq), pc.symbol() if pc else "none"))
    print("  ROOT material %+d | piece already attacked at root? %s (white attackers %s)"
          %(mat(b),atk,[chess.square_name(s) for s in b.attackers(chess.WHITE,sq)]))
    for label,mv in (("base bail move",base_mv),("PC move",pc_mv)):
        sc=score(fen,[mv])
        c=b.copy(); c.push_uci(mv)
        print("  %-14s %-6s score=%s"%(label,mv,sc))
