"""Family 6: the `0000` roots, and which of them carries an `info string`.

The audit's §1b says three shapes give `0000`:
  * checkmate root          -> `mate 0`
  * stalemate root          -> `cp 0`, no `info string` at all
  * empty `searchmoves`     -> `cp 0`, WITH an `info string`
This script confirms each on this build, records the raw wire, and checks the
discriminator the report claims (score kind separates checkmate from the other
two).
"""
import json
import sys
import chess

from forge_drv import Forge, RefusedFen

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family6_0000.json"

CASES = [
    # (label, fen) -- both colours; mirrored so the white-to-move pair is a
    # true checkmate / true stalemate, not merely "not mate".
    ("checkmate_root_b", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 60", None),
    ("stalemate_root_b", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 60", None),
    ("checkmate_root_w", "8/8/8/8/8/6k1/6q1/7K w - - 0 60", None),
    ("stalemate_root_w", "8/8/8/8/8/6k1/5q2/7K w - - 0 60", None),
]


def main():
    rows = []
    with Forge(EXE) as eng:
        for label, fen, _ in CASES:
            # python-chess side of the proof
            b = chess.Board(fen)
            pc = {"valid": b.is_valid(),
                  "is_checkmate": b.is_checkmate(),
                  "is_stalemate": b.is_stalemate(),
                  "legal_moves": b.legal_moves.count(),
                  "in_check": b.is_check()}
            rec = eng.search(fen, "go depth 12")
            rows.append({
                "label": label, "fen": fen, "python_chess": pc,
                "bestmove": rec.bestmove,
                "score": rec.score(),
                "nodes": rec.nodes(),
                "depth": rec.depth(),
                "seldepth": rec.seldepth(),
                "pv": rec.pv(),
                "info_strings": rec.info_strings(),
                "n_info_lines": len(rec.infos),
                "raw": rec.raw,
            })

        # empty searchmoves restriction
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        rec = eng.search(fen, "go depth 8 searchmoves")
        rows.append({
            "label": "empty_searchmoves", "fen": fen,
            "python_chess": {"valid": True, "legal_moves": 20},
            "bestmove": rec.bestmove, "score": rec.score(),
            "nodes": rec.nodes(), "depth": rec.depth(),
            "seldepth": rec.seldepth(), "pv": rec.pv(),
            "info_strings": rec.info_strings(),
            "n_info_lines": len(rec.infos), "raw": rec.raw,
        })

        # all-illegal searchmoves (documented as reporting)
        rec = eng.search(fen, "go depth 8 searchmoves a1a8 h1h8")
        rows.append({
            "label": "all_illegal_searchmoves", "fen": fen,
            "python_chess": {"valid": True, "legal_moves": 20},
            "bestmove": rec.bestmove, "score": rec.score(),
            "nodes": rec.nodes(), "depth": rec.depth(),
            "seldepth": rec.seldepth(), "pv": rec.pv(),
            "info_strings": rec.info_strings(),
            "n_info_lines": len(rec.infos), "raw": rec.raw,
        })

        # control: a normal position must NOT be 0000
        rec = eng.search(fen, "go depth 8")
        rows.append({
            "label": "CONTROL_normal", "fen": fen,
            "python_chess": {"valid": True, "legal_moves": 20},
            "bestmove": rec.bestmove, "score": rec.score(),
            "nodes": rec.nodes(), "depth": rec.depth(),
            "seldepth": rec.seldepth(), "pv": rec.pv(),
            "info_strings": rec.info_strings(),
            "n_info_lines": len(rec.infos), "raw": rec.raw,
        })

    with open(OUT, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"{'label':28} {'bestmove':9} {'score':14} {'nodes':>8} {'infos':>6}  info_string")
    for r in rows:
        print(f"{r['label']:28} {str(r['bestmove']):9} {str(r['score']):14} "
              f"{str(r['nodes']):>8} {r['n_info_lines']:>6}  {r['info_strings']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
