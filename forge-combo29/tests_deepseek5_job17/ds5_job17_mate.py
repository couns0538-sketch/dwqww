#!/usr/bin/env python3
"""job17 A3: the mate harness with the engine able to SEE repetitions.

Protocol repair (Fable file 17, WRONG 1): before EVERY move the harness sends
    position fen <start position> moves <every move so far>
so the engine's repetition detection sees the real game. A game ends at mate, stalemate,
insufficient material, halfmove clock 100, an ACTUAL third occurrence (board.is_repetition(3)),
or 200 plies. Controls J1/J2/J3 run first and their files are committed.
"""
import chess
import random
import statistics
import subprocess
import sys
import time

import os
ENGINE = os.environ.get("DS5ENGINE", "/tmp/ds5_fresh/build/forge")
OUT = "/tmp/glmflash/ds5j17"
os.makedirs(OUT, exist_ok=True)
JOB = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job17"


class Eng:
    def __init__(self, opts, log=None):
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.log = log
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
        if self.log is not None:
            self.log.write(s + "\n")
            self.log.flush()
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def rl_line(self):
        return self.p.stdout.readline()


def play(e, start_fen, node_limit, max_plies=200):
    parts = start_fen.split("|")[0].strip()
    b0 = chess.Board(); b0.set_fen(parts)
    strong_white = sum(1 for p in b0.piece_map().values() if p.piece_type != chess.KING and p.color == chess.WHITE) > 0
    board = chess.Board(); board.set_fen(parts)
    e.send("ucinewgame")
    e.send("isready")
    while True:
        if e.rl_line().startswith("readyok"):
            break
    moves = []
    plies = 0
    while True:
        if board.is_checkmate():
            return ("mate", "strong" if (board.turn != chess.WHITE) == strong_white else "lone", plies, board.fen())
        if board.is_stalemate():
            return ("stalemate", None, plies, board.fen())
        if board.is_insufficient_material():
            return ("insufficient", None, plies, board.fen())
        if board.halfmove_clock >= 100:
            return ("fifty", None, plies, board.fen())
        if board.is_repetition(3):
            return ("repetition", None, plies, board.fen())
        if plies >= max_plies:
            return ("cap", None, plies, board.fen())
        mv_str = " ".join(moves)
        if mv_str:
            e.send(f"position fen {parts} moves {mv_str}")
        else:
            e.send(f"position fen {parts}")
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
            print(f"DEBUG illegal: fen-sent last, best={best!r} board_turn={board.turn} legal={[m.uci() for m in list(board.legal_moves)[:5]]}")
            return ("illegal-move", None, plies, board.fen())
        moves.append(best)
        board.push(mv)
        plies += 1


def j1():
    lines = []
    b = chess.Board()
    b.set_fen("4k3/8/8/8/8/8/8/4K2Q w - - 0 1")
    seq = ["h1h2", "e8d8", "h2h1", "d8e8", "h1h2", "e8d8", "h2h1", "d8e8"]
    rep_new = rep_old = None
    for i, m in enumerate(seq, 1):
        b.push(chess.Move.from_uci(m))
        new = b.is_repetition(3)
        old = b.can_claim_threefold_repetition()
        lines.append(f"ply {i}: is_repetition(3)={new}  can_claim_threefold={old}")
        if new:
            rep_new = i if rep_new is None else rep_new
        if old:
            rep_old = i if rep_old is None else rep_old
    lines.append(f"first is_repetition(3) at ply {rep_new} (must be 8)")
    lines.append(f"first can_claim_threefold_repetition at ply {rep_old} (the old test: fires before the occurrence)")
    ok = rep_new == 8 and rep_old == 7
    lines.append(f"J1 {'PASS' if ok else 'FAIL'}")
    open(f"{JOB}/j1_repetition.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return ok


def j2():
    e = Eng([], log=open(f"{OUT}/j2_input.log", "w"))
    res = play(e, open("/agent/repos/dwqww/forge-combo29/tests_deepseek5_job15/KQ_60.epd").readline(), 2000)
    e.send("quit")
    pos_with = pos_without = 0
    for ln in open(f"{OUT}/j2_input.log"):
        if ln.startswith("position "):
            if " moves " in ln:
                pos_with += 1
            else:
                pos_without += 1
    lines = [f"game result: {res[0]} after {res[2]} plies",
             f"position lines WITH moves: {pos_with}",
             f"position lines WITHOUT moves: {pos_without} (must be 1: the game's first move)",
             f"J2 {'PASS' if pos_without == 1 else 'FAIL'}"]
    open(f"{JOB}/j2_protocol.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return pos_without == 1


def j3():
    rng = random.Random(9503)
    lines = []
    ok = True
    for i in range(20):
        while True:
            b = chess.Board()
            b.clear()
            squares = rng.sample(range(64), 3)
            b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
            b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
            b.set_piece_at(squares[2], chess.Piece(chess.BISHOP, rng.choice([chess.WHITE, chess.BLACK])))
            if b.is_valid() and not b.is_checkmate() and not b.is_stalemate():
                break
        ins = b.is_insufficient_material()
        ok &= ins
        lines.append(f"{i+1}: {b.fen()} insufficient={ins}")
    lines.append(f"J3 {'PASS' if ok else 'FAIL'} (20/20 insufficient material at ply 0)")
    open(f"{JOB}/j3_insufficient.txt", "w").write("\n".join(lines) + "\n")
    print(lines[-1])
    return ok


def main():
    ok = j1() and j2() and j3()
    if not ok:
        print("A CONTROL FAILED - the 180-run does not start")
        raise SystemExit(1)
    lists = [("KQ", "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job15/KQ_60.epd"),
             ("KR", "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job15/KR_60.epd"),
             ("KBN", "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job15/KBN_60.epd")]
    fens = []
    for kind, path in lists:
        for ln in open(path):
            fens.append((kind, ln.strip()))
    print(f"total start positions: {len(fens)}")
    e = Eng([])
    games = []
    for kind, fen in fens:
        r = play(e, fen, 2000)
        games.append((kind, fen, r))
        print(f"{kind} {r[0]:>12} plies {r[2]}", flush=True)
    e.send("quit")
    with open(f"{JOB}/run2000_none_fixed.games", "w") as f:
        for kind, fen, r in games:
            f.write(f"{fen}|{r[0]}|{r[1]}|{r[2]}|{r[3]}\n")
    endings = {}
    for _, _, r in games:
        endings[r[0]] = endings.get(r[0], 0) + 1
    print("ENDINGS:", dict(sorted(endings.items(), key=lambda kv: -kv[1])))
    abnormal = [k for k in endings if k in ("no-bestmove", "bad-move", "illegal-move")]
    mates = [r[2] for _, _, r in games if r[0] == "mate"]
    strong_mates = [r[2] for _, _, r in games if r[0] == "mate" and r[1] == "strong"]
    lines = [f"games: {len(games)}", "endings: " + str(dict(sorted(endings.items(), key=lambda kv: -kv[1]))),
             f"abnormal endings (no-bestmove/bad-move/illegal-move): {sum(endings.get(k, 0) for k in abnormal)}",
             f"mates: {len(mates)}  median {statistics.median(mates) if mates else None}  longest {max(mates) if mates else None}",
             f"mates by the strong side: {len(strong_mates)}  median {statistics.median(strong_mates) if strong_mates else None}  longest {max(strong_mates) if strong_mates else None}"]
    open(f"{JOB}/run2000_none_fixed.summary.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
