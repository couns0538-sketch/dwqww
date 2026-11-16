#!/usr/bin/env python3
"""f12_which_path.py EXE OUTDIR : WHICH fabrication is 19-F12 on the PC build?

Three candidate mechanisms, each with a prediction that separates it:

  H1  "first legal move of the position on the board" — the engine answers without searching, and names
      whatever move its generator emits first. Prediction: change the position and the answer changes to
      THAT position's first legal move.
  H2  "stale bestmove from a previous search" — the engine re-publishes an earlier result. Prediction: with a
      prior completed search returning move M, the aborted answer is M, not the new position's first move.
  H3  "a fixed literal such as a2a3" — prediction: the answer is a2a3 regardless of position.

Three experiments, each in a fresh process:

  A. ONLY a refused-free position P1 (`black to move`, where a2a3 is not even legal for the side to move)
     followed by immediate quit. H1 predicts P1's first legal move; H3 predicts a2a3; H2 predicts no move
     (there was no previous search).
  B. Previous completed search from startpos (returns M), THEN position P1, THEN immediate quit.
     H2 predicts M; H1 predicts P1's first legal move.
  C. Two different positions P1 and P2 (both where a2a3 is illegal), each in its own process, aborted.
     H1 predicts two DIFFERENT answers; H3 predicts a2a3 twice.

I compute "first legal move" independently with python-chess, so the prediction for H1 is not taken from the
engine itself.
"""
import os
import subprocess
import sys

import chess

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

P1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"      # black to move
P2 = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"     # white, a2a3 blocked? check below
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def first_legal(fen):
    b = chess.Board(fen)
    moves = sorted(b.legal_moves, key=lambda m: m.uci())
    return moves[0].uci() if moves else None


def uci_list(fen):
    b = chess.Board(fen)
    return [m.uci() for m in b.legal_moves]


def run(name, lines):
    proc = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n",
                          capture_output=True, text=True, timeout=180)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("lines:\n" + "\n".join(">>> " + l for l in lines) + "\n\nstdout:\n" + proc.stdout)
    bests = [l.strip() for l in proc.stdout.splitlines() if l.startswith("bestmove")]
    infos = [l for l in proc.stdout.splitlines() if l.startswith("info depth")]
    return bests, len(infos)


fl1, fl2 = first_legal(P1), first_legal(P2)
lines = []
lines.append("python-chess first legal move (lexicographic): P1=%s  P2=%s" % (fl1, fl2))
lines.append("a2a3 legal in P1? %s   in P2? %s" % ("a2a3" in uci_list(P1), "a2a3" in uci_list(P2)))
lines.append("P1 side to move: %s ; P2 side to move: %s"
             % (chess.Board(P1).turn, chess.Board(P2).turn))
lines.append("")

# A: only the position, immediate quit
bests, infos = run("A_only_P1", ["position fen " + P1, "isready", "go depth 12"])
lines.append("A. position P1 + go depth 12 + quit immediately:")
lines.append("   info depth lines %d ; bestmove(s) %s" % (infos, bests))
lines.append("   H1 (first legal of P1) predicts %s ; H2 predicts (none, no prior search) ; H3 predicts a2a3" % fl1)

# B needs the FIRST search to actually COMPLETE (so there is a real previous bestmove), and only the second
# to be aborted. A blind pipe would abort both, so this case uses a driver that waits for the first bestmove.
def run_B():
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        proc.stdin.write(l + "\n")
        proc.stdin.flush()

    def readto(pred):
        got = []
        while True:
            line = proc.stdout.readline()
            if not line:
                return got
            got.append(line.rstrip("\n"))
            if pred(line):
                return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    send("position fen " + START)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("go depth 10")
    first_block = readto(lambda l: l.startswith("bestmove"))
    first_best = [l for l in first_block if l.startswith("bestmove")]
    # now the second position, and quit IMMEDIATELY after go -- the 19-F12 trigger
    send("position fen " + P1)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("go depth 12")
    send("quit")
    rest = []
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            rest.append(line.rstrip("\n"))
    except Exception:  # noqa: BLE001
        pass
    proc.kill()
    second = [l for l in rest if l.startswith("bestmove")]
    infos = len([l for l in rest if l.startswith("info depth")])
    with open(os.path.join(outdir, "B_search_then_P1.txt"), "w") as fh:
        fh.write("previous completed search bestmove: %s\n" % (first_best[-1] if first_best else "(none)"))
        fh.write("aborted second search: %d info depth lines, bestmove(s) %s\n" % (infos, second))
        fh.write("\nsecond-search output:\n" + "\n".join(rest))
    return (first_best[-1] if first_best else None), second, infos


prev_best, bests_b, infos_b = run_B()
lines.append("")
lines.append("B. completed startpos search, then P1, then go depth 12 + quit immediately:")
lines.append("   previous completed bestmove: %s" % prev_best)
lines.append("   aborted second search: %d info depth lines ; bestmove(s) %s" % (infos_b, bests_b))
lines.append("   if the aborted answer equals the PREVIOUS bestmove, that is H2 (stale)")
lines.append("   if it equals P1's first legal move (%s), that is H1" % fl1)

# C: two positions, each its own process
bests1, i1 = run("C_P1_alone", ["position fen " + P1, "isready", "go depth 12"])
bests2, i2 = run("C_P2_alone", ["position fen " + P2, "isready", "go depth 12"])
lines.append("")
lines.append("C. P1 and P2 each alone in a fresh process, aborted:")
lines.append("   P1 -> %s (python first legal %s)" % (bests1, fl1))
lines.append("   P2 -> %s (python first legal %s)" % (bests2, fl2))
lines.append("   H1 predicts these DIFFER and match the python first-legal moves; H3 predicts a2a3 twice")

text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
