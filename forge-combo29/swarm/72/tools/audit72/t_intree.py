"""Does the search see a repetition that occurs INSIDE the tree?

Method: make the root position the SECOND occurrence of a cycle whose period
is 4 plies.  The third occurrence therefore first appears 4 plies below the
root.  A search that detects repetition only at the root cannot see it before
depth 4; a search that detects it in-tree must drop to 0 as soon as the depth
reaches the third occurrence.

That gives a decisive, mechanism-level A/B on the SAME position:

    depth 3  -> third occurrence not reachable -> expect the material score
    depth 4+ -> third occurrence reachable     -> expect 0

The minimum period of a repetition is 4 plies (positions alternate side to
move), so "three plies deep" in the brief is realised as "ply 4" here; a
3-ply repetition is not constructible.

Every fixture goes through Probe: python-chess validation, both reply streams
scanned for a refusal, and perft-1 agreement.
"""

import chess

from engine import Probe

BASE = "4k3/8/8/8/8/8/8/1R2K3 w - - 0 1"
CYCLE = ["b1b2", "e8d8", "b2b1", "d8e8"]


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


def main():
    moves = CYCLE  # exactly one cycle: root sits on occurrence #2
    board = chess.Board(BASE)
    for m in moves:
        board.push_uci(m)
    occ = occurrences(board)
    assert occ == 2, "fixture must sit on occurrence #2, got %d" % occ
    print("root = occurrence #%d of the cycle; third occurrence is 4 plies below" % occ)
    print("root fen: %s" % board.fen())
    print()

    print("=" * 84)
    print("DEPTH SWEEP on the occurrence-#2 root (material +575 for the mover)")
    print("=" * 84)
    print("%-6s %-12s %-8s %s" % ("depth", "score", "nodes", "reading"))
    rows = []
    for depth in range(1, 8):
        p = Probe(BASE, name="occ2-d%d" % depth, moves=moves)
        try:
            res = p.search("depth %d" % depth)
        finally:
            p.close()
        score = res["score"]
        text = "%s%d" % score if score else "-"
        sees = score == ("cp", 0)
        reading = "draw (in-tree repetition seen)" if sees else "material score"
        rows.append((depth, score, res["nodes"], sees))
        print("%-6d %-12s %-8d %s" % (depth, text, res["nodes"], reading))

    # Decisive assertions.
    fails = []
    shallow = [r for r in rows if r[0] <= 3]
    deep = [r for r in rows if r[0] >= 4]
    if not any(not r[3] for r in shallow):
        fails.append("no shallow depth failed to see the repetition (test not discriminating)")
    if not all(r[3] for r in deep):
        bad = [r[0] for r in deep if not r[3]]
        fails.append("depth(s) %s reached the third occurrence but did not score 0" % bad)

    print()
    if fails:
        print("VERDICT: in-tree repetition NOT reliably detected")
        for f in fails:
            print("  -", f)
    else:
        print("VERDICT: in-tree repetition IS detected -- score falls to 0 exactly")
        print("         when the search depth first reaches the third occurrence.")
    return fails


if __name__ == "__main__":
    main()
