#!/usr/bin/env python3
"""A3: planted bugs. The unmodified pipeline must PASS both tests; every planted bug must make its test FAIL.

usage: a3_mutation_check.py --trainer <opus_nnue_smoke_*.py copy> --ckpt <epoch.pt> --net <epoch.fnn>
                            --pos <h000.pos> --fens <fens.txt> --tmp <new scratch dir>

Bugs are planted by patching the reference evaluator / converter in memory (parity test on 200 + 200 positions,
incremental test on 20,000 positions, seed 11), one at a time, and undone afterwards.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a3_incremental_200k as I  # noqa: E402
import a3_parity_1k as P  # noqa: E402
import forge_astra_A3_converter_20261027 as C  # noqa: E402
import forge_astra_A3_refeval_20261027 as R  # noqa: E402


class Patch:
    def __init__(self, obj, name, value):
        self.obj, self.name, self.value = obj, name, value

    def __enter__(self):
        self.old = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.value)

    def __exit__(self, *exc):
        setattr(self.obj, self.name, self.old)


def main():
    ap = argparse.ArgumentParser()
    for k in ("--trainer", "--ckpt", "--net", "--pos", "--fens", "--tmp"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=False)

    def parity(net=None):
        return P.run(a.trainer, a.ckpt, net or a.net, a.pos, a.fens, n=200)

    def incremental():
        return I.run(a.net, a.fens, 20000, seed=11)

    orig_key, orig_bucket, orig_dense = R.king_key, R.output_bucket, R.dense_engine_order
    orig_changes, orig_rebuild = R.chess_changes, R.RefreshCache.rebuild

    def key_no_mirror(net, codes, p):
        return orig_key(net, codes, p)[0], 0

    def bucket_plus_one(net, codes):
        return min(net.ob - 1, orig_bucket(net, codes) + 1)

    def dense_15_lanes(x, w, b):
        y = orig_dense(x, w, b)
        n_out, n_in = w.shape
        last = np.zeros(n_out, np.float32)
        for c in range(15, n_in, 16):
            last = last + x[c] * w[:, c]
        return (y - last).astype(np.float32)

    def changes_no_rook(board, move):
        ch = orig_changes(board, move)
        return ch[:2] if board.is_castling(move) else ch

    def changes_ep_wrong_square(board, move):
        ch = orig_changes(board, move)
        if board.is_en_passant(move):
            code, sq, add = ch[1]
            ch[1] = (code, move.to_square, add)
        return ch

    def rebuild_forget_board(self, p, key, codes):
        acc = orig_rebuild(self, p, key, codes)
        self.entries[(p, key)] = (self.entries[(p, key)][0], np.zeros(64, np.uint8))
        return acc

    def accumulator_no_key_check(self, p):
        top = len(self.stack) - 1
        ply = self.stack[top]
        if ply.acc[p] is not None:
            return ply.acc[p]
        j = top - 1
        while j >= 0 and self.stack[j].acc[p] is None:
            j -= 1
        if j < 0:
            acc = self._rebuild(p, ply)
        else:
            acc = self.stack[j].acc[p]
            for i in range(j + 1, top + 1):
                acc = R.apply_changes(self.net, acc, p, ply.key[p], self.stack[i].changes)
        ply.acc[p] = acc
        return acc

    # converter bug: export without the factoriser block
    import torch
    ck = torch.load(a.ckpt, map_location="cpu", weights_only=True)
    ck["config"]["factor"] = False
    bad_pt = tmp / "no_factor.pt"
    torch.save(ck, bad_pt)
    bad_net = tmp / "no_factor.fnn"
    C.convert(bad_pt, bad_net)

    cases = [
        ("baseline: parity", None, parity, True),
        ("baseline: incremental", None, incremental, True),
        ("reference ignores mirroring (flip 0)", Patch(R, "king_key", key_no_mirror), parity, False),
        ("reference output bucket + 1", Patch(R, "output_bucket", bucket_plus_one), parity, False),
        ("reference dense layer drops lane 15", Patch(R, "dense_engine_order", dense_15_lanes), parity, False),
        ("converter exports without the factoriser", None, lambda: parity(bad_net), False),
        ("lazy evaluator replays across a king-key change", Patch(R.LazyEvaluator, "accumulator", accumulator_no_key_check), incremental, False),
        ("refresh cache forgets its board", Patch(R.RefreshCache, "rebuild", rebuild_forget_board), incremental, False),
        ("castling dirty pieces without the rook", Patch(R, "chess_changes", changes_no_rook), incremental, False),
        ("en passant removes the pawn on the target square", Patch(R, "chess_changes", changes_ep_wrong_square), incremental, False),
    ]
    all_ok = True
    for name, patch, test, expect_pass in cases:
        if patch is None:
            ok, msg = test()
        else:
            with patch:
                ok, msg = test()
        good = ok == expect_pass
        all_ok &= good
        print(f"{'OK  ' if good else 'BAD '} {name}: test {'PASS' if ok else 'FAIL'} (expected {'PASS' if expect_pass else 'FAIL'})")
        for ln in msg.splitlines():
            s = ln.strip()
            if s.startswith(("E1", "E2", "E3", "E4", "mismatches:")):
                print("       " + s)
            elif s.startswith("walk:"):
                w = dict(zip(s.split()[1::2], s.split()[2::2]))
                print("       walk coverage: " + " ".join(f"{k} {w.get(k)}" for k in
                                                       ("evaluated", "key_changes", "castles", "en_passant", "promotions", "null_moves")))
    print("mutation check: " + ("every planted bug caught, baseline passes" if all_ok else "PROBLEM"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
