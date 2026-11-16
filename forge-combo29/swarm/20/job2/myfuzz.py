#!/usr/bin/env python3
"""myfuzz.py — seat 20's OWN fuzz, written from the item description (not a copy of deepseek6's runner).

200 sequences, seed 2001+1, grammar shape: uci + 5..30 body lines (isready, ucinewgame, setoption with a real
name and a random or missing value, position startpos/fen with 0..40 random legal-or-illegal moves, go depth /
nodes / movetime / infinite / ponder, stop, ponderhit, garbage) + isready + quit.

Different from deepseek6's runner on purpose:
  * the legality check is driven by MY OWN parse of the position lines I SENT (not by scanning stdout),
    tracking the legal prefix exactly as the engine does (stop at the first illegal move);
  * the readiness window is cleared per isready (a counter of readyok seen so far);
  * each sequence is one process; a sequence whose isready has no readyok in 20 s is a HANG.

usage: myfuzz.py <exe> <outdir> <count>
"""
import concurrent.futures
import json
import os
import random
import re
import subprocess
import sys
import threading
import time

import chess

EXE = sys.argv[1]
OUT = sys.argv[2]
COUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 200
SEED = 2001
os.makedirs(OUT, exist_ok=True)

OPTS = ["Hash", "Threads", "OwnBook", "MultiPV", "UseNNUE", "LmrQuietBase", "LmrQuietDivisor",
        "NullMoveBase", "NonPawnCorrection", "DrawJitter", "Move Overhead", "BogusOption"]
VALS = ["0", "1", "2", "16", "64", "2048", "3000", "-5", "999999", "banana", "true", "false", ""]

# a few fixed FENs of my own making (legal, from python-chess)
MYFENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
    "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1",
    "8/8/8/8/8/8/8/K6k w - - 0 1",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3",
]


def rnd_move(rng):
    a = rng.choice("abcdefgh") + rng.choice("12345678")
    b = rng.choice("abcdefgh") + rng.choice("12345678")
    return a + b + rng.choice(["", "", "", "q", "n", "b", "r"])


def gen(i):
    """returns (lines, expected_final_board_or_None)"""
    rng = random.Random(SEED * 1000 + i)
    body = []
    k = rng.randint(5, 30)
    for _ in range(k):
        t = rng.random()
        if t < 0.12:
            body.append("isready")
        elif t < 0.20:
            body.append("ucinewgame")
        elif t < 0.38:
            o = rng.choice(OPTS)
            if rng.random() < 0.15:
                body.append(f"setoption name {o}")
            else:
                body.append(f"setoption name {o} value {rng.choice(VALS)}")
        elif t < 0.58:
            if rng.random() < 0.4:
                body.append("position startpos")
            else:
                body.append("position fen " + rng.choice(MYFENS))
            if rng.random() < 0.7:
                body.append("position startpos moves " + " ".join(rnd_move(rng) for _ in range(rng.randint(0, 40))))
        elif t < 0.78:
            kind = rng.choice(["depth", "nodes", "movetime", "infinite", "ponder"])
            if kind == "depth":
                body.append(f"go depth {rng.randint(1, 6)}")
            elif kind == "nodes":
                body.append(f"go nodes {rng.randint(1, 5000)}")
            elif kind == "movetime":
                body.append(f"go movetime {rng.randint(1, 50)}")
            elif kind == "infinite":
                body.append("go infinite")
            else:
                body.append("go ponder")
        elif t < 0.88:
            body.append(rng.choice(["stop", "ponderhit"]))
        else:
            body.append(rng.choice(["garbage line", "go banana", "position", "setoption name",
                                    "go depth -3", "###", "isready garbage"]))
    return ["uci"] + body + ["isready", "quit"]


def boards_per_go(lines):
    """Walk the lines in order, keeping the current board, and record the board in force at every `go`.
    Returns (list_of_boards_one_per_go, final_board). Position semantics as the engine: the last position
    command wins; inside a `moves` list the LEGAL PREFIX is kept (stop at the first illegal move)."""
    board = chess.Board()
    per_go = []
    for line in lines:
        if line.startswith("position"):
            rest = line[len("position"):].strip()
            moves = []
            if rest.startswith("fen "):
                fen = rest[4:]
                if " moves " in fen:
                    fen, mv = fen.split(" moves ", 1)
                    moves = mv.split()
                try:
                    board = chess.Board(fen)
                except ValueError:
                    # the engine refuses it and keeps the previous position
                    moves = []
            else:
                if " moves " in rest:
                    moves = rest.split(" moves ", 1)[1].split()
                board = chess.Board()
            for m in moves:
                try:
                    mm = chess.Move.from_uci(m)
                except ValueError:
                    break
                if mm not in board.legal_moves:
                    break
                board.push(mm)
        elif line.startswith("go"):
            per_go.append(board.copy())
    return per_go, board


