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

import chess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fable_nnue_data as fd  # noqa: E402
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
    bound = v3.random_net(32, 1, 1, False, False, 99)
    bound.w1[:] = 1000
    bound.b1[:] = 700
    bound_cp = tr.centipawns(bound, codes, meta)
    for i, fen in enumerate(fens):
        cp = v3.evaluate(bound, v3.board_from_fen(fen))[0]
        rows += 1
        if cp < 0:
            negative += 1
        if int(bound_cp[i]) != cp:
            mismatches += 1
            if mismatches <= 5:
                print(f"MISMATCH near-bound {fen} scorer {int(bound_cp[i])} reference {cp}")
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
        for i, fen in enumerate(fens):
            board = chess.Board(fen)
            for sq, piece in board.piece_map().items():
                codes[i, sq] = piece.piece_type + (0 if piece.color else 6)
            meta[i] = 0 if board.turn else 1
        got = tr.centipawns(net, codes, meta)
        mismatches = 0
        for i, line in enumerate(lines):
            parts = [int(x) for x in line.split()]
            eng, bucket, kb_w, fl_w, kb_b, fl_b = parts
            cp, ob, white_key, black_key, _total = v3.evaluate(net, v3.board_from_fen(fens[i]))
            if eng != cp or int(got[i]) != cp or bucket != ob or (kb_w, fl_w) != white_key or (kb_b, fl_b) != black_key:
                mismatches += 1
                if mismatches <= 5:
                    print(f"ENGINE MISMATCH {fens[i]} tool {parts} reference {(cp, ob, white_key, black_key)} scorer {int(got[i])}")
        if "MISMATCH" in proc.stderr:
            raise SystemExit("engine tool reported a fast-path mismatch against its scalar reference")
        sum_proc = subprocess.run([tool, "sum", path, fen_path], check=False, capture_output=True, text=True)
        if sum_proc.returncode != 0:
            raise SystemExit(f"engine sum failed ({sum_proc.returncode}): {sum_proc.stderr}")
        sums = [int(ln) for ln in sum_proc.stdout.splitlines() if ln.strip()]
        if len(sums) != len(fens):
            raise SystemExit(f"sum lines {len(sums)} vs fens {len(fens)}")
        for i, fen in enumerate(fens):
            total = v3.evaluate(net, v3.board_from_fen(fen))[4]
            if sums[i] != total:
                mismatches += 1
                if mismatches <= 5:
                    print(f"SUM MISMATCH {fen} tool {sums[i]} reference {total}")
        print(f"engine tool vs reference and scorer: rows {len(fens)} mismatches {mismatches} (cp, bucket, king key, raw sum)")
        return mismatches


def check_b2_clip_limit():
    """clip() must keep round(b2 * QA * QB) inside int32. 131586 fits; 131587 does not."""
    q = v3.QA * v3.QB
    limit = tr.B2_ABS_MAX
    if q != 16320:
        raise SystemExit(f"QA * QB is {q}, the b2 clip constant was chosen for 16320")
    for sign in (1.0, -1.0):
        rounded = int(np.rint(sign * limit * q))
        if rounded < -2147483648 or rounded > 2147483647:
            raise SystemExit(f"b2 clip limit rounds outside int32: {rounded}")
        as_f32 = float(np.float32(np.float32(sign * limit) * np.float32(q)))
        rounded_f32 = int(np.rint(as_f32))
        if rounded_f32 < -2147483648 or rounded_f32 > 2147483647:
            raise SystemExit(f"float32 export of the b2 clip limit is outside int32: {rounded_f32}")
    if 131587 * q <= 2147483647 or -131587 * q >= -2147483648:
        raise SystemExit("b2 clip limit is not the last safe integer count")
    try:
        import torch
    except ImportError:
        print("b2 clip limit: integer and float32 bounds hold; torch is not installed, clip() was not executed")
        return
    cfg = {
        "hidden": 32, "king_buckets": 1, "output_buckets": 2, "mirror": False, "residual": False,
        "factorizer": True, "eval_scale": 400, "blend": 1.0, "seed": 1, "init_scale": 0.01,
        "king_map": v3.king_layout(1), "output_map": v3.output_layout(2),
    }
    model = tr.build_model(cfg, torch)
    with torch.no_grad():
        model.b2.fill_(1.0e9)
        model.clip()
        after = float(model.b2.abs().max())
        rounded = torch.round(model.b2 * q)
    if after > limit + 1.0e-5:
        raise SystemExit(f"clip() left b2 at {after}, above {limit}")
    if int(rounded.abs().max()) > 2147483647:
        raise SystemExit("clip() left a b2 whose rounded multiple does not fit in int32")
    print(f"b2 clip limit: {limit:.6f} holds in float32, and clip() pulled 1e9 down to {after:.6f}")


