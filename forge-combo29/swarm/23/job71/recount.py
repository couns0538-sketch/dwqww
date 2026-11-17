#!/usr/bin/env python3
"""recount.py : recount the HANDOFF master table's "root occ" column under the key the
table's HEADER states (placement + side + castling), and under the key 23-F122 says the
ORIGINAL count used (placement + side + EP). If the column is stale, the two disagree."""
import chess

def count_occ(fen, moves, key):
    b = chess.Board(fen)
    seen = {}
    def ident(bd):
        if key == "fide":   # placement + side + CASTLING  (23-F122's corrected key)
            return (bd.board_fen(), bd.turn, bd.castling_rights)
        else:               # the ORIGINAL key: placement + side + EP
            return (bd.board_fen(), bd.turn, bd.ep_square)
    seen[ident(b)] = 1
    for mv in moves.split():
        b.push(chess.Move.from_uci(mv))
        k = ident(b)
        seen[k] = seen.get(k, 0) + 1
    return seen[ident(b)]      # occurrences of the ROOT (position at end of list)

ROWS = [
 ("E1","1k6/3q1p1p/rp5p/4P3/pQ3P2/7P/3R2PK/8 b - - 0 1","b8c8 b4e7 c8b8 e7b4 b8c8 b4e7 c8b8 e7b4",3,"BAIL"),
 ("E2","1K6/8/8/3R4/8/8/8/k7 w - - 0 1","b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1",3,"BAIL"),
 ("E3","6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1","g1h1 g8h8 h1g1 h8g8 g1h1 g8h8 h1g1 h8g8",3,"BAIL"),
 ("E4","7k/8/8/8/8/8/6PP/7K b - - 0 1","h8g8 h1g1 g8h8 g1h1 h8g8 h1g1 g8h8 h1g1",3,"BAIL"),
 ("M1","rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b KQkq - 0 4","g8e7 d3a6 e7g8 a6d3 g8e7 d3a6 e7g8 a6d3",3,"BAIL"),
 ("M1s","rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b - - 0 4","g8e7 d3a6 e7g8 a6d3 g8e7 d3a6 e7g8 a6d3",3,"BAIL"),
 ("M4","r1bqkbnr/R2pp2p/5p2/1Ppn2p1/5P2/1P1P1N2/2P1P1PP/1NBQKB1R w Kkq - 0 8","a7c7 g8h6 c7a7 h6g8 a7c7 g8h6 c7a7 h6g8",3,"BAIL"),
 ("M4s","r1bqkbnr/R2pp2p/5p2/1Ppn2p1/5P2/1P1P1N2/2P1P1PP/1NBQKB1R w - - 0 8","a7c7 g8h6 c7a7 h6g8 a7c7 g8h6 c7a7 h6g8",3,"BAIL"),
 ("M7","rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15","c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8",3,"searched"),
 ("M7s","rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w - - 1 15","c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8",3,"BAIL"),
 ("C1","r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8",3,"searched"),
 ("C1s","r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1","a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8",3,"BAIL"),
 ("C1h","r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 13 7","a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8",3,"searched"),
]
print("%-5s %-9s %-9s %-9s %-11s %s" % ("row","table","FIDE","orig(EP)","verdict","agreement"))
bad=[]
for name,fen,moves,stated,verdict in ROWS:
    try:
        fide = count_occ(fen,moves,"fide")
        ep   = count_occ(fen,moves,"ep")
    except Exception as e:
        print("%-5s ERROR %s" % (name,e)); continue
    # what each key PREDICTS: FIDE key says >=3 -> bails
    pred = "BAIL" if fide >= 3 else "searched"
    ok = (pred == verdict.replace("**",""))
    mark = "" if ok else "  <-- CONTRADICTS"
    print("%-5s %-9s %-9s %-9s %-11s %s%s" % (name, stated, fide, ep, verdict.replace("**",""), "yes" if ok else "NO", mark))
    if not ok: bad.append(name)
print()
print("rows where the stated occurrence count disagrees with the FIDE key:",
      [n for n,f,m,s,v in ROWS if count_occ(f,m,"fide")!=s])
print("rows where the VERDICT disagrees with the FIDE key prediction:", bad)
