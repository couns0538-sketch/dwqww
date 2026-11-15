#!/usr/bin/env python3
"""FORGENN4 (blind implementation) - job 5 part A.

Written ONLY from the specification in FABLE_TO_deepseek_5.md. No engine code for
FORGENN4 exists in the repository and none was consulted; the only related code I had
read before is FORGENN3 (nnue_v3.hpp / nnue_v3.cpp), which the spec says this is a
superset of.

Arithmetic (all integer; "/" truncates toward zero as in C/C++):
 1. acc[p][h] = b1[h] + sum over that perspective's features of w1[index][h]
 2. a[p][h]    = clamp(acc[p][h], 0, 255); v = a[us][0..H-1] then a[them][0..H-1]
 3. ob         = output_bucket_map[min(pieces, 32)]
 4. direct     = (sum_i v_i*v_i*w2[ob][i]) / 255 + b2[ob]
 5. x_i        = v_i*v_i / 255                      (0..255)
    s1_j      = b1d[ob][j] + sum_i x_i*w1d[ob][j][i]          for j < 16
    y1_j      = clamp(s1_j, 0, 16320) * 127 / 16320            (0..127)
 6. s2_k      = b2d[ob][k] + sum_j y1_j*w2d[ob][k][j]          for k < 32
    y2_k      = clamp(s2_k, 0, 8128) / 64                      (0..127)
 7. dense     = b3d[ob] + sum_k y2_k*w3d[ob][k]
 8. cp         = (direct + dense) * eval_scale / 16320, clamped to +-30000

The spec states that the values divided in steps 4-7 are never negative, so truncating
division and floor division agree there; trunc_div is used anyway so the intent is
explicit.

Usage:
  python3 -I forge_v4.py random  <out.fnn4> <seed>
  python3 -I forge_v4.py values  <net.fnn4> <fens.txt> <out.txt>
  python3 -I forge_v4.py detail  <net.fnn4> <fens.txt> <count> <out.jsonl>
  python3 -I forge_v4.py info    <net.fnn4>
"""
import json
import struct
import sys

import numpy as np

MAGIC = b"FORGENN4"
VERSION = 4
HEADER_BYTES = 192
INPUTS = 768
QA = 255
MAX_PIECES = 32
D1 = 16
D2 = 32

# From the spec's bounds section.
MAX_W2 = 127
MAX_W1D = 127
MAX_W2D = 127
MAX_B1D = 2 ** 28
MAX_B2D = 2 ** 28
MAX_B3D = 2 ** 28
Y1_CAP = 16320
Y2_CAP = 8128


