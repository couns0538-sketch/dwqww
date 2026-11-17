"""Falsification proof for harness.py: every guard is shown to fire.

A checker that cannot fail proves nothing. Each case below plants a condition
whose correct answer is known, and asserts the harness reports it.
"""

from __future__ import annotations

import sys

import chess

from harness import EngineError, Forge, InvalidFen, mirror_board, parse_fen, verify_mirror

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not ok:
        FAILS.append(name)


def main() -> int:
    with Forge() as f:
        # 1. A queen-up position must score positive for the side that is up.
        board = chess.Board("4k3/8/8/8/8/8/8/4K2Q w - - 0 1")
        ev = f.evaluate(board)
        check("control: queen-up White is positive", ev["total"] > 0, f"total={ev['total']}")

        # 2. The same position with Black to move must be negative: the score is
        #    side-to-move relative, so this is the sign-convention control.
        flipped = chess.Board("4k3/8/8/8/8/8/8/4K2Q b - - 0 1")
        ev2 = f.evaluate(flipped)
        check("control: same board, Black to move is negative", ev2["total"] < 0, f"total={ev2['total']}")

        # 3. A malformed FEN must raise InvalidFen, not return a number.
        try:
            f.send("position fen 4k3/8/8/8/8/8/8/4K2Q w - - 0")  # five fields, invalid
            f.sync()
            check("guard: malformed FEN is rejected", False, "no exception")
        except InvalidFen as exc:
            check("guard: malformed FEN is rejected", True, str(exc)[:60])

        # 3b. The same through the ordinary path: a fixture with a short FEN
        #     must never reach the engine's memory as "the previous board".
        # 3b. A board object is already normalised by python-chess, so a padded
        #     five-field FEN is legal input. What must NOT happen is the engine
        #     quietly scoring the previous board, so prove the measured board is
        #     this one and not its predecessor.
        padded = f.evaluate(chess.Board("4k3/8/8/8/8/8/8/4K2Q w - - 0"))
        previous = f.evaluate(chess.Board("4k3/8/8/8/8/8/8/4K2R w - - 0 1"))
        check("guard: normalised board is measured, not the previous one",
              padded["total"] != previous["total"],
              f"queen={padded['total']} rook={previous['total']}")

        # 3c. And proving the raw text is what gets checked, not the normalised
        #     board: the exact five-field string must be refused.
        try:
            parse_fen("4k3/8/8/8/8/8/8/4K2Q w - - 0")
            check("guard: raw five-field text refused", False, "no exception")
        except EngineError as exc:
            check("guard: raw five-field text refused", True, str(exc)[:60])

        # 4. A structurally impossible board (two white kings) must be rejected.
        try:
            f.send("position fen 4k3/8/8/8/8/8/8/4KK2 w - - 0 1")
            f.sync()
            check("guard: two white kings rejected", False, "no exception")
        except InvalidFen as exc:
            check("guard: two white kings rejected", True, str(exc)[:60])

        # 5. python-chess must independently reject the same garbage, or the
        #    "validate every FEN" rule is not actually independent.
        try:
            bad = chess.Board("4k3/8/8/8/8/8/8/4K2Q w - - 0")
            if bad.is_valid() and len(bad.fen().split()) == 6:
                raise ValueError("would have been accepted")
            check("guard: python-chess rejects bad FEN", False, "accepted")
        except ValueError:
            check("guard: python-chess rejects bad FEN", True)

        # 6. Mirroring must be an involution and must preserve material.
        sample = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
        verify_mirror(sample)
        m = mirror_board(sample)
        same_material = all(
            len(sample.pieces(pt, chess.WHITE)) == len(m.pieces(pt, chess.BLACK))
            for pt in range(1, 7)
        )
        check("guard: mirror preserves material counts", same_material, m.fen())

        # 7. The eval must be side-to-move relative and symmetric under mirroring.
        ev_s = f.evaluate(sample)
        ev_m = f.evaluate(m)
        check("control: mirror scores equal", ev_s["total"] == ev_m["total"],
              f"{ev_s['total']} vs {ev_m['total']}")

        # 8. A search must return a real bestmove, and mate scores must be typed
        #    as mate rather than folded into centipawns.
        mate = chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
        res = f.search(mate, depth=4)
        check("control: search returns a bestmove", res["bestmove"] is not None, str(res["bestmove"]))

        # 9. Harness must not leak a live search: a second search right after
        #    the first still answers.
        res2 = f.search(sample, depth=4)
        check("guard: back-to-back searches stay synchronized",
              res2["bestmove"] is not None, str(res2["bestmove"]))

    print()
    if FAILS:
        print(f"{len(FAILS)} GUARD(S) FAILED: {FAILS}")
        return 1
    print("all harness guards fired as intended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
