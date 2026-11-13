#!/usr/bin/env python3
"""Scorer and b2-write checks that do not need a checkpoint, a GPU, or a test set.

  python3 h512/train/test_scorer_parity.py [engine_tool]

centipawns() is compared with fable_nnue_v3.evaluate on synthetic nets and played positions.
If an engine tool path is given, its `eval` lines are compared as well. A value of b2 that
does not fit in int32 must be rejected; values that fit must keep the previous little-endian bytes.
"""
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fable_nnue_train as tr  # noqa: E402
import fable_nnue_v3 as v3  # noqa: E402

STARTS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
    "8/P7/8/8/8/8/8/4K1k1 w - - 0 1",
]


def played_fens(n_plies, seed):
    import chess
    rng = np.random.default_rng(seed)
    fens = list(STARTS)
    for start in STARTS:
        board = chess.Board(start)
        for _ in range(n_plies):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(moves[int(rng.integers(0, len(moves)))])
            fens.append(board.fen())
            if board.is_game_over():
                break
    return fens


def check_b2():
    net = v3.random_net(32, 1, 2, False, False, 7)
    in_range = [np.array([0, -1, 5000, -5000], np.int64),
                np.array([2147483647, -2147483648], np.int64),
                np.array([1.0, -2.0, 200.0], np.float32),
                np.array([1.0, -2.0], np.float64)]
    for values in in_range:
        got = v3.as_i32(values, "b2").tobytes()
        old = np.ascontiguousarray(np.rint(np.asarray(values, dtype=np.float64)).astype(np.int64), dtype="<i4").tobytes()
        if got != old:
            raise SystemExit(f"in-range b2 bytes changed for {values}")
    for bad in (np.array([2147483648]), np.array([-2147483649]), np.array([1.5]), np.array([np.inf])):
        try:
            v3.as_i32(bad, "b2")
        except ValueError:
            continue
        raise SystemExit(f"out-of-range b2 was accepted: {bad}")
    saved = net.b2.copy()
    net.b2 = np.array([2147483648, -5], np.int64)
    try:
        v3.write_net(os.devnull, net)
    except ValueError:
        pass
    else:
        raise SystemExit("write_net accepted an int32 overflow in b2")
    net.b2 = saved
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "roundtrip.fnn3")
        v3.write_net(path, net)
        back = v3.read_net(path)
        if not np.array_equal(back.b2, saved):
            raise SystemExit("b2 did not round-trip")
    print("b2 write: in-range bytes unchanged, overflow and non-integers rejected")


def check_scores(fens):
    import chess
    shapes = [
        (32, 1, 1, False, 11),
        (32, 8, 8, True, 12),
        (64, 4, 2, True, 13),
        (64, 1, 8, False, 14),
    ]
    codes = np.zeros((len(fens), 64), np.uint8)
    meta = np.zeros(len(fens), np.int64)
    for i, fen in enumerate(fens):
        board = chess.Board(fen)
        for sq, piece in board.piece_map().items():
            codes[i, sq] = piece.piece_type + (0 if piece.color else 6)
        meta[i] = 0 if board.turn else 1
    mismatches = 0
    negative = 0
    rows = 0
    for hidden, kb, ob, mirror, seed in shapes:
        net = v3.random_net(hidden, kb, ob, mirror, False, seed)
        if seed == 14:
            net.w2[:] = -np.abs(net.w2)
            net.b2[:] = -np.abs(net.b2)
        got = tr.centipawns(net, codes, meta)
        for i, fen in enumerate(fens):
            cp = v3.evaluate(net, v3.board_from_fen(fen))[0]
            rows += 1
            if cp < 0:
                negative += 1
            if int(got[i]) != cp:
                mismatches += 1
                if mismatches <= 5:
                    print(f"MISMATCH seed {seed} {fen} scorer {int(got[i])} reference {cp}")
    print(f"scorer vs python reference: rows {rows} mismatches {mismatches} negative {negative}")
    return mismatches, codes, meta


def check_engine(tool, fens):
    net = v3.random_net(32, 8, 8, True, False, 21)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "net.fnn3")
        fen_path = os.path.join(d, "fens.txt")
        v3.write_net(path, net)
        with open(fen_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fens) + "\n")
        proc = subprocess.run([tool, "eval", path, fen_path], check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"engine tool failed ({proc.returncode}): {proc.stderr}")
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if len(lines) != len(fens):
            raise SystemExit(f"engine lines {len(lines)} vs fens {len(fens)}")
        codes = np.zeros((len(fens), 64), np.uint8)
        meta = np.zeros(len(fens), np.int64)
        import chess
        for i, fen in enumerate(fens):
            board = chess.Board(fen)
            for sq, piece in board.piece_map().items():
                codes[i, sq] = piece.piece_type + (0 if piece.color else 6)
            meta[i] = 0 if board.turn else 1
        got = tr.centipawns(net, codes, meta)
        mismatches = 0
        for i, line in enumerate(lines):
            eng = int(line.split()[0])
            ref = v3.evaluate(net, v3.board_from_fen(fens[i]))[0]
            if eng != ref or int(got[i]) != ref:
                mismatches += 1
                if mismatches <= 5:
                    print(f"ENGINE MISMATCH {fens[i]} tool {eng} reference {ref} scorer {int(got[i])}")
        if "MISMATCH" in proc.stderr:
            raise SystemExit("engine tool reported a fast-path mismatch against its scalar reference")
        print(f"engine tool vs reference and scorer: rows {len(fens)} mismatches {mismatches}")
        return mismatches


def main():
    tool = sys.argv[1] if len(sys.argv) > 1 else None
    check_b2()
    fens = played_fens(12, 20261113)
    mismatches, _, _ = check_scores(fens)
    if tool:
        mismatches += check_engine(tool, fens)
    if mismatches:
        raise SystemExit(f"{mismatches} mismatches")
    print("ok")


if __name__ == "__main__":
    main()
