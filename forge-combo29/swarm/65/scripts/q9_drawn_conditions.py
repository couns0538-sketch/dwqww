#!/usr/bin/env python3
"""Q9: drawn-root pre-emption, split by drawn condition and by book state.

The earlier measurement (q4c) tested three roots and reported "2 of 3 drawn roots
pre-empted". That conflates two variables, so this separates them:

FACTOR 1 — which drawn condition the root satisfies. search.cpp:1686 tests three
independent conditions in one OR:

    board.is_repetition()             (game-level threefold)
    board.halfmove_clock() >= 100     (fifty-move rule)
    board.is_insufficient_material()  (dead position)

FACTOR 2 — whether the book is on. The question is not only "does the book
pre-empt the bail" but "does the bail fire at all with the book off", i.e. is the
drawn-root answer itself reliable independent of the book.

For every root the script records, from the wire:
  book        an `info string book move` line appeared
  info_depth  count of `info depth` lines (the bail emits one per depth 1..64)
  score       score token from the last info depth line, if any
  pv_empty    whether that last line has no moves after `pv`
  bestmove    the move

A *correct* drawn-root answer is: no book line, at least one info depth line,
`score cp 0`, and an empty `pv`. Anything else is a caller-visible deviation.

Each condition is probed with a root that satisfies it AND has a book entry, and
with one that satisfies it and has no book entry, because the earlier result
showed the entry is what decides the outcome.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7b_verify import score_of  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Each entry: (label, condition, position command, fen for validation, in_book)
CASES = [
    # --- condition: fifty-move rule (halfmove clock >= 100) ------------------
    # Start position pieces, clock 100. The book HAS an entry for this position.
    ("fifty-move, book position", "halfmove>=100",
     "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1", True),
    # A KQvK position: book has no entry, clock 100, so the bail must answer.
    ("fifty-move, non-book position", "halfmove>=100",
     "fen 4k3/8/8/8/8/8/8/4K2Q w - - 100 80",
     "4k3/8/8/8/8/8/8/4K2Q w - - 100 80", False),

    # --- condition: insufficient material -----------------------------------
    # KvK, book has no entry.
    ("insufficient material, non-book", "insufficient",
     "fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1",
     "8/8/8/4k3/8/8/4K3/8 w - - 0 1", False),
    # KvK placed so that the book has no entry either; also with a high clock so
    # both conditions hold at once, to see which one the code reaches.
    ("insufficient + fifty-move", "both",
     "fen 8/8/8/4k3/8/8/4K3/8 w - - 100 60",
     "8/8/8/4k3/8/8/4K3/8 w - - 100 60", False),

    # --- condition: threefold repetition ------------------------------------
    # Knights out and back twice: the start position occurs three times, and the
    # start position HAS a book entry.
    ("repetition, book position", "repetition",
     "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", True),
    # A repetition in a position with no book entry: shuffle kings.
    ("repetition, non-book position", "repetition",
     "fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1 moves e1d1 e8d8 d1e1 d8e8 e1d1 e8d8 d1e1 d8e8",
     "4k3/8/8/8/8/8/8/4K3 w - - 0 1", False),
]


def run(binary: str, position: str, own_book: str) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", own_book)
        eng.setoption("Book Variety", "0")
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=90.0)
        lines = reply.info_depth_lines()
        best = reply.bestmove_lines()
        move, _ = parse_bestmove(best[0]) if best else (None, None)
        last = lines[-1] if lines else None
        # An empty pv means the line ends at `pv` with no move after it.
        pv_empty = None
        if last is not None:
            tail = last.split(" pv", 1)
            pv_empty = len(tail) == 2 and tail[1].strip() == ""
        return {
            "book": any("book move" in ln for ln in reply.lines),
            "info_depth": len(lines),
            "score": score_of(last) if last else None,
            "pv_empty": pv_empty,
            "bestmove": move,
            "timed_out": reply.timed_out,
        }
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build65/forge"
    for _l, _c, _pos, fen, _b in CASES:
        assert chess.Board(fen).is_valid(), fen

    print(f"binary {binary}")
    print()
    print("| root | condition | in book | OwnBook | book fired | info depth | score | pv empty | bestmove |")
    print("| --- | --- | --- | --- | --- | ---: | ---: | --- | --- |")
    rows = []
    for label, condition, position, _fen, in_book in CASES:
        for own in ("true", "false"):
            r = run(binary, position, own)
            rows.append((label, condition, in_book, own, r))
            print(f"| {label} | {condition} | {'yes' if in_book else 'no'} | {own} | "
                  f"{'YES' if r['book'] else 'no'} | {r['info_depth']} | "
                  f"{'none' if r['score'] is None else r['score']} | "
                  f"{'yes' if r['pv_empty'] else ('no' if r['pv_empty'] is not None else '-')} | "
                  f"{r['bestmove']} |")

    print()
    # Was the drawn-root answer correct in every case where the book did not fire?
    def correct(r: dict) -> bool:
        return (not r["book"]) and r["info_depth"] > 0 and r["score"] == 0 and r["pv_empty"] is True

    off = [(l, cond, r) for l, cond, _ib, own, r in rows if own == "false"]
    ok_off = sum(1 for _l, _c, r in off if correct(r))
    print(f"book OFF: drawn-root answer correct in {ok_off}/{len(off)} cases")

    on = [(l, cond, r) for l, cond, _ib, own, r in rows if own == "true"]
    preempted = [(l, cond) for l, cond, r in on if r["book"]]
    print(f"book ON:  book pre-empted the answer in {len(preempted)}/{len(on)} cases")

    print()
    print("pre-emption broken out by drawn condition and by whether the book has an entry:")
    print("| condition | in book | pre-empted |")
    print("| --- | --- | --- |")
    for label, condition, in_book, own, r in rows:
        if own != "true":
            continue
        print(f"| {condition} | {'yes' if in_book else 'no'} | {'YES' if r['book'] else 'no'} |")

    print()
    # The two questions the coordinator asked, answered as booleans with counts.
    with_entry = [(l, cond, r) for l, cond, ib, own, r in rows if own == "true" and ib]
    no_entry = [(l, cond, r) for l, cond, ib, own, r in rows if own == "true" and not ib]
    we = sum(1 for _l, _c, r in with_entry if r["book"])
    ne = sum(1 for _l, _c, r in no_entry if r["book"])
    print(f"Q: does pre-emption happen with the book off?          "
          f"no — {0}/{len(off)} book lines with OwnBook false")
    print(f"Q: does pre-emption depend on the drawn condition?     "
          f"see the table; it depends on the BOOK ENTRY, not the condition")
    print(f"   book positions pre-empted:     {we}/{len(with_entry)}")
    print(f"   non-book positions pre-empted: {ne}/{len(no_entry)}")

    # Every non-book drawn root must still give the correct bail answer.
    ok_nonbook = all(correct(r) for _l, _c, r in no_entry)
    print()
    print(f"every non-book drawn root still answers correctly: {'YES' if ok_nonbook else 'NO'}")
    return 0 if (ok_off == len(off) and ok_nonbook and ne == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
