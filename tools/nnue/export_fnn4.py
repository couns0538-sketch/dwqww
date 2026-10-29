#!/usr/bin/env python3
"""R5C M4: export a J7 (fable-fb2-j7 `--l2 N`) checkpoint to an FNN4 file and check parity (opus_r5/r5c/FNN4_FORMAT.md).

  export_fnn4.py export <checkpoint.pt> <out.fnn4> [--json report.json]
  export_fnn4.py parity <checkpoint.pt> <net.fnn4> <fens.txt> <engine_out.txt> [--json report.json] [--limit N]
  export_fnn4.py holdout <net.fnn4> <holdout.pos> [--hce holdout.hce] [--json report.json]

export: reads {"cfg", "state", "steps"} (torch, CPU, read-only), merges the factoriser into w1, quantises w1/b1 x QA
(the trainer's fake-quant grid), l2w x QW, l2b x ONE, l2o x QO and b2 (trainer grid 1/(QA*64)) x ONE*QO, refuses a
net outside the loader bounds, writes header + arrays + FNV-1a 64 and prints the quantisation error of the three
layer-2 tensors (the J7 trainer does not fake-quantise them).
parity: for every FEN, (1) the exact integer forward of FNN4_FORMAT.md in numpy int64 from the FILE, (2) the engine's
values (engine_out.txt from r5c_v4_eval: `scalar avx2` per line), (3) the trainer's float forward from the
CHECKPOINT (fake-quantised w1/b1/b2 as in training, float l2). Integer reference == engine scalar == engine AVX2 must
hold for every position; the float gap is reported (it is the cost of not fake-quantising layer 2).
holdout: the exact integer MSE (blends 1.0 / 0.6 / 0.8) of an FNN4 file on an FPOS holdout (+ FHCE for residual nets),
with the J7 trainer's loss definition; the input of the gate rule "holdout b0.6 < AL1 0.014417".
Python: the PC venv (numpy, torch, python-chess), `-I -B`, OPENBLAS/OMP threads 1.
"""
import argparse
import json
import struct
import sys

import numpy as np

QA, SSHIFT, QW, QO = 255, 6, 1024, 256
ONE = QA * QA * QW >> SSHIFT          # 1,040,400
QB_TRAIN = 64                          # the trainer's b2 grid is 1/(QA * 64)
HEADER = 256


