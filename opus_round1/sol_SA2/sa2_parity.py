#!/usr/bin/env python3
"""S-A2 parity: the engine's NnueInt16 path vs an exact Python integer reference, and the float path vs a
float32 emulation of the engine's lane order, on "FEN | ..." lines; plus the float/int16 difference statistics.

  python -I -B sa2_parity.py --net nnue_weights.inc --fens fens_10k.txt --dump dump_avx2.tsv [--dump dump_scalar.tsv ...]
         --out parity.json

--dump files come from nnue_int16_dump.cpp built against the engine with the same net (one per build, e.g. the box
recipe = AVX2 kernels and -march=x86-64 = scalar kernels). Every dump must have one line per FEN.

Integer reference (the number format, same rounding as the engine; numpy int64 + IEEE double):
  A = b1 + sum w1[f] over the active features f = (rel*6 + type)*64 + sq' (rel = piece colour != perspective,
  sq' = sq ^ 56 for the black perspective); a = clamp(A, 0, 4096); q = (a*a + 1024) // 2048;
  T = q_stm . w2[:H] + q_opp . w2[H:]  (exact int64); logit = T / 2^25 + b2 / 4096  (double, in that order);
  cp = trunc(clamp(logit * 400 / 2.25, -30000, 30000))  (double: (logit * 400) / 2.25).
Float emulation (the OFF path; numpy float32, no FMA): acc = A / 4096 (exact while |A| < 2^24); a = min(max(acc, 0), 1);
  term = (a_s*a_s)*w2s + (a_o*a_o)*w2o with w2 = w2_int / 4096; 16 lane sums (lane j takes h % 16 == j, h ascending);
  out = b2/4096 + lane 0 + ... + lane 15; cp = trunc(clamp((out * 400) / 2.25)) in float32.
Also reported: the float64 forward (S21 style) vs the engine's float path (info only).
Acceptance (exit 0): every dump's int_cp == integer reference on all positions, its accumulator signatures equal the
reference's, its incremental-vs-fresh mismatch counts are 0, and its float_cp == float32 emulation on all positions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

PIECE_CODE = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def read_inc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def arr(name):
        m = re.search(name + r"\[(\d+)\]\s*=\s*\{([^}]*)\}", text, re.S)
        values = np.array([int(x) for x in m.group(2).replace("\n", " ").split(",") if x.strip()], np.int64)
        if len(values) != int(m.group(1)):
            raise ValueError(f"{path}: {name} length")
        return values

    w1, b1, w2 = arr("NnueW1"), arr("NnueB1"), arr("NnueW2")
    b2 = int(re.search(r"NnueB2\s*=\s*(-?\d+)", text).group(1))
    hidden = len(b1)
    if len(w1) != 768 * hidden or len(w2) != 2 * hidden:
        raise ValueError(f"{path}: not a Forge-768 net")
    for name, v in (("w1", w1), ("b1", b1), ("w2", w2), ("b2", np.array([b2]))):
        if np.abs(v).max() > 32767:
            raise ValueError(f"{path}: {name} outside int16")
    residual = re.search(r"#define FORGE_NNUE_RESIDUAL\s+(\d)", text)
    raw = path.read_bytes()
    return {"w1": w1.reshape(768, hidden), "b1": b1, "w2": w2, "b2": b2, "hidden": hidden,
            "residual": bool(int(residual.group(1))) if residual else False,
            "md5": hashlib.md5(raw).hexdigest(), "sha256": hashlib.sha256(raw).hexdigest()}


def read_fens(path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    fens, codes, stm = [], [], []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fen = line.split("|")[0].strip()
        fields = fen.split()
        row = np.zeros(64, np.int64)
        for rank_index, rank in enumerate(fields[0].split("/")):
            file = 0
            for ch in rank:
                if ch.isdigit():
                    file += int(ch)
                else:
                    row[(7 - rank_index) * 8 + file] = PIECE_CODE[ch]
                    file += 1
        fens.append(fen)
        codes.append(row)
        stm.append(0 if fields[1] == "w" else 1)
    return fens, np.asarray(codes), np.asarray(stm, np.int64)


def features(codes: np.ndarray, persp: np.ndarray) -> np.ndarray:
    sq = np.arange(64)[None, :]
    c = codes - 1
    color = np.floor_divide(c, 6)
    typ = c - color * 6
    bl = persp[:, None]
    rel = (color != bl).astype(np.int64)
    rsq = np.where(bl == 1, sq ^ 56, sq)
    f = (rel * 6 + typ) * 64 + rsq
    return np.where(codes > 0, f, 768)


def accumulators(net: dict, codes: np.ndarray, persp: np.ndarray) -> np.ndarray:
    padded = np.vstack([net["w1"], np.zeros((1, net["hidden"]), np.int64)])
    return padded[features(codes, persp)].sum(axis=1) + net["b1"][None, :]


def int_reference(net: dict, acc_s: np.ndarray, acc_o: np.ndarray) -> np.ndarray:
    h = net["hidden"]
    a = np.clip(acc_s, 0, 4096)
    b = np.clip(acc_o, 0, 4096)
    q_s = (a * a + 1024) // 2048
    q_o = (b * b + 1024) // 2048
    total = q_s @ net["w2"][:h] + q_o @ net["w2"][h:]          # exact int64 (|T| < 2^53)
    logit = total.astype(np.float64) / 33554432.0 + (net["b2"] / 4096.0)
    cp = logit * 400.0 / 2.25
    return np.trunc(np.clip(cp, -30000.0, 30000.0)).astype(np.int64)


def float_emulation(net: dict, acc_s: np.ndarray, acc_o: np.ndarray) -> np.ndarray:
    h = net["hidden"]
    f32 = np.float32
    if max(np.abs(acc_s).max(), np.abs(acc_o).max()) >= 1 << 24:
        raise ValueError("accumulator outside the exact float grid")
    scale = f32(4096.0)
    a = np.minimum(np.maximum(acc_s.astype(f32) / scale, f32(0.0)), f32(1.0))
    b = np.minimum(np.maximum(acc_o.astype(f32) / scale, f32(0.0)), f32(1.0))
    w2 = net["w2"].astype(f32) / scale
    term = (a * a) * w2[None, :h] + (b * b) * w2[None, h:]
    assert term.dtype == np.float32
    lanes = np.zeros((len(acc_s), 16), f32)
    for g in range(h // 16):
        lanes = lanes + term[:, g * 16:(g + 1) * 16]
    out = np.full(len(acc_s), f32(net["b2"]) / scale, f32)
    for j in range(16):
        out = out + lanes[:, j]
    cp = out * f32(400.0) / f32(2.25)
    assert cp.dtype == np.float32
    return np.trunc(np.clip(cp, f32(-30000.0), f32(30000.0))).astype(np.int64)


def float64_forward(net: dict, acc_s: np.ndarray, acc_o: np.ndarray) -> np.ndarray:
    h = net["hidden"]
    a = np.clip(acc_s / 4096.0, 0.0, 1.0) ** 2
    b = np.clip(acc_o / 4096.0, 0.0, 1.0) ** 2
    return (a @ net["w2"][:h] + b @ net["w2"][h:] + net["b2"]) / 4096.0 * 400.0 / 2.25


def signatures(acc: np.ndarray) -> np.ndarray:
    return acc @ np.arange(1, acc.shape[1] + 1, dtype=np.int64)


def read_dump(path: Path) -> dict:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if parts[1] == "BAD":
            raise ValueError(f"{path}: engine rejected FEN #{parts[0]}")
        rows.append([int(x) for x in parts])
    arr = np.asarray(rows, np.int64)
    return {"idx": arr[:, 0], "float": arr[:, 1], "int": arr[:, 2], "hce": arr[:, 3], "sigW": arr[:, 4], "sigB": arr[:, 5],
            "inc_int": arr[:, 6], "inc_float": arr[:, 7], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def sign_stats(x: np.ndarray, y: np.ndarray) -> dict:
    return {"strict_sign_flips": int(((x > 0) & (y < 0)).sum() + ((x < 0) & (y > 0)).sum()),
            "zero_vs_nonzero": int(((x == 0) != (y == 0)).sum())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--net", type=Path, required=True)
    ap.add_argument("--fens", type=Path, required=True)
    ap.add_argument("--dump", type=Path, action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        ap.error("--out must be a new file")
    net = read_inc(a.net)
    fens, codes, stm = read_fens(a.fens)
    n = len(fens)
    acc_s = accumulators(net, codes, stm)
    acc_o = accumulators(net, codes, 1 - stm)
    acc_w = np.where((stm == 0)[:, None], acc_s, acc_o)
    acc_b = np.where((stm == 0)[:, None], acc_o, acc_s)
    ref_int = int_reference(net, acc_s, acc_o)
    ref_float = float_emulation(net, acc_s, acc_o)
    py64 = float64_forward(net, acc_s, acc_o)
    lane_bound = int((np.abs(net["b1"]) + np.abs(net["w1"]).sum(axis=0)).max() + 4 * np.abs(net["w1"]).max())
    result = {"tool": "sa2_parity", "net": str(a.net), "net_md5": net["md5"], "net_sha256": net["sha256"],
              "hidden": net["hidden"], "residual": net["residual"], "fens": str(a.fens),
              "fens_sha256": hashlib.sha256(a.fens.read_bytes()).hexdigest(), "positions": n,
              "max_abs_accumulator": int(max(np.abs(acc_s).max(), np.abs(acc_o).max())),
              "lane_bound_768_plus_4_columns": lane_bound, "lane_bound_below_2^24": lane_bound < (1 << 24),
              "reference_float_vs_int": {
                  "max_abs_cp": int(np.abs(ref_float - ref_int).max()), "mean_abs_cp": float(np.abs(ref_float - ref_int).mean()),
                  "different": int((ref_float != ref_int).sum()), **sign_stats(ref_float, ref_int)},
              "dumps": []}
    ok = True
    for path in a.dump:
        d = read_dump(path)
        if len(d["idx"]) != n or not np.array_equal(d["idx"], np.arange(n)):
            raise SystemExit(f"{path}: {len(d['idx'])} lines for {n} FENs")
        diff = d["float"] - d["int"]
        full_float = d["hce"] + d["float"]
        full_int = d["hce"] + d["int"]
        row = {"dump": str(path), "sha256": d["sha256"],
               "int16_eq_integer_reference": int((d["int"] == ref_int).sum()),
               "int16_max_abs_diff_vs_reference": int(np.abs(d["int"] - ref_int).max()),
               "accumulator_signatures_eq_reference": int(((d["sigW"] == signatures(acc_w)) & (d["sigB"] == signatures(acc_b))).sum()),
               "float_eq_float32_emulation": int((d["float"] == ref_float).sum()),
               "float_max_abs_diff_vs_emulation": int(np.abs(d["float"] - ref_float).max()),
               "float_vs_float64_forward_max_abs": float(np.abs(d["float"] - py64).max()),
               "incremental_mismatch_plies_int16": int(d["inc_int"].sum()),
               "incremental_mismatch_plies_float": int(d["inc_float"].sum()),
               "float_vs_int16": {
                   "max_abs_cp": int(np.abs(diff).max()), "mean_abs_cp": float(np.abs(diff).mean()),
                   "p99_abs_cp": float(np.percentile(np.abs(diff), 99)), "different": int((diff != 0).sum()),
                   "histogram": {str(k): int(v) for k, v in zip(*np.unique(diff, return_counts=True))},
                   "raw_net": sign_stats(d["float"], d["int"]),
                   "full_static_hce_plus_net": sign_stats(full_float, full_int)}}
        good = (row["int16_eq_integer_reference"] == n and row["accumulator_signatures_eq_reference"] == n
                and row["float_eq_float32_emulation"] == n and row["incremental_mismatch_plies_int16"] == 0
                and row["incremental_mismatch_plies_float"] == 0)
        row["pass"] = bool(good)
        ok &= good
        result["dumps"].append(row)
        fv = row["float_vs_int16"]
        print(f"{path.name}: int16 == integer reference {row['int16_eq_integer_reference']}/{n}, accumulators "
              f"{row['accumulator_signatures_eq_reference']}/{n}, float == float32 emulation {row['float_eq_float32_emulation']}/{n}, "
              f"incremental mismatches int {row['incremental_mismatch_plies_int16']} float {row['incremental_mismatch_plies_float']}; "
              f"float vs int16: max {fv['max_abs_cp']} cp, mean {fv['mean_abs_cp']:.4f} cp, {fv['different']} differ, "
              f"raw sign flips {fv['raw_net']['strict_sign_flips']}, full-static sign flips {fv['full_static_hce_plus_net']['strict_sign_flips']}",
              flush=True)
    if len(a.dump) > 1:
        first = read_dump(a.dump[0])
        result["dumps_identical_int"] = all(np.array_equal(first["int"], read_dump(p)["int"]) for p in a.dump[1:])
        result["dumps_identical_float"] = all(np.array_equal(first["float"], read_dump(p)["float"]) for p in a.dump[1:])
        ok &= result["dumps_identical_int"] and result["dumps_identical_float"]
    result["pass"] = bool(ok)
    a.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("PARITY PASS" if ok else "PARITY FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
