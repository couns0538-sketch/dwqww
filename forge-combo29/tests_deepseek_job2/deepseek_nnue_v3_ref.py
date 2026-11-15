#!/usr/bin/env python3
"""Job 2 B1: an independent Python FORGENN3 evaluator.

Written from forge-combo29/include/forge/nnue_v3.hpp (the format and arithmetic
comments) and forge-combo29/src/nnue_v3.cpp (the loader and the scalar reference
path). No other implementation was consulted for this file.

The arithmetic that has to match the engine exactly:

  kr      = perspective == White ? ksq : ksq ^ 56
  flip    = (mirror and (kr & 7) >= 4) ? 7 : 0
  bucket  = king_map[kr]
  index   = bucket*768 + (rel_colour*6 + piece_type-1)*64 + ((perspective==White ? sq : sq^56) ^ flip)

  acc     = b1 + sum of w1[index]                    int16
  a       = clamp(acc, 0, 255)                       SCReLU
  sum     = sum_h a_us[h]^2 * w2[ob][h] + a_them[h]^2 * w2[ob][H+h]
  out     = trunc_div(sum, 255) + b2[ob]
  cp      = trunc_div(out * eval_scale, 255*64), then clamped to +-30000

`trunc_div` is C++ integer division, which truncates toward zero; Python's //
floors, so it is wrong for negatives and is not used here.

Piece codes are Forge's: WP..WK = 1..6, BP..BK = 7..12, colour_of = (code <= 6).
"""
import struct
import sys

import numpy as np

MAGIC = b"FORGENN3"
HEADER_BYTES = 192
INPUTS = 768
QA = 255
QB = 64
MAX_PIECES = 32
FLAG_MIRROR = 2


def trunc_div(a, b):
    """C++ integer division: truncate toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def fnv1a64(data):
    h = 14695981039346656037
    for b in data:
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


class Net:
    __slots__ = ("hidden", "king_buckets", "output_buckets", "flags", "eval_scale",
                 "king_map", "output_map", "w1", "b1", "w2", "b2", "checksum",
                 "mirror", "residual", "path")

    def __init__(self):
        pass

    @property
    def w1_flat(self):
        return self.w1.reshape(-1, self.hidden)


def load_net(path):
    """Reads a FORGENN3 file and checks it the way the engine's loader does."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != MAGIC:
        raise SystemExit(f"{path}: bad magic")
    (version, header_bytes, inputs, hidden, kb, ob, flags) = struct.unpack_from("<IIIIIII", data, 8)
    (qa, qb, eval_scale) = struct.unpack_from("<iii", data, 36)
    if version != 3 or header_bytes != HEADER_BYTES or inputs != INPUTS:
        raise SystemExit(f"{path}: bad header fields")
    if qa != QA or qb != QB:
        raise SystemExit(f"{path}: unexpected quantisation {qa}/{qb}")
    net = Net()
    net.path = path
    net.hidden = hidden
    net.king_buckets = kb
    net.output_buckets = ob
    net.flags = flags
    net.mirror = (flags & FLAG_MIRROR) != 0
    net.residual = (flags & 1) != 0
    net.eval_scale = eval_scale
    net.king_map = list(data[48:112])
    net.output_map = list(data[112:145])
    off = HEADER_BYTES
    n_w1 = kb * INPUTS * hidden
    net.w1 = np.frombuffer(data, dtype="<i2", count=n_w1, offset=off).astype(np.int64).reshape(kb, INPUTS, hidden)
    off += 2 * n_w1
    net.b1 = np.frombuffer(data, dtype="<i2", count=hidden, offset=off).astype(np.int64)
    off += 2 * hidden
    n_w2 = ob * 2 * hidden
    net.w2 = np.frombuffer(data, dtype="<i2", count=n_w2, offset=off).astype(np.int64).reshape(ob, 2 * hidden)
    off += 2 * n_w2
    net.b2 = np.frombuffer(data, dtype="<i4", count=ob, offset=off).astype(np.int64)
    off += 4 * ob
    net.checksum = struct.unpack_from("<Q", data, off)[0]
    # The engine's file_size_for() must equal the file length.
    expected = (HEADER_BYTES + 2 * kb * INPUTS * hidden + 2 * hidden
                + 2 * ob * 2 * hidden + 4 * ob + 8)
    if len(data) != expected:
        raise SystemExit(f"{path}: size {len(data)} != expected {expected}")
    if fnv1a64(data[:-8]) != net.checksum:
        raise SystemExit(f"{path}: checksum mismatch")
    return net


