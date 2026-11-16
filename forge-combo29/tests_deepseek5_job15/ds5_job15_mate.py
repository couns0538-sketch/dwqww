#!/usr/bin/env python3
"""deepseek5 job15 Part C: what the SoundMatePruning arms buy — a mate test with known answers."""
import chess
import json
import random
import subprocess
import sys
import time

import os
ENGINE = os.environ.get("DS5ENGINE", "/tmp/ds5_arms/build/forge")
OUT = "/tmp/glmflash/ds5j15"

class Eng:
    def __init__(self, opts):
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        while True:
            if self.rl_line().startswith("uciok"):
                break
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("setoption name OwnBook value false")
        for n, v in opts:
            self.send(f"setoption name {n} value {v}")
        self.send("isready")
        while True:
            if self.rl_line().startswith("readyok"):
                break

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def rl_line(self):
        return self.p.stdout.readline()

def gen_positions(kind, n, seed):
    """kind: KQ, KR, KBN — n positions each, half White-strong, half Black-strong, side to move random."""
    rng = random.Random(seed)
    out = []
    guard = 0
    while len(out) < n and guard < 200000:
        guard += 1
        board = chess.Board(None)
        wk = rng.randrange(64); bk = rng.randrange(64)
        if wk == bk:
            continue
        squares = [wk, bk]
        if kind == "KQ": pieces = [(chess.QUEEN,)]
        elif kind == "KR": pieces = [(chess.ROOK,)]
        else: pieces = [(chess.BISHOP,), (chess.KNIGHT,)]
        ok = True
        for grp in pieces:
            sq = rng.randrange(64)
            if sq in squares:
                ok = False; break
            squares.append(sq)
        if not ok:
            continue
        strong_white = rng.random() < 0.5
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        pi = 0
        for grp in pieces:
            for pt in grp:
                board.set_piece_at(squares[2 + pi], chess.Piece(pt, chess.WHITE if strong_white else chess.BLACK))
                pi += 1
        board.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        if not board.is_valid():
            continue
        if board.is_check():
            continue
        if board.is_insufficient_material():
            continue
        if not any(board.legal_moves):
            continue
        lone = chess.BLACK if strong_white else chess.WHITE
        # the lone king cannot take a piece at once: no strong piece adjacent to it
        bad = False
        for sq in squares[2:]:
            if chess.square_distance(sq, bk if lone == chess.BLACK else wk) <= 1:
                bad = True
        if bad:
            continue
        if strong_white and board.turn == chess.BLACK and chess.square_distance(wk, bk) <= 1:
            continue
        out.append(fen0_of(board) + f"|{strong_white}|{board.turn == chess.WHITE}")
    return out

def fen0_of(board):
    return " ".join(board.fen().split()[:4]) + " 0 1"

def play(e, start_fen, node_limit, max_plies=200):
    board = chess.Board()
    parts = start_fen.split("|")[0]
    b0 = chess.Board(); b0.set_fen(parts)
    strong_white = sum(1 for p in b0.piece_map().values() if p.piece_type != chess.KING and p.color == chess.WHITE) > 0
    board.set_fen(parts)
    e.send("ucinewgame")
    e.send("isready")
    while True:
        if e.rl_line().startswith("readyok"):
            break
    plies = 0
    while True:
        if board.is_checkmate():
            return ("mate", "strong" if (board.turn != chess.WHITE) == strong_white else "lone", plies, board.fen())
        if board.is_stalemate():
            return ("stalemate", None, plies, board.fen())
        if board.can_claim_threefold_repetition():
            return ("repetition", None, plies, board.fen())
        if board.halfmove_clock >= 100:
            return ("fifty", None, plies, board.fen())
        if plies >= max_plies:
            return ("cap", None, plies, board.fen())
        e.send(f"position fen {board.fen()}")
        e.send(f"go nodes {node_limit}")
        best = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            line = e.rl_line()
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        if best is None:
            return ("no-bestmove", None, plies, board.fen())
        try:
            mv = chess.Move.from_uci(best)
        except Exception:
            return ("bad-move", None, plies, board.fen())
        if mv not in board.legal_moves:
            return ("illegal-move", None, plies, board.fen())
        board.push(mv)
        plies += 1