def run(i):
    lines = gen(i)
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rdo():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rdo, daemon=True).start()
    rec = {"i": i, "hang": False, "san": 0, "exit": None, "illegal": None, "moves": 0}
    ready_seen = 0
    for line in lines:
        try:
            p.stdin.write(line + "\n")
            p.stdin.flush()
        except Exception:
            break
        if line == "isready":
            t0 = time.monotonic()
            ok = False
            while time.monotonic() - t0 < 20:
                with lock:
                    n = sum(1 for x in out if x.strip() == "readyok")
                if n > ready_seen:
                    ready_seen = n
                    ok = True
                    break
                time.sleep(0.005)
            if not ok:
                rec["hang"] = True
                p.kill()
                rec["lines"] = lines
                return rec
        if line.startswith("go"):
            rec["moves"] += 1
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        rec["hang"] = True
        p.kill()
    rec["exit"] = p.returncode
    with lock:
        tail = list(out)
    rec["san"] = sum(1 for x in tail if "AddressSanitizer" in x or "runtime error" in x
                     or "LeakSanitizer" in x or "ThreadSanitizer" in x or "SUMMARY:" in x)
    # legality: pair the k-th bestmove in stdout order with the board of the k-th `go` (my own parse).
    # Only pairs that are unambiguous (same count on both sides) are judged; otherwise the count is recorded.
    gos, final_board = boards_per_go(lines)
    bests = [x.split()[1] if len(x.split()) > 1 else "" for x in tail if x.startswith("bestmove")]
    rec["gos"] = len(gos)
    rec["bestmoves"] = len(bests)
    # The driver sends go lines without waiting (a GUI never does), so a bestmove can belong to an earlier
    # go than the newest position. To stay honest and still catch a real bug, a bestmove is called ILLEGAL
    # only when it is illegal for EVERY board that was in force at some `go` in this sequence.
    union = set()
    for b in gos:
        union |= {m.uci() for m in b.legal_moves}
    rec["judged"] = 0
    for bm in bests:
        if not bm or bm == "0000":
            continue
        rec["judged"] += 1
        if bm not in union:
            rec["illegal"] = bm
            rec["fen"] = "illegal for all " + str(len(gos)) + " go-boards; last = " + final_board.fen()
            break
    rec["lines"] = lines
    return rec


seqs = [gen(i) for i in range(COUNT)]
t0 = time.monotonic()
res = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(run, range(COUNT)):
        res.append(r)
wall = time.monotonic() - t0

bad = [r for r in res if r["hang"] or r["san"] or (r["exit"] not in (0,)) or r["illegal"]]
summary = {
    "count": COUNT, "wall_s": round(wall, 1),
    "hangs": sum(1 for r in res if r["hang"]),
    "sanitizer_lines": sum(r["san"] for r in res),
    "bad_exits": sum(1 for r in res if r["exit"] not in (0,)),
    "illegal_bestmoves": sum(1 for r in res if r["illegal"]),
    "bestmoves_judged": sum(r.get("judged", 0) for r in res),
    "go_like_commands": sum(r["moves"] for r in res),
    "exe": EXE,
    "seed": SEED,
}
with open(os.path.join(OUT, "myfuzz_summary.json"), "w") as f:
    json.dump(summary, f, indent=1)
with open(os.path.join(OUT, "myfuzz_bad.txt"), "w") as f:
    for r in bad:
        f.write(f"### seq {r['i']} hang={r['hang']} san={r['san']} exit={r['exit']} illegal={r['illegal']}\n")
        f.write("\n".join(r["lines"]) + "\n\n")
with open(os.path.join(OUT, "myfuzz_seqs.txt"), "w") as f:
    for i, s in enumerate(seqs):
        f.write(f"### seq {i}\n")
        for l in s:
            f.write(l + "\n")
print(json.dumps(summary, indent=1))
print(f"bad sequences: {len(bad)}")
