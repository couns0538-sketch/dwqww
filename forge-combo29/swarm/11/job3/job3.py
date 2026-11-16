#!/usr/bin/env python3
"""job3.py EXE MOVESFILE OUTDIR — `position startpos moves` cases for area 1 job 3.

Cases: the full 1,000-ply list; one illegal move inserted at ply 1, 10, 500 and after the
list; the brief's known e2e4 e7e5 e1e3; a non-UCI token. For each, `position ... ` + `isready`
(answer lines) then `go perft 1`, compared with python-chess's legal move count at the
LEGAL PREFIX (which is what the brief says the engine must keep).
"""
import os, subprocess, sys, chess

EXE, MOVES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
moves = [l.strip() for l in open(MOVES) if l.strip()]
assert len(moves) == 1000, f"expected 1000 plies, got {len(moves)}"


def run(lines, timeout=180):
    inp = "uci\n" + "".join(l + "\n" for l in lines) + "quit\n"
    p = subprocess.run([EXE], input=inp, capture_output=True, text=True, timeout=timeout)
    return p.stdout, p.stderr


def measure(position_line, prefix_for_py):
    out, err = run([position_line, "isready", "go perft 1"])
    answer, count = [], None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("info string"):
            answer.append(s)
        if s.startswith("nodes "):
            count = int(s.split()[1])
    b = chess.Board()
    for u in prefix_for_py:
        b.push(chess.Move.from_uci(u))
    return answer, count, b.legal_moves.count(), err


def illegal_in(prefix):
    """A UCI-looking but illegal move in the position after `prefix`."""
    b = chess.Board()
    for u in prefix:
        b.push(chess.Move.from_uci(u))
    for cand in ("e1e3", "a1a8", "h1h8", "e8e1", "a8a1", "e1e8"):
        mv = chess.Move.from_uci(cand)
        if mv not in b.legal_moves:
            return cand
    return "zzzz"


rows = []

def add(name, desc, position_line, prefix_for_py):
    answer, eng, py, err = measure(position_line, prefix_for_py)
    rows.append((name, desc, position_line, answer, eng, py, err.strip()))
    print(f"{name:10} engine={eng} py={py} {'EQUAL' if eng == py else '*** DIFFERS ***'} {answer}")

add("full1000", "all 1,000 legal plies",
    "position startpos moves " + " ".join(moves), moves)

for label, k in (("ill@1", 0), ("ill@10", 9), ("ill@500", 499)):
    pref = moves[:k]
    bad = illegal_in(pref)
    line = ("position startpos moves " + " ".join(pref) + (" " if pref else "") + bad)
    add(label, f"illegal {bad} at ply {k+1}, legal prefix {k} plies", line, pref)

bad = illegal_in(moves)
add("ill@end", f"illegal {bad} after the full list",
    "position startpos moves " + " ".join(moves) + " " + bad, moves)

add("known", "the brief's known case e2e4 e7e5 e1e3",
    "position startpos moves e2e4 e7e5 e1e3", ["e2e4", "e7e5"])

add("garbage", "non-UCI token zzzz at ply 6",
    "position startpos moves " + " ".join(moves[:5]) + " zzzz", moves[:5])

with open(f"{OUT}/results.txt", "w") as f:
    for name, desc, line, answer, eng, py, err in rows:
        f.write(f"{name}: {desc}\n")
        f.write(f"  command   : {line if len(line) < 200 else line[:200] + '...'}\n")
        f.write(f"  answer    : {answer}\n")
        f.write(f"  perft1    : engine {eng}  python-chess {py}  {'EQUAL' if eng == py else '*** DIFFERS ***'}\n")
        f.write(f"  stderr    : {err[:400]!r}\n\n")

with open(f"{OUT}/summary.txt", "w") as f:
    f.write(f"exe {EXE}\nmoves file {MOVES} ({len(moves)} plies)\n")
    eq = sum(1 for r in rows if r[4] == r[5])
    f.write(f"cases {len(rows)}, equal {eq}, differing {len(rows)-eq}\n")
    for name, desc, line, answer, eng, py, err in rows:
        f.write(f"{name:10} engine={eng} py={py} {'OK' if eng == py else 'DIFF'} {answer}\n")
print(open(f"{OUT}/summary.txt").read())
