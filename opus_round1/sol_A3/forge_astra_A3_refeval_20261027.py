#!/usr/bin/env python3
"""Forge full-NNUE reference evaluator (Astra A3, 2026-10-27): pure Python + numpy, outside the engine tree.

It reads a FORGEFN1 file (forge_astra_A3_converter_20261027.py) and evaluates positions exactly as the planned
engine path must (spec forge_astra_A3_fullnnue_spec_20261027.md, section 4):
  * feature transformer: float32 accumulator = bias + sum of weight columns, every value a multiple of 1/4096,
    so every summation order gives the same bits (incremental update == refresh == refresh-cache rebuild);
  * dense layers in the engine order: float32, no fused multiply-add, 16 lanes (input i goes to lane i % 16,
    lanes summed in increasing i), then bias + lane 0 + lane 1 + ... + lane 15;
  * cp = trunc(clamp((out * 400) / 2.25, -30000, 30000)) in float32 (the lock's evaluate() conversion).
It also implements the incremental plan (LazyEvaluator: per-perspective validity, refresh on an own-king key
change straight at the evaluated ply, refresh cache keyed by (perspective, key)).

usage:
  forge_astra_A3_refeval_20261027.py eval <net.fnn> <positions.txt> [count]
      positions.txt: one FEN per line (anything after '|' is ignored); prints "out_f32 cp out_f64 | FEN"
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

MAGIC = b"FORGEFN1"
INPUTS = 768
F32 = np.float32
LANES = 16


def fnv1a64(data: bytes) -> int:
    h = 0xcbf29ce484222325
    for b in data:
        h = ((h ^ b) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


class Net:
    """A loaded FORGEFN1 network. Arrays: ft_w float32 [KB*768, H] (row = feature), ft_b float32 [H],
    l1_w [OB, L1, 2H], l1_b [OB, L1], l2_w [OB, L2, L1], l2_b [OB, L2], out_w [OB, Lk], out_b [OB]."""

    def __init__(self, path, verify_checksum=True):
        data = Path(path).read_bytes()
        if len(data) < 264 or data[:8] != MAGIC:
            raise ValueError(f"{path}: not a FORGEFN1 file")
        (version, hb, inputs, hidden, kb, flags, ob, l1, l2, act_ft, act_h, scale, k) = struct.unpack_from("<IIIIIIIIIIIff", data, 8)
        problems = []
        if version != 1 or hb != 256 or inputs != INPUTS:
            problems.append(f"version {version} header {hb} inputs {inputs}")
        if hidden % 16 or not 16 <= hidden <= 2048 or not 1 <= kb <= 64 or not 1 <= ob <= 16:
            problems.append(f"sizes H {hidden} KB {kb} OB {ob}")
        if l1 % 16 or not 16 <= l1 <= 256 or l2 % 16 or l2 > 256:
            problems.append(f"hidden widths L1 {l1} L2 {l2}")
        if flags & ~1 or act_ft != 1 or act_h != 1 or scale != 4096.0 or k != F32(2.25):
            problems.append(f"flags {flags} activations {act_ft}/{act_h} scale {scale} K {k}")
        king_map = list(data[60:124])
        output_map = list(data[124:157])
        if any(b >= kb for b in king_map) or any(b >= ob for b in output_map) or any(data[157:256]):
            problems.append("map out of range or reserved bytes not zero")
        lk = l2 if l2 else l1
        n_i16 = kb * INPUTS * hidden + hidden
        n_f32 = ob * l1 * 2 * hidden + ob * l1 + (ob * l2 * l1 + ob * l2 if l2 else 0) + ob * lk + ob
        expect = 256 + 2 * n_i16 + 4 * n_f32 + 8
        if len(data) != expect:
            problems.append(f"file size {len(data)} != {expect} implied by the header")
        if problems:
            raise ValueError(f"{path}: " + "; ".join(problems))
        if verify_checksum and fnv1a64(data[:-8]) != struct.unpack_from("<Q", data, len(data) - 8)[0]:
            raise ValueError(f"{path}: checksum mismatch")
        self.hidden, self.kb, self.mirror, self.ob, self.l1, self.l2 = hidden, kb, bool(flags & 1), ob, l1, l2
        self.king_map, self.output_map = king_map, output_map
        off = 256
        ft = np.frombuffer(data, "<i2", kb * INPUTS * hidden, off)
        off += 2 * kb * INPUTS * hidden
        fb = np.frombuffer(data, "<i2", hidden, off)
        off += 2 * hidden
        self.ft_w_int = ft.reshape(kb * INPUTS, hidden)
        self.ft_b_int = fb
        self.ft_w = (self.ft_w_int.astype(F32) / F32(4096.0)).astype(F32)   # exact: power-of-two scale
        self.ft_b = (fb.astype(F32) / F32(4096.0)).astype(F32)

        def take(n, shape):
            nonlocal off
            a = np.frombuffer(data, "<f4", n, off).reshape(shape).astype(F32)
            off += 4 * n
            return a

        self.l1_w = take(ob * l1 * 2 * hidden, (ob, l1, 2 * hidden))
        self.l1_b = take(ob * l1, (ob, l1))
        if l2:
            self.l2_w = take(ob * l2 * l1, (ob, l2, l1))
            self.l2_b = take(ob * l2, (ob, l2))
        else:
            self.l2_w = self.l2_b = None
        self.out_w = take(ob * lk, (ob, lk))
        self.out_b = take(ob, (ob,))


# ----------------------------------------------------------------------------- boards
def codes_from_fen(fen: str):
    """-> (codes uint8[64] a1..h8: 0 empty, 1..6 white PNBRQK, 7..12 black; stm 0 white / 1 black)."""
    parts = fen.split()
    codes = np.zeros(64, np.uint8)
    rank, file = 7, 0
    for ch in parts[0]:
        if ch == "/":
            rank, file = rank - 1, 0
        elif ch.isdigit():
            file += int(ch)
        else:
            t = "pnbrqk".index(ch.lower()) + 1
            codes[rank * 8 + file] = t if ch.isupper() else t + 6
            file += 1
    return codes, (1 if parts[1] == "b" else 0)


def king_square(codes, p) -> int:
    """First own king on a1..h8 (absolute square), 0 if none (malformed synthetic records), as C4 / the trainer."""
    hits = np.flatnonzero(codes == (12 if p else 6))
    return int(hits[0]) if len(hits) else 0


def king_key(net: Net, codes, p):
    kr = king_square(codes, p) ^ (56 if p else 0)
    flip = 7 if (net.mirror and (kr & 7) >= 4) else 0
    return net.king_map[kr], flip


def feature_index(p, key, code, square) -> int:
    block, flip = key
    c = code - 1
    color, typ = c // 6, c % 6
    rel = 0 if color == p else 1
    r = square ^ (56 if p else 0)
    return block * INPUTS + (rel * 6 + typ) * 64 + (r ^ flip)


def refresh(net: Net, codes, p, key=None):
    """Accumulator of perspective p from scratch: bias, then the columns in square order a1..h8 (float32)."""
    key = king_key(net, codes, p) if key is None else key
    acc = net.ft_b.copy()
    for sq in np.flatnonzero(codes):
        acc += net.ft_w[feature_index(p, key, int(codes[sq]), int(sq))]
    return acc


def apply_changes(net: Net, acc, p, key, changes):
    """Incremental update: changes = [(code, square, add), ...] in the engine's dirty-piece order."""
    out = acc.copy()
    for code, sq, add in changes:
        col = net.ft_w[feature_index(p, key, code, sq)]
        if add:
            out += col
        else:
            out -= col
    return out


