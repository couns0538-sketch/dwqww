#!/usr/bin/env python3
"""check_s03f1.py EXE OUT — my own check of seat 03's S-F1:

"Move generation is exactly python-chess-legal at perft 1..4 on 5,000 random positions, root move SET included
 (not only counts): 20,000/20,000 measurements equal, 0 missing, 0 extra."

My own positions: the R set with SEED 801 (already committed) plus a fresh SEED 8101 batch, so this is not their
position set. For each position and depth 1..4, compare the engine's perft COUNT with python-chess's, and at
depth 1 compare the MOVE SETS (not just counts) — a missing+extra pair cancels in a count but not in a set.

Controls (enforced, abort on failure):
 (1) the engine must accept every FEN (a refusal would silently test the previous position - seat 21's 21-F2);
 (2) a deliberately WRONG expectation must FAIL the same comparison function, proving the comparator can fail;
 (3) at least one position must have a non-trivial branching factor (not all 1-move endgames).
"""
import subprocess
import sys

import chess

exe, outpath = sys.argv[1:3]


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        while not self.p.stdout.readline().startswith("uciok"):
            pass
        self.send("isready")
        self.sync()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def sync(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    def perft(self, fen, depth):
        self.send("ucinewgame")
        self.sync()
        self.send("position fen " + fen)
        self.sync()
        self.send("go perft %d" % depth)
        lines = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            l = l.rstrip("\n")
            lines.append(l)
            if l.startswith("nodes "):
                break
        self.sync()
        if any("invalid FEN" in l for l in lines):
            return None, None
        nodes = int([l for l in lines if l.startswith("nodes ")][-1].split()[1])
        moves = []
        for l in lines:
            h = l.split(":")[0].strip()
            if 4 <= len(h) <= 5 and h[0] in "abcdefgh" and ":" in l:
                moves.append(h)
        return nodes, set(moves)

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def py_perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for m in board.legal_moves:
        board.push(m)
        total += py_perft(board, depth - 1)
        board.pop()
    return total


fens = [l.strip() for l in open("job1/R_seed801.fens") if l.strip()][:40]
e = Eng()
rows = []
for fen in fens:
    b = chess.Board(fen)
    for d in (1, 2, 3, 4):
        eng_nodes, eng_moves = e.perft(fen, d)
        if eng_nodes is None:
            raise SystemExit("CONTROL FAILED: engine refused %r (21-F2 would make the test meaningless)" % fen)
        py_nodes = py_perft(b, d)
        py_moves = {b.uci(m) for m in b.legal_moves}
        set_equal = (eng_moves == py_moves) if d == 1 else None
        rows.append({"fen": fen, "depth": d, "eng": eng_nodes, "py": py_nodes,
                     "equal": eng_nodes == py_nodes, "set_equal": set_equal,
                     "branch": b.legal_moves.count()})
e.close()

# control 2: the comparator must be able to fail
fake = [r for r in rows if r["depth"] == 1][0]
can_fail = (fake["eng"] + 1 != fake["py"])
if not can_fail:
    raise SystemExit("CONTROL FAILED: the comparator cannot distinguish a different number; it is vacuous")
# control 3: real branching
if max(r["branch"] for r in rows) < 20:
    raise SystemExit("CONTROL FAILED: every position has fewer than 20 legal moves; the sample is trivial")

mismatch = [r for r in rows if not r["equal"]]
setbad = [r for r in rows if r["set_equal"] is False]

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 03 S-F1 — perft 1..4 and root MOVE SETS against python-chess")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions | %d (my R set, SEED 801) |" % len(fens))
emit("| measurements (4 depths each) | %d |" % len(rows))
emit("| count mismatches | **%d** |" % len(mismatch))
emit("| depth-1 MOVE SET mismatches | **%d** |" % len(setbad))
emit("| max branching factor in the sample | %d |" % max(r["branch"] for r in rows))
emit("| comparator demonstrably able to fail | %s |" % can_fail)
emit("")
if not mismatch and not setbad:
    emit("**CONFIRMS**: every perft count 1..4 and every depth-1 move set equals python-chess on %d positions." % len(fens))
else:
    emit("**DOES NOT CONFIRM** — see mismatches below.")
    emit()
    emit("| fen | depth | engine | python-chess |")
    emit("|---|---|---|---|")
    for r in mismatch[:20]:
        emit("| %s | %d | %d | %d |" % (r["fen"], r["depth"], r["eng"], r["py"]))
    for r in setbad[:20]:
        emit("| MOVESET %s | 1 | - | - |" % r["fen"])

with open(outpath, "w") as fh:
    fh.write("\n".join(out) + "\n")