def trunc_div(a, b):
    """C/C++ division: truncate toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def fnv1a64(data):
    h = 14695981039346656037
    for b in memoryview(data):
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


# ---- the test-net recipe from the spec ----

def king_layout_8():
    """rank 0..7, file 0..7 (a1 first); digit at rank*4 + min(file, 7-file) of the string."""
    rows = ["0123", "4455", "6666", "7777", "7777", "7777", "7777", "7777"]
    out = [0] * 64
    for rank in range(8):
        for file in range(8):
            out[rank * 8 + file] = int(rows[rank][rank * 0 + min(file, 7 - file)])
    return out


def output_layout_8():
    return [min(7, max(p - 2, 0) * 8 // 32) for p in range(33)]


def make_random_net(seed, H=512, KB=8, OB=8):
    """Exactly the draw order the spec gives."""
    rng = np.random.default_rng(seed)
    net = {
        "H": H, "KB": KB, "OB": OB, "flags": 2, "eval_scale": 400,
        "king_map": king_layout_8() if KB == 8 else None,
        "output_map": output_layout_8() if OB == 8 else None,
        "D1": D1, "D2": D2, "w_scale": 64, "act_max": 127,
    }
    if net["king_map"] is None or net["output_map"] is None:
        raise SystemExit("the test-net recipe fixes KB = 8 and OB = 8")
    net["w1"] = rng.integers(-40, 41, size=(KB, INPUTS, H), dtype=np.int64)
    net["b1"] = rng.integers(-200, 201, size=H, dtype=np.int64)
    net["w2"] = rng.integers(-127, 128, size=(OB, 2 * H), dtype=np.int64)
    net["b2"] = rng.integers(-10000, 10001, size=OB, dtype=np.int64)
    net["w1d"] = rng.integers(-8, 9, size=(OB, D1, 2 * H), dtype=np.int64)
    net["b1d"] = rng.integers(-20000, 20001, size=(OB, D1), dtype=np.int64)
    net["w2d"] = rng.integers(-60, 61, size=(OB, D2, D1), dtype=np.int64)
    net["b2d"] = rng.integers(-2000, 2001, size=(OB, D2), dtype=np.int64)
    net["w3d"] = rng.integers(-255, 256, size=(OB, D2), dtype=np.int64)
    net["b3d"] = rng.integers(-5000, 5001, size=OB, dtype=np.int64)
    return net


def write_net(path, net):
    H, KB, OB = net["H"], net["KB"], net["OB"]
    header = bytearray(HEADER_BYTES)
    struct.pack_into("<8sIIIIIIIiii", header, 0, MAGIC, VERSION, HEADER_BYTES, INPUTS, H,
                     KB, OB, net["flags"], QA, 64, net["eval_scale"])
    header[48:112] = bytes(net["king_map"])
    header[112:145] = bytes(net["output_map"])
    # 145..147 zero (already), 148 D1, 152 D2, 156 w_scale, 160 act_max, 164..191 zero
    struct.pack_into("<IIii", header, 148, net["D1"], net["D2"], net["w_scale"], net["act_max"])
    body = bytes(header)
    body += np.ascontiguousarray(net["w1"], dtype="<i2").tobytes()
    body += np.ascontiguousarray(net["b1"], dtype="<i2").tobytes()
    body += np.ascontiguousarray(net["w2"], dtype="<i2").tobytes()
    body += np.ascontiguousarray(net["b2"], dtype="<i4").tobytes()
    body += np.ascontiguousarray(net["w1d"], dtype="<i1").tobytes()
    body += np.ascontiguousarray(net["b1d"], dtype="<i4").tobytes()
    body += np.ascontiguousarray(net["w2d"], dtype="<i1").tobytes()
    body += np.ascontiguousarray(net["b2d"], dtype="<i4").tobytes()
    body += np.ascontiguousarray(net["w3d"], dtype="<i2").tobytes()
    body += np.ascontiguousarray(net["b3d"], dtype="<i4").tobytes()
    checksum = fnv1a64(body)
    with open(path, "wb") as f:
        f.write(body)
        f.write(struct.pack("<Q", checksum))
    return checksum, len(body) + 8


def expected_size(H, KB, OB, D1n=D1, D2n=D2):
    return (HEADER_BYTES
            + 2 * KB * INPUTS * H            # w1
            + 2 * H                          # b1
            + 2 * OB * 2 * H                 # w2
            + 4 * OB                         # b2
            + OB * D1n * 2 * H               # w1d (i8)
            + 4 * OB * D1n                   # b1d
            + OB * D2n * D1n                 # w2d (i8)
            + 4 * OB * D2n                   # b2d
            + 2 * OB * D2n                   # w3d
            + 4 * OB                         # b3d
            + 8)                             # checksum


def load_net(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != MAGIC:
        raise SystemExit(f"{path}: bad magic")
    (version, header_bytes, inputs, H, KB, OB, flags) = struct.unpack_from("<IIIIIII", data, 8)
    (qa, qb, eval_scale) = struct.unpack_from("<iii", data, 36)
    if version != 4 or header_bytes != HEADER_BYTES or inputs != INPUTS:
        raise SystemExit(f"{path}: bad header")
    if qa != QA or qb != 64:
        raise SystemExit(f"{path}: bad quantisation {qa}/{qb}")
    net = {"H": H, "KB": KB, "OB": OB, "flags": flags, "eval_scale": eval_scale}
    net["king_map"] = list(data[48:112])
    net["output_map"] = list(data[112:145])
    (d1, d2, w_scale, act_max) = struct.unpack_from("<IIii", data, 148)
    net["D1"], net["D2"], net["w_scale"], net["act_max"] = d1, d2, w_scale, act_max
    size = expected_size(H, KB, OB, d1, d2)
    if len(data) != size:
        raise SystemExit(f"{path}: size {len(data)} != expected {size}")
    checksum = struct.unpack_from("<Q", data, len(data) - 8)[0]
    if fnv1a64(data[:-8]) != checksum:
        raise SystemExit(f"{path}: checksum mismatch")
    net["checksum"] = checksum

    off = HEADER_BYTES
    def take(dtype, count, shape):
        nonlocal off
        arr = np.frombuffer(data, dtype=dtype, count=count, offset=off).astype(np.int64)
        off += count * np.dtype(dtype).itemsize
        return arr.reshape(shape)

    net["w1"] = take("<i2", KB * INPUTS * H, (KB, INPUTS, H))
    net["b1"] = take("<i2", H, (H,))
    net["w2"] = take("<i2", OB * 2 * H, (OB, 2 * H))
    net["b2"] = take("<i4", OB, (OB,))
    net["w1d"] = take("<i1", OB * d1 * 2 * H, (OB, d1, 2 * H))
    net["b1d"] = take("<i4", OB * d1, (OB, d1))
    net["w2d"] = take("<i1", OB * d2 * d1, (OB, d2, d1))
    net["b2d"] = take("<i4", OB * d2, (OB, d2))
    net["w3d"] = take("<i2", OB * d2, (OB, d2))
    net["b3d"] = take("<i4", OB, (OB,))
    if off != len(data) - 8:
        raise SystemExit(f"{path}: consumed {off}, expected {len(data) - 8}")

    # Bounds the spec says a reader must refuse to break.
    if int(np.abs(net["w2"]).max()) > MAX_W2:
        raise SystemExit(f"{path}: |w2| > {MAX_W2}")
    acc_max = int(np.abs(net["b1"]).max()) + 32 * int(np.abs(net["w1"]).max())
    if acc_max > 32767:
        raise SystemExit(f"{path}: accumulator bound {acc_max} > 32767")
    for key, limit in (("w1d", MAX_W1D), ("w2d", MAX_W2D)):
        if int(np.abs(net[key]).max()) > limit:
            raise SystemExit(f"{path}: |{key}| > {limit}")
    for key in ("b1d", "b2d", "b3d"):
        if int(np.abs(net[key]).max()) > MAX_B1D:
            raise SystemExit(f"{path}: |{key}| > 2^28")
    if flags & 1:
        raise SystemExit(f"{path}: FORGENN4 nets must be stand-alone (flag bit 0 must be 0)")
    return net


# ---- board side: FEN placement + side to move only (the features need nothing else) ----

def parse_fen(fen):
    parts = fen.split()
    pieces = {}
    rank, file = 7, 0
    for ch in parts[0]:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            kind = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6}[ch.lower()]
            code = kind if ch.isupper() else kind + 6
            pieces[rank * 8 + file] = code
            file += 1
    return pieces, (parts[1] if len(parts) > 1 else "w")


def accumulate(net, pieces, white_perspective, ksq):
    H, KB = net["H"], net["KB"]
    kr = ksq if white_perspective else ksq ^ 56
    flip = 7 if ((net["flags"] & 2) and (kr % 8) >= 4) else 0
    bucket = net["king_map"][kr]
    acc = net["b1"].copy()
    w1_flat = net["w1"].reshape(-1, H)
    for s, code in pieces.items():
        is_white = code <= 6
        rel = 0 if (is_white == white_perspective) else 1
        ptype = (code - 1) % 6
        r = s if white_perspective else s ^ 56
        index = bucket * INPUTS + (rel * 6 + ptype) * 64 + (r ^ flip)
        acc += w1_flat[index]
    return acc, bucket, flip


def evaluate(net, fen, with_detail=False):
    pieces, stm = parse_fen(fen)
    H = net["H"]
    wk = next(s for s, c in pieces.items() if c == 6)
    bk = next(s for s, c in pieces.items() if c == 12)
    acc_w, kb_w, fl_w = accumulate(net, pieces, True, wk)
    acc_b, kb_b, fl_b = accumulate(net, pieces, False, bk)
    us_white = stm == "w"
    ours = acc_w if us_white else acc_b
    theirs = acc_b if us_white else acc_w

    ob = net["output_map"][min(len(pieces), MAX_PIECES)]
    a_us = np.clip(ours, 0, QA)
    a_them = np.clip(theirs, 0, QA)
    v = np.concatenate([a_us, a_them])          # 2H values

    total = int(np.sum(v * v * net["w2"][ob], dtype=np.int64))
    direct = trunc_div(total, QA) + int(net["b2"][ob])          # step 4

    x = (v * v) // QA                                           # step 5, 0..255
    s1 = net["b1d"][ob] + net["w1d"][ob] @ x                    # int32 in numpy int64
    y1 = (np.clip(s1, 0, Y1_CAP) * 127) // Y1_CAP               # 0..127

    s2 = net["b2d"][ob] + net["w2d"][ob] @ y1                   # step 6
    y2 = np.clip(s2, 0, Y2_CAP) // 64                           # 0..127

    dense = int(net["b3d"][ob] + int(net["w3d"][ob] @ y2))      # step 7

    cp = trunc_div((direct + dense) * net["eval_scale"], 16320)  # step 8
    cp = max(-30000, min(30000, cp))
    if with_detail:
        return cp, {
            "ob": int(ob), "direct": int(direct),
            "y1": [int(t) for t in y1], "y2": [int(t) for t in y2],
            "dense": int(dense), "cp": int(cp),
            "kb_w": int(kb_w), "fl_w": int(fl_w), "kb_b": int(kb_b), "fl_b": int(fl_b),
        }
    return cp


def main():
    cmd = sys.argv[1]
    if cmd == "random":
        out, seed = sys.argv[2], int(sys.argv[3])
        net = make_random_net(seed)
        checksum, size = write_net(out, net)
        print(f"wrote {out} seed {seed} size {size} checksum {checksum:016x}")
    elif cmd == "values":
        net_path, fens_path, out_path = sys.argv[2:5]
        net = load_net(net_path)
        with open(fens_path) as f:
            fens = [l.strip() for l in f if l.strip()]
        with open(out_path, "w") as f:
            f.write("\n".join(str(evaluate(net, fen)) for fen in fens) + "\n")
        print(f"{len(fens)} values -> {out_path}")
    elif cmd == "detail":
        net_path, fens_path, count, out_path = sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
        net = load_net(net_path)
        with open(fens_path) as f:
            fens = [l.strip() for l in f if l.strip()][:count]
        with open(out_path, "w") as f:
            for fen in fens:
                cp, detail = evaluate(net, fen, with_detail=True)
                f.write(json.dumps({"fen": fen, "cp": cp, **detail}, sort_keys=True) + "\n")
        print(f"{len(fens)} detail lines -> {out_path}")
    elif cmd == "info":
        net = load_net(sys.argv[2])
        print(json.dumps({"H": net["H"], "KB": net["KB"], "OB": net["OB"],
                          "checksum": f"{net['checksum']:016x}",
                          "eval_scale": net["eval_scale"], "D1": net["D1"], "D2": net["D2"]},
                         sort_keys=True))
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
