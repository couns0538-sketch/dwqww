#!/usr/bin/env python3
"""Q8c: where the `game_ply` defect actually bites, and what each fix does.

Key realisation from measuring: a bare `position fen` carries NO move history, so
the counter is the only depth information that exists. No derivation can recover a
true ply there — trusting the counter is not a bug when the counter is all there is.
The defect is narrower and sharper than that:

  `position fen <FEN> moves <m1> <m2> ...`

gives the board a real history AND a caller-supplied counter, and nothing forces
the two to agree. That is the case where a corrected derivation changes behaviour,
and it is testable.

Three derivations, compared on four scenarios:

  LOCK   `2*(fullmove-1) + (black?1:0)`
  NAIVE  `history_size() - 1`                      (0 when there is no history)
  HYBRID `history_size() > 1 ? history-1 : counter`

  S1  real book line via `startpos moves`, book data present — all must book
  S2  real book line via `startpos moves`, past Book Depth — none may book
  S3  `fen <honest> moves ...` (history and counter agree) — all must book
  S4  `fen <counter inflated> moves ...` (history and counter disagree) — the
      correct answer is the history's, so LOCK must be wrong here

Exit code 1 if HYBRID does not satisfy all four, so the report's recommendation
cannot drift from the measurement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def probe(binary: str, position: str, depth: int) -> bool:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", "0")
        eng.setoption("Book Depth", str(depth))
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=30.0)
        return any("book move" in ln for ln in reply.lines)
    finally:
        eng.quit()


def norm_key(board: chess.Board) -> str:
    ep = "-" if not any(board.is_en_passant(m) for m in board.legal_moves) else chess.square_name(board.ep_square)
    parts = board.fen().split()
    parts[3] = ep
    return " ".join(parts)


def main() -> int:
    lock = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build65/forge"
    naive = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fixbuild/forge"
    hybrid = sys.argv[3] if len(sys.argv) > 3 else "/tmp/fix2build/forge"
    tsv = sys.argv[4] if len(sys.argv) > 4 else "/tmp/book_full.txt"

    builds = [("LOCK", lock), ("NAIVE", naive), ("HYBRID", hybrid)]
    rows = parse_probe(Path(tsv))
    line_by_key: dict[str, str] = {}
    for fen, _k, _ply, mv in rows:
        if mv:
            line_by_key[norm_key(chess.Board(fen))] = mv.split(",")[0].split(":")[0]

    def replay(n: int) -> tuple[list[str], chess.Board]:
        moves, b = [], chess.Board()
        for _ in range(n):
            u = line_by_key.get(norm_key(b))
            if not u:
                break
            moves.append(u)
            b.push(chess.Move.from_uci(u))
        return moves, b

    results: dict[str, dict[str, bool]] = {name: {} for name, _ in builds}

    # ---- S1/S2: startpos moves, data present / past depth -------------------
    print("S1  real book line via `startpos moves`, Book Depth 10 (data present)")
    m6, _ = replay(6)
    s1 = "startpos moves " + " ".join(m6)
    for name, binary in builds:
        results[name]["S1"] = probe(binary, s1, 10)
        print(f"    {name:<7} books: {'YES' if results[name]['S1'] else 'no'}")
    print()

    print("S2  real book line via `startpos moves`, Book Depth 6 (ply 6 is past it)")
    for name, binary in builds:
        results[name]["S2"] = probe(binary, s1, 6)
        print(f"    {name:<7} books: {'YES' if results[name]['S2'] else 'no (correct)'}")
    print()

    # ---- S3: fen + moves, counter honest ------------------------------------
    # Take the position after 4 plies, write it as a FEN with its true counter,
    # then supply the remaining 2 moves. History (4+2) and counter (6) agree.
    m4, b4 = replay(4)
    honest_fen = b4.fen()
    tail = m6[4:]
    s3 = f"fen {honest_fen} moves " + " ".join(tail)
    print(f"S3  `fen` + `moves`, counter honest (counter ply 4, history 4+{len(tail)})")
    print(f"    {honest_fen}")
    for name, binary in builds:
        results[name]["S3"] = probe(binary, s3, 10)
        print(f"    {name:<7} books: {'YES' if results[name]['S3'] else 'no'}")
    print()

    # ---- S4: fen + moves, counter inflated ---------------------------------
    parts = honest_fen.split()
    parts[5] = str(int(parts[5]) + 20)  # +20 fullmoves -> +40 plies in the counter
    inflated_fen = " ".join(parts)
    s4 = f"fen {inflated_fen} moves " + " ".join(tail)
    print("S4  `fen` + `moves`, counter inflated by 40 plies (history still 6)")
    print(f"    {inflated_fen}")
    print("    true depth is 6, so Book Depth 10 must allow the book.")
    for name, binary in builds:
        results[name]["S4"] = probe(binary, s4, 10)
        print(f"    {name:<7} books: {'YES' if results[name]['S4'] else 'no (WRONG)'}")
    print()

    print("| scenario | LOCK | NAIVE | HYBRID | correct answer |")
    print("| --- | --- | --- | --- | --- |")
    answers = {"S1": "book", "S2": "do not book", "S3": "book", "S4": "book"}
    for s in ("S1", "S2", "S3", "S4"):
        cells = " | ".join("book" if results[n][s] else "no book" for n, _ in builds)
        print(f"| {s} | {cells} | {answers[s]} |")

    print()
    print("S5  bare `position fen` at true ply 14, honest counter, Book Depth 4.")
    print("    No history exists, so the counter is the only depth information;")
    print("    the position is past Book Depth 4 and must not book. This is the")
    print("    scenario that separates NAIVE from HYBRID.")
    deep = [f for f, _k, p, mv in rows if p == 14 and mv][:8]
    print(f"    positions: {len(deep)}")
    for name, binary in builds:
        yes = sum(1 for fen in deep if probe(binary, f"fen {fen}", 4))
        # Store "does it book", the same quantity as every other scenario, so the
        # summary table means one thing throughout.
        results[name]["S5"] = yes > 0
        print(f"    {name:<7} booked {yes}/{len(deep)} "
              f"({'correct' if yes == 0 else 'WRONG: past Book Depth'})")

    print()
    print("| scenario | LOCK | NAIVE | HYBRID | correct answer |")
    print("| --- | --- | --- | --- | --- |")
    answers = {"S1": "book", "S2": "do not book", "S3": "book", "S4": "book", "S5": "do not book"}
    for s in ("S1", "S2", "S3", "S4", "S5"):
        cells = " | ".join("book" if results[n][s] else "no book" for n, _ in builds)
        print(f"| {s} | {cells} | {answers[s]} |")

    print()
    expect = {"S1": True, "S2": False, "S3": True, "S4": True, "S5": False}
    for name, _ in builds:
        wrong = [s for s, want in expect.items() if results[name][s] != want]
        print(f"{name:<7} wrong on {len(wrong)}/{len(expect)}: "
              f"{', '.join(wrong) if wrong else 'none'}")

    ok = all(results["HYBRID"][s] == expect[s] for s in expect)
    print()
    print(f"HYBRID is correct on all {len(expect)} scenarios: {'YES' if ok else 'NO'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
