"""The FORGENN3 net file ("v3": king-bucketed inputs, output buckets, int16) for the engine tree forge/r7.

Written on the owner's PC on 2026-11-15 from the format description at the top of forge/r7/include/forge/nnue_v3.hpp
(which came, after a line-by-line read, from branch fable/standalone-h512-20261111 of the owner's repo). The
layouts of the king buckets and output buckets are those of that branch's candidate nets, so that results can
be compared.

Feature of piece `pc` on `square` for perspective p (own king on `ksq`), squares 0 = a1 .. 63 = h8:
    r      = square if p is White else square ^ 56
    kr     = ksq    if p is White else ksq ^ 56
    flip   = 7 if the net is mirrored and kr is on files e-h, else 0
    bucket = king_map[kr]
    index  = bucket * 768 + ((0 if colour(pc) == p else 1) * 6 + type(pc)) * 64 + (r ^ flip)      type: P=0 .. K=5
Evaluation, all integers (QA = 255, QB = 64):
    acc[p] = b1 + sum of w1[index] over all pieces (both kings included)
    a = clamp(acc, 0, QA)
    s = sum_h a_us[h]^2 * w2[ob][h] + a_them[h]^2 * w2[ob][H + h]
    out = trunc(s / QA) + b2[ob];  cp = trunc(out * eval_scale / (QA * QB)), clamped to +-30000, side to move's view
    ob = output_map[min(number of pieces, 32)]
File (little-endian): 192-byte header, w1 int16 [KB][768][H], b1 int16 [H], w2 int16 [OB][2H], b2 int32 [OB],
then the 64-bit FNV-1a of every preceding byte. The engine refuses |w2| > 127 and max|b1| + 32 max|w1| > 32767.

Command line (tools):
    python forge_v3.py random <out.fnn3> [hidden=512] [seed=1]      a random net inside the engine's bounds
    python forge_v3.py info <net.fnn3>
"""
from __future__ import annotations

import struct
import sys

import numpy as np

MAGIC = b"FORGENN3"
HEADER_BYTES = 192
INPUTS = 768
QA = 255
QB = 64
FLAG_RESIDUAL = 1
FLAG_MIRROR = 2
MAX_W2 = 127


def king_layout(n: int = 8) -> list[int]:
    """King bucket of every square (as seen by the king's own side, before mirroring): the half-board layouts of
    the earlier candidate nets, files a-d, mirrored onto files e-h."""
    half = {1: "0" * 32,
            4: "0011" "0011" "2222" "2222" "3333" "3333" "3333" "3333",
            8: "0123" "4455" "6666" "7777" "7777" "7777" "7777" "7777"}.get(n)
    if half is None:
        raise ValueError(f"no layout for {n} king buckets (1, 4, 8)")
    full = [0] * 64
    for sq in range(64):
        rank, file = sq >> 3, sq & 7
        full[sq] = int(half[rank * 4 + (file if file < 4 else 7 - file)])
    return full


