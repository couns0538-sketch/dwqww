#!/usr/bin/env python3
"""Export parity, PyTorch (train_resid_v3b.py model) vs C++ (engine kernels via nnue_v2_tool), for v2 nets.

usage: v2_parity.py <checkpoint.pt> <net.fnn2> <positions.fen> <cpp_prefix> [--json out.json]
  <cpp_prefix>.tsv / .acc come from `nnue_v2_tool eval <net.fnn2> <positions.fen> <cpp_prefix>`.

Checks, each over every position:
  export   the .fnn2 integers equal the checkpoint's quantised weights (q() of the trained parameters,
           king buckets folded with the factoriser)
  keys     king bucket and mirror flip of both perspectives: trainer feature function == engine
  outbkt   output bucket (C5): trainer (output_map[pieces]) == engine, for every position
  acc      accumulators of both perspectives, computed by the trainer's model (its own feature
           function, QAT weights, F.linear) == the engine's, bit for bit (float32)
  output   the network output computed in PyTorch float32 in the engine's operation order (16 lanes,
           fixed association) == the engine's float bits, and the centipawns (trunc) are equal
  forward  the training-time model forward (logit * 400 / 2.25, hce_logit = 0) vs the engine's centipawns:
           max |diff| and the number of positions where trunc(forward) == engine (informational: the
           GEMM summation order differs from the engine's, so the last float bit can differ)
PASS requires export, keys, outbkt, acc and output to hold on all positions."""
import argparse
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forge_nnue_v2 as V2  # noqa: E402
import train_resid_v3b as T  # noqa: E402

CODE = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}


def parse_fen(fen):
    parts = fen.split()
    codes = np.zeros(64, np.int64)
    rank, file = 7, 0
    for ch in parts[0]:
        if ch == "/":
            rank, file = rank - 1, 0
        elif ch.isdigit():
            file += int(ch)
        else:
            codes[rank * 8 + file] = CODE[ch]
            file += 1
    return codes, 0 if parts[1] == "w" else 1


