#!/usr/bin/env python3
"""check_21f2.py — seat 28's INDEPENDENT check of seat 21's S-F2.

Claim restated from its sentence alone (no file of seat 21 is read by this script):
  "A refused `position fen` silently leaves the PREVIOUS position on the board and still answers
   `readyok`; a GUI that trusts readyok then searches and plays a move in the wrong game. Every refusal
   kind shows it (bad castling rights, 3 fields, pure garbage); 8902 after startpos in all four cases."

Design: put startpos on the board, send a refused FEN, then `go perft 3`. Startpos perft 3 is 8,902, so
the number alone says which board was searched. Every case records: the refusal line(s), whether
readyok came, the perft result, and a `bestmove` search on the stale board judged legal by python-chess.
CONTROL (P6): a LEGAL FEN right after a refusal must give that FEN's own perft, which proves the harness
can see the board change.

Also asks whether the engine has a `d` (display) command, so the stale board can be observed directly.

Usage: check_21f2.py EXE OUT.tsv
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

STARTPOS_PERFT3 = 8902
# Three refusal kinds, each of a different class.
REFUSALS = [
    ("bad castling right", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"),
    ("three fields", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"),
    ("pure garbage", "this is not a fen at all"),
]
# A legal non-startpos position for the control, whose perft 3 is computed here by python-chess.
CONTROL_FEN = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"


def py_perft(board, depth):
    if depth == 0:
        return 1
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += py_perft(board, depth - 1)
        board.pop()
    return total


def session(exe, steps):
    """Run a list of (command, wait_token). `isready` is appended after every step except a search.

    The original version waited for the token each step names, but a step like ("ucinewgame",
    "readyok") asks for a token ucinewgame never prints — the session blocked until the caller's
    timeout. That is exactly seat 19's warning (a parser waiting for a line the engine never prints).
    Now every non-search step is followed by `isready` and we wait for readyok, so the wait token is
    always one the engine really sends.
    """
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        _l, ok = eng.read_until("readyok", 20)
        if not ok:
            raise SystemExit(f"no readyok after setoption {opt}")
    lines_all = []
    for cmd, token in steps:
        eng.send(cmd)
        if token in ("nodes", "bestmove"):
            out, ok = eng.read_until(token, 90)
        else:
            eng.send("isready")
            out, ok = eng.read_until("readyok", 20)
        lines_all.extend(out)
        if not ok:
            raise SystemExit(f"no `{token}` after `{cmd}` — refusing to continue silently")
    eng.close()
    return lines_all


def main() -> int:
    exe, out = sys.argv[1], sys.argv[2]
    control_perft = py_perft(chess.Board(CONTROL_FEN), 3)
    print(f"python-chess perft 3 of the CONTROL FEN ({CONTROL_FEN}) = {control_perft}")
    print(f"startpos perft 3 = {STARTPOS_PERFT3} (the brief's known number)")
    print()

    rows = []
    print("| case | refusal lines seen | readyok after refusal | perft 3 result | board searched | bestmove on stale board | that bestmove legal in startpos |")
    print("|---|---|---|---|---|---|---|")
    for name, fen in REFUSALS:
        steps = [("ucinewgame", "readyok"),
                 ("position startpos", "readyok"),
                 ("position fen " + fen, "readyok"),
                 ("go perft 3", "nodes"),
                 ("position startpos", "readyok"),
                 ("position fen " + fen, "readyok"),
                 ("go depth 4", "bestmove")]
        lines = session(exe, steps)
        refusals = [l for l in lines if "invalid FEN" in l or "invalid" in l.lower() and "info string" in l]
        nodes = ""
        for i, l in enumerate(lines):
            if l.startswith("nodes "):
                nodes = l.split()[-1]
        best = ""
        for l in lines:
            if l.startswith("bestmove"):
                p = l.split()
                best = p[1] if len(p) > 1 else ""
        legal = "n/a"
        if best and best != "0000":
            try:
                legal = str(chess.Move.from_uci(best) in chess.Board().legal_moves)
            except ValueError:
                legal = "unparsable"
        board_searched = ("startpos (STALE)" if nodes == str(STARTPOS_PERFT3) else
                          ("the refused FEN" if nodes == "" else "something else"))
        print(f"| {name} | {len(refusals)}: {' / '.join(r[:60] for r in refusals) or 'NONE'} | "
              f"yes | {nodes} | {board_searched} | {best} | {legal} |")
        rows.append((name, refusals, nodes, board_searched, best, legal))

    # CONTROL: a legal FEN after a refusal must be the board searched.
    steps = [("ucinewgame", "readyok"),
             ("position startpos", "readyok"),
             ("position fen " + REFUSALS[0][1], "readyok"),
             ("position fen " + CONTROL_FEN, "readyok"),
             ("go perft 3", "Nodes searched")]
    lines = session(exe, steps)
    nodes = ""
    for l in lines:
        if l.startswith("nodes "):
            nodes = l.split()[-1]
    print(f"| CONTROL: legal FEN after a refusal | - | yes | {nodes} | "
          f"{'the control FEN (GOOD)' if nodes == str(control_perft) else 'WRONG'} | - | - |")
    rows.append(("CONTROL", [], nodes, "control" if nodes == str(control_perft) else "wrong", "", ""))

    # Is there a display command? `d` prints a board; a following `isready` is what produces readyok.
    lines = session(exe, [("ucinewgame", "readyok"), ("position startpos", "readyok"),
                          ("d", "readyok"), ("isready", "readyok")])
    display = [l for l in lines if l.startswith("|") or " a b c d" in l or "+---+---+" in l]
    print()
    print(f"`d` command produces a board diagram: {bool(display)} "
          f"({len(display)} diagram lines)")

    with open(out, "w") as fh:
        fh.write("case\trefusal_lines\tnodes\tboard_searched\tbestmove\tlegal\n")
        for r in rows:
            fh.write(f"{r[0]}\t{len(r[1])}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\n")
        fh.write(f"control_py_perft3\t-\t{control_perft}\t-\t-\t-\n")
        fh.write(f"display_command_diagram\t{bool(display)}\t{len(display)}\t-\t-\t-\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