# ----------------------------------------------------------------------------- dense layers
def dense_engine_order(x, w, b):
    """float32 y = b + W x in the engine order: products rounded, lane j sums inputs j, j+16, ... in increasing
    order, then y = ((b + lane0) + lane1) + ... + lane15. x [n_in], w [n_out, n_in], b [n_out]; n_in % 16 == 0."""
    n_out, n_in = w.shape
    lanes = np.zeros((n_out, LANES), F32)
    for c in range(0, n_in, LANES):
        lanes = lanes + x[c:c + LANES][None, :] * w[:, c:c + LANES]
    y = b.astype(F32).copy()
    for j in range(LANES):
        y = y + lanes[:, j]
    return y


def output_bucket(net: Net, codes) -> int:
    return net.output_map[min(int(np.count_nonzero(codes)), 32)]


def evaluate_acc(net: Net, acc_stm, acc_other, bucket):
    """-> (out float32, cp int) from the two accumulators (side to move first), engine order."""
    a = np.clip(acc_stm, F32(0), F32(1)).astype(F32)
    o = np.clip(acc_other, F32(0), F32(1)).astype(F32)
    x = np.concatenate([a * a, o * o]).astype(F32)
    h = np.clip(dense_engine_order(x, net.l1_w[bucket], net.l1_b[bucket]), F32(0), F32(1))
    if net.l2:
        h = np.clip(dense_engine_order(h, net.l2_w[bucket], net.l2_b[bucket]), F32(0), F32(1))
    out = dense_engine_order(h, net.out_w[bucket][None, :], net.out_b[bucket:bucket + 1])[0]
    cp = F32(F32(out * F32(400.0)) / F32(2.25))
    return F32(out), int(np.trunc(np.clip(cp, F32(-30000), F32(30000))))