def build_model(ck):
    cfg = ck["config"]
    if cfg.get("king_buckets"):
        m = T.NNUEKB(cfg["hidden"], cfg["king_map"], mirror=cfg["king_mirror"], factor=cfg["king_factor"],
                     qat=True, residual=cfg["residual"], output_map=cfg.get("output_map"))
    else:
        m = T.NNUE(cfg["hidden"], qat=True, residual=cfg["residual"])
    m.load_state_dict(ck["model"])
    m.eval()
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkpoint")
    ap.add_argument("net")
    ap.add_argument("fens")
    ap.add_argument("cpp_prefix")
    ap.add_argument("--json")
    a = ap.parse_args()
    torch.set_num_threads(1)
    ck = torch.load(a.checkpoint, map_location="cpu", weights_only=True)
    model = build_model(ck)
    kb_model = isinstance(model, T.NNUEKB)
    H = model.hidden
    net = V2.read_v2(a.net)
    res = {}

    # export: file integers == quantised checkpoint weights
    with torch.no_grad():
        if kb_model:
            w1 = T.quant_int(model.ft_sum()).transpose(0, 2, 1).ravel()
            b1 = T.quant_int(model.ft_b)
            kmap, mirror = model.king_map.tolist(), model.mirror
            omap = model.output_map.tolist()
        else:
            w1 = T.quant_int(model.ft.weight).T.ravel()
            b1 = T.quant_int(model.ft.bias)
            kmap, mirror = [0] * 64, False
            omap = [0] * 33
        w2 = T.quant_int(model.out.weight).ravel()
        b2 = T.quant_int(model.out.bias).ravel()
    export_ok = (np.array_equal(np.frombuffer(net["w1"].tobytes(), "<i2"), w1) and
                 np.array_equal(np.frombuffer(net["b1"].tobytes(), "<i2"), b1) and
                 np.array_equal(np.frombuffer(net["w2"].tobytes(), "<i2"), w2) and
                 np.array_equal(np.frombuffer(net["b2"].tobytes(), "<i2"), b2) and
                 net["king_map"] == kmap and net["mirror"] == mirror and net["hidden"] == H and
                 net["output_map"] == omap and net["output_buckets"] == max(omap) + 1 and
                 net["residual"] == bool(ck["config"]["residual"]))
    res["export"] = bool(export_ok)

    fens = [l.strip() for l in open(a.fens) if l.strip()]
    n = len(fens)
    codes = np.zeros((n, 64), np.int64)
    stm = np.zeros(n, np.int64)
    for i, f in enumerate(fens):
        codes[i], stm[i] = parse_fen(f)
    codes_t, stm_t = torch.from_numpy(codes), torch.from_numpy(stm)
    cpp = np.genfromtxt(a.cpp_prefix + ".tsv", delimiter="\t", names=True, dtype=None, encoding="ascii")
    if len(cpp) != n:
        raise SystemExit(f"tsv has {len(cpp)} rows, fen file {n}")
    cpp_acc = np.fromfile(a.cpp_prefix + ".acc", "<f4").reshape(n, 2, H)

    with torch.no_grad():
        # keys: the trainer's feature function, read back from the features of the own king
        if kb_model:
            km = model.king_map
            keys_ok = np.ones(n, bool)
            for p, (bcol, fcol) in ((0, ("white_bucket", "white_flip")), (1, ("black_bucket", "black_flip"))):
                black = torch.full((n,), p, dtype=torch.long)
                own_king = torch.where(black == 1, 12, 6).unsqueeze(1)
                ksq = torch.argmax((codes_t == own_king).long(), dim=1)
                kr = torch.where(black == 1, ksq ^ 56, ksq)
                bucket = km[kr].numpy()
                flip = (torch.where((kr & 7) >= 4, 7, 0) if model.mirror else torch.zeros_like(kr)).numpy()
                # cross-check with the full feature function: the own king's feature index encodes both
                f = T.king_features(codes_t, black, km, model.mirror, model.kb)
                fk = torch.gather(f, 1, ksq.unsqueeze(1)).squeeze(1).numpy()
                rsq = np.where(p == 1, ksq.numpy() ^ 56, ksq.numpy())
                expect = bucket * 768 + 5 * 64 + (rsq ^ flip)
                keys_ok &= (bucket == cpp[bcol]) & (flip == cpp[fcol]) & (fk == expect)
        else:
            keys_ok = (cpp["white_bucket"] == 0) & (cpp["black_bucket"] == 0) & (cpp["white_flip"] == 0) & (cpp["black_flip"] == 0)
        res["keys_exact"] = int(keys_ok.sum())

        # outbkt: the trainer's output row selection (C5)
        pieces = (codes_t > 0).sum(1)
        ob = model.output_map[pieces] if kb_model else torch.zeros(n, dtype=torch.long)
        res["outbkt_exact"] = int((ob.numpy() == cpp["out_bucket"]).sum())

        # acc: the model's own first layer on its own features
        if kb_model:
            W = model.q(model.ft_sum()).permute(1, 0, 2).reshape(H, model.kb * T.FEATURES)
            bias = model.q(model.ft_b)
            dense = lambda black: T.king_dense(codes_t, black, model.king_map, model.mirror, model.kb)
        else:
            W, bias = model.q(model.ft.weight), model.q(model.ft.bias)
            dense = lambda black: T.dense(codes_t, black)
        acc = torch.stack([torch.nn.functional.linear(dense(torch.full((n,), p, dtype=torch.long)), W, bias)
                           for p in (0, 1)], dim=1)                       # [n, 2, H] White, Black
        acc_np = acc.numpy().astype("<f4")
        acc_ok = (acc_np.view("<u4") == cpp_acc.view("<u4")).all(axis=(1, 2))
        res["acc_exact"] = int(acc_ok.sum())

        # output in the engine's float32 order
        idx = torch.arange(n)
        ours = acc[idx, stm_t]
        theirs = acc[idx, 1 - stm_t]
        w2q = model.q(model.out.weight).reshape(-1, 2 * H)[ob]          # [n, 2H]: each position's output row
        b2q = model.q(model.out.bias).reshape(-1)[ob]                   # [n]
        a_ = torch.clamp(torch.clamp(ours, min=0.0), max=1.0)
        b_ = torch.clamp(torch.clamp(theirs, min=0.0), max=1.0)
        term = (a_ * a_) * w2q[:, :H] + (b_ * b_) * w2q[:, H:]
        lanes = torch.zeros(n, 16, dtype=torch.float32)
        for h0 in range(0, H, 16):
            lanes = lanes + term[:, h0:h0 + 16]
        out = b2q.clone().to(torch.float32)
        for j in range(16):
            out = out + lanes[:, j]
        cp = torch.clamp((out * torch.tensor(400.0)) / torch.tensor(2.25), -30000.0, 30000.0).trunc().to(torch.int64).numpy()
        out_bits = out.numpy().astype("<f4").view("<u4")
        cpp_bits = np.array([int(x, 16) for x in cpp["out_bits"]], dtype=np.uint32)
        out_ok = (out_bits == cpp_bits) & (cp == cpp["cp"])
        res["output_exact"] = int(out_ok.sum())

        # forward: training-time model
        logit = model(codes_t, stm_t, torch.zeros(n))
        fwd_cp = (logit * 400.0 / 2.25).numpy().astype(np.float64)
        diff = np.abs(fwd_cp - cpp["cp"])
        res["forward_max_abs_diff_cp"] = float(diff.max())
        res["forward_trunc_equal"] = int((np.trunc(fwd_cp) == cpp["cp"]).sum())

    res["positions"] = n
    res["king_buckets"] = net["king_buckets"]
    res["mirror"] = net["mirror"]
    res["bucket_coverage"] = {f"{p}{b}{'f' if fl else ''}": int(((cpp[p + '_bucket'] == b) & (cpp[p + '_flip'] == fl)).sum())
                              for p in ("white", "black") for b in range(net["king_buckets"]) for fl in (0, 7)
                              if ((cpp[p + '_bucket'] == b) & (cpp[p + '_flip'] == fl)).any()}
    res["piece_counts"] = {int(k): int((cpp["pieces"] == k).sum()) for k in sorted(set(cpp["pieces"].tolist()))}
    res["output_buckets"] = net["output_buckets"]
    res["output_bucket_coverage"] = {int(k): int((cpp["out_bucket"] == k).sum()) for k in sorted(set(cpp["out_bucket"].tolist()))}
    res["max_abs_cp"] = int(np.abs(cpp["cp"]).max())
    ok = (res["export"] and res["keys_exact"] == n and res["outbkt_exact"] == n and res["acc_exact"] == n and
          res["output_exact"] == n)
    res["verdict"] = "PASS" if ok else "FAIL"
    print(f"positions {n}  king buckets {net['king_buckets']} mirror {net['mirror']}  output buckets {net['output_buckets']}  "
          f"max |engine cp| {res['max_abs_cp']}")
    print(f"export (file ints == quantised checkpoint): {'OK' if res['export'] else 'MISMATCH'}")
    print(f"keys   (bucket, flip both perspectives):    {res['keys_exact']}/{n}")
    print(f"outbkt (output bucket by piece count):      {res['outbkt_exact']}/{n}")
    print(f"acc    (both perspectives, float32 bits):   {res['acc_exact']}/{n}")
    print(f"output (engine-order float32 bits and cp):  {res['output_exact']}/{n}")
    print(f"forward (training model, GEMM order): max |cp diff| {res['forward_max_abs_diff_cp']:.6f}, "
          f"trunc equal {res['forward_trunc_equal']}/{n}")
    print("bucket coverage:", " ".join(f"{k}={v}" for k, v in res["bucket_coverage"].items()))
    print("piece counts:", " ".join(f"{k}:{v}" for k, v in res["piece_counts"].items()))
    print("output bucket coverage:", " ".join(f"{k}:{v}" for k, v in res["output_bucket_coverage"].items()))
    print(res["verdict"])
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
