"""Probe: does a restricted root lose its TT entry, and does that trigger IIR?

Code under test (src/search.cpp):
  2093  if (excluded.is_none() && !(root_node && root_restricted_)) { store_tt(...); }
  1784  if (... depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;

So naming every legal move should (i) leave move order and move_count identical,
(ii) drop the root TT store, (iii) force the IIR depth reduction at every iteration.

If IIR is the mechanism, raising IirDepth above the search depth kills the effect.
Run: python3 job1/probe_iir.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

FENS = [
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6",
    "r2q1rk1/ppp2ppp/2np1n2/2b1p1B1/2B1P3/2NP1N2/PPP2PPP/R2Q1RK1 w - - 0 9",
]


def legal_uci(fen):
    import chess
    b = chess.Board(fen)
    return [m.uci() for m in b.legal_moves]


def main():
    out = []
    for fen in FENS:
        legal = legal_uci(fen)
        out.append(f"=== {fen}  ({len(legal)} legal) ===")
        for iir in (2, 20):
            opts = [(k, v) for k, v in engine.S14 if k != "IirDepth"] + [("IirDepth", str(iir))]
            for depth in (10, 12):
                base = engine.run_session(f"position fen {fen}", f"go depth {depth}", options=opts)
                allm = engine.run_session(f"position fen {fen}",
                                          f"go depth {depth} searchmoves {' '.join(legal)}", options=opts)
                out.append(
                    f"IirDepth {iir:2d} d{depth}: base {base.bestmove} {base.score:>5} "
                    f"nodes {base.raw_go.count('info depth'):2d}ln  |  all {allm.bestmove} {allm.score:>5} "
                    f"| {'SAME' if base.bestmove == allm.bestmove else 'DIFF'} "
                    f"{'score=' + str(base.score - allm.score) if base.score is not None and allm.score is not None else ''}"
                )
                # node counts from the last info line
                def last_nodes(r):
                    import re
                    m = re.findall(r"nodes (\d+)", r.raw_go)
                    return m[-1] if m else "?"
                out.append(f"              nodes base {last_nodes(base)} all {last_nodes(allm)}")
    text = "\n".join(out)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "probe_iir.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
