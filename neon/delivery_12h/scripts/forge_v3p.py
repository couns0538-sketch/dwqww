"""FORGENN3-P: Backward-compatible extension of FORGENN3 adding:
  - FlagPairwise (4): Pairwise CReLU activation a_lo * a_hi (hidden/2 pairs per perspective; w2 shape [OB, hidden])
  - FlagPsqt     (8): Direct per-king-bucket per-output-bucket PSQT (int32 [KB, 768, OB], scale QA * QB = 16320)

Any file without FlagPairwise / FlagPsqt is 100% bit-identical to pipeline/forge_v3.py.
Exact integer arithmetic (QA=255, QB=64, |w2|<=127, |psqt|<=261120):
  - Pairwise sum: sum_{h=0..H/2-1} a_us[h]*a_us[h+H/2]*w2[ob][h] + a_them[h]*a_them[h+H/2]*w2[ob][H/2+h]
  - PSQT term:    trunc((sum_{f in us} psqt[f][ob] - sum_{f in them} psqt[f][ob]) / 2)
  - out = trunc(sum / QA) + b2[ob] + psqt_term
  - cp  = clamp(trunc(out * eval_scale / (QA * QB)), -30000, 30000)
"""
from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipeline"))
import forge_v3 as base  # noqa: E402

MAGIC = base.MAGIC
HEADER_BYTES = base.HEADER_BYTES
INPUTS = base.INPUTS
QA = base.QA
QB = base.QB
MAX_W2 = base.MAX_W2
MAX_PSQT = 16 * QA * QB  # 261,120 -> 32 * 261,120 = 8,355,840 << 2^31 (overflow-free int32)
FLAG_RESIDUAL = 1
FLAG_MIRROR = 2
FLAG_PAIRWISE = 4
FLAG_PSQT = 8


def king_layout(n: int = 8) -> list[int]:
    """Return 64-square mirrored king bucket map (delegates 1/4/8 to forge_v3; adds 16-bucket layout)."""
    if n in (1, 4, 8):
        return base.king_layout(n)
    if n == 16:
        # Data-balanced 16 mirrored king buckets (calibrated via OPENING_AND_KB16_DIVERSITY.json):
        # Rank 1: a1(0), b1(1), c1(2), d1(3); Rank 2: a2(4), b2(5), c2(6), d2(7);
        # Rank 3: ab(8), cd(9); Rank 4: ab(10), cd(11);
        # Ranks 5-6: ab(12), cd(13); Ranks 7-8: ab(14), cd(15) — avoids ultra-sparse 4-way rank 7-8 split!
        half = (
            [0, 1, 2, 3]
            + [4, 5, 6, 7]
            + [8, 8, 9, 9]
            + [10, 10, 11, 11]
            + [12, 12, 13, 13]
            + [12, 12, 13, 13]
            + [14, 14, 15, 15]
            + [14, 14, 15, 15]
        )
        full = [0] * 64
        for sq in range(64):
            rank, file = sq >> 3, sq & 7
            full[sq] = half[rank * 4 + (file if file < 4 else 7 - file)]
        return full
    raise ValueError(f"no layout for {n} king buckets (1, 4, 8, 16)")


