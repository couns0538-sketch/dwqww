"""Does the trap-2 patch (drawn root before book) close the route §9 found?

The route: a book position can recur after leaving the book (the book's own last
move can be undone by a 3-ply shuffle), and at the third occurrence the book fired
on a genuine threefold root -- trap 19a reached in real play, on the lock build.

Trap 2 adds `!root_drawn` to the book gate. If it works, the same POSITION on the
trap-2 build must show the SEARCH answering instead of the book: the drawn-root
bail's signature, a `cp 0 / nodes 0` score with an empty pv, and NO
`info string book move`.

DESIGN: the positions are frozen once, built with python-chess from the lock's own
book sequence, and then BOTH builds are asked at exactly those move lists. Letting
each build drive its own continuation would let the sequence diverge at the first
non-book reply and the two columns would no longer compare the same thing -- the
first version of this script did exactly that and crashed on an illegal move when
the trap-2 build declined to book.

The gate is deliberately NOT "the trap-2 build must show the signature": on a fixed
build the signature's ABSENCE is the expected result. The gate is:

  * the LOCK must show the signature (otherwise there is nothing to fix);
  * the TRAP-2 build must NOT show it;
  * the TRAP-2 build must still book an ordinary position, so the result cannot be
    satisfied merely by the book being removed.
"""

from __future__ import annotations

import json
import sys

import chess

from forge_uci import Engine

LINE16 = ("e2e4 c7c5 c2c3 e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1d3 c5c4 "
          "d3c2 b8c6 e1g1 f8e7").split()
CYCLE = ["f3g5", "e7f8", "g5f3"]
BOOK_MOVE = "f8e7"


def ask(engine: Engine, moves: list[str], timeout: float = 30.0) -> dict:
    body = "startpos moves " + " ".join(moves) if moves else "startpos"
    engine.position_checked(body)
    reply = engine.go("wtime 60000 btime 60000", timeout)
    depths = reply.depth_lines()
    last = depths[-1] if depths else ""
    bail = (" nodes 0 " in (" " + last + " ")) and last.rstrip().endswith("pv")
    return {"book": reply.book_move(),
            "best": reply.bestmove(),
            "depth_lines": len(depths),
            "drawn_root_bail": bail,
            "last_depth_line": last[:120]}


def frozen_occurrences() -> list[tuple[int, list[str], bool]]:
    """The three occurrence positions, from the lock's own book sequence."""
    moves = list(LINE16)
    out = []
    for cycle in (1, 2, 3):
        moves.extend(CYCLE)
        probe = chess.Board()
        for m in moves:
            probe.push_uci(m)
        out.append((cycle, list(moves), probe.is_repetition(3)))
        moves.append(BOOK_MOVE)
    return out


def main() -> int:
    lock_path, trap2_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    occ = frozen_occurrences()
    results: dict[str, list] = {"lock": [], "trap2": []}
    controls: dict[str, dict] = {}

    for label, path in (("lock", lock_path), ("trap2", trap2_path)):
        eng = Engine(path)
        try:
            eng.handshake()
            eng.newgame()
            eng.setoption("OwnBook", "true")
            eng.setoption("Book Variety", "0")   # pin the RNG; see q0_rng.py
            controls[label] = ask(eng, ["e2e4"])
            for cycle, moves, threefold in occ:
                r = ask(eng, moves)
                r.update(cycle=cycle, ply=len(moves), threefold=threefold)
                results[label].append(r)
        finally:
            eng.quit()

    def shows_signature(rows) -> bool:
        return any(r["threefold"] and r["book"] is not None and r["depth_lines"] == 0
                   for r in rows)

    def shows_bail(rows) -> bool:
        return any(r["threefold"] and r["book"] is None and r["drawn_root_bail"]
                   for r in rows)

    lock_sig = shows_signature(results["lock"])
    trap2_sig = shows_signature(results["trap2"])
    trap2_bail = shows_bail(results["trap2"])
    trap2_books = controls["trap2"]["book"] is not None

    report = {
        "lock": results["lock"], "trap2": results["trap2"],
        "controls": controls,
        "lock_shows_trap19a_signature": lock_sig,
        "trap2_shows_trap19a_signature": trap2_sig,
        "trap2_shows_drawn_root_bail_instead": trap2_bail,
        "trap2_still_books_an_ordinary_position": trap2_books,
    }
    if not lock_sig:
        report["verdict"] = ("VOID: the lock shows no trap-19a signature on these "
                             "positions, so there is nothing for trap 2 to fix")
        ok = False
    elif trap2_sig:
        report["verdict"] = "TRAP 2 DOES NOT CLOSE THIS ROUTE on these positions"
        ok = False
    elif not trap2_books:
        report["verdict"] = ("INCONCLUSIVE: no signature on the trap-2 build, but it also "
                             "stops booking an ordinary position, so this cannot be told "
                             "apart from the book being disabled")
        ok = False
    else:
        report["verdict"] = (
            "TRAP 2 CLOSES THIS ROUTE on the same positions. On the lock the threefold "
            "occurrence gets a book move with zero depth lines; on the trap-2 build it "
            "gets no book move"
            + (" and the search's drawn-root bail instead (cp 0, nodes 0, empty pv)"
               if trap2_bail else " (the search answers it)")
            + ", while an ordinary book position still books -- so the fix removes the "
            "pre-emption without removing the book."
        )
        ok = True
    json.dump(report, open(out_path, "w"), indent=1)
    for label in ("lock", "trap2"):
        print(f"--- {label} (control books: {controls[label]['book']}) ---")
        for r in results[label]:
            print(f"  cycle {r['cycle']} ply {r['ply']} threefold={r['threefold']!s:5s} "
                  f"book={str(r['book']):6s} best={str(r['best']):6s} "
                  f"depth_lines={r['depth_lines']:3d} bail={r['drawn_root_bail']}")
    print()
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("lock", "trap2", "controls")}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