def fnv1a64(data: bytes) -> int:
    h = 0xcbf29ce484222325
    for b in data:
        h = ((h ^ b) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def load_ckpt(path):
    import torch
    ck = torch.load(path, map_location="cpu", weights_only=True)
    cfg, state = ck["cfg"], ck["state"]
    # float32, as the trainer computes: the factoriser merge and the fake quantisation round in float32.
    t = {k: v.detach().float().numpy() for k, v in state.items()}
    H, kb = int(cfg["hidden"]), int(cfg["king_buckets"])
    w1 = t["w1"]
    if "wf" in t:
        w1 = (w1.reshape(kb, 768, H) + t["wf"].reshape(1, 768, H)).reshape(kb * 768, H)
    if "l2w" not in t:
        raise SystemExit("export_fnn4: the checkpoint has no second layer (trained without --l2)")
    if cfg.get("pairwise"):
        raise SystemExit("export_fnn4: pairwise output term (w3) is not part of FNN4")
    return cfg, ck.get("steps"), w1, t


def quantise(cfg, w1f, t):
    # w1, b1, b2: the trainer's own grid, rounded like torch.round (half to even) on float32 products.
    w1 = np.clip(np.round(w1f * np.float32(QA)), -32767, 32767).astype(np.int64)
    b1 = np.clip(np.round(t["b1"] * np.float32(QA)), -32767, 32767).astype(np.int64)
    b2q = np.round(t["b2"] * np.float32(QA * QB_TRAIN)).astype(np.int64)
    b_out = b2q * (ONE * QO // (QA * QB_TRAIN))                    # x 16320: exact
    assert ONE * QO % (QA * QB_TRAIN) == 0
    # Layer 2 was trained in float: round to the FNN4 grid in float64.
    l2w_raw = t["l2w"].astype(np.float64) * QW
    l2w = np.clip(np.round(l2w_raw), -32768, 32767).astype(np.int64)
    l2b = np.round(t["l2b"].astype(np.float64) * ONE).astype(np.int64)
    l2o = np.clip(np.round(t["l2o"].astype(np.float64) * QO), -32768, 32767).astype(np.int64)
    stats = {
        "l2w_clipped": int((np.abs(np.round(l2w_raw)) > 32767).sum()),
        "l2o_clipped": int((np.abs(np.round(t["l2o"] * QO)) > 32767).sum()),
        "l2w_max_abs_err": float(np.abs(l2w / QW - t["l2w"]).max()),
        "l2b_max_abs_err": float(np.abs(l2b / ONE - t["l2b"]).max()),
        "l2o_max_abs_err": float(np.abs(l2o / QO - t["l2o"]).max()),
        "max_w1": int(np.abs(w1).max()), "max_b1": int(np.abs(b1).max()),
    }
    return w1, b1, l2w, l2b, l2o, b_out, stats


def check_bounds(w1, b1, l2w, l2b, b_out):
    if int(np.abs(b1).max()) + 32 * int(np.abs(w1).max()) > 32767:
        raise SystemExit("export_fnn4: accumulator bound max|b1| + 32*max|w1| > 32767")
    rows = np.abs(l2b) + 1016 * np.abs(l2w).sum(axis=1)
    if int(rows.max()) > 2**31 - 1:
        raise SystemExit(f"export_fnn4: layer-2 bound {int(rows.max())} > 2^31 - 1")
    if int(np.abs(b_out).max()) > 2**40:
        raise SystemExit("export_fnn4: b_out beyond 2^40")
    return int(rows.max())


def write_fnn4(path, cfg, w1, b1, l2w, l2b, l2o, b_out):
    H, kb, ob, L2 = int(cfg["hidden"]), int(cfg["king_buckets"]), int(cfg["output_buckets"]), int(l2w.shape[0])
    flags = (1 if cfg.get("residual") else 0) | (2 if cfg.get("mirror") else 0)
    head = bytearray(HEADER)
    head[0:8] = b"FORGENN4"
    struct.pack_into("<IIIIIIIIiIIII", head, 8, 1, HEADER, 768, H, kb, ob, L2, flags, int(cfg["eval_scale"]),
                     QA, SSHIFT, QW, QO)
    head[60:124] = bytes(int(v) for v in cfg["king_map"])
    head[124:157] = bytes(int(v) for v in cfg["output_map"])
    body = (w1.astype("<i2").tobytes() + b1.astype("<i2").tobytes() + l2w.astype("<i2").tobytes() +
            l2b.astype("<i4").tobytes() + l2o.astype("<i2").tobytes() + b_out.astype("<i8").tobytes())
    data = bytes(head) + body
    checksum = fnv1a64(data)
    with open(path, "wb") as f:
        f.write(data + struct.pack("<Q", checksum))
    return len(data) + 8, checksum


def read_fnn4(path):
    data = open(path, "rb").read()
    assert data[:8] == b"FORGENN4", "magic"
    ver, hb, inputs, H, kb, ob, L2, flags, scale, qa, ss, qw, qo = struct.unpack_from("<IIIIIIIIiIIII", data, 8)
    assert (ver, hb, inputs, qa, ss, qw, qo) == (1, HEADER, 768, QA, SSHIFT, QW, QO)
    king_map = np.frombuffer(data, np.uint8, 64, 60).astype(np.int64)
    output_map = np.frombuffer(data, np.uint8, 33, 124).astype(np.int64)
    off = HEADER

    def take(dtype, count):
        nonlocal off
        a = np.frombuffer(data, dtype, count, off).astype(np.int64)
        off += count * np.dtype(dtype).itemsize
        return a

    w1 = take("<i2", kb * 768 * H).reshape(kb * 768, H)
    b1 = take("<i2", H)
    l2w = take("<i2", L2 * 2 * H).reshape(L2, 2 * H)
    l2b = take("<i4", L2)
    l2o = take("<i2", ob * L2).reshape(ob, L2)
    b_out = take("<i8", ob)
    stored = struct.unpack_from("<Q", data, off)[0]
    assert off + 8 == len(data), "size"
    assert stored == fnv1a64(data[:off]), "checksum"
    return dict(H=H, kb=kb, ob=ob, L2=L2, mirror=bool(flags & 2), residual=bool(flags & 1), scale=scale,
                king_map=king_map, output_map=output_map, w1=w1, b1=b1, l2w=l2w, l2b=l2b, l2o=l2o, b_out=b_out)


def features(fens, king_map, mirror):
    """Feature rows [N, 2, 32] (pad -1) for (side to move, opponent), piece counts [N]."""
    import chess
    n = len(fens)
    idx = np.full((n, 2, 32), -1, np.int64)
    pieces = np.zeros(n, np.int64)
    for i, fen in enumerate(fens):
        board = chess.Board(fen)
        pm = board.piece_map()
        pieces[i] = min(len(pm), 32)
        for side, persp in enumerate((board.turn, not board.turn)):
            ksq = board.king(persp)
            kr = ksq if persp == chess.WHITE else ksq ^ 56
            flip = 7 if (mirror and (kr & 7) >= 4) else 0
            bucket = int(king_map[kr])
            for c, (sq, p) in enumerate(pm.items()):
                rel = 0 if p.color == persp else 1
                r = (sq if persp == chess.WHITE else sq ^ 56) ^ flip
                idx[i, side, c] = bucket * 768 + (rel * 6 + p.piece_type - 1) * 64 + r
    return idx, pieces


def gather_sum(table, idx):
    """sum over the 32 slots of table[idx] ([N, 2, 32] -> [N, 2, H]); -1 = empty slot (a zero pad row)."""
    padded = np.vstack([table, np.zeros((1, table.shape[1]), table.dtype)])
    rows = np.where(idx < 0, table.shape[0], idx)
    acc = np.zeros(idx.shape[:2] + (table.shape[1],), table.dtype)
    for c in range(idx.shape[2]):   # slot by slot: [N, 2, H] at a time, not [N, 2, 32, H]
        acc += padded[rows[:, :, c]]
    return acc


def int_forward(net, idx, pieces):
    n = idx.shape[0]
    acc = gather_sum(net["w1"], idx) + net["b1"]                         # [N, 2, H] int64
    s = (np.clip(acc, 0, QA) ** 2) >> SSHIFT
    s = s.reshape(n, 2 * net["H"])                                        # us then them
    z = s @ net["l2w"].T + net["l2b"]                                     # [N, L2] (int64)
    h = np.clip(z, 0, ONE)
    ob = net["output_map"][np.minimum(pieces, 32)]
    out = net["b_out"][ob] + (h * net["l2o"][ob]).sum(axis=1)
    num = out * net["scale"]
    den = ONE * QO
    cp = np.sign(num) * (np.abs(num) // den)                              # C++ division: toward zero
    return np.clip(cp, -30000, 30000), acc


def read_fpos(pos_path, hce_path):
    """FPOS rows (fable_nnue_data.py layout): codes [N, 64] (1-6 white P..K, 7-12 black), score, meta, hce."""
    head = np.fromfile(pos_path, np.uint8, 16)
    if bytes(head[:4]) != b"FPOS":
        raise SystemExit(f"{pos_path}: not an FPOS file")
    n = int(np.frombuffer(head[8:16].tobytes(), "<u8")[0])
    raw = np.memmap(pos_path, np.uint8, "r")
    boards = np.asarray(raw[16:16 + 32 * n]).reshape(n, 32)
    score = np.asarray(raw[16 + 32 * n:16 + 34 * n]).view("<i2").astype(np.int64)
    meta = np.asarray(raw[16 + 34 * n:16 + 35 * n]).astype(np.int64)
    codes = np.empty((n, 64), np.int64)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    hce = None
    if hce_path:
        hraw = np.memmap(hce_path, np.uint8, "r")
        if bytes(hraw[:4]) != b"FHCE":
            raise SystemExit(f"{hce_path}: not an FHCE file")
        hce = np.asarray(hraw[16:16 + 2 * n]).view("<i2").astype(np.int64)
    return codes, score, meta, hce


def features_from_codes(codes, meta, king_map, mirror):
    """[N, 2, 64] feature rows (-1 = empty square) for (side to move, opponent), piece counts [N]."""
    sq = np.arange(64)
    occupied = codes != 0
    ptype = (codes - 1) % 6
    out = []
    for white in (True, False):
        rel = (codes >= 7) if white else ((codes >= 1) & (codes <= 6))
        own_king = 6 if white else 12
        ksq = np.argmax(codes == own_king, axis=1)
        kr = ksq if white else ksq ^ 56
        flip = np.where(mirror & ((kr & 7) >= 4), 7, 0)
        rsq = (sq if white else sq ^ 56)[None, :] ^ flip[:, None]
        f = king_map[kr][:, None] * 768 + (rel.astype(np.int64) * 6 + ptype) * 64 + rsq
        out.append(np.where(occupied, f, -1))
    stm_black = (meta & 1).astype(bool)[:, None]
    us = np.where(stm_black, out[1], out[0])
    them = np.where(stm_black, out[0], out[1])
    return np.stack([us, them], axis=1), np.minimum(occupied.sum(axis=1), 32)


def holdout_mse(net, codes, score, meta, hce, chunk=2000):
    """Exact integer holdout MSE (blends 1.0 / 0.6 / 0.8) of an FNN4 file; the trainer's loss definition (K 2.25,
    teacher = sigmoid(clamp(score * K / 400, +-40)), result from meta, residual adds hce)."""
    k = 2.25
    sums = {1.0: 0.0, 0.6: 0.0, 0.8: 0.0}
    n = codes.shape[0]
    for start in range(0, n, chunk):
        sl = slice(start, min(start + chunk, n))
        idx, pieces = features_from_codes(codes[sl], meta[sl], net["king_map"], net["mirror"])
        cp, _ = int_forward(net, idx, pieces)
        logit = cp * (k / 400.0)
        if net["residual"]:
            logit = logit + hce[sl] * (k / 400.0)
        pred = 1.0 / (1.0 + np.exp(-logit))
        teacher = 1.0 / (1.0 + np.exp(-np.clip(score[sl] * (k / 400.0), -40.0, 40.0)))
        white_result = (meta[sl] >> 1) * 0.5
        stm_res = np.where((meta[sl] & 1) == 0, white_result, 1.0 - white_result)
        for b in sums:
            sums[b] += float(np.sum((pred - (b * teacher + (1.0 - b) * stm_res)) ** 2))
    return {f"mse_b{b}": sums[b] / n for b in sums}


def float_forward(cfg, w1f, t, idx, pieces):
    def fq(x, q):  # the trainer's fake quantisation (float32 product, round half to even), then float64
        return np.round(x * np.float32(q)).astype(np.float64) / q

    H = int(cfg["hidden"])
    acc = gather_sum(fq(w1f, QA), idx) + fq(t["b1"], QA)
    s = np.clip(acc, 0.0, 1.0) ** 2
    s = s.reshape(idx.shape[0], 2 * H)
    hidden = np.clip(s @ t["l2w"].astype(np.float64).T + t["l2b"].astype(np.float64), 0.0, 1.0)
    ob = np.asarray(cfg["output_map"], np.int64)[np.minimum(pieces, 32)]
    out = (hidden * t["l2o"].astype(np.float64)[ob]).sum(axis=1) + fq(t["b2"], QA * QB_TRAIN)[ob]
    return out * float(cfg["eval_scale"])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("ckpt")
    e.add_argument("out")
    e.add_argument("--json")
    p = sub.add_parser("parity")
    p.add_argument("ckpt")
    p.add_argument("net")
    p.add_argument("fens")
    p.add_argument("engine_out")
    p.add_argument("--json")
    p.add_argument("--limit", type=int, default=0)
    h = sub.add_parser("holdout")
    h.add_argument("net")
    h.add_argument("pos")
    h.add_argument("--hce")
    h.add_argument("--json")
    args = ap.parse_args()
    if args.cmd == "holdout":
        net = read_fnn4(args.net)
        codes, score, meta, hce = read_fpos(args.pos, args.hce)
        if net["residual"] and hce is None:
            raise SystemExit("holdout: a residual net needs --hce")
        report = {"net": args.net, "pos": args.pos, "rows": int(codes.shape[0]), **holdout_mse(net, codes, score, meta, hce),
                  "gate_rule": "gate only if mse_b0.6 < 0.014417 (AL1 lock net on the same 200k holdout)"}
        print(json.dumps(report, indent=1))
        if args.json:
            with open(args.json, "w", newline="\n") as f:
                json.dump(report, f, indent=1)
        return
    cfg, steps, w1f, t = load_ckpt(args.ckpt)
    if args.cmd == "export":
        w1, b1, l2w, l2b, l2o, b_out, stats = quantise(cfg, w1f, t)
        stats["layer2_bound_max"] = check_bounds(w1, b1, l2w, l2b, b_out)
        size, checksum = write_fnn4(args.out, cfg, w1, b1, l2w, l2b, l2o, b_out)
        report = {"ckpt": args.ckpt, "steps": steps, "out": args.out, "bytes": size, "checksum": f"{checksum:016x}",
                  "hidden": cfg["hidden"], "king_buckets": cfg["king_buckets"], "output_buckets": cfg["output_buckets"],
                  "l2": int(l2w.shape[0]), "mirror": bool(cfg.get("mirror")), "residual": bool(cfg.get("residual")),
                  "eval_scale": cfg["eval_scale"], **stats}
        net = read_fnn4(args.out)  # round trip through the file reader (checksum, size, field order)
        assert np.array_equal(net["w1"], w1) and np.array_equal(net["l2w"], l2w) and np.array_equal(net["b_out"], b_out)
        print(json.dumps(report, indent=1))
    else:
        net = read_fnn4(args.net)
        fens = [l.split("|")[0].strip() for l in open(args.fens, encoding="utf-8") if l.strip()]
        eng = [tuple(int(x) for x in l.split()[:2]) for l in open(args.engine_out, encoding="utf-8") if l.strip()]
        if args.limit:
            fens, eng = fens[:args.limit], eng[:args.limit]
        if len(eng) != len(fens):
            raise SystemExit(f"parity: {len(fens)} FENs but {len(eng)} engine lines")
        ints, floats = [], []
        acc_max = 0
        for start in range(0, len(fens), 2000):
            chunk = fens[start:start + 2000]
            idx, pieces = features(chunk, net["king_map"], net["mirror"])
            cp, acc = int_forward(net, idx, pieces)
            acc_max = max(acc_max, int(np.abs(acc).max()))
            ints.append(cp)
            floats.append(float_forward(cfg, w1f, t, idx, pieces))
        ref = np.concatenate(ints)
        flt = np.concatenate(floats)
        eng = np.asarray(eng, np.int64)
        mism_scalar = int((eng[:, 0] != ref).sum())
        mism_avx2 = int((eng[:, 1] != ref).sum())
        gap = np.abs(ref - flt)
        report = {"positions": len(fens), "int_ref_vs_engine_scalar_mismatches": mism_scalar,
                  "int_ref_vs_engine_avx2_mismatches": mism_avx2, "max_abs_accumulator": acc_max,
                  "float_gap_cp": {"mean": float(gap.mean()), "p99": float(np.percentile(gap, 99)),
                                   "max": float(gap.max())},
                  "int_cp": {"mean_abs": float(np.abs(ref).mean()), "max_abs": int(np.abs(ref).max())},
                  "verdict": "PASS" if mism_scalar == 0 and mism_avx2 == 0 else "FAIL"}
        print(json.dumps(report, indent=1))
        if args.json:
            with open(args.json, "w", newline="\n") as f:
                json.dump(report, f, indent=1)
        sys.exit(0 if report["verdict"] == "PASS" else 1)
    if args.cmd == "export" and args.json:
        with open(args.json, "w", newline="\n") as f:
            json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