class NetP:
    def __init__(self, hidden: int, king_buckets: int = 8, output_buckets: int = 8, mirror: bool = True,
                 pairwise: bool = True, has_psqt: bool = True, eval_scale: int = 400,
                 king_map: list[int] | None = None):
        self.hidden = hidden
        self.king_buckets = king_buckets
        self.output_buckets = output_buckets
        self.mirror = mirror
        self.pairwise = pairwise
        self.has_psqt = has_psqt
        self.eval_scale = eval_scale
        self.king_map = list(king_map) if king_map is not None else king_layout(king_buckets)
        self.output_map = base.output_layout(output_buckets)
        self.w1 = np.zeros((king_buckets, INPUTS, hidden), np.int16)
        self.b1 = np.zeros(hidden, np.int16)
        w2_cols = hidden if pairwise else 2 * hidden
        self.w2 = np.zeros((output_buckets, w2_cols), np.int16)
        self.b2 = np.zeros(output_buckets, np.int32)
        self.psqt = np.zeros((king_buckets, INPUTS, output_buckets), np.int32) if has_psqt else None

    def check_bounds(self) -> None:
        step = 64 if self.pairwise else 32
        h_max = 1536 if self.pairwise else 1024
        if self.hidden % step or not step <= self.hidden <= h_max:
            raise ValueError(f"hidden must be a multiple of {step} in {step}..{h_max}, got {self.hidden}")
        if not 1 <= self.king_buckets <= 32 or not 1 <= self.output_buckets <= 16:
            raise ValueError(f"invalid bucket counts kb={self.king_buckets} ob={self.output_buckets}")
        if not 1 <= self.eval_scale <= 10000:
            raise ValueError(f"eval_scale {self.eval_scale} outside 1..10000")
        w2_max = int(np.abs(self.w2.astype(np.int64)).max())
        if w2_max > MAX_W2:
            raise ValueError(f"|w2| reaches {w2_max}, max is {MAX_W2}")
        reach = int(np.abs(self.b1.astype(np.int64)).max()) + 32 * int(np.abs(self.w1.astype(np.int64)).max())
        if reach > 32767:
            raise ValueError(f"max|b1| + 32 max|w1| = {reach} > 32767")
        if self.has_psqt:
            assert self.psqt is not None and self.psqt.shape == (self.king_buckets, INPUTS, self.output_buckets)
            p_max = int(np.abs(self.psqt.astype(np.int64)).max())
            if p_max > MAX_PSQT:
                raise ValueError(f"|psqt| reaches {p_max}, max is {MAX_PSQT}")


def write_net(path: str, net: NetP) -> int:
    net.check_bounds()
    flags = (FLAG_MIRROR if net.mirror else 0) | (FLAG_PAIRWISE if net.pairwise else 0) | (FLAG_PSQT if net.has_psqt else 0)
    header = bytearray(HEADER_BYTES)
    struct.pack_into("<8sIIIIIIIiii", header, 0, MAGIC, 3, HEADER_BYTES, INPUTS, net.hidden,
                     net.king_buckets, net.output_buckets, flags, QA, QB, net.eval_scale)
    header[48:112] = bytes(net.king_map)
    header[112:145] = bytes(net.output_map)
    parts = [
        bytes(header),
        np.ascontiguousarray(net.w1, "<i2").tobytes(),
        np.ascontiguousarray(net.b1, "<i2").tobytes(),
        np.ascontiguousarray(net.w2, "<i2").tobytes(),
        np.ascontiguousarray(net.b2, "<i4").tobytes(),
    ]
    if net.has_psqt:
        parts.append(np.ascontiguousarray(net.psqt, "<i4").tobytes())
    body = b"".join(parts)
    checksum = base.fnv1a64(body)
    tmp = str(path) + ".part"
    with open(tmp, "wb") as fh:
        fh.write(body)
        fh.write(struct.pack("<Q", checksum))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return checksum


def read_net(path: str) -> NetP:
    data = open(path, "rb").read()
    if data[:8] != MAGIC:
        raise ValueError(f"{path}: bad magic")
    version, header_bytes, inputs, hidden, kb, ob, flags, qa, qb, eval_scale = struct.unpack_from("<IIIIIIIiii", data, 8)
    if (version, header_bytes, inputs, qa, qb) != (3, HEADER_BYTES, INPUTS, QA, QB):
        raise ValueError(f"{path}: unexpected header")
    if base.fnv1a64(data[:-8]) != struct.unpack_from("<Q", data, len(data) - 8)[0]:
        raise ValueError(f"{path}: checksum mismatch")
    pairwise = bool(flags & FLAG_PAIRWISE)
    has_psqt = bool(flags & FLAG_PSQT)
    net = NetP(hidden, kb, ob, bool(flags & FLAG_MIRROR), pairwise, has_psqt, eval_scale)
    net.king_map = list(data[48:112])
    net.output_map = list(data[112:145])
    off = HEADER_BYTES
    n1 = kb * INPUTS * hidden
    net.w1 = np.frombuffer(data, "<i2", n1, off).reshape(kb, INPUTS, hidden).copy(); off += 2 * n1
    net.b1 = np.frombuffer(data, "<i2", hidden, off).copy(); off += 2 * hidden
    w2_cols = hidden if pairwise else 2 * hidden
    n2 = ob * w2_cols
    net.w2 = np.frombuffer(data, "<i2", n2, off).reshape(ob, w2_cols).copy(); off += 2 * n2
    net.b2 = np.frombuffer(data, "<i4", ob, off).copy(); off += 4 * ob
    if has_psqt:
        np_cnt = kb * INPUTS * ob
        net.psqt = np.frombuffer(data, "<i4", np_cnt, off).reshape(kb, INPUTS, ob).copy(); off += 4 * np_cnt
    assert off + 8 == len(data), f"{path}: size mismatch {off + 8} != {len(data)}"
    return net