# ---- board side: only what the feature indices need ----

def parse_fen(fen):
    """Returns (piece_by_square dict, side_to_move_char)."""
    parts = fen.split()
    placement = parts[0]
    stm = parts[1] if len(parts) > 1 else "w"
    pieces = {}
    rank = 7
    file = 0
    for ch in placement:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            # Forge piece codes: white P..K = 1..6, black p..k = 7..12.
            kind = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6}[ch.lower()]
            code = kind if ch.isupper() else kind + 6
            pieces[rank * 8 + file] = code
            file += 1
    return pieces, stm


def king_key(net, perspective_white, ksq):
    kr = ksq if perspective_white else ksq ^ 56
    flip = 7 if (net.mirror and (kr & 7) >= 4) else 0
    return net.king_map[kr], flip


def accumulate(net, pieces, perspective_white, ksq):
    bucket, flip = king_key(net, perspective_white, ksq)
    acc = net.b1.copy()
    w1_flat = net.w1_flat
    for sq, code in pieces.items():
        is_white = code <= 6
        rel_colour = 0 if (is_white == perspective_white) else 1
        ptype = (code - 1) % 6
        rel_sq = (sq if perspective_white else sq ^ 56) ^ flip
        idx = bucket * INPUTS + (rel_colour * 6 + ptype) * 64 + rel_sq
        acc += w1_flat[idx]
    return acc, bucket, flip


def evaluate(net, fen):
    """Value in centipawns from the side to move's view: the engine's evaluate_reference()."""
    pieces, stm = parse_fen(fen)
    white_king = next(sq for sq, c in pieces.items() if c == 6)
    black_king = next(sq for sq, c in pieces.items() if c == 12)
    acc_w, kb_w, fl_w = accumulate(net, pieces, True, white_king)
    acc_b, kb_b, fl_b = accumulate(net, pieces, False, black_king)
    us_white = (stm == "w")
    ours = acc_w if us_white else acc_b
    theirs = acc_b if us_white else acc_w
    ob = net.output_map[min(len(pieces), MAX_PIECES)]
    a = np.clip(ours, 0, QA)
    b = np.clip(theirs, 0, QA)
    w2 = net.w2[ob]
    # int64 throughout: 512 terms of up to 255^2*127 = 8.26e6 would overflow int32.
    total = int(np.sum(a * a * w2[:net.hidden], dtype=np.int64)) + \
            int(np.sum(b * b * w2[net.hidden:], dtype=np.int64))
    out = trunc_div(total, QA) + int(net.b2[ob])
    cp = trunc_div(out * net.eval_scale, QA * QB)
    cp = max(-30000, min(30000, cp))
    return cp, {"ob": ob, "kb_w": kb_w, "fl_w": fl_w, "kb_b": kb_b, "fl_b": fl_b,
                "acc_w": acc_w, "acc_b": acc_b, "total": total}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("fens")
    ap.add_argument("--out", default="-")
    ap.add_argument("--detail", default=None,
                    help="write one line per position: cp ob kb_w fl_w kb_b fl_b")
    args = ap.parse_args()
    net = load_net(args.net)
    with open(args.fens) as f:
        fens = [l.strip() for l in f if l.strip()]
    values = []
    detail = []
    for fen in fens:
        cp, info = evaluate(net, fen)
        values.append(cp)
        detail.append(f"{cp} {info['ob']} {info['kb_w']} {info['fl_w']} {info['kb_b']} {info['fl_b']}")
    out = sys.stdout if args.out == "-" else open(args.out, "w")
    out.write("\n".join(str(v) for v in values) + "\n")
    if out is not sys.stdout:
        out.close()
    if args.detail:
        with open(args.detail, "w") as f:
            f.write("\n".join(detail) + "\n")


if __name__ == "__main__":
    main()
