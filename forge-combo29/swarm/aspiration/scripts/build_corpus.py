"""Build the aspiration corpus and validate every fixture two ways.

Corpora:
  A) depth  -- real positions used for score-vs-depth ladders and for the
               narrow-vs-never-narrow comparison. The 8 bench FENs plus
               positions sampled from engine self-play, so the material is real
               game material rather than hand-arranged.
  B) mate   -- mates at distances 1..4 whose DTM was PROVED by
               `gen_mates.py` with an AND/OR search that does not involve the
               engine. Labels come from that proof, not from the engine.

Two independent validations, per the shared brief (a refused FEN manufactures a
pass):
  1. python-chess parses the FEN and reports STATUS_VALID.
  2. The engine's own `position` command is watched for `invalid FEN`; a refusal
     aborts the run instead of being silently dropped.
"""
import json
import pathlib
import sys

import chess

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from uci import Engine, RefusedFen  # noqa: E402

OUT = pathlib.Path("/tmp/asp/evidence")

BENCH_FENS = [
    chess.STARTING_FEN,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]


def selfplay_positions(engine_path, games=3, max_plies=90):
    """Sample one position per two plies from engine self-play."""
    positions = []
    for game in range(games):
        with Engine(engine_path) as eng:
            eng.newgame()
            board = chess.Board()
            eng.position(board.fen())
            depth = 8 + 2 * game
            for ply in range(max_plies):
                if board.is_game_over(claim_draw=False):
                    break
                res = eng.search(f"go depth {depth}")
                uci = res["bestmove"]
                if uci == "0000":
                    break
                try:
                    move = chess.Move.from_uci(uci)
                except ValueError:
                    break
                if move not in board.legal_moves:
                    break
                if ply % 2 == 0:
                    positions.append(board.fen())
                board.push(move)
                eng.position(board.fen())
    return positions


def main():
    engine_path = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)

    mates = json.loads((OUT / "mates_verified.json").read_text())["rows"]
    mate_fens = [r["fen"] for r in mates]

    depth_fens = list(BENCH_FENS)
    for fen in selfplay_positions(engine_path):
        if fen not in depth_fens:
            depth_fens.append(fen)

    all_fens = depth_fens + mate_fens
    for fen in all_fens:
        status = chess.Board(fen).status()
        if status != chess.STATUS_VALID:
            raise SystemExit(f"python-chess rejected {fen}: {status}")

    refused = []
    with Engine(engine_path) as eng:
        for fen in all_fens:
            try:
                eng.position(fen)
            except RefusedFen as exc:
                refused.append((fen, str(exc)))
    if refused:
        for fen, msg in refused:
            print(f"  REFUSED {fen}: {msg}")
        raise SystemExit("engine refused a fixture; a pass here would be manufactured")

    payload = {
        "engine": engine_path,
        "audit_base": "6b98f217",
        "depth_positions": [{"fen": f, "label": f"depth-{i:02d}"}
                            for i, f in enumerate(depth_fens)],
        "mate_positions": [{"fen": r["fen"], "dtm_plies": r["dtm_plies"],
                            "mate_in": r["mate_in"], "label": r["label"]}
                           for r in mates],
        "validation": {
            "python_chess": "all STATUS_VALID",
            "engine_refused": len(refused),
            "total_fixtures": len(all_fens),
            "mate_labels_from": "gen_mates.py AND/OR proof, engine not involved",
        },
    }
    (OUT / "corpus.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"corpus: {len(depth_fens)} depth positions, {len(mate_fens)} mate positions")
    print(f"refused by engine: {len(refused)}   python-chess invalid: 0")


if __name__ == "__main__":
    main()
