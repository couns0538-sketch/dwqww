#!/usr/bin/env python3
"""Does the HALFMOVE CLOCK survive a long replay?

Perft cannot see the clock, so the position-identity result (perft-visible fields) does not
cover it. This does, and it matters because the drawn-root bail keys on
`halfmove_clock() >= 100`: a clock bug shows up as a VERDICT CHANGE at a specific clock.

THE INSTRUMENT AND WHY IT IS BUILT THIS WAY. The engine exposes no board dump, so the clock is
read through its only observable consequence at the boundary: for a position with a legal move,
  clock < 100  -> searches (nodes > 0)
  clock >= 100 -> bails (0 nodes, empty pv, generator head)
That is a 1-bit read of "is the clock >= 100". Two things make it usable:

  1. EVERY probe runs in a FRESH process. My first version ran both arms in one warm engine and
     the A/A control caught it: 195/200 "disagreements" against itself, because a repeat search
     on a warm table returns 0 nodes and the hash move (trap 2d0) -- indistinguishable on the
     wire from a bail. The A/A control is what stopped that from becoming a reported finding.

  2. Only positions where the repetition and insufficient-material arms CANNOT fire are probed
     (occurrence count < 3, and not insufficient material). Otherwise a bare-FEN arm legitimately
     does not bail where the move-list arm does, and the difference is repetition history, not
     the clock.

Measurements:
  C. boundary sweep: one board at clock 0..102, proving the boundary sits exactly at 100.
  A. A/A control: the same probe twice, fresh processes, nothing between.
  B. clock agreement at every eligible ply of the 40-game sample.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
import chess

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")


def verdict(pos, go="go depth 6"):
    """Fresh process, one search. -> (bailed, bestmove, nodes)."""
    e = Engine(ENG)
    e.uci(); e.sync()
    e.send(pos)
    e.send(go)
    lines = e.read_until(lambda l: l.startswith("bestmove"))
    e.quit()
    infos = [l for l in lines if l.startswith("info depth")]
    nodes, pv = None, []
    if infos:
        parts = infos[-1].split()
        nodes = int(parts[parts.index("nodes") + 1])
        pv = parts[parts.index("pv") + 1:] if "pv" in parts else []
    bm = lines[-1].split()[1] if len(lines[-1].split()) > 1 else None
    return (nodes == 0 and not pv and bm not in (None, "0000"), bm, nodes)


def clock_fen(b):
    ep = chess.square_name(b.ep_square) if b.ep_square is not None else "-"
    return (f"{b.board_fen()} {'w' if b.turn else 'b'} {b.castling_xfen() or '-'} "
            f"{ep} {b.halfmove_clock} {b.fullmove_number}")


def walk(g):
    """(ply, board_after, occurrence_count) for each ply, matching the engine's own history."""
    b = chess.Board(g["start_fen"])
    counts = {b._transposition_key(): 1}
    for i, mv in enumerate(g["moves"], 1):
        b.push(chess.Move.from_uci(mv))
        k = b._transposition_key()
        counts[k] = counts.get(k, 0) + 1
        yield i, b.copy(), counts[k]


def main():
    corpus = {g["id"]: g for g in json.load(open("evidence/games.json"))["games"]}
    ids = json.load(open("evidence/divergence_sample.json"))["games"]

    print("C. planted clock fault: one board, clock swept, fresh process each")
    board = "8/8/8/8/8/1R6/8/k1K5 w - - %d 1"
    sweep = {}
    for clk in (0, 97, 98, 99, 100, 101, 102):
        b, bm, n = verdict(f"position fen {board % clk}")
        sweep[clk] = {"bail": b, "bm": bm, "nodes": n}
        print(f"   clock {clk:3d} -> bail={str(b):5s} bm={bm} nodes={n}")
    boundary_ok = (not sweep[99]["bail"]) and sweep[100]["bail"] and (not sweep[0]["bail"])
    print(f"   boundary is exactly 100 (99 searches, 100 bails): {boundary_ok}")

    print("\nA. A/A control: 60 positions, identical probe twice, fresh process each")
    import random
    random.seed(11)
    allp = []
    for gid in ids[:4]:
        for k, b, occ in walk(corpus[gid]):
            if occ < 3 and not b.is_insufficient_material() and b.legal_moves.count():
                allp.append((gid, k, corpus[gid]["start_fen"], list(corpus[gid]["moves"][:k]),
                             clock_fen(b)))
    aa = random.sample(allp, 60)
    diffs = 0
    for gid, k, start, pre, fen in aa:
        cmds = [f"position fen {start} moves " + " ".join(pre), f"position fen {fen}"]
        vs = [verdict(c) for c in cmds for _ in range(2)]  # each command twice
        if vs[0] != vs[1]:
            diffs += 1
        if vs[2] != vs[3]:
            diffs += 1
    print(f"   A/A disagreements: {diffs}/{2*len(aa)}   <- the instrument's own error rate")

    print("\nB. clock agreement at every eligible ply (fresh process per arm)")
    n = 0
    mism = []
    skipped = 0
    for gid in ids:
        g = corpus[gid]
        for k, b, occ in walk(g):
            if occ >= 3 or b.is_insufficient_material() or b.legal_moves.count() == 0:
                skipped += 1
                continue
            pre = " ".join(g["moves"][:k])
            va, bma, na = verdict(f"position fen {g['start_fen']} moves {pre}")
            vb, bmb, nb = verdict(f"position fen {clock_fen(b)}")
            n += 1
            if va != vb:
                mism.append({"game": gid, "ply": k, "halfmove": b.halfmove_clock,
                             "movelist_bail": va, "fen_bail": vb,
                             "movelist_bm": bma, "fen_bm": bmb,
                             "movelist_nodes": na, "fen_nodes": nb})
        print(f"   ... {gid} done, {n} plies probed", flush=True)

    print(f"\n   eligible plies probed: {n}  (skipped {skipped}: repetition>=3, "
          f"insufficient material, or terminal)")
    print(f"   clock verdict mismatches: {len(mism)}")
    for m in mism[:10]:
        print("    ", m)

    over = [k for k in range(n)]
    json.dump({"boundary_sweep": sweep, "boundary_exactly_100": boundary_ok,
               "aa_control_disagreements": diffs, "aa_control_n": 2 * len(aa),
               "plies_probed": n, "plies_skipped": skipped,
               "clock_mismatches": len(mism), "examples": mism[:20]},
              open("evidence/halfmove_clock.json", "w"), indent=0)


if __name__ == "__main__":
    main()
