#!/usr/bin/env python3
"""NNUE v3 (FORGENN3) file reader/writer and exact integer reference evaluator (job FB1).

Format and arithmetic: include/forge/nnue_v3.hpp. The evaluator here uses Python
integers with C++ truncating division, so its output must equal the engine's
`forge_nnue_v3_tool eval` bit for bit.

Commands:
  random  <out.fnn3> [--hidden 512] [--king-buckets 8] [--output-buckets 8] [--mirror] [--residual] [--seed 1]
  info    <net.fnn3>
  eval    <net.fnn3> <fens.txt>                 prints "cp bucket kb_w flip_w kb_b flip_b" per FEN (as the engine tool)
  compare <net.fnn3> <fens.txt> <engine_out.txt>  0 mismatches == PASS
  positions <out.txt> <count> <seed>            random legal positions covering every piece count 2..32
"""
import argparse
import random
import struct
import sys

import numpy as np

MAGIC = b"FORGENN3"
VERSION = 3
HEADER_BYTES = 192
INPUTS = 768
QA = 255
QB = 64
MAX_W2 = 127
FLAG_RESIDUAL = 1
FLAG_MIRROR = 2


def fnv1a64(data: bytes) -> int:
    h = 14695981039346656037
    for b in data:
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def fnv1a64_fast(data: bytes) -> int:
    # Same result as fnv1a64, vectorised per byte in chunks (Python ints are the bottleneck otherwise).
    h = 14695981039346656037
    mask = 0xFFFFFFFFFFFFFFFF
    for b in memoryview(data):
        h = ((h ^ b) * 1099511628211) & mask
    return h