def evaluate_acc_f64(net: Net, acc_stm, acc_other, bucket) -> float:
    """Same function in float64 with library dot products (a math reference, not the engine order)."""
    a = np.clip(acc_stm.astype(np.float64), 0, 1)
    o = np.clip(acc_other.astype(np.float64), 0, 1)
    x = np.concatenate([a * a, o * o])
    h = np.clip(net.l1_w[bucket].astype(np.float64) @ x + net.l1_b[bucket], 0, 1)
    if net.l2:
        h = np.clip(net.l2_w[bucket].astype(np.float64) @ h + net.l2_b[bucket], 0, 1)
    return float(net.out_w[bucket].astype(np.float64) @ h + net.out_b[bucket])


def evaluate_codes(net: Net, codes, stm):
    """Full evaluation from scratch: (out f32, cp, out f64, acc_white, acc_black)."""
    acc = [refresh(net, codes, 0), refresh(net, codes, 1)]
    b = output_bucket(net, codes)
    out, cp = evaluate_acc(net, acc[stm], acc[1 - stm], b)
    return out, cp, evaluate_acc_f64(net, acc[stm], acc[1 - stm], b), acc[0], acc[1]


# ----------------------------------------------------------------------------- incremental plan
class RefreshCache:
    """One entry per (perspective, key): the accumulator of the board it was last brought to + that board.
    A rebuild applies only the squares that differ (cold entry = bias + empty board = a refresh from scratch)."""

    def __init__(self, net: Net):
        self.net, self.entries = net, {}
        self.columns = 0

    def rebuild(self, p, key, codes):
        acc, cached = self.entries.get((p, key), (self.net.ft_b, np.zeros(64, np.uint8)))
        acc = acc.copy()
        for sq in np.flatnonzero(cached != codes):
            old, new = int(cached[sq]), int(codes[sq])
            if old:
                acc -= self.net.ft_w[feature_index(p, key, old, int(sq))]
                self.columns += 1
            if new:
                acc += self.net.ft_w[feature_index(p, key, new, int(sq))]
                self.columns += 1
        self.entries[(p, key)] = (acc.copy(), codes.copy())
        return acc


class Ply:
    __slots__ = ("codes", "stm", "changes", "acc", "key")

    def __init__(self, codes, stm, changes, keys):
        self.codes, self.stm, self.changes, self.acc, self.key = codes, stm, changes, [None, None], keys


