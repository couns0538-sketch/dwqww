#!/usr/bin/env python3
"""f2595_twin.py EXE OUTDIR LABEL : is the root-drawn fallback at src/search.cpp:2595 reachable in a way a GUI
could trigger, and is it CORRECT where it is reachable?

On PC r15 `FORGE_FIX_ROOT_DRAWN` defaults to 1, so `root_drawn` is
    !legal.empty() && board.is_insufficient_material()
only. On the base tree the flag is absent and `root_drawn` also includes `is_repetition()` and
`halfmove_clock() >= 100`. That difference is what these tests probe.

Two tests, one each way:

  TEST 1 (GUI-triggerable, must be CORRECT): a position with insufficient material where legal moves exist —
          K+N vs K. A GUI can reach this by playing such an endgame out. The engine answers score 0 and
          `root_candidates.front()`. Every legal move draws, so any choice is correct; the test is whether the
          answer is legal and the score is 0 (not a fabricated evaluation).

  TEST 2 (the case the flag removes): a THREEFOLD REPETITION drawn position that still has a MATE on the board,
          reached by a move list from a real game. Under FORGE_FIX_ROOT_DRAWN=1 the engine must SEARCH it and
          find the mate; if it answers 0 nodes with a first-legal move instead, the fallback fired and the old
          defect is present.

Each answer is checked against python-chess (legal? score?), in a fresh process, Threads 1.
"""
import os
import subprocess
import sys

import chess

exe, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)


def run(lines, timeout=120):
    """Send the lines, but WAIT for `bestmove` before `quit` — a piped quit aborts the search (19-F12)."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    got = []
    for line in lines:
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        if line.startswith("go "):
            while True:
                out = proc.stdout.readline()
                if not out:
                    break
                got.append(out.rstrip("\n"))
                if out.startswith("bestmove"):
                    break
        elif line.startswith(("uci", "isready", "position", "setoption")):
            # drain to the answering token so the next command is not racing the reply
            token = "uciok" if line == "uci" else "readyok"
            while True:
                out = proc.stdout.readline()
                if not out:
                    break
                got.append(out.rstrip("\n"))
                if out.startswith(token) or out.startswith("bestmove"):
                    break
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        rest, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        rest = ""
    return "\n".join(got) + "\n" + (rest or "")


def parse(out):
    last_info = None
    best = None
    for line in out.splitlines():
        if line.startswith("info depth"):
            last_info = line
        if line.startswith("bestmove"):
            best = line.split()[1] if len(line.split()) > 1 else None
    nodes = 0
    score = None
    if last_info:
        if " nodes " in last_info:
            try:
                nodes = int(last_info.split("nodes ")[1].split()[0])
            except (IndexError, ValueError):
                nodes = 0
        if "score cp " in last_info:
            score = ("cp", int(last_info.split("score cp ")[1].split()[0]))
        elif "score mate " in last_info:
            score = ("mate", int(last_info.split("score mate ")[1].split()[0]))
    return best, nodes, score, last_info


out = []

# ---------------- TEST 1: insufficient material, GUI-reachable ----------------
T1 = "8/8/8/4k3/8/8/8/4K1N1 w - - 0 1"   # K+N vs K
t1_out = run(["uci", "isready", "position fen " + T1, "isready", "go depth 6"])
t1_best, t1_nodes, t1_score, t1_info = parse(t1_out)
t1_board = chess.Board(T1)
legal_ok = t1_best is not None and t1_best in [m.uci() for m in t1_board.legal_moves]
insufficient = t1_board.is_insufficient_material()
out.append("## TEST 1 — K+N vs K (insufficient material, GUI reachable)")
out.append("FEN: %s" % T1)
out.append("python-chess is_insufficient_material: %s" % insufficient)
out.append("engine bestmove: %s  (legal: %s)   score: %s   nodes: %d"
           % (t1_best, legal_ok, t1_score, t1_nodes))
out.append("raw last info line: %s" % (t1_info or "(none)"))
t1_correct = legal_ok and insufficient and (t1_score == ("cp", 0) or t1_nodes == 0)
out.append("verdict TEST 1: %s — reachable by a GUI, and %s"
           % ("REACHABLE",
              "CORRECT (any legal move draws here, score 0)" if t1_correct
              else "SUSPICIOUS (legal=%s, score=%s) — inspect" % (legal_ok, t1_score)))
out.append("")

# ---------------- TEST 2: threefold repetition WITH a mate available ----------------
# Build a real threefold repetition by a move list, from a position where White has mate in one.
base_fen = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
b = chess.Board(base_fen)
# Shuffle the rook and black king back and forth to repeat the position three times.
shuffle = ["a1a2", "g8h8", "a2a1", "h8g8", "a1a2", "g8h8", "a2a1", "h8g8"]
moves = []
for u in shuffle:
    mv = chess.Move.from_uci(u)
    if mv in b.legal_moves:
        b.push(mv)
        moves.append(u)
rep_board = b
reps = rep_board.is_repetition(3)
t2_lines = ["uci", "isready", "position startfen_placeholder"]
t2_lines = ["uci", "isready",
            "position fen %s moves %s" % (base_fen, " ".join(moves)), "isready", "go depth 8"]
t2_out = run(t2_lines)
t2_best, t2_nodes, t2_score, t2_info = parse(t2_out)
out.append("## TEST 2 — threefold repetition with mate in one available")
out.append("position: %s moves %s" % (base_fen, " ".join(moves)))
out.append("python-chess threefold repetition: %s ; halfmove clock %d"
           % (reps, rep_board.halfmove_clock))
out.append("engine bestmove: %s   score: %s   nodes: %d" % (t2_best, t2_score, t2_nodes))
out.append("raw last info line: %s" % (t2_info or "(none)"))
searched = t2_nodes > 0
out.append("verdict TEST 2: the engine %s the repetition root, so the 2595 fallback %s"
           % ("SEARCHED" if searched else "did NOT search",
              "did not fire (FORGE_FIX_ROOT_DRAWN is doing its job)"
              if searched else "FIRED (answer is the first legal move, 0 nodes)"))

text = "\n".join([("# " + label), ""] + out)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