def tdiv(a: int, b: int) -> int:
    """C++ truncating integer division."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def king_layout(n: int):
    """Half-board king-bucket layouts (files a-d after mirroring), rank 1..8; mirrored to files e-h.
    Ideas: the standard mirrored layouts used by C4 (4 and 8 buckets); others are simple rank bands."""
    if n == 1:
        half = [0] * 32
    elif n == 2:
        half = [0] * 4 + [0] * 4 + [1] * 24
    elif n == 4:
        half = [int(c) for c in "0011" "0011" "2222" "2222" "3333" "3333" "3333" "3333"]
    elif n == 8:
        half = [int(c) for c in "0123" "4455" "6666" "7777" "7777" "7777" "7777" "7777"]
    elif n == 16:
        half = [int(ch, 16) for ch in "0123" "4567" "8899" "aabb" "cccc" "dddd" "eeee" "ffff"]
    elif n == 32:
        half = list(range(32))
    else:
        raise SystemExit(f"no standard layout for {n} king buckets (1, 2, 4, 8, 16, 32)")
    full = [0] * 64
    for sq in range(64):
        rank, file = sq >> 3, sq & 7
        hf = file if file < 4 else 7 - file
        full[sq] = half[rank * 4 + hf]
    return full


def output_layout(n: int):
    """Output bucket by total piece count 0..32 (C5's default map: (pieces - 2) * N // 32, capped)."""
    m = []
    for pieces in range(33):
        k = max(pieces - 2, 0)
        m.append(min(n - 1, k * n // 32))
    return m


class Net:
    def __init__(self):
        self.hidden = 0
        self.king_buckets = 1
        self.output_buckets = 1
        self.flags = 0
        self.eval_scale = 400
        self.king_map = [0] * 64
        self.output_map = [0] * 33
        self.w1 = None   # int16 [KB, 768, H]
        self.b1 = None   # int16 [H]
        self.w2 = None   # int16 [OB, 2H]
        self.b2 = None   # int32 [OB]
        self.checksum = 0

    @property
    def mirror(self):
        return (self.flags & FLAG_MIRROR) != 0

    @property
    def residual(self):
        return (self.flags & FLAG_RESIDUAL) != 0


def write_net(path: str, net: Net):
    header = bytearray(HEADER_BYTES)
    struct.pack_into("<8sIIIIIIIiii", header, 0, MAGIC, VERSION, HEADER_BYTES, INPUTS, net.hidden,
                     net.king_buckets, net.output_buckets, net.flags, QA, QB, net.eval_scale)
    header[48:112] = bytes(net.king_map)
    header[112:145] = bytes(net.output_map)
    body = bytes(header) + np.ascontiguousarray(net.w1, dtype="<i2").tobytes() + \
        np.ascontiguousarray(net.b1, dtype="<i2").tobytes() + \
        np.ascontiguousarray(net.w2, dtype="<i2").tobytes() + \
        np.ascontiguousarray(net.b2, dtype="<i4").tobytes()
    checksum = fnv1a64_fast(body)
    with open(path, "wb") as f:
        f.write(body)
        f.write(struct.pack("<Q", checksum))
    net.checksum = checksum
    return checksum


def read_net(path: str) -> Net:
    data = open(path, "rb").read()
    if data[:8] != MAGIC:
        raise SystemExit(f"{path}: bad magic")
    (version, header_bytes, inputs, hidden, kb, ob, flags, qa, qb, eval_scale) = struct.unpack_from("<IIIIIIIiii", data, 8)
    if version != VERSION or header_bytes != HEADER_BYTES or inputs != INPUTS or qa != QA or qb != QB:
        raise SystemExit(f"{path}: unsupported header fields")
    net = Net()
    net.hidden, net.king_buckets, net.output_buckets, net.flags, net.eval_scale = hidden, kb, ob, flags, eval_scale
    net.king_map = list(data[48:112])
    net.output_map = list(data[112:145])
    off = HEADER_BYTES
    n = kb * INPUTS * hidden
    net.w1 = np.frombuffer(data, dtype="<i2", count=n, offset=off).reshape(kb, INPUTS, hidden).astype(np.int64)
    off += 2 * n
    net.b1 = np.frombuffer(data, dtype="<i2", count=hidden, offset=off).astype(np.int64)
    off += 2 * hidden
    net.w2 = np.frombuffer(data, dtype="<i2", count=ob * 2 * hidden, offset=off).reshape(ob, 2 * hidden).astype(np.int64)
    off += 2 * ob * 2 * hidden
    net.b2 = np.frombuffer(data, dtype="<i4", count=ob, offset=off).astype(np.int64)
    off += 4 * ob
    net.checksum = struct.unpack_from("<Q", data, off)[0]
    if off + 8 != len(data):
        raise SystemExit(f"{path}: size mismatch")
    if fnv1a64_fast(data[:-8]) != net.checksum:
        raise SystemExit(f"{path}: checksum mismatch")
    return net


def random_net(hidden, king_buckets, output_buckets, mirror, residual, seed, eval_scale=400):
    rng = np.random.default_rng(seed)
    net = Net()
    net.hidden, net.king_buckets, net.output_buckets, net.eval_scale = hidden, king_buckets, output_buckets, eval_scale
    net.flags = (FLAG_MIRROR if mirror else 0) | (FLAG_RESIDUAL if residual else 0)
    net.king_map = king_layout(king_buckets)
    net.output_map = output_layout(output_buckets)
    # Ranges chosen so that SCReLU is exercised on both sides of the clamp:
    # 32 pieces * 40 + 200 < 32767 and the typical accumulator sits around 0..255.
    net.w1 = rng.integers(-40, 41, size=(king_buckets, INPUTS, hidden), dtype=np.int64)
    net.b1 = rng.integers(-200, 201, size=hidden, dtype=np.int64)
    net.w2 = rng.integers(-MAX_W2, MAX_W2 + 1, size=(output_buckets, 2 * hidden), dtype=np.int64)
    net.b2 = rng.integers(-5000, 5001, size=output_buckets, dtype=np.int64)
    return net


# ---- board side (python-chess) ----

def board_from_fen(fen):
    import chess
    return chess.Board(fen)


def piece_code(piece):
    # Forge Piece codes: WP..WK = 1..6, BP..BK = 7..12
    return piece.piece_type + (0 if piece.color else 6)


def king_key(net: Net, perspective_white: bool, king_square: int):
    kr = king_square if perspective_white else king_square ^ 56
    flip = 7 if (net.mirror and (kr & 7) >= 4) else 0
    return net.king_map[kr], flip


def feature_index(bucket, flip, perspective_white, code, square):
    is_white = code <= 6
    rel = 0 if is_white == perspective_white else 1
    ptype = (code - 1) % 6
    r = (square if perspective_white else square ^ 56) ^ flip
    return bucket * INPUTS + (rel * 6 + ptype) * 64 + r


def accumulate(net: Net, board, perspective_white: bool):
    import chess
    ksq = board.king(chess.WHITE if perspective_white else chess.BLACK)
    bucket, flip = king_key(net, perspective_white, ksq)
    acc = net.b1.copy()
    for square, piece in board.piece_map().items():
        idx = feature_index(bucket, flip, perspective_white, piece_code(piece), square)
        acc = acc + net.w1.reshape(-1, net.hidden)[idx]
    assert np.all(np.abs(acc) <= 32767)
    return acc, bucket, flip


def evaluate(net: Net, board):
    """Returns (cp, output_bucket, (kb_w, flip_w), (kb_b, flip_b), raw_sum)."""
    acc_w, kb_w, fl_w = accumulate(net, board, True)
    acc_b, kb_b, fl_b = accumulate(net, board, False)
    ours, theirs = (acc_w, acc_b) if board.turn else (acc_b, acc_w)
    pieces = min(len(board.piece_map()), 32)
    ob = net.output_map[pieces]
    a = np.clip(ours, 0, QA)
    b = np.clip(theirs, 0, QA)
    w2 = net.w2[ob]
    total = int(np.sum(a * a * w2[:net.hidden])) + int(np.sum(b * b * w2[net.hidden:]))
    out = tdiv(total, QA) + int(net.b2[ob])
    cp = tdiv(out * net.eval_scale, QA * QB)
    cp = max(-30000, min(30000, cp))
    return cp, ob, (kb_w, fl_w), (kb_b, fl_b), total


def evaluate_float(net_float, board):
    """Float forward of de-quantised weights (w1/QA, b1/QA, w2/QB, b2/(QA*QB)) -> centipawns (float)."""
    w1, b1, w2, b2, king_map, output_map, mirror, hidden, eval_scale = net_float
    import chess

    def acc_for(white):
        ksq = board.king(chess.WHITE if white else chess.BLACK)
        kr = ksq if white else ksq ^ 56
        flip = 7 if (mirror and (kr & 7) >= 4) else 0
        bucket = king_map[kr]
        acc = b1.copy()
        for square, piece in board.piece_map().items():
            acc = acc + w1.reshape(-1, hidden)[feature_index(bucket, flip, white, piece_code(piece), square)]
        return acc

    aw, ab = acc_for(True), acc_for(False)
    ours, theirs = (aw, ab) if board.turn else (ab, aw)
    ob = output_map[min(len(board.piece_map()), 32)]
    a = np.clip(ours, 0.0, 1.0)
    b = np.clip(theirs, 0.0, 1.0)
    out = float(np.sum(a * a * w2[ob][:hidden]) + np.sum(b * b * w2[ob][hidden:])) + float(b2[ob])
    return out * eval_scale


def random_positions(count, seed):
    """Random legal positions: random playouts from the start position plus random-material placements,
    so that every total piece count 2..32 occurs."""
    import chess
    rng = random.Random(seed)
    out = []
    # 1) playouts
    while len(out) < count // 2:
        board = chess.Board()
        plies = rng.randint(0, 120)
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over():
                break
            board.push(rng.choice(moves))
        if board.is_game_over():
            continue
        out.append(board.fen())
    # 2) random material, equal share per piece count 2..32
    pieces_cycle = list(range(2, 33))
    i = 0
    while len(out) < count:
        target = pieces_cycle[i % len(pieces_cycle)]
        i += 1
        board = chess.Board(None)
        squares = rng.sample(range(64), target)
        wk, bk = squares[0], squares[1]
        if chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        ok = True
        # A random subset of the standard inventory (no promotions), so the engine's
        # piece-inventory check accepts every position.
        pool = [chess.Piece(t, c) for c in (chess.WHITE, chess.BLACK)
                for t in [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]]
        rng.shuffle(pool)
        for sq, piece in zip(squares[2:], pool):
            if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, piece)
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        # the side not to move must not be in check; the side to move may be
        board.turn = not board.turn
        if board.is_check():
            ok = False
        board.turn = not board.turn
        if not ok or not board.is_valid():
            continue
        out.append(board.fen())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("random")
    r.add_argument("out")
    r.add_argument("--hidden", type=int, default=512)
    r.add_argument("--king-buckets", type=int, default=8)
    r.add_argument("--output-buckets", type=int, default=8)
    r.add_argument("--mirror", action="store_true")
    r.add_argument("--residual", action="store_true")
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--eval-scale", type=int, default=400)
    i = sub.add_parser("info")
    i.add_argument("net")
    e = sub.add_parser("eval")
    e.add_argument("net")
    e.add_argument("fens")
    c = sub.add_parser("compare")
    c.add_argument("net")
    c.add_argument("fens")
    c.add_argument("engine_out")
    p = sub.add_parser("positions")
    p.add_argument("out")
    p.add_argument("count", type=int)
    p.add_argument("seed", type=int)
    w = sub.add_parser("widen", help="zero-pad a net to a wider hidden layer (function-preserving: same evaluations)")
    w.add_argument("net")
    w.add_argument("out")
    w.add_argument("hidden", type=int)
    args = ap.parse_args()

    if args.cmd == "widen":
        net = read_net(args.net)
        H, H2 = net.hidden, args.hidden
        if H2 < H or H2 % 32 or H2 > 1024:
            raise SystemExit("new hidden must be >= old, a multiple of 32 and <= 1024")
        w1 = np.zeros((net.king_buckets, INPUTS, H2), np.int64)
        w1[:, :, :H] = net.w1
        b1 = np.zeros(H2, np.int64)
        b1[:H] = net.b1
        w2 = np.zeros((net.output_buckets, 2 * H2), np.int64)
        w2[:, :H] = net.w2[:, :H]
        w2[:, H2:H2 + H] = net.w2[:, H:]
        net.w1, net.b1, net.w2, net.hidden = w1, b1, w2, H2
        checksum = write_net(args.out, net)
        print(f"wrote {args.out} hidden {H2} (from {H}) checksum {checksum:x}")
        return

    if args.cmd == "random":
        net = random_net(args.hidden, args.king_buckets, args.output_buckets, args.mirror, args.residual, args.seed, args.eval_scale)
        checksum = write_net(args.out, net)
        print(f"wrote {args.out} hidden {net.hidden} kb {net.king_buckets} ob {net.output_buckets} flags {net.flags} checksum {checksum:x}")
    elif args.cmd == "info":
        net = read_net(args.net)
        print(f"v3 {args.net} hidden {net.hidden} king_buckets {net.king_buckets}{' mirrored' if net.mirror else ''} "
              f"output_buckets {net.output_buckets} {'residual' if net.residual else 'standalone'} eval_scale {net.eval_scale} "
              f"checksum {net.checksum:x} max|w1| {int(np.abs(net.w1).max())} max|b1| {int(np.abs(net.b1).max())} max|w2| {int(np.abs(net.w2).max())}")
    elif args.cmd in ("eval", "compare"):
        net = read_net(args.net)
        fens = [l.strip() for l in open(args.fens) if l.strip()]
        lines = []
        for fen in fens:
            cp, ob, (kw, fw), (kb, fb), _ = evaluate(net, board_from_fen(fen))
            lines.append(f"{cp} {ob} {kw} {fw} {kb} {fb}")
        if args.cmd == "eval":
            print("\n".join(lines))
        else:
            engine = [l.strip() for l in open(args.engine_out) if l.strip()]
            if len(engine) != len(lines):
                print(f"FAIL: {len(engine)} engine lines vs {len(lines)} reference lines")
                sys.exit(1)
            mism = [(k, a, b) for k, (a, b) in enumerate(zip(lines, engine)) if a != b]
            cps = [int(l.split()[0]) for l in lines]
            buckets = sorted(set(int(l.split()[1]) for l in lines))
            print(f"positions {len(lines)} mismatches {len(mism)} cp range {min(cps)}..{max(cps)} output buckets used {buckets}")
            for k, a, b in mism[:10]:
                print(f"  line {k + 1}: reference '{a}' engine '{b}'")
            print("PASS" if not mism else "FAIL")
            sys.exit(0 if not mism else 1)
    elif args.cmd == "positions":
        fens = random_positions(args.count, args.seed)
        with open(args.out, "w", newline="\n") as f:
            f.write("\n".join(fens) + "\n")
        counts = {}
        for fen in fens:
            n = len(board_from_fen(fen).piece_map())
            counts[n] = counts.get(n, 0) + 1
        print(f"wrote {len(fens)} positions to {args.out}; piece counts {min(counts)}..{max(counts)} ({len(counts)} distinct)")


if __name__ == "__main__":
    main()
