#!/usr/bin/env python3
"""all_five.py : for EVERY F72 fixture, does the base's 0-node move CREATE a loss,
or FAIL TO ANSWER one that already existed? Decides which verb is correct."""
import json, chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())
BASE={"1":"e6e5","2":"a5a4","3":"c4c5","5":"g3g4","6":"c6c5"}
games=json.load(open('../job30/games.json'))
print("For each F72 fixture: threats against the mover that ALREADY existed at the root,")
print("and whether the base's 0-node move still leaves them. material = black minus white.\n")
print("%-2s %-6s %-22s %-22s %-12s %s"%("g","base","hanging at root","still hanging after","material","verdict"))
n_new=n_ignore=0
for i,gd in enumerate(games,1):
    g=str(i); bmv=BASE[g]; moves=gd[1]; fen=gd[2][2]
    b=chess.Board(); [b.push_uci(m) for m in moves]
    if b.fen()!=fen: print("FEN mismatch g%s\n %s\n %s"%(g,b.fen(),fen)); continue
    mover=b.turn
    hang=[(sq,b.piece_at(sq)) for sq in chess.SQUARES
          if b.piece_at(sq) and b.piece_at(sq).color==mover and b.piece_at(sq).piece_type!=chess.KING
          and b.is_attacked_by(not mover,sq)]
    c=b.copy(); c.push_uci(bmv)
    still=[(sq,p) for sq,p in hang if c.piece_at(sq) and c.piece_at(sq).symbol()==p.symbol()
           and c.is_attacked_by(not mover,sq)]
    # did the move newly expose something? compare attacked non-king set before/after
    def aset(bd):
        m=bd.turn; return {(sq,bd.piece_at(sq).symbol()) for sq in chess.SQUARES
            if bd.piece_at(sq) and bd.piece_at(sq).color==m and bd.piece_at(sq).piece_type!=chess.KING
            and bd.is_attacked_by(not m,sq)}
    newly = aset(c)-{(sq,p.symbol()) for sq,p in hang}
    verdict = ("IGNORES existing threat" if hang and still==hang
               else "ANSWERS/CHANGES threat" if hang
               else "creates a NEW threat" if newly else "no threat either way")
    if hang and still==hang: n_ignore+=1
    if not hang and newly: n_new+=1
    print("%-2s %-6s %-22s %-22s %+d->%+d   %s"%(g,bmv,
        ",".join(p.symbol().upper()+chess.square_name(sq) for sq,p in hang) or "-",
        ",".join(p.symbol().upper()+chess.square_name(sq) for sq,p in still) or "-",
        mat(b),mat(c),verdict))
    if newly: print("     NEWLY attacked after the move: %s"%",".join(p+chess.square_name(sq) for sq,p in sorted(newly)))
print("\nSUMMARY: %d of 5 IGNORE a threat that already existed; %d CREATE a new one."%(n_ignore,n_new))