class LazyEvaluator:
    """The engine plan in miniature: a stack of plies (push = record_move + make_move, pop = unmake), each with
    the dirty pieces that produced it and one accumulator per perspective that stays invalid until needed.
    accumulator(p): valid -> use it; else find the nearest ancestor with a valid p-accumulator; if the own-king key
    of p is the same there, replay the changes (intermediate plies with that key become valid); if it differs (or
    there is no valid ancestor), rebuild p at this ply from the refresh cache."""

    def __init__(self, net: Net, codes, stm, cache: RefreshCache | None = None):
        self.net, self.cache = net, cache
        self.stack = [Ply(codes, stm, [], (king_key(net, codes, 0), king_key(net, codes, 1)))]
        self.stats = {"valid": 0, "replay": 0, "replayed_plies": 0, "key_rebuild": 0, "root_rebuild": 0}

    def push(self, codes, stm, changes):
        self.stack.append(Ply(codes, stm, changes, (king_key(self.net, codes, 0), king_key(self.net, codes, 1))))

    def pop(self):
        self.stack.pop()

    def _rebuild(self, p, ply):
        if self.cache is None:
            return refresh(self.net, ply.codes, p, ply.key[p])
        return self.cache.rebuild(p, ply.key[p], ply.codes)

    def accumulator(self, p):
        top = len(self.stack) - 1
        ply = self.stack[top]
        if ply.acc[p] is not None:
            self.stats["valid"] += 1
            return ply.acc[p]
        j = top - 1
        while j >= 0 and self.stack[j].acc[p] is None:
            j -= 1
        key = ply.key[p]
        if j < 0:
            acc = self._rebuild(p, ply)
            self.stats["root_rebuild"] += 1
        elif self.stack[j].key[p] != key:
            acc = self._rebuild(p, ply)
            self.stats["key_rebuild"] += 1
        else:
            acc = self.stack[j].acc[p]
            for i in range(j + 1, top + 1):
                acc = apply_changes(self.net, acc, p, key, self.stack[i].changes)
                if self.stack[i].key[p] == key:
                    self.stack[i].acc[p] = acc
            self.stats["replay"] += 1
            self.stats["replayed_plies"] += top - j
        ply.acc[p] = acc
        return acc

    def evaluate(self):
        ply = self.stack[-1]
        acc = [self.accumulator(0), self.accumulator(1)]
        out, cp = evaluate_acc(self.net, acc[ply.stm], acc[1 - ply.stm], output_bucket(self.net, ply.codes))
        return out, cp, acc


def chess_changes(board, move):
    """Dirty pieces of a python-chess move about to be played, in the lock's dirty_pieces order:
    remove mover@from, [remove captured], add mover-or-promotion@to, [castling: remove rook@from, add rook@to]."""
    import chess
    us = board.turn
    moved = board.piece_at(move.from_square)
    code_m = moved.piece_type + (0 if moved.color == chess.WHITE else 6)
    changes = [(code_m, move.from_square, False)]
    if board.is_castling(move):
        kingside = board.is_kingside_castling(move)
        rank = 0 if us == chess.WHITE else 56
        king_to = rank + (6 if kingside else 2)
        rook_from, rook_to = rank + (7 if kingside else 0), rank + (5 if kingside else 3)
        rook = 4 + (0 if us == chess.WHITE else 6)
        return changes + [(code_m, king_to, True), (rook, rook_from, False), (rook, rook_to, True)]
    if board.is_en_passant(move):
        cap = move.to_square + (-8 if us == chess.WHITE else 8)
        pawn = board.piece_at(cap)
        changes.append((pawn.piece_type + (0 if pawn.color == chess.WHITE else 6), cap, False))
    elif board.is_capture(move):
        cp = board.piece_at(move.to_square)
        changes.append((cp.piece_type + (0 if cp.color == chess.WHITE else 6), move.to_square, False))
    add = (move.promotion + (0 if us == chess.WHITE else 6)) if move.promotion else code_m
    changes.append((add, move.to_square, True))
    return changes


def apply_to_codes(codes, changes):
    out = codes.copy()
    for code, sq, add in changes:
        out[sq] = code if add else 0
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) >= 3 and argv[0] == "eval":
        net = Net(argv[1])
        count = int(argv[3]) if len(argv) > 3 else 0
        n = 0
        for line in open(argv[2], encoding="ascii"):
            fen = line.split("|")[0].strip()
            if not fen:
                continue
            codes, stm = codes_from_fen(fen)
            out, cp, out64, _, _ = evaluate_codes(net, codes, stm)
            print(f"{out:.9g} {cp} {out64:.12g} | {fen}")
            n += 1
            if count and n >= count:
                break
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