def output_layout(n: int = 8) -> list[int]:
    """Output bucket for 0..32 pieces on the board: (pieces - 2) * n // 32, capped."""
    return [min(n - 1, max(p - 2, 0) * n // 32) for p in range(33)]


def fnv1a64(data: bytes) -> int:
    h = 14695981039346656037
    for b in data:
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


class Net:
    def __init__(self, hidden: int, king_buckets: int = 8, output_buckets: int = 8, mirror: bool = True,
                 eval_scale: int = 400):
        self.hidden, self.king_buckets, self.output_buckets = hidden, king_buckets, output_buckets
        self.mirror, self.eval_scale = mirror, eval_scale
        self.king_map = king_layout(king_buckets)
        self.output_map = output_layout(output_buckets)
        self.w1 = np.zeros((king_buckets, INPUTS, hidden), np.int16)
        self.b1 = np.zeros(hidden, np.int16)
        self.w2 = np.zeros((output_buckets, 2 * hidden), np.int16)
        self.b2 = np.zeros(output_buckets, np.int32)

    def check_bounds(self) -> None:
        if self.hidden % 32 or not 32 <= self.hidden <= 1024:
            raise ValueError("hidden must be a multiple of 32 in 32..1024")
        if int(np.abs(self.w2).max()) > MAX_W2:
            raise ValueError(f"|w2| reaches {int(np.abs(self.w2).max())}, the engine allows 127")
        reach = int(np.abs(self.b1).max()) + 32 * int(np.abs(self.w1).max())
        if reach > 32767:
            raise ValueError(f"max|b1| + 32 max|w1| = {reach}, the engine allows 32767")


def write_net(path: str, net: Net) -> int:
    net.check_bounds()
    header = bytearray(HEADER_BYTES)
    struct.pack_into("<8sIIIIIIIiii", header, 0, MAGIC, 3, HEADER_BYTES, INPUTS, net.hidden, net.king_buckets,
                     net.output_buckets, FLAG_MIRROR if net.mirror else 0, QA, QB, net.eval_scale)
    header[48:112] = bytes(net.king_map)
    header[112:145] = bytes(net.output_map)
    body = (bytes(header) + np.ascontiguousarray(net.w1, "<i2").tobytes() + np.ascontiguousarray(net.b1, "<i2").tobytes()
            + np.ascontiguousarray(net.w2, "<i2").tobytes() + np.ascontiguousarray(net.b2, "<i4").tobytes())
    checksum = fnv1a64(body)
    with open(path, "wb") as fh:
        fh.write(body)
        fh.write(struct.pack("<Q", checksum))
    return checksum


def read_net(path: str) -> Net:
    data = open(path, "rb").read()
    if data[:8] != MAGIC:
        raise ValueError(f"{path}: not a FORGENN3 file")
    version, header_bytes, inputs, hidden, kb, ob, flags, qa, qb, eval_scale = struct.unpack_from("<IIIIIIIiii", data, 8)
    if (version, header_bytes, inputs, qa, qb) != (3, HEADER_BYTES, INPUTS, QA, QB):
        raise ValueError(f"{path}: unexpected header")
    if fnv1a64(data[:-8]) != struct.unpack_from("<Q", data, len(data) - 8)[0]:
        raise ValueError(f"{path}: checksum mismatch")
    net = Net(hidden, kb, ob, bool(flags & FLAG_MIRROR), eval_scale)
    net.king_map = list(data[48:112])
    net.output_map = list(data[112:145])
    off = HEADER_BYTES
    n = kb * INPUTS * hidden
    net.w1 = np.frombuffer(data, "<i2", n, off).reshape(kb, INPUTS, hidden).copy()
    off += 2 * n
    net.b1 = np.frombuffer(data, "<i2", hidden, off).copy()
    off += 2 * hidden
    net.w2 = np.frombuffer(data, "<i2", ob * 2 * hidden, off).reshape(ob, 2 * hidden).copy()
    off += 4 * ob * hidden
    net.b2 = np.frombuffer(data, "<i4", ob, off).copy()
    return net


def random_net(hidden: int = 512, seed: int = 1) -> Net:
    rng = np.random.default_rng(seed)
    net = Net(hidden)
    net.w1 = rng.integers(-40, 41, net.w1.shape).astype(np.int16)
    net.b1 = rng.integers(-200, 201, hidden).astype(np.int16)
    net.w2 = rng.integers(-MAX_W2, MAX_W2 + 1, net.w2.shape).astype(np.int16)
    net.b2 = rng.integers(-5000, 5001, net.output_buckets).astype(np.int32)
    return net


def _tdiv(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def feature_rows(net: Net, codes: np.ndarray, white_to_move: bool) -> tuple[list[int], list[int]]:
    """The input indices of one position for (side to move, other side). codes: 64 piece codes, 0 empty,
    1..6 white PNBRQK, 7..12 black, square 0 = a1."""
    rows = []
    for persp_white in (white_to_move, not white_to_move):
        ksq = int(np.nonzero(codes == (6 if persp_white else 12))[0][0])
        kr = ksq if persp_white else ksq ^ 56
        flip = 7 if (net.mirror and (kr & 7) >= 4) else 0
        bucket = net.king_map[kr]
        idx = []
        for sq in np.nonzero(codes)[0]:
            c = int(codes[sq]) - 1
            white_piece, ptype = c < 6, c % 6
            r = (int(sq) if persp_white else int(sq) ^ 56) ^ flip
            idx.append(bucket * INPUTS + ((0 if white_piece == persp_white else 1) * 6 + ptype) * 64 + r)
        rows.append(idx)
    return rows[0], rows[1]


def reference_eval(net: Net, codes: np.ndarray, white_to_move: bool) -> int:
    """The engine's value in centipawns from the side to move, computed here with plain integers."""
    ours, theirs = feature_rows(net, codes, white_to_move)
    w1 = net.w1.reshape(-1, net.hidden).astype(np.int64)
    a = np.clip(net.b1.astype(np.int64) + w1[ours].sum(0), 0, QA)
    b = np.clip(net.b1.astype(np.int64) + w1[theirs].sum(0), 0, QA)
    ob = net.output_map[min(int(np.count_nonzero(codes)), 32)]
    w2 = net.w2[ob].astype(np.int64)
    s = int((a * a * w2[:net.hidden]).sum() + (b * b * w2[net.hidden:]).sum())
    out = _tdiv(s, QA) + int(net.b2[ob])
    return max(-30000, min(30000, _tdiv(out * net.eval_scale, QA * QB)))


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "random":
        net = random_net(int(sys.argv[3]) if len(sys.argv) > 3 else 512, int(sys.argv[4]) if len(sys.argv) > 4 else 1)
        print(f"wrote {sys.argv[2]}, checksum {write_net(sys.argv[2], net):016x}")
        return 0
    if len(sys.argv) >= 3 and sys.argv[1] == "info":
        net = read_net(sys.argv[2])
        print(f"hidden {net.hidden}, king buckets {net.king_buckets}{' mirrored' if net.mirror else ''}, output buckets "
              f"{net.output_buckets}, eval scale {net.eval_scale}, max|w1| {int(np.abs(net.w1).max())}, "
              f"max|b1| {int(np.abs(net.b1).max())}, max|w2| {int(np.abs(net.w2).max())}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