def _tdiv(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def reference_eval(net: NetP, codes: np.ndarray, white_to_move: bool) -> int:
    ours, theirs = base.feature_rows(net, codes, white_to_move)
    w1 = net.w1.reshape(-1, net.hidden).astype(np.int64)
    a = np.clip(net.b1.astype(np.int64) + w1[ours].sum(0), 0, QA)
    b = np.clip(net.b1.astype(np.int64) + w1[theirs].sum(0), 0, QA)
    ob = net.output_map[min(int(np.count_nonzero(codes)), 32)]
    w2 = net.w2[ob].astype(np.int64)
    if net.pairwise:
        half = net.hidden // 2
        s = int((a[:half] * a[half:] * w2[:half]).sum() + (b[:half] * b[half:] * w2[half:]).sum())
    else:
        s = int((a * a * w2[:net.hidden]).sum() + (b * b * w2[net.hidden:]).sum())
    psqt_term = 0
    if net.has_psqt:
        ps = net.psqt.reshape(-1, net.output_buckets).astype(np.int64)
        p_us = int(ps[ours, ob].sum())
        p_th = int(ps[theirs, ob].sum())
        psqt_term = _tdiv(p_us - p_th, 2)
    out = _tdiv(s, QA) + int(net.b2[ob]) + psqt_term
    return max(-30000, min(30000, _tdiv(out * net.eval_scale, QA * QB)))


def selftest() -> None:
    rng = np.random.default_rng(7)
    # 1. Standard v3 net bit-exact parity with pipeline/forge_v3.py
    n_old = base.random_net(512, seed=3)
    p3 = Path(r"C:\nnue-lab\neon\forge_fixes\_tmp_test_v3.fnn3")
    base.write_net(str(p3), n_old)
    n_read = read_net(str(p3))
    codes = np.zeros(64, dtype=np.uint8)
    codes[4] = 6; codes[60] = 12; codes[12] = 1; codes[52] = 7; codes[3] = 5; codes[59] = 11
    assert reference_eval(n_read, codes, True) == base.reference_eval(n_old, codes, True)
    p3.unlink()
    # 2. Pairwise + PSQT round-trip + exact color-flip symmetry!
    np_net = NetP(hidden=1024, pairwise=True, has_psqt=True)
    np_net.w1 = rng.integers(-30, 31, np_net.w1.shape, dtype=np.int16)
    np_net.b1 = rng.integers(-100, 101, np_net.b1.shape, dtype=np.int16)
    np_net.w2 = rng.integers(-MAX_W2, MAX_W2 + 1, np_net.w2.shape, dtype=np.int16)
    np_net.b2 = rng.integers(-4000, 4001, np_net.b2.shape, dtype=np.int32)
    np_net.psqt = rng.integers(-5000, 5001, np_net.psqt.shape, dtype=np.int32)
    pp = Path(r"C:\nnue-lab\neon\forge_fixes\_tmp_test_v3p.fnn3")
    cs = write_net(str(pp), np_net)
    np_r = read_net(str(pp))
    ev1 = reference_eval(np_net, codes, True)
    ev2 = reference_eval(np_r, codes, True)
    assert ev1 == ev2
    # Color-flip codes: rank^56 and swap 1..6 <-> 7..12 -> MUST give identical eval!
    flipped = np.zeros(64, dtype=np.uint8)
    for sq in range(64):
        c = codes[sq]
        if c:
            flipped[sq ^ 56] = (c + 6) if c <= 6 else (c - 6)
    assert reference_eval(np_r, flipped, False) == ev2
    pp.unlink()
    print(f"FORGE_V3P SELFTEST PASS (v3 parity=0cp, v3p checksum={cs:016x}, ev={ev2}, color_flip_diff=0)")


if __name__ == "__main__":
    selftest()
