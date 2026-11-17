import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())
FEN2="5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
b=chess.Board(FEN2)
# Black queen on e4. After c6c5, is the queen attacked / does white win it?
c=b.copy(); c.push_uci("c6c5"); c.turn=chess.WHITE; c.ep_square=None
print("after c6c5, black queen e4 attacked by white?", c.is_attacked_by(chess.WHITE,chess.E4),
      [chess.square_name(s) for s in c.attackers(chess.WHITE,chess.E4)])
print("white queen b3 - black queen e4 line? f4? g5?  b3-e4 not a line.")
# what does white have: Qb3 vs Qe4 - b3 to e4 is diagonal? b3,c4,d5,e6. no.
print()
# the -39 is small; check what white plays
import subprocess
def score(fen,mv,dep=16):
    p=subprocess.run(["/home/ubuntu/pcbuild/forge","-c","setoption name Threads value 1","-c","setoption name Hash value 16",
        "-c","position fen %s moves %s"%(fen,mv)],input="go depth %d\nquit\n"%dep,capture_output=True,text=True)
    lines=[l for l in p.stdout.splitlines() if l.startswith("info") and " score cp " in l]
    return lines[-1].split("score")[1].strip()[:40] if lines else "none"
print("root cp as black:", score(FEN2,""))
print("after c6c5 (base's move):", score(FEN2,"c6c5"))
print("after e4b1 (PC's move):", score(FEN2,"e4b1"))
