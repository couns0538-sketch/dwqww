#!/usr/bin/env python3
"""Forge NNUE file format v2 ("FORGENN2"): reader, writer, king-bucket layouts and a converter.

Format (little-endian; the engine's loader is forge::nnue::v2::load in src/nnue.cpp):
  0   char[8] "FORGENN2"        8   u32 version = 2           12  u32 header_bytes = 160
  16  u32 feature_set           20  u32 inputs = 768          24  u32 hidden H
      (feature_set 0 = piece-square inputs only; bit 0 = threat inputs, O6: a block wt[9216][H] follows w1;
       bit 1 = pawn-pair inputs, O7: a block wp[1792][H] follows w1 / wt)
  28  u32 king_buckets KB 1-32  32  u32 output_buckets OB     36  u32 flags: bit0 residual, bit1 king mirror
  40  f32 weight_scale 4096     44  f32 output_scale 4096     48  f32 sigmoid_k 2.25
  52  u8  king_bucket_map[64]   own-king square in the perspective's frame (rank-flipped for Black,
                                a1 = 0), BEFORE mirroring -> bucket
  116 u8  output_bucket_map[33] total piece count 0..32 (kings included) -> output bucket (C5; all 0 when OB = 1);
                                default map output_layout(N): n = pieces - 2 -> min(N - 1, n * N // 32)
  149 u8  reserved[11] = 0
  160 i16 w1[KB][768][H]  i16 b1[H]  i16 w2[OB][2H]  i16 b2[OB]   (round(w * 4096))
  end u64 FNV-1a 64 of every preceding byte

Feature of piece pc on square s for perspective p with own king on k (engine and trainer):
  r = s if p is White else s ^ 56;  kr = k if p is White else k ^ 56
  flip = 7 if (mirror and kr % 8 >= 4) else 0
  index = king_bucket_map[kr] * 768 + ((0 if colour(pc) == p else 1) * 6 + type(pc) - 1) * 64 + (r ^ flip)

Pure Python (struct/array); numpy arrays are accepted as weight inputs.

CLI:
  forge_nnue_v2.py info <net.fnn2>
  forge_nnue_v2.py from-inc <nnue_weights.inc> <out.fnn2> [--replica r1|r4|rm2|rm8|rm16] [--output-buckets N]
      Converts a compiled-in (v1) network. Every replica evaluates exactly like the v1 network, so a
      search with it must reproduce the v1 bench node counts: r1 = 1 bucket; r4 = 4 identical buckets
      (king-bucket changes, no mirroring); rm2 / rm8 / rm16 = mirrored nets whose e-h half buckets hold
      the file-flipped v1 weights (rm8 / rm16 refresh exactly where a mirrored 4- / 8-bucket net does).
      --output-buckets N (C5) replicates the output layer into N identical heads with output_layout(N).
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from array import array

MAGIC = b"FORGENN2"
VERSION = 2
HEADER_BYTES = 160
INPUTS = 768
FLAG_RESIDUAL = 1
FLAG_MIRROR = 2
FEATURE_SET_THREATS = 1          # O6: threat inputs (definition in include/forge/nnue_v2.hpp at ThreatFeatures)
THREAT_FEATURES = 12 * 12 * 64
FEATURE_SET_PAWN_PAIRS = 2       # O7: pawn-pair inputs (definition in include/forge/nnue_v2.hpp at PawnPairFeatures)
PAWN_PAIR_FEATURES = 4 * 7 * 64
WEIGHT_SCALE = 4096.0
OUTPUT_SCALE = 4096.0
SIGMOID_K = 2.25


def fnv1a64(data: bytes) -> int:
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


# ----------------------------------------------------------------------------- king bucket layouts
# Half-board layouts: 32 entries, index rank * 4 + file for files a-d (file 0 = a) of the perspective's
# own side after mirroring (a king on g1 counts as b1), ranks 1-8 from the perspective's back rank.
_LAYOUT_ROWS = {
    1: ["0000"] * 8,
    2: ["0000", "0000"] + ["1111"] * 6,
    4: ["0011", "0011", "2222", "2222"] + ["3333"] * 4,
    6: ["0011", "2233", "4444", "4444"] + ["5555"] * 4,
    8: ["0123", "4455", "6666"] + ["7777"] * 5,
    16: ["0123", "4567", "8899", "aabb", "cccc", "dddd", "eeee", "ffff"],
}


def half_layout(buckets: int) -> list[int]:
    """Standard half-board layout (32 entries) for 1, 2, 4, 6, 8, 16 or 32 buckets."""
    if buckets == 32:
        return list(range(32))
    if buckets not in _LAYOUT_ROWS:
        raise ValueError(f"no standard layout for {buckets} king buckets (have 1, 2, 4, 6, 8, 16, 32)")
    return [int(ch, 16) for row in _LAYOUT_ROWS[buckets] for ch in row]


def half_index(square: int) -> int:
    """Half-board index of a perspective-relative square (files e-h fold onto d-a)."""
    f, r = square & 7, square >> 3
    return r * 4 + (f if f < 4 else 7 - f)


def symmetric_map(half: list[int]) -> list[int]:
    """64-entry map with map[s] == map[s ^ 7] from a 32-entry half-board layout."""
    if len(half) != 32:
        raise ValueError("half-board layout needs 32 entries")
    return [half[half_index(s)] for s in range(64)]


def split_halves_map(half: list[int]) -> tuple[list[int], int]:
    """64-entry map where files e-h use their own buckets (offset by the layout's bucket count)."""
    n = max(half) + 1
    return [half[half_index(s)] + (n if (s & 7) >= 4 else 0) for s in range(64)], 2 * n


def output_layout(buckets: int) -> list[int]:
    """Default output bucket map (33 entries, pieces 0..32 incl. kings): n = pieces - 2 non-king pieces ->
    min(N - 1, n * N // 32); for N = 8: n // 4 (2-5 pieces -> 0, 6-9 -> 1, ..., 30-32 -> 7)."""
    if not 1 <= buckets <= 16:
        raise ValueError("output buckets must be 1-16")
    return [min(buckets - 1, max(p - 2, 0) * buckets // 32) for p in range(33)]


def parse_map(text: str) -> list[int]:
    """'0,0,1,...' with 32 (half-board, mirrored symmetric) or 64 entries -> 64-entry map."""
    vals = [int(x) for x in re.split(r"[,\s]+", text.strip()) if x]
    if len(vals) == 32:
        return symmetric_map(vals)
    if len(vals) == 64:
        return vals
    raise ValueError(f"king map needs 32 or 64 entries, got {len(vals)}")


# ----------------------------------------------------------------------------- read / write
def _i16_bytes(values, count: int, name: str) -> bytes:
    try:  # numpy fast path
        import numpy as np  # noqa: WPS433
        if isinstance(values, np.ndarray):
            a = values.astype("<i2", copy=False).ravel()
            if a.size != count:
                raise ValueError(f"{name}: {a.size} values, expected {count}")
            if values.dtype.kind == "f" or (values.min(initial=0) < -32768 or values.max(initial=0) > 32767):
                raise ValueError(f"{name}: needs int16 values")
            return a.tobytes()
    except ImportError:
        pass
    a = array("h", values)
    if len(a) != count:
        raise ValueError(f"{name}: {len(a)} values, expected {count}")
    if sys.byteorder != "little":
        a.byteswap()
    return a.tobytes()


def write_v2(path, *, hidden: int, king_buckets: int, residual: bool, mirror: bool, king_map, w1, b1, w2, b2,
             output_buckets: int = 1, output_map=None, feature_set: int = 0, wt=None, wp=None) -> int:
    """Writes a v2 file; returns its FNV-1a 64 checksum. w1 order [bucket][feature][hidden]; wt (feature_set bit 0,
    O6) order [threat feature][hidden]."""
    king_map = list(king_map)
    output_map = [0] * 33 if output_map is None else list(output_map)
    if len(king_map) != 64 or any(not 0 <= b < king_buckets for b in king_map):
        raise ValueError("king map needs 64 entries in [0, king_buckets)")
    if len(output_map) != 33 or any(not 0 <= b < output_buckets for b in output_map):
        raise ValueError("output map needs 33 entries in [0, output_buckets)")
    if not 1 <= king_buckets <= 32:
        raise ValueError("king buckets must be 1-32")
    if feature_set & ~(FEATURE_SET_THREATS | FEATURE_SET_PAWN_PAIRS):
        raise ValueError(f"unknown feature set {feature_set}")
    if bool(feature_set & FEATURE_SET_THREATS) != (wt is not None):
        raise ValueError("threat weights (wt) go with feature_set bit 0")
    if bool(feature_set & FEATURE_SET_PAWN_PAIRS) != (wp is not None):
        raise ValueError("pawn-pair weights (wp) go with feature_set bit 1")
    flags = (FLAG_RESIDUAL if residual else 0) | (FLAG_MIRROR if mirror else 0)
    head = MAGIC + struct.pack("<IIIIIIII", VERSION, HEADER_BYTES, feature_set, INPUTS, hidden, king_buckets, output_buckets, flags)
    head += struct.pack("<fff", WEIGHT_SCALE, OUTPUT_SCALE, SIGMOID_K)
    head += bytes(king_map) + bytes(output_map)
    head += bytes(HEADER_BYTES - len(head))
    assert len(head) == HEADER_BYTES
    body = _i16_bytes(w1, king_buckets * INPUTS * hidden, "w1")
    if wt is not None:
        body += _i16_bytes(wt, THREAT_FEATURES * hidden, "wt")
    if wp is not None:
        body += _i16_bytes(wp, PAWN_PAIR_FEATURES * hidden, "wp")
    body += (_i16_bytes(b1, hidden, "b1") + _i16_bytes(w2, output_buckets * 2 * hidden, "w2") +
             _i16_bytes(b2, output_buckets, "b2"))
    data = head + body
    checksum = fnv1a64(data)
    with open(path, "wb") as f:
        f.write(data + struct.pack("<Q", checksum))
    return checksum


def read_v2(path) -> dict:
    data = open(path, "rb").read()
    if len(data) < HEADER_BYTES + 8 or data[:8] != MAGIC:
        raise ValueError("not a FORGENN2 file")
    (version, header_bytes, feature_set, inputs, hidden, kb, ob, flags) = struct.unpack_from("<IIIIIIII", data, 8)
    ws, os_, k = struct.unpack_from("<fff", data, 40)
    if (version != VERSION or header_bytes != HEADER_BYTES or (feature_set & ~(FEATURE_SET_THREATS | FEATURE_SET_PAWN_PAIRS)) or
            inputs != INPUTS):
        raise ValueError("unsupported v2 header")
    stored = struct.unpack_from("<Q", data, len(data) - 8)[0]
    if fnv1a64(data[:-8]) != stored:
        raise ValueError("checksum mismatch")
    threats = bool(feature_set & FEATURE_SET_THREATS)
    pawn_pairs = bool(feature_set & FEATURE_SET_PAWN_PAIRS)
    names = ["w1"] + (["wt"] if threats else []) + (["wp"] if pawn_pairs else []) + ["b1", "w2", "b2"]
    counts = ([kb * INPUTS * hidden] + ([THREAT_FEATURES * hidden] if threats else []) +
              ([PAWN_PAIR_FEATURES * hidden] if pawn_pairs else []) + [hidden, ob * 2 * hidden, ob])
    if len(data) != HEADER_BYTES + 2 * sum(counts) + 8:
        raise ValueError("size mismatch")
    out = dict(version=version, hidden=hidden, king_buckets=kb, output_buckets=ob,
               residual=bool(flags & FLAG_RESIDUAL), mirror=bool(flags & FLAG_MIRROR),
               weight_scale=ws, output_scale=os_, sigmoid_k=k, checksum=stored,
               king_map=list(data[52:116]), output_map=list(data[116:149]), feature_set=feature_set,
               threats=threats, wt=None, pawn_pairs=pawn_pairs, wp=None)
    off = HEADER_BYTES
    for name, n in zip(names, counts):
        a = array("h")
        a.frombytes(data[off:off + 2 * n])
        if sys.byteorder != "little":
            a.byteswap()
        out[name] = a
        off += 2 * n
    return out


def read_inc(path) -> dict:
    """Arrays of a compiled-in network include file (train_resid*.py export)."""
    text = open(path, encoding="ascii").read()
    m = re.search(r"#define FORGE_NNUE_RESIDUAL\s+(\d)", text)
    residual = bool(int(m.group(1))) if m else False

    def arr(name):
        mm = re.search(name + r"\[(\d+)\]\s*=\s*\{([^}]*)\}", text, re.S)
        vals = array("h", (int(x) for x in mm.group(2).replace("\n", " ").split(",") if x.strip()))
        if len(vals) != int(mm.group(1)):
            raise ValueError(f"{name}: size mismatch")
        return vals
    b2 = int(re.search(r"NnueB2\s*=\s*(-?\d+)", text).group(1))
    w1, b1, w2 = arr("NnueW1"), arr("NnueB1"), arr("NnueW2")
    hidden = len(b1)
    if len(w1) != INPUTS * hidden or len(w2) != 2 * hidden:
        raise ValueError("unexpected include shapes")
    return dict(w1=w1, b1=b1, w2=w2, b2=array("h", [b2]), residual=residual, hidden=hidden)


def flipped_files(w1_bucket, hidden: int):
    """Weights of one bucket with every square mirrored horizontally (feature (pt, s) <- (pt, s ^ 7))."""
    out = array("h", bytes(2 * INPUTS * hidden))
    for f in range(INPUTS):
        src = (f & ~63) | ((f & 63) ^ 7)
        out[f * hidden:(f + 1) * hidden] = w1_bucket[src * hidden:(src + 1) * hidden]
    return out


def with_zero_threats(net: dict) -> dict:
    """O6: the same net with a threat block of zeros (feature_set bit 0): it evaluates exactly like `net`, so a search
    with it runs the threat-input machinery on the tree of `net` (engine cost of threat inputs at equal nodes)."""
    return dict(net, feature_set=net.get("feature_set", 0) | FEATURE_SET_THREATS,
                wt=array("h", bytes(2 * THREAT_FEATURES * net["hidden"])))


def with_zero_pawn_pairs(net: dict) -> dict:
    """O7: the same net with a pawn-pair block of zeros (feature_set bit 1): it evaluates exactly like `net`."""
    return dict(net, feature_set=net.get("feature_set", 0) | FEATURE_SET_PAWN_PAIRS,
                wp=array("h", bytes(2 * PAWN_PAIR_FEATURES * net["hidden"])))


def replica(inc: dict, kind: str, output_buckets: int = 1) -> dict:
    """v2 network that evaluates exactly like the v1 include (see module docstring)."""
    hidden, w1 = inc["hidden"], inc["w1"]
    if kind == "r1":
        kb, mirror, kmap, flips = 1, False, [0] * 64, [False]
    elif kind == "r4":
        kb, mirror, kmap, flips = 4, False, symmetric_map(half_layout(4)), [False] * 4
    elif kind in ("rm2", "rm8", "rm16"):
        base = {"rm2": 1, "rm8": 4, "rm16": 8}[kind]
        kmap, kb = split_halves_map(half_layout(base))
        mirror, flips = True, [b >= base for b in range(kb)]
    else:
        raise ValueError(f"unknown replica {kind}")
    flipped = flipped_files(w1, hidden) if any(flips) else None
    big = array("h")
    for b in range(kb):
        big.extend(flipped if flips[b] else w1)
    w2, b2 = array("h"), array("h")
    for _ in range(output_buckets):   # C5: identical heads
        w2.extend(inc["w2"])
        b2.extend(inc["b2"])
    return dict(hidden=hidden, king_buckets=kb, residual=inc["residual"], mirror=mirror, king_map=kmap,
                w1=big, b1=inc["b1"], w2=w2, b2=b2, output_buckets=output_buckets,
                output_map=output_layout(output_buckets))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info")
    p.add_argument("net")
    p = sub.add_parser("from-inc")
    p.add_argument("inc")
    p.add_argument("out")
    p.add_argument("--replica", default="r1", choices=["r1", "r4", "rm2", "rm8", "rm16"])
    p.add_argument("--threats-zero", action="store_true", help="O6: add a threat block of zeros (feature_set bit 0)")
    p.add_argument("--pawn-pairs-zero", action="store_true", help="O7: add a pawn-pair block of zeros (feature_set bit 1)")
    p.add_argument("--output-buckets", type=int, default=1, help="identical output heads (C5), default map")
    a = ap.parse_args(argv)
    if a.cmd == "info":
        n = read_v2(a.net)
        print(f"{a.net}: hidden {n['hidden']} king_buckets {n['king_buckets']} mirror {n['mirror']} "
              f"output_buckets {n['output_buckets']} residual {n['residual']} threats {n['threats']} "
              f"pawn_pairs {n['pawn_pairs']} fnv1a {n['checksum']:016x}")
        print("king map (rank 8 first, files a-h, perspective frame):")
        for r in range(7, -1, -1):
            print("  " + " ".join(f"{n['king_map'][r * 8 + f]:2d}" for f in range(8)))
        print("output map (pieces 0..32):", " ".join(map(str, n["output_map"])))
        return 0
    net = replica(read_inc(a.inc), a.replica, a.output_buckets)
    if a.threats_zero:
        net = with_zero_threats(net)
    if a.pawn_pairs_zero:
        net = with_zero_pawn_pairs(net)
    checksum = write_v2(a.out, **net)
    print(f"wrote {a.out}: replica {a.replica}{' + zero threat inputs' if a.threats_zero else ''}"
          f"{' + zero pawn-pair inputs' if a.pawn_pairs_zero else ''}, king_buckets "
          f"{net['king_buckets']}, mirror {net['mirror']}, output_buckets {net['output_buckets']}, fnv1a {checksum:016x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
