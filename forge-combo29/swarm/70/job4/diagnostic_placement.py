"""Job 4 part A: where does `info string invalid FEN` land, and what does an
unusable searchmoves list do?

Three probe arms, each on a fresh process:
  A1  position fen <bad>  + isready            -> diagnostic must be in the POSITION reply
  A2  position fen <bad>  (no isready)         -> diagnostic must be in the GO output
  A3  good position, illegal move in searchmoves
Run:  python3 job4/diagnostic_placement.py
Writes job4/diagnostic_placement.txt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

GOOD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BAD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"  # no rook on h1


def raw(label, lines):
    return [f"--- {label} ---"] + list(lines)


def main():
    out = []
    out.append(f"engine: {engine.ENGINE}")

    # A1: isready between position and go
    r = engine.run_session(f"position fen {BAD}", "go depth 4", options=[])
    out += raw("A1 position reply (bad FEN, isready after position)", r.raw_position.split("\n"))
    out.append(f"A1 position has 'invalid FEN': {'invalid FEN' in r.raw_position}")
    out.append(f"A1 go output  has 'invalid FEN': {'invalid FEN' in r.raw_go}")
    out.append(f"A1 fatal: {r.fatal}")

    # A3: illegal move inside searchmoves on a legal board
    r = engine.run_session(f"position fen {GOOD}", "go depth 4 searchmoves e2e5", options=[])
    out += raw("A3 go output (searchmoves e2e5 illegal)", r.raw_go.split("\n"))
    out.append(f"A3 bestmove: {r.bestmove}  score: {r.score_kind} {r.score}  fatal: {r.fatal}")

    # A4: legal and illegal together
    r = engine.run_session(f"position fen {GOOD}", "go depth 8 searchmoves e2e4 e2e5", options=[])
    out += raw("A4 go output (searchmoves e2e4 e2e5)", r.raw_go.split("\n"))
    out.append(f"A4 bestmove: {r.bestmove}  score: {r.score_kind} {r.score}  fatal: {r.fatal}")

    # A5: illegal only, two of them
    r = engine.run_session(f"position fen {GOOD}", "go depth 4 searchmoves e2e5 d2d5", options=[])
    out += raw("A5 go output (two illegal)", r.raw_go.split("\n"))
    out.append(f"A5 bestmove: {r.bestmove}  fatal: {r.fatal}")

    # A6: bare searchmoves, nothing after it
    r = engine.run_session(f"position fen {GOOD}", "go depth 6 searchmoves", options=[])
    out += raw("A6 go output (bare searchmoves)", r.raw_go.split("\n"))
    out.append(f"A6 bestmove: {r.bestmove}  score: {r.score_kind} {r.score}")

    # A7: baseline for A6 comparison
    r6 = engine.run_session(f"position fen {GOOD}", "go depth 6", options=[])
    out.append(f"A7 unrestricted depth 6 bestmove: {r6.bestmove} score {r6.score_kind} {r6.score}")

    text = "\n".join(out)
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "diagnostic_placement.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
