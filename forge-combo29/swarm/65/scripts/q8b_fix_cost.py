#!/usr/bin/env python3
"""Q8b: the cost of the naive `game_ply` fix, so the owner can choose.

`game_ply = history_size() - 1` removes the metadata dependence, but a bare
`position fen ...` carries no history, so that derivation returns 0 for *every*
FEN. The book then becomes eligible on any position that happens to be in it,
however deep the game actually is.

That is a real behaviour change in the opposite direction, and it is the number the
owner needs before picking a fix. This measures it:

  A. take book positions at true ply 20/30/40, load each as a bare FEN,
     and ask both builds whether they book at a generous Book Depth;
  B. the same positions reached by playing the moves from startpos, so the
     history is present, and confirm both builds agree there.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def probe(binary: str, position: str, depth: int = 100) -> tuple[bool, str | None]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", "0")
        eng.setoption("Book Depth", str(depth))
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=30.0)
        best = reply.bestmove_lines()
        move, _ = parse_bestmove(best[0]) if best else (None, None)
        return any("book move" in ln for ln in reply.lines), move
    finally:
        eng.quit()


def main() -> int:
    lock = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build65/forge"
    fixed = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fixbuild/forge"
    tsv = sys.argv[3] if len(sys.argv) > 3 else "/tmp/book_full.txt"

    rows = parse_probe(Path(tsv))
    by_ply: dict[int, list[str]] = {}
    for fen, _key, ply, mv in rows:
        if mv:
            by_ply.setdefault(ply, []).append(fen)

    print(f"lock build:  {lock}")
    print(f"fixed build: {fixed}")
    print()
    print("The book walk only reaches ply 16, so those are the depths available.")
    print("Book Depth is set to the position's true ply, so the lock refuses it")
    print("(game_ply < book_depth is false) while the naive fix allows it (0 < depth).")
    print()
    print("A. bare `position fen` for book positions at a known true ply")
    print("| true ply | Book Depth | positions | lock books | fixed books |")
    print("| ---: | ---: | ---: | ---: | ---: |")
    for ply in (10, 14, 16):
        fens = by_ply.get(ply, [])[:12]
        if not fens:
            continue
        lock_yes = 0
        fixed_yes = 0
        for fen in fens:
            l, _ = probe(lock, f"fen {fen}", depth=ply)
            f, _ = probe(fixed, f"fen {fen}", depth=ply)
            lock_yes += 1 if l else 0
            fixed_yes += 1 if f else 0
        print(f"| {ply} | {ply} | {len(fens)} | {lock_yes}/{len(fens)} | {fixed_yes}/{len(fens)} |")

    print()
    print("B. the same positions reached by playing moves (history present)")
    print("| true ply | Book Depth | lock books | fixed books | agree |")
    print("| ---: | ---: | ---: | ---: | --- |")

    def norm_key(board: chess.Board) -> str:
        ep = "-" if not any(board.is_en_passant(m) for m in board.legal_moves) else chess.square_name(board.ep_square)
        parts = board.fen().split()
        parts[3] = ep
        return " ".join(parts)

    line_by_key: dict[str, str] = {}
    for fen, _k, _p, mv in rows:
        if mv:
            line_by_key[norm_key(chess.Board(fen))] = mv.split(",")[0].split(":")[0]

    for target in (10, 14, 16):
        replay = []
        b = chess.Board()
        for _ in range(target):
            u = line_by_key.get(norm_key(b))
            if not u:
                break
            replay.append(u)
            b.push(chess.Move.from_uci(u))
        if len(replay) != target:
            print(f"| {target} | {target} | line too short ({len(replay)}) | - | - |")
            continue
        command = "startpos moves " + " ".join(replay)
        l, _ = probe(lock, command, depth=target)
        f, _ = probe(fixed, command, depth=target)
        print(f"| {target} | {target} | {'YES' if l else 'no (refused)'} | "
              f"{'YES' if f else 'no (refused)'} | {'yes' if l == f else 'NO'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