def main():
    mode = sys.argv[1]
    import os
    os.makedirs(OUT, exist_ok=True)
    if mode == "gen":
        for kind, seed in (("KQ", 9401), ("KR", 9402), ("KBN", 9403)):
            ps = gen_positions(kind, 60, seed)
            open(f"{OUT}/{kind}_60.epd", "w").write("\n".join(p.split("|")[0] for p in ps) + "\n")
            json_meta = [(p.split("|")[0], p.split("|")[1], p.split("|")[2]) for p in ps]
            json.dump(json_meta, open(f"{OUT}/{kind}_60.meta.json", "w"), indent=0)
            print(kind, len(ps))
        return
    if mode == "c1":
        # 20 positions K+B vs K at N=2000: 0 mates expected
        ps = gen_positions("KB", 20, 9410)
        e = Eng([])
        mates = 0
        games = []
        for p in ps:
            r = play(e, p, 2000)
            games.append(f"{p.split('|')[0]}|{r[0]}|{r[1]}|{r[2]}")
            if r[0] == "mate":
                mates += 1
        e.send("quit")
        open(f"{OUT}/c1_kb_games.txt", "w").write("\n".join(games) + "\n")
        print(f"c1: mates={mates} of {len(ps)} (expected 0)")
        return
    if mode == "c2":
        ps = [l.split("|")[0] for l in open(f"{OUT}/KQ_60.epd")][:20]
        e = Eng([])
        mates = 0; games = []
        for p in ps:
            board = chess.Board(); board.set_fen(p)
            plies = 0
            res = "unfinished"
            while True:
                if board.is_checkmate(): res = "mate"; break
                if board.is_stalemate() or board.can_claim_threefold_repetition() or board.halfmove_clock >= 100: res = "draw"; break
                if plies >= 200: res = "cap"; break
                e.send(f"position fen {board.fen()}")
                e.send("go depth 12")
                best = None
                t0 = time.monotonic()
                while time.monotonic() - t0 < 60:
                    l = e.rl_line()
                    if l.startswith("bestmove"):
                        best = l.split()[1]; break
                if best is None: res = "no-bestmove"; break
                board.push(chess.Move.from_uci(best)); plies += 1
            if res == "mate": mates += 1
            games.append(f"{p}|{res}|{plies}")
        e.send("quit")
        open(f"{OUT}/c2_depth12_games.txt", "w").write("\n".join(games) + "\n")
        print(f"c2: mates={mates} of {len(ps)} (the harness's own number; fewer than 15 = look at the harness)")
        return
    if mode == "c3":
        ps = [l.split("|")[0] for l in open(f"{OUT}/KQ_60.epd")][:5]
        e = Eng([])
        same = 0
        for p in ps:
            outs = []
            for run in (1, 2):
                e.send("ucinewgame")
                e.send("isready")
                while True:
                    if e.rl_line().startswith("readyok"):
                        break
                board = chess.Board(); board.set_fen(p)
                seq = []
                plies = 0
                while plies < 200:
                    if board.is_game_over(claim_draw=True): break
                    e.send(f"position fen {board.fen()}")
                    e.send("go nodes 2000")
                    best = None
                    t0 = time.monotonic()
                    while time.monotonic() - t0 < 60:
                        l = e.rl_line()
                        if l.startswith("bestmove"):
                            best = l.split()[1]; break
                    board.push(chess.Move.from_uci(best)); plies += 1
                seq = board.fen()
                outs.append(seq)
            if outs[0] == outs[1]:
                same += 1
        e.send("quit")
        print(f"c3: identical={same} of {len(ps)}")
        return
    if mode == "run":
        setting_name = sys.argv[2]
        N = int(sys.argv[3])
        tag = sys.argv[4]
        rest = sys.argv[5:]
        opts = [(rest[i], rest[i + 1]) for i in range(0, len(rest), 2)]
        e = Eng(opts)
        rows = []
        for kind in ("KQ", "KR", "KBN"):
            for line in open(f"{OUT}/{kind}_60.epd"):
                parts = line.strip()
                if not parts: continue
                meta = parts
                r = play(e, meta, N)
                rows.append(f"{kind}|{meta}|{r[0]}|{r[1]}|{r[2]}|{r[3]}")
        e.send("quit")
        open(f"{OUT}/{tag}.games", "w").write("\n".join(rows) + "\n")
        kinds = {}
        for r in rows:
            k = r.split("|")[2]
            kinds[k] = kinds.get(k, 0) + 1
        print(f"{tag}: endings={kinds}", flush=True)

if __name__ == "__main__":
    main()
