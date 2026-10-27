#!/usr/bin/env python3
"""A3 acceptance 2: in the reference evaluator, incremental == full refresh on 200k positions, 0 mismatches.

usage: a3_incremental_200k.py <net.fnn> <fens.txt> [--positions 200000] [--seed 1] [--no-cache]

Random search-like walks with python-chess (legal moves only): from a start position (20%: one of 8 fixed FENs
with castling, en passant, promotions and rook endings; else one of the first 3000 lines of <fens.txt> or a fixed
FEN) the walk makes a random move (a castling / en-passant / promotion move half of the time when one is legal,
else a king move 30% of the time so king keys change often, else any legal move; a null move 4% of the time when
not in check and the last move was not null), or takes back the last move (25%, always at depth 16), and
evaluates the current ply with probability 0.6, so later evaluations replay several plies. Evaluation goes through
forge_astra_A3_refeval_20261027.LazyEvaluator (per-perspective validity, replay while the own-king key holds,
rebuild through the refresh cache when it changed); each evaluated position is checked against a refresh from
scratch: both accumulators (float32 bytes) and the output (float32 bytes, cp); at every evaluated position the
piece codes kept from the dirty pieces are also compared with python-chess's board (this checks the dirty-piece
generation itself). Exit 0 only with 0 mismatches.
"""
import argparse
import random
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import forge_astra_A3_refeval_20261027 as R  # noqa: E402

FIXED = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "8/2P5/8/8/8/8/5p2/K6k w - - 0 1",
    "8/1P4k1/8/8/8/8/6p1/K7 b - - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
]


def board_codes(board):
    codes = np.zeros(64, np.uint8)
    for sq, pc in board.piece_map().items():
        codes[sq] = pc.piece_type + (0 if pc.color else 6)
    return codes


def run(net_path, fens_path, positions, seed, use_cache=True, mutate=None):
    import chess
    net = R.Net(net_path)
    rng = random.Random(seed)
    starts = list(FIXED)
    for line in open(fens_path, encoding="ascii"):
        fen = line.split("|")[0].strip()
        if fen:
            starts.append(fen)
        if len(starts) >= 3000:
            break
    cache = R.RefreshCache(net) if use_cache else None
    st = {"evaluated": 0, "acc_mismatch": 0, "out_mismatch": 0, "moves": 0, "takebacks": 0, "null_moves": 0,
          "king_moves": 0, "key_changes": 0, "castles": 0, "en_passant": 0, "promotions": 0, "captures": 0,
          "walks": 0, "codes_checks": 0, "codes_bad": 0}
    lazy_totals = {}
    first_bad = None
    t0 = time.time()
    while st["evaluated"] < positions:
        fixed = rng.random() < 0.2
        board = chess.Board(FIXED[rng.randrange(len(FIXED))] if fixed else starts[rng.randrange(len(starts))])
        codes = board_codes(board)
        ev = R.LazyEvaluator(net, codes, 1 if board.turn == chess.BLACK else 0, cache)
        if mutate:
            mutate(ev)
        st["walks"] += 1
        null_stack = []
        for _ in range(rng.randrange(40, 400)):
            depth = len(ev.stack) - 1
            if depth > 0 and (depth >= 16 or rng.random() < 0.25):
                board.pop()
                ev.pop()
                null_stack.pop()
                st["takebacks"] += 1
            else:
                if (rng.random() < 0.04 and not board.is_check() and depth > 0 and not null_stack[-1]):
                    board.push(chess.Move.null())
                    ev.push(ev.stack[-1].codes, 1 - ev.stack[-1].stm, [])
                    null_stack.append(True)
                    st["null_moves"] += 1
                else:
                    moves = list(board.legal_moves)
                    if not moves:
                        if depth == 0:
                            break
                        board.pop()
                        ev.pop()
                        null_stack.pop()
                        st["takebacks"] += 1
                        continue
                    kmoves = [m for m in moves if board.piece_type_at(m.from_square) == chess.KING]
                    special = [m for m in moves if board.is_castling(m) or board.is_en_passant(m) or m.promotion]
                    if special and rng.random() < 0.5:
                        move = rng.choice(special)
                    elif kmoves and rng.random() < 0.3:
                        move = rng.choice(kmoves)
                    else:
                        move = rng.choice(moves)
                    changes = R.chess_changes(board, move)
                    st["castles"] += board.is_castling(move)
                    st["en_passant"] += board.is_en_passant(move)
                    st["promotions"] += move.promotion is not None
                    st["captures"] += board.is_capture(move)
                    if board.piece_type_at(move.from_square) == chess.KING:
                        st["king_moves"] += 1
                    before = ev.stack[-1].key
                    board.push(move)
                    new_codes = R.apply_to_codes(ev.stack[-1].codes, changes)
                    ev.push(new_codes, 1 - ev.stack[-1].stm, changes)
                    st["key_changes"] += ev.stack[-1].key != before
                    null_stack.append(False)
                    st["moves"] += 1
            if rng.random() < 0.6:
                top = ev.stack[-1]
                st["codes_checks"] += 1
                st["codes_bad"] += not np.array_equal(board_codes(board), top.codes)
                out, cp, acc = ev.evaluate()
                ref = [R.refresh(net, top.codes, 0), R.refresh(net, top.codes, 1)]
                ref_out, ref_cp = R.evaluate_acc(net, ref[top.stm], ref[1 - top.stm], R.output_bucket(net, top.codes))
                bad_acc = acc[0].tobytes() != ref[0].tobytes() or acc[1].tobytes() != ref[1].tobytes()
                bad_out = np.float32(out).tobytes() != np.float32(ref_out).tobytes() or cp != ref_cp
                st["acc_mismatch"] += bad_acc
                st["out_mismatch"] += bad_out
                if (bad_acc or bad_out) and first_bad is None:
                    first_bad = f"{board.fen()} lazy {out} {cp} refresh {ref_out} {ref_cp}"
                st["evaluated"] += 1
                if st["evaluated"] >= positions:
                    break
        for k, v in ev.stats.items():
            lazy_totals[k] = lazy_totals.get(k, 0) + v
    st["seconds"] = round(time.time() - t0, 1)
    ok = st["acc_mismatch"] == 0 and st["out_mismatch"] == 0 and st["codes_bad"] == 0 and st["evaluated"] >= positions
    lines = [f"net {net_path} seed {seed} refresh cache {'on' if use_cache else 'off'}",
             "walk: " + " ".join(f"{k} {v}" for k, v in st.items()),
             "lazy accumulator paths (per perspective): " + " ".join(f"{k} {v}" for k, v in lazy_totals.items()),
             f"refresh-cache columns applied: {cache.columns if cache else 0}",
             f"mismatches: accumulators {st['acc_mismatch']}, outputs {st['out_mismatch']}, piece codes {st['codes_bad']}"
             + (f"; first: {first_bad}" if first_bad else ""),
             "PASS" if ok else "FAIL"]
    return ok, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("net")
    ap.add_argument("fens")
    ap.add_argument("--positions", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()
    ok, msg = run(a.net, a.fens, a.positions, a.seed, not a.no_cache)
    print(msg, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
