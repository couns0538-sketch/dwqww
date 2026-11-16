#!/usr/bin/env python3
"""refused_readyok.py : 21-F2b — a REFUSED `position fen` still answers readyok, and the next search returns a move
of the OLD game, on the base AND the PC build.

Protocol (19-F12-safe: every command drained):
 1. `position fen A` ; isready ; `go depth 6`  -> move_A
 2. `position fen B_REFUSED` (a board with an impossible castling right) ; isready
      -> does an `invalid FEN` line appear? does `readyok` still arrive?
 3. `go depth 6` -> move_C.  If refused, the engine still holds A -> move_C == move_A.
 4. CONTROL, and it must be able to fail: the SAME board in a form the engine ACCEPTS must give a DIFFERENT move
    from move_A. Without that, "move_C == move_A" could just mean both boards happen to share a best move.

Board A is the Ruy Lopez position (best move f1c4 at depth 6). Board B is the start position with a queen added at
b1-style square so its best move differs clearly, and a castling right that no king/rook justifies.
"""
import re, subprocess
import chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")

def session(exe, cmds, opts):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in opts:
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    out=[]
    for c in cmds:
        p.stdin.write(c+"\n");p.stdin.flush()
        if c.startswith("go"):
            bm=None
            while True:
                l=p.stdout.readline()
                if not l: break
                if l.strip().startswith("bestmove"): bm=l.split()[1]; break
            out.append(bm)
        elif c=="isready":
            seen=[]
            while True:
                l=p.stdout.readline()
                if not l: break
                s=l.strip()
                if s: seen.append(s)
                if s=="readyok": break
            out.append(seen)
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=5)
    except: p.kill()
    return out

A  = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
# board B: start position with white queen already on the b1 rank area is illegal; use a clean but DIFFERENT board
B_BOARD = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"   # black queen removed
B_REFUSED = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1"  # impossible right for the kingside rook
B_ACCEPT  = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Q - 0 1"   # same, right removed -> accepted

OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
for name,exe in (("base","/home/ubuntu/build/forge"),("PC r15 + PC20","/home/ubuntu/pcbuild/forge")):
    r=session(exe,[f"position fen {A}","isready","go depth 6",f"position fen {B_REFUSED}","isready","go depth 6"],OPTS)
    moveA, isr, moveC = r[1], r[2], r[3]
    invalid=[x for x in isr if "invalid FEN" in x]
    # control: B_ACCEPT must produce a different move from A
    c=session(exe,[f"position fen {A}","isready","go depth 6",f"position fen {B_ACCEPT}","isready","go depth 6"],OPTS)
    moveB=c[3]
    print("==",name)
    print("  move on A                    :",moveA)
    print("  invalid-FEN line             :",invalid or "NONE")
    print("  readyok still answered       :","readyok" in isr)
    print("  move AFTER the refused FEN   :",moveC,"| == A?",moveC==moveA)
    print("  CONTROL: accepted B gives    :",moveB,"| differs from A?",moveB!=moveA)
    print("  -> refusal genuinely detected:",bool(invalid) and "readyok" in isr and moveC==moveA and moveB!=moveA)
    print()