def check_piece_counts(fens):
    """The phase LUT looks like it has a precedence bug. In Python != binds looser than &,
    so `c & 15 != 0` is `(c & 15) != 0`. It must keep matching a direct nibble count."""
    disagree = 0
    for c in range(256):
        direct = int((c & 15) != 0) + int((c >> 4) != 0)
        if int(fd.PIECE_COUNT_LUT[c]) != direct:
            disagree += 1
    if disagree:
        raise SystemExit(f"piece-count LUT differs from a nibble count on {disagree} byte values")
    bad_fens = 0
    for fen in fens:
        board = chess.Board(fen)
        codes = np.zeros(64, np.uint8)
        for sq, piece in board.piece_map().items():
            codes[sq] = piece.piece_type + (0 if piece.color else 6)
        packed = (codes[0::2] | (codes[1::2] << 4)).reshape(1, 32)
        got = int(fd.piece_counts(packed)[0])
        if got != len(board.piece_map()):
            bad_fens += 1
            if bad_fens <= 5:
                print(f"PIECE COUNT {fen} lut {got} board {len(board.piece_map())}")
    print(f"piece-count LUT: 256 byte values agree, fens {len(fens)} mismatches {bad_fens}")
    return bad_fens


def check_final_test_gate():
    try:
        tr.refuse_final_test(["fb2_013.pos", os.path.join("set", "final_test_2m.pos")])
    except SystemExit as exc:
        if "final-test" not in str(exc):
            raise
    else:
        raise SystemExit("helper did not refuse")
    if tr.refuse_final_test(["fb2_013.pos", "fb2_014.pos"]):
        raise SystemExit("helper refused a training shard")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fable_nnue_train.py")
    refused = subprocess.run(
        [sys.executable, script, "score", "--net", "missing.fnn3", "--pos", "final_test3_2m.pos"],
        capture_output=True, text=True)
    if refused.returncode == 0 or "final-test" not in (refused.stderr + refused.stdout):
        raise SystemExit(f"score did not refuse a final-test name:\n{refused.stderr}")
    ordinary = subprocess.run(
        [sys.executable, script, "score", "--net", "missing.fnn3", "--pos", "holdout.pos"],
        capture_output=True, text=True)
    if "final-test" in (ordinary.stderr + ordinary.stdout):
        raise SystemExit("score refused a holdout name")
    with tempfile.TemporaryDirectory() as tmp:
        final = os.path.join(tmp, "final_test3_2m.pos")
        open(final, "wb").close()
        train = subprocess.run(
            [sys.executable, script, "train", "--out", tmp, "--pos", final],
            capture_output=True, text=True)
        text = train.stderr + train.stdout
        if train.returncode == 0 or "final-test" not in text or "torch" in text:
            raise SystemExit(f"train did not refuse before torch:\n{text}")
        open(os.path.join(tmp, "fb2_001.pos"), "wb").close()
        globbed = subprocess.run(
            [sys.executable, script, "train", "--out", tmp, "--pos-glob", os.path.join(tmp, "*.pos")],
            capture_output=True, text=True)
        glob_text = globbed.stderr + globbed.stdout
        if globbed.returncode == 0 or "final-test" not in glob_text or "torch" in glob_text:
            raise SystemExit(f"train glob did not refuse before torch:\n{glob_text}")
        opened = subprocess.run(
            [sys.executable, script, "score", "--net", "missing.fnn3", "--pos", final, "--final-test-unlock"],
            capture_output=True, text=True)
        if "final-test" in (opened.stderr + opened.stdout):
            raise SystemExit("unlock still refused")
        log = os.path.join(tmp, "FINAL_TEST_ACCESS.log")
        if not os.path.isfile(log) or "final_test3_2m.pos" not in open(log, encoding="utf-8").read():
            raise SystemExit("unlock did not record the read")
    print("final-test gate: score and train refuse the name; unlock records the read")


def main():
    tool = sys.argv[1] if len(sys.argv) > 1 else None
    check_final_test_gate()
    check_b2()
    check_b2_clip_limit()
    fens = played_fens(12, 20261113)
    mismatches = check_piece_counts(fens)
    mismatches += check_scores(fens)[0]
    if tool:
        mismatches += check_engine(tool, fens)
    if mismatches:
        raise SystemExit(f"{mismatches} mismatches")
    print("ok")


if __name__ == "__main__":
    main()
