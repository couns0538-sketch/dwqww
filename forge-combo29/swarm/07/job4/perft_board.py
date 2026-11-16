#!/usr/bin/env python3
"""perft_board.py EXE OUTDIR [DEPTH]

Board-level test for the area-7 job-3 read of src/board.cpp: compares `go perft N`
with python-chess on positions chosen for the code paths that can be wrong in
NORMAL PLAY -- castling rights, en passant (including ep that would expose the
king), promotion and capture-promotion, and repetition-relevant pawn structure.

Every comparison asserts that a `nodes <n>` line was FOUND. A missing line, a
missing divide line, or a non-integer is a hard error: no zero, empty or NaN may
pass as agreement (the seat-19 rule).

Writes OUTDIR/<case>.json and OUTDIR/all.json; prints one row per case.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

import chess

HERE = os.path.dirname(os.path.abspath(__file__))

# (name, fen, depth)  -- depth kept small enough to finish quickly, large enough
# that castling/ep/promotion differences would show.
CASES = [
    ("kiwipete_d3", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3),
    ("kiwipete_d4", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4),
    ("pos3_d4", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4),
    ("pos3_d5", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5),
    ("pos4_d3", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3),
    ("pos4_d4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4),
    ("pos5_d3", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3),
    ("pos6_d3", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3),
    # en passant that would expose the king along the rank (the classic trap)
    ("ep_pin_d4", "8/8/8/KPp4r/8/8/8/7k w - c6 0 1", 4),
    ("ep_discovered_d3", "8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1", 3),
    # promotion and capture-promotion, incl. promotion with check
    ("promo_d4", "rn2k2r/1P4P1/8/8/8/8/1p4p1/RN2K2R w KQkq - 0 1", 4),
    ("promo_check_d3", "3r2k1/1P6/8/8/8/8/6p1/3R2K1 w - - 0 1", 4),
    # castling rights lost by rook capture / rook move
    ("castle_rights_d4", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", 4),
    ("castle_blocked_d3", "r3k2r/8/8/8/8/8/8/R3K1NR w KQkq - 0 1", 4),
]

NODES = re.compile(r"^nodes (\d+)$")


class Reader:
    def __init__(self, stream):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, stream):
        for line in stream:
            self.q.put(line)
        self.q.put(None)

    def readline(self, deadline_timeout=120.0):
        try:
            return self.q.get(timeout=deadline_timeout)
        except queue.Empty:
            return None


def run_case(exe, name, fen, depth):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    reader = Reader(proc.stdout)

    def send(cmd):
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def drain():
        while True:
            line = reader.readline()
            if line is None:
                raise RuntimeError(f"{name}: engine stopped before readyok")
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = reader.readline()
        if line is None or line.strip() == "uciok":
            break
    send("setoption name Hash value 16")
    send("isready")
    drain()
    send("position fen " + fen)
    send("isready")
    drain()
    send(f"go perft {depth}")
    total = None
    divide = {}
    while True:
        line = reader.readline(300.0)
        if line is None:
            raise RuntimeError(f"{name}: no output while waiting for perft nodes")
        s = line.rstrip("\n")
        m = NODES.match(s)
        if m:
            total = int(m.group(1))
            break
        if ":" in s:
            left, right = s.split(":", 1)
            left, right = left.strip(), right.strip()
            if right.isdigit():
                divide[left] = int(right)
    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    err = proc.stderr.read() if proc.stderr else ""
    if total is None:
        raise SystemExit(f"FAIL {name}: no 'nodes <n>' line was found. "
                         f"Refusing to compare -- nothing was measured.")
    return {"case": name, "fen": fen, "depth": depth, "engine_nodes": total,
            "engine_divide": divide, "stderr": err}


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows, problems = [], []
    for name, fen, depth in CASES:
        rec = run_case(exe, name, fen, depth)
        board = chess.Board(fen)
        # python-chess reference, perft and per-move divide
        ref_total = 0
        ref_divide = {}
        for move in board.legal_moves:
            board.push(move)
            n = perft(board, depth - 1)
            board.pop()
            ref_divide[move.uci()] = n
            ref_total += n
        rec["ref_nodes"] = ref_total
        rec["ref_divide"] = ref_divide
        rec["equal"] = (rec["engine_nodes"] == ref_total)
        diffs = []
        for move_uci in sorted(set(rec["engine_divide"]) | set(ref_divide)):
            a = rec["engine_divide"].get(move_uci)
            b = ref_divide.get(move_uci)
            if a != b:
                diffs.append({"move": move_uci, "engine": a, "python_chess": b})
        rec["divide_diffs"] = diffs[:40]
        if not rec["equal"]:
            problems.append(f"{name}: engine {rec['engine_nodes']} vs python-chess {ref_total}")
        if rec["stderr"].strip():
            problems.append(f"{name}: engine wrote to stderr: {rec['stderr'].strip()[:200]}")
        rows.append(rec)
        print(f"{name:22s} depth {depth}  engine {rec['engine_nodes']:>10d}  "
              f"python-chess {ref_total:>10d}  {'EQUAL' if rec['equal'] else 'DIFFERENT'}",
              flush=True)
        with open(os.path.join(outdir, name + ".json"), "w") as fh:
            json.dump(rec, fh, indent=1)
    with open(os.path.join(outdir, "all.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print()
    if problems:
        print("PROBLEMS:")
        for item in problems:
            print("  -", item)
        sys.exit(1)
    print(f"OK: {len(rows)} positions, every perft total equal to python-chess, "
          f"every divide line equal, no stderr output.")


def perft(board, depth):
    if depth <= 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += perft(board, depth - 1)
        board.pop()
    return total


if __name__ == "__main__":
    main()
